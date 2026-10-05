'use client';
import {useEffect,useRef,useState} from 'react';
import 'leaflet/dist/leaflet.css';
import {authorizedFetch} from '@/lib/supabase-browser';
import {toast} from 'sonner';

type Scope={lat:number,lng:number,radius:number}|null;
const DEFAULT_RADIUS=500;
const fmt=(m:number)=>m>=1000?(m/1000).toFixed(1)+' km':Math.round(m)+' m';

export default function ScopeLocator({initialLat,initialLng,initialRadius}:{initialLat?:number,initialLng?:number,initialRadius?:number}){
 const box=useRef<HTMLDivElement>(null);
 const lib=useRef<any>(null),map=useRef<any>(null),marker=useRef<any>(null),circle=useRef<any>(null),observer=useRef<ResizeObserver|null>(null);
 const [ready,setReady]=useState(false),[busy,setBusy]=useState(false);
 const [scope,setScope]=useState<Scope>(typeof initialLat==='number'&&typeof initialLng==='number'?{lat:initialLat,lng:initialLng,radius:typeof initialRadius==='number'&&initialRadius>0?initialRadius:DEFAULT_RADIUS}:null);
 const latest=useRef<Scope>(scope);
 latest.current=scope;

 // Create the map once, on the client only.
 useEffect(()=>{
  let dead=false;
  (async()=>{
   const mod:any=await import('leaflet');
   const L:any=mod.default||mod;
   if(dead||!box.current)return;
   lib.current=L;
   const start=latest.current;
   const m=L.map(box.current,{scrollWheelZoom:false}).setView(start?[start.lat,start.lng]:[39.5,-40],start?14:2);
   L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',referrerPolicy:'strict-origin-when-cross-origin'}).addTo(m);
   m.on('click',(e:any)=>setScope({lat:e.latlng.lat,lng:e.latlng.lng,radius:latest.current?.radius||DEFAULT_RADIUS}));
   map.current=m;
   observer.current=new ResizeObserver(()=>m.invalidateSize());
   observer.current.observe(box.current);
   setTimeout(()=>{if(map.current)map.current.invalidateSize()},300);
   setReady(true);
  })();
  return()=>{
   dead=true;
   observer.current?.disconnect();observer.current=null;
   if(map.current){map.current.remove();map.current=null}
   marker.current=null;circle.current=null;lib.current=null;
  };
 },[]);

 // Draw or update the pin and radius circle whenever the scope changes.
 useEffect(()=>{
  const L=lib.current,m=map.current;
  if(!ready||!L||!m)return;
  if(!scope){
   if(marker.current){m.removeLayer(marker.current);marker.current=null}
   if(circle.current){m.removeLayer(circle.current);circle.current=null}
   return;
  }
  const pos:[number,number]=[scope.lat,scope.lng];
  if(!circle.current){circle.current=L.circle(pos,{radius:scope.radius,color:'#c32643',weight:2,fillOpacity:0.12}).addTo(m)}
  else{circle.current.setLatLng(pos);circle.current.setRadius(scope.radius)}
  if(!marker.current){
   marker.current=L.marker(pos,{draggable:true,icon:L.divIcon({className:'',html:'<div style="width:18px;height:18px;border-radius:50%;background:#c32643;border:3px solid #fff;box-shadow:0 0 0 1px #c32643"></div>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(m);
   marker.current.on('dragend',()=>{const p=marker.current.getLatLng();setScope({lat:p.lat,lng:p.lng,radius:latest.current?.radius||DEFAULT_RADIUS})});
  }else marker.current.setLatLng(pos);
  m.fitBounds(circle.current.getBounds(),{padding:[20,20],maxZoom:17});
 },[scope,ready]);

 async function locate(btn:HTMLButtonElement){
  const form=btn.form;
  if(!form)return;
  const fd=new FormData(form);
  const q=String(fd.get('address')||'').trim();
  const country=String(fd.get('addressCountry')||'USA');
  if(!q){toast.error('Enter an address first');return}
  setBusy(true);
  try{
   const r=await authorizedFetch('/api/geocode?q='+encodeURIComponent(q)+'&country='+encodeURIComponent(country));
   const d=await r.json();
   if(!r.ok)throw new Error(d.error);
   setScope({lat:d.lat,lng:d.lng,radius:latest.current?.radius||DEFAULT_RADIUS});
   toast.success('Address located');
  }catch(e){toast.error((e as Error).message)}
  finally{setBusy(false)}
 }

 return <div className="form">
  <p className="footnote">Coverage area (optional): locate the address, then drag the pin or click the map to fine-tune, and set the radius this contract covers.</p>
  <button type="button" className="secondary" disabled={busy} onClick={e=>locate(e.currentTarget)}>{busy?'Locating...':'Locate address on map'}</button>
  <div ref={box} style={{height:260,width:'100%',borderRadius:8,overflow:'hidden',border:'1px solid #e5e7eb',isolation:'isolate'}}/>
  {scope?<>
   <label>Scope radius: {fmt(scope.radius)}<input type="range" min={100} max={10000} step={50} value={Math.min(10000,Math.max(100,scope.radius))} onChange={e=>setScope({...scope,radius:Number(e.target.value)})}/></label>
   <input type="hidden" name="scopeLat" value={scope.lat.toFixed(6)}/>
   <input type="hidden" name="scopeLng" value={scope.lng.toFixed(6)}/>
   <input type="hidden" name="scopeRadius" value={Math.round(scope.radius)}/>
   <button type="button" className="text-button" onClick={()=>setScope(null)}>Clear scope area</button>
  </>:<p className="footnote">No scope area set.</p>}
 </div>;
}
