import fs from 'node:fs/promises';

export async function connect({signup=false}={}) {
  const env=Object.fromEntries((await fs.readFile(new URL('.env',import.meta.url),'utf8')).trim().split('\n').map(line=>{
    const i=line.indexOf('=');return [line.slice(0,i),line.slice(i+1)];
  }));
  const base='http://127.0.0.1:2283/api';
  const credentials={email:env.ADMIN_EMAIL,password:env.ADMIN_PASSWORD};
  if(signup){
    const r=await fetch(base+'/auth/admin-sign-up',json('POST',{...credentials,name:'Martin'}));
    if(!r.ok){
      // An existing administrator is not overwritten; login below must succeed.
      if(r.status!==400)throw Error(`Crear administrador: HTTP ${r.status}: ${(await r.text()).slice(0,300)}`);
    }
  }
  const login=await fetch(base+'/auth/login',json('POST',credentials));
  if(!login.ok)throw Error(`Login Immich: HTTP ${login.status}`);
  const {accessToken,userId}=await login.json();
  const request=async(endpoint,options={})=>{
    const r=await fetch(base+endpoint,{signal:AbortSignal.timeout(120000),...options,headers:{Authorization:`Bearer ${accessToken}`,...options.headers}});
    if(!r.ok)throw Error(`${endpoint}: HTTP ${r.status}: ${(await r.text()).slice(0,500)}`);
    return r;
  };
  const api=async(endpoint,options)=>{const r=await request(endpoint,options);return r.status===204?null:r.json();};
  return {api,request,userId};
}
export const json=(method,data)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
export async function saveJSON(file,data){await fs.writeFile(file+'.tmp',JSON.stringify(data,null,2),{mode:0o600});await fs.rename(file+'.tmp',file);}
