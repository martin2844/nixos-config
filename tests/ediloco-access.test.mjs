import assert from 'node:assert/strict';
import {once} from 'node:events';
import http from 'node:http';
import test from 'node:test';
import {createLocalAccess} from '../services/immich/acceso-local.mjs';

async function fixture(t,{rejectLogin=false}={}){
  let logins=0;
  const valid=new Set();
  const original=http.createServer(async(req,res)=>{
    if(req.url==='/api/auth/login'){
      logins++;
      if(rejectLogin){res.writeHead(401);res.end('upstream private error');return;}
      let body='';for await(const part of req)body+=part;
      assert.deepEqual(JSON.parse(body),{email:'test@local',password:'test-secret'});
      const token=`token-${logins}`;valid.add(token);
      res.writeHead(200,{'Set-Cookie':[
        `immich_access_token=${token}; Path=/; HttpOnly; SameSite=Lax`,
        'immich_is_authenticated=true; Path=/; SameSite=Lax',
        'immich_auth_type=password; Path=/; HttpOnly; SameSite=Lax',
      ]});res.end('{}');return;
    }
    const token=/immich_access_token=([^;]+)/.exec(req.headers.cookie??'')?.[1];
    if(!valid.has(token)){res.writeHead(401);res.end('Unauthorized');return;}
    if(req.url==='/bytes'){
      assert.equal(req.headers.range,'bytes=2-4');
      res.writeHead(206,{'Content-Range':'bytes 2-4/6','Content-Type':'application/octet-stream'});
      res.write(Buffer.from([2]));res.end(Buffer.from([3,4]));return;
    }
    if(req.url==='/post'){
      res.writeHead(201);req.pipe(res);return;
    }
    res.setHeader('Content-Type','application/json');
    res.end(JSON.stringify({user:'test-user',cookie:req.headers.cookie}));
  });
  original.on('upgrade',(req,socket)=>{
    t.after(()=>socket.destroy());
    if(!req.headers.cookie?.includes('immich_access_token=')){socket.destroy();return;}
    socket.write('HTTP/1.1 101 Switching Protocols\r\nConnection: Upgrade\r\nUpgrade: websocket\r\n\r\n');
    socket.on('data',chunk=>socket.write(chunk));
  });
  original.listen(0,'127.0.0.1');await once(original,'listening');
  const gateway=createLocalAccess({upstream:`http://127.0.0.1:${original.address().port}`,email:'test@local',password:'test-secret',hosts:['localhost:2283']});
  gateway.listen(0,'127.0.0.1');await once(gateway,'listening');
  t.after(()=>{gateway.closeAllConnections();gateway.close();original.closeAllConnections();original.close();});
  const url=`http://127.0.0.1:${gateway.address().port}`;
  const request=(path,opts={})=>new Promise((resolve,reject)=>{
    const req=http.request(url+path,{method:opts.method??'GET',headers:{Host:'localhost:2283',...opts.headers}},res=>{
      const chunks=[];res.on('data',chunk=>chunks.push(chunk));res.on('end',()=>{
        const headers=new Headers();
        for(let i=0;i<res.rawHeaders.length;i+=2)headers.append(res.rawHeaders[i],res.rawHeaders[i+1]);
        resolve(new Response(Buffer.concat(chunks),{status:res.statusCode,headers}));
      });
    });
    req.on('error',reject);req.end(opts.body);
  });
  return {request,gateway,valid,get logins(){return logins;}};
}

test('fresh browsers receive a real session, including concurrent requests',async t=>{
  const f=await fixture(t);
  const responses=await Promise.all(Array.from({length:4},()=>f.request('/api/users/me')));
  for(const r of responses){
    assert.equal(r.status,200);
    assert.equal((await r.json()).user,'test-user');
    assert.ok(r.headers.getSetCookie().some(c=>c.startsWith('immich_is_authenticated=true')));
    assert.ok(r.headers.getSetCookie().some(c=>c.includes('HttpOnly')));
  }
  assert.equal(f.logins,1);
});

test('expired sessions refresh on reads and preserve unrelated cookies',async t=>{
  const f=await fixture(t);
  const r=await f.request('/api/users/me',{headers:{Cookie:'immich_access_token=expired; theme=dark'}});
  assert.equal(r.status,200);
  const body=await r.json();
  assert.ok(body.cookie.includes('theme=dark'));
  assert.ok(!body.cookie.includes('expired'));
  assert.equal(f.logins,1);
});

test('uploads and range downloads pass through without changing their bytes',async t=>{
  const {request}=await fixture(t);
  const body=Buffer.from([0,1,2,255,128,13,10]);
  const uploaded=await request('/post',{method:'POST',body});
  assert.equal(uploaded.status,201);
  assert.deepEqual(Buffer.from(await uploaded.arrayBuffer()),body);
  const range=await request('/bytes',{headers:{Range:'bytes=2-4'}});
  assert.equal(range.status,206);
  assert.equal(range.headers.get('content-range'),'bytes 2-4/6');
  assert.deepEqual(Buffer.from(await range.arrayBuffer()),Buffer.from([2,3,4]));
});

test('foreign hosts and origins cannot cause an automatic login',async t=>{
  const f=await fixture(t);
  for(const headers of [{Host:'evil.example'},{Origin:'https://evil.example'},{Origin:'http://localhost:8010'},{'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'cors'}]){
    assert.equal((await f.request('/api/users/me',{headers})).status,403);
  }
  assert.equal(f.logins,0);
});

test('login navigation goes directly to photos',async t=>{
  const {request}=await fixture(t);
  const r=await request('/auth/login?continue=%2Fphotos',{redirect:'manual'});
  assert.equal(r.status,302);
  assert.equal(r.headers.get('location'),'/photos');
  assert.ok(r.headers.getSetCookie().length>=2);
});

test('logout returns a full local navigation so the client reloads its auth state',async t=>{
  const {request}=await fixture(t);
  const r=await request('/api/auth/logout',{method:'POST'});
  assert.equal(r.status,200);
  assert.equal((await r.json()).redirectUri,'http://localhost:2283/photos');
});

test('a login failure reports unavailability without exposing private details',async t=>{
  const {request}=await fixture(t,{rejectLogin:true});
  const r=await request('/api/users/me');
  assert.equal(r.status,503);
  const message=await r.text();
  assert.ok(!message.includes('test-secret'));
  assert.ok(!message.includes('private error'));
});

test('WebSocket upgrade and bidirectional bytes survive the gateway',async t=>{
  const f=await fixture(t);
  const req=http.request({host:'127.0.0.1',port:f.gateway.address().port,path:'/socket.io/',headers:{Host:'localhost:2283',Connection:'Upgrade',Upgrade:'websocket',Origin:'http://localhost:2283'}});
  const upgraded=once(req,'upgrade',{signal:AbortSignal.timeout(5000)});
  req.end();
  const [response,socket]=await upgraded;
  assert.equal(response.statusCode,101);
  const echoed=once(socket,'data',{signal:AbortSignal.timeout(5000)});
  socket.write('local-websocket');
  assert.equal((await echoed)[0].toString(),'local-websocket');
  socket.destroy();
});
