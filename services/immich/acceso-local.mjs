// Loopback-only browser access. Immich retains its normal private account;
// this gateway obtains ordinary session cookies without a login form.
import http from 'node:http';
import {pathToFileURL} from 'node:url';

const authNames=new Set(['immich_access_token','immich_auth_type','immich_is_authenticated']);
const hasToken=headers=>headers.authorization || /(?:^|;\s*)immich_access_token=[^;]+/.test(headers.cookie??'');
const combineCookies=(original,session)=>[
  ...(original??'').split(';').map(s=>s.trim()).filter(s=>s && !authNames.has(s.split('=')[0])),
  session.cookie,
].join('; ');

export function createLocalAccess({upstream,email,password,hosts=['localhost:2283','127.0.0.1:2283']}) {
  const target=new URL(upstream);
  if(target.protocol!=='http:' || !email || !password)throw Error('Falta la configuración del acceso local.');
  let cached;
  let pending;
  const session=async()=>{
    if(cached && cached.until>Date.now())return cached;
    if(!pending)pending=(async()=>{
      const response=await fetch(new URL('/api/auth/login',target),{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({email,password}),signal:AbortSignal.timeout(30000),
      });
      if(!response.ok)throw Error('No se pudo iniciar la sesión local de Immich.');
      const cookies=response.headers.getSetCookie();
      await response.arrayBuffer();
      if(!cookies.some(c=>c.startsWith('immich_access_token=')))throw Error('Immich no devolvió una sesión.');
      cached={cookies,cookie:cookies.map(c=>c.split(';')[0]).join('; '),until:Date.now()+30*60*1000};
      return cached;
    })().finally(()=>{pending=undefined;});
    return pending;
  };
  const allowed=req=>{
    if(!hosts.includes(req.headers.host))return false;
    if(!req.url?.startsWith('/') || req.url.startsWith('//'))return false;
    if(req.headers.origin && req.headers.origin!==`http://${req.headers.host}`)return false;
    return req.headers['sec-fetch-site']!=='cross-site' || (req.method==='GET' && req.headers['sec-fetch-mode']==='navigate');
  };
  const upstreamHeaders=(req,login)=>({
    ...req.headers,
    ...(login?{cookie:combineCookies(req.headers.cookie,login),authorization:undefined}:{}),
    'x-forwarded-proto':'http',
    'x-forwarded-host':req.headers.host,
    'x-forwarded-for':req.socket.remoteAddress,
  });
  const options=(req,login)=>({
    hostname:target.hostname,port:target.port,method:req.method,path:req.url,
    headers:Object.fromEntries(Object.entries(upstreamHeaders(req,login)).filter(([,v])=>v!==undefined)),
  });
  const server=http.createServer(async(req,res)=>{
    if(!allowed(req)){res.writeHead(403);res.end('Acceso local solamente.');return;}
    try {
      if(req.url==='/_local/health'){
        const ping=await fetch(new URL('/api/server/ping',target),{signal:AbortSignal.timeout(3000)});
        res.writeHead(ping.ok?200:503);res.end();return;
      }
      if(req.method==='POST' && req.url==='/api/auth/logout'){
        // Immich's client uses a full navigation for an absolute redirect.
        // Reloading renews its auth state in this intentionally automatic mode.
        res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});
        res.end(JSON.stringify({redirectUri:`http://${req.headers.host}/photos`}));return;
      }
      if(req.method==='GET' && /^\/auth\/(login|change-password)(?:[/?]|$)/.test(req.url)){
        const login=await session();
        res.writeHead(302,{'Location':'/photos','Set-Cookie':login.cookies,'Cache-Control':'no-store'});
        res.end();return;
      }
      // Keep normal API authentication available to the local indexing tools.
      const isAuthApi=req.url.startsWith('/api/auth/');
      let login=!hasToken(req.headers) && !isAuthApi?await session():undefined;
      const forward=(retry=false)=>{
        const proxy=http.request(options(req,login),async response=>{
          if(response.statusCode===401 && !isAuthApi && !retry && ['GET','HEAD'].includes(req.method)){
            response.resume();
            try {
              if(!login || login===cached)cached=undefined;
              login=await session();forward(true);
            } catch {res.writeHead(503);res.end('Immich todavía no está disponible.');}
            return;
          }
          const headers={...response.headers};
          if(login){
            headers['set-cookie']=[...(headers['set-cookie']??[]),...login.cookies];
            headers['cache-control']='no-store';
          }
          res.writeHead(response.statusCode??502,headers);
          response.pipe(res);
        });
        proxy.on('error',()=>{if(!res.headersSent)res.writeHead(503);res.end('Immich todavía no está disponible.');});
        res.once('close',()=>proxy.destroy());
        if(retry)proxy.end();else req.pipe(proxy);
      };
      forward();
    } catch {res.writeHead(503);res.end('Immich todavía no está disponible.');}
  });
  server.on('upgrade',async(req,socket,head)=>{
    if(!allowed(req)){socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n');return;}
    try {
      const login=!hasToken(req.headers)?await session():undefined;
      const proxy=http.request(options(req,login));
      proxy.on('upgrade',(response,remote,remoteHead)=>{
        const headers=response.rawHeaders;
        let start=`HTTP/1.1 ${response.statusCode} ${response.statusMessage}\r\n`;
        for(let i=0;i<headers.length;i+=2)start+=`${headers[i]}: ${headers[i+1]}\r\n`;
        socket.write(start+'\r\n');
        if(remoteHead.length)socket.write(remoteHead);
        if(head.length)remote.write(head);
        socket.on('error',()=>remote.destroy());remote.on('error',()=>socket.destroy());
        socket.on('close',()=>remote.destroy());remote.on('close',()=>socket.destroy());
        remote.pipe(socket);socket.pipe(remote);
      });
      proxy.on('response',response=>{response.resume();socket.destroy();});
      proxy.on('error',()=>socket.destroy());
      proxy.end();
    } catch {socket.destroy();}
  });
  return server;
}

if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
  createLocalAccess({upstream:process.env.UPSTREAM_URL,email:process.env.ADMIN_EMAIL,password:process.env.ADMIN_PASSWORD})
    .listen(2283,'0.0.0.0',()=>console.log('Acceso local a Immich preparado.'));
}
