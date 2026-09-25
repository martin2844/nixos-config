import fs from 'node:fs/promises';

export async function connect() {
  const env=Object.fromEntries((await fs.readFile(new URL('.env',import.meta.url),'utf8')).trim().split('\n').map(line=>{
    const i=line.indexOf('=');return [line.slice(0,i),line.slice(i+1)];
  }));
  const base='http://127.0.0.1:8010';
  const login=await fetch(base+'/api/token/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'martin',password:env.ADMIN_PASSWORD})});
  if(!login.ok)throw Error(`Login HTTP ${login.status}`);
  const {token}=await login.json();
  const request=async(endpoint,options={})=>{
    const res=await fetch(base+endpoint,{...options,headers:{Authorization:`Token ${token}`,...options.headers}});
    if(!res.ok)throw Error(`${endpoint}: HTTP ${res.status}: ${(await res.text()).slice(0,500)}`);
    return res;
  };
  const api=async(endpoint,options)=> (await request(endpoint,options)).json();
  const all=async(endpoint)=>{const result=[];let next=endpoint;while(next){const page=await api(next);if(Array.isArray(page))return page;result.push(...page.results);next=page.next?new URL(page.next).pathname+new URL(page.next).search:null;}return result;};
  return {api,all,request};
}
export const json=(method,data)=>({method,headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
export async function saveJSON(file,data){await fs.writeFile(file+'.tmp',JSON.stringify(data,null,2),{mode:0o600});await fs.rename(file+'.tmp',file);}
