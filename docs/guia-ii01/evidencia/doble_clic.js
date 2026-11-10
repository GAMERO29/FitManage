// Guía II-01 · R14: doble clic en «Anular pago» del aplicativo real (a358229). Uso: node doble_clic.js
const { chromium } = require('playwright');
const URL='http://127.0.0.1:8765', DOC='1090000011', CLAVE='clave-de-demo-local';
async function api(r,{metodo='GET',token,cuerpo,clave}={}){const h={'Content-Type':'application/json'};if(token)h.Authorization='Bearer '+token;if(clave)h['Idempotency-Key']=clave;const x=await fetch(URL+'/api/v1'+r,{method:metodo,headers:h,body:cuerpo?JSON.stringify(cuerpo):undefined});let j=null;try{j=await x.json()}catch{};return{estado:x.status,json:j};}
(async()=>{
 const admin=(await api('/auth/token',{metodo:'POST',cuerpo:{correo:'admin@demo.local',contrasena:CLAVE}})).json.tokenAcceso;
 const planes=(await api('/planes',{token:admin})).json; const m=planes.find(p=>p.nombre==='Mensual');
 await api('/socios',{metodo:'POST',token:admin,cuerpo:{tipoDocumento:'CC',numeroDocumento:DOC,nombres:'Ana',apellidos:'Prueba Demo',telefono:'3001234567',autorizaTratamientoDatos:true}});
 const pg=await api('/pagos',{metodo:'POST',token:admin,clave:crypto.randomUUID(),cuerpo:{tipoDocumento:'CC',numeroDocumento:DOC,planId:m.id,medio:'EFECTIVO'}});
 console.log('pago',pg.estado);
 const b=await chromium.launch(); const p=await (await b.newContext({viewport:{width:1366,height:860}})).newPage();
 const peticiones=[]; p.on('request',r=>{if(r.method()==='PATCH')peticiones.push(r.url())});
 await p.goto(URL+'/'); await p.fill('#correo','admin@demo.local'); await p.fill('#clave',CLAVE); await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
 await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b',DOC); await p.press('#doc-b','Enter'); await p.waitForSelector('h2:has-text("Historial de pagos")');
 await p.click('button:has-text("Anular último pago")'); await p.fill('#motivo','Doble clic en anular');
 await p.dblclick('button:has-text("Anular pago")'); await p.waitForTimeout(2500);
 console.log('PATCH enviados:',peticiones.length);
 console.log('aviso ok:', await p.$eval('.aviso', e=>e.textContent.trim()).catch(()=>'-'));
 console.log('errores visibles:', await p.$$eval('.msg-error, .aviso.a-error', es=>es.map(e=>e.textContent.trim())));
 await p.screenshot({path:'./r14-doble-clic-anular.png',fullPage:true});
 await b.close();})();
