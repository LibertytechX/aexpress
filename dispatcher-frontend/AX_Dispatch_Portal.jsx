import { useState, useRef, useEffect } from "react";
import { AuthAPI, RidersAPI, OrdersAPI, MerchantsAPI, VehiclesAPI } from "./src/api.js";

// ─── ICONS ──────────────────────────────────────────────────────
const I = {
  dashboard: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>,
  orders: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 16h6"/><path d="M19 13v6"/><path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"/><path d="m7.5 4.27 9 5.15"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/></svg>,
  riders: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="15" cy="5" r="1"/><path d="M12 17.5V14l-3-3 4-3 2 3h2"/></svg>,
  merchants: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9Z"/><path d="m3 9 2.45-4.9A2 2 0 0 1 7.24 3h9.52a2 2 0 0 1 1.8 1.1L21 9"/><path d="M12 3v6"/></svg>,
  customers: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  messaging: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>,
  settings: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>,
  search: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
  phone: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>,
  edit: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>,
  print: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>,
  download: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
  plus: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>,
  back: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>,
  send: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>,
  copy: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
  x: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  check: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>,
};

const S = {
  navy: "#1B2A4A", navyLight: "#243656", bg: "#f5f7fa", card: "#FFFFFF", border: "#e2e8f0", borderLight: "#f1f5f9",
  text: "#1B2A4A", textDim: "#64748b", textMuted: "#94a3b8",
  gold: "#E8A838", goldLight: "#F5C563", goldPale: "#FFF8EC",
  green: "#16a34a", greenBg: "#dcfce7",
  red: "#dc2626", redBg: "#fee2e2",
  blue: "#2563eb", blueBg: "#dbeafe",
  purple: "#8B5CF6", purpleBg: "rgba(139,92,246,0.08)",
  yellow: "#F59E0B", yellowBg: "rgba(245,158,11,0.08)",
};
// ─── LAGOS MAP COMPONENT (Enhanced with zones & routes) ─────────
function LagosMap({ orders, riders, highlightOrder, small, showZones }) {
  const [hoverPin, setHoverPin] = useState(null);
  const [mapView, setMapView] = useState("live"); // live | zones | heatmap
  const h = small ? 140 : 320;

  // Lagos zones with real approximate positions
  const zones = [
    {id:"mainland-core",label:"Mainland Core",x:32,y:32,w:22,h:20,color:"rgba(59,130,246,0.08)",areas:"Ikeja · Maryland · Yaba · Surulere"},
    {id:"island",label:"Island",x:50,y:48,w:22,h:22,color:"rgba(232,168,56,0.08)",areas:"V.I. · Ikoyi · Lekki Phase 1"},
    {id:"lekki-ajah",label:"Lekki-Ajah",x:74,y:45,w:20,h:18,color:"rgba(139,92,246,0.08)",areas:"Lekki · Ajah · Sangotedo · VGC"},
    {id:"apapa",label:"Apapa/Wharf",x:16,y:55,w:16,h:16,color:"rgba(239,68,68,0.06)",areas:"Apapa · Tin Can · Wharf"},
    {id:"outer-north",label:"Outer Lagos",x:10,y:15,w:24,h:18,color:"rgba(16,185,129,0.06)",areas:"Ikorodu · Agbara · Ojo · Badagry"},
  ];

  // Order pins with pickup→dropoff routes
  const pins = [
    {id:"AX-6158260",px:36,py:40,dx:55,dy:52,label:"Yaba→VI",color:S.gold,status:"In Transit",rider:"Musa K."},
    {id:"AX-6158261",px:38,py:48,dx:56,dy:56,label:"Surulere→VI",color:S.purple,status:"Picked Up",rider:"Chinedu O."},
    {id:"AX-6158262",px:30,py:28,dx:78,dy:50,label:"Ikeja→Lekki",color:S.yellow,status:"Pending",rider:null},
    {id:"AX-6158263",px:26,py:42,dx:34,dy:30,label:"Mushin→Ikeja",color:S.blue,status:"Assigned",rider:"Kola A."},
    {id:"AX-6158258",px:55,py:50,dx:72,dy:50,label:"VI→Lekki Ph1",color:S.gold,status:"Assigned",rider:"Ahmed B."},
    {id:"AX-6158257",px:36,py:40,dx:54,dy:52,label:"Yaba→VI",color:S.green,status:"Delivered",rider:"Musa K."},
    {id:"AX-6158255",px:72,py:48,dx:76,dy:52,label:"Lekki→Lekki",color:S.green,status:"Delivered",rider:"Emeka N."},
  ];
  const riderDots = [
    {id:"R001",x:48,y:46,name:"Musa K.",status:"on_delivery",vehicle:"🏍️"},
    {id:"R002",x:58,y:50,name:"Ahmed B.",status:"on_delivery",vehicle:"🏍️"},
    {id:"R003",x:52,y:52,name:"Chinedu O.",status:"on_delivery",vehicle:"🚗"},
    {id:"R005",x:28,y:38,name:"Ibrahim S.",status:"online",vehicle:"🏍️"},
    {id:"R006",x:30,y:36,name:"Kola A.",status:"on_delivery",vehicle:"🚗"},
    {id:"R007",x:70,y:44,name:"Emeka N.",status:"online",vehicle:"🏍️"},
  ];

  const activeOrders = pins.filter(p => !["Delivered","Cancelled","Failed"].includes(p.status));
  const displayPins = highlightOrder ? pins.filter(p=>p.id===highlightOrder) : (mapView==="live"?activeOrders:pins);

  return (
    <div style={{position:"relative",width:"100%",height:h,borderRadius:14,overflow:"hidden",border:`1px solid ${S.border}`,background:"#EEF2F7"}}>
      {/* Background map layers */}
      <svg width="100%" height="100%" style={{position:"absolute",top:0,left:0}} viewBox="0 0 100 100" preserveAspectRatio="none">
        {/* Lagos Lagoon */}
        <path d="M0,68 Q12,62 25,65 Q38,68 45,63 Q52,58 58,62 Q65,66 72,63 Q80,60 88,64 Q94,67 100,65 L100,78 Q88,74 75,77 Q62,80 50,76 Q38,72 25,75 Q12,78 0,75 Z" fill="rgba(59,130,246,0.12)"/>
        {/* Atlantic Ocean */}
        <path d="M0,82 Q25,78 50,82 Q75,86 100,80 L100,100 L0,100 Z" fill="rgba(59,130,246,0.18)"/>
        {/* Five Cowrie Creek */}
        <path d="M48,45 Q50,48 52,52 Q54,56 52,60 Q50,64 48,68" fill="none" stroke="rgba(59,130,246,0.15)" strokeWidth="1.2"/>
        {/* Third Mainland Bridge */}
        <line x1="34" y1="38" x2="52" y2="55" stroke="rgba(232,168,56,0.35)" strokeWidth="0.8" strokeDasharray="2,1"/>
        {/* Carter Bridge */}
        <line x1="28" y1="52" x2="42" y2="58" stroke="rgba(232,168,56,0.25)" strokeWidth="0.6" strokeDasharray="2,1"/>
        {/* Lekki-Ikoyi Link Bridge */}
        <line x1="58" y1="52" x2="66" y2="48" stroke="rgba(232,168,56,0.25)" strokeWidth="0.6" strokeDasharray="2,1"/>
        {/* Major roads */}
        <line x1="8" y1="35" x2="42" y2="35" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6"/>
        <line x1="30" y1="15" x2="30" y2="55" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6"/>
        <line x1="50" y1="50" x2="95" y2="50" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6"/>
        <line x1="30" y1="35" x2="50" y2="50" stroke="rgba(0,0,0,0.04)" strokeWidth="0.5"/>
        {/* Express road */}
        <path d="M10,30 Q20,28 30,28 Q45,28 55,35 Q65,42 75,45 Q85,48 95,47" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="0.7"/>
      </svg>

      {/* Zone overlays */}
      {(mapView==="zones"||showZones) && zones.map(z=>(
        <div key={z.id} style={{position:"absolute",left:`${z.x}%`,top:`${z.y}%`,width:`${z.w}%`,height:`${z.h}%`,background:z.color,border:"1px dashed rgba(0,0,0,0.12)",borderRadius:8,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",zIndex:1}}>
          <div style={{fontSize:7,fontWeight:800,color:S.navy,opacity:0.5,textTransform:"uppercase",letterSpacing:"0.5px"}}>{z.label}</div>
          <div style={{fontSize:6,color:S.textMuted,opacity:0.6,textAlign:"center"}}>{z.areas}</div>
        </div>
      ))}

      {/* Area labels (when no zones) */}
      {mapView!=="zones"&&!showZones&&!small && <>
        <div style={{position:"absolute",left:"6%",top:"18%",fontSize:8,color:"rgba(27,42,74,0.2)",fontWeight:800,letterSpacing:"1px"}}>IKORODU</div>
        <div style={{position:"absolute",left:"26%",top:"22%",fontSize:9,color:"rgba(27,42,74,0.3)",fontWeight:800,letterSpacing:"1px"}}>IKEJA</div>
        <div style={{position:"absolute",left:"38%",top:"32%",fontSize:8,color:"rgba(27,42,74,0.25)",fontWeight:700}}>MARYLAND</div>
        <div style={{position:"absolute",left:"32%",top:"42%",fontSize:8,color:"rgba(27,42,74,0.2)",fontWeight:700}}>YABA</div>
        <div style={{position:"absolute",left:"14%",top:"50%",fontSize:8,color:"rgba(27,42,74,0.2)",fontWeight:700}}>APAPA</div>
        <div style={{position:"absolute",left:"32%",top:"50%",fontSize:8,color:"rgba(27,42,74,0.2)",fontWeight:700}}>SURULERE</div>
        <div style={{position:"absolute",left:"50%",top:"44%",fontSize:9,color:"rgba(232,168,56,0.5)",fontWeight:800,letterSpacing:"1px"}}>V.I.</div>
        <div style={{position:"absolute",left:"56%",top:"55%",fontSize:8,color:"rgba(27,42,74,0.25)",fontWeight:700}}>IKOYI</div>
        <div style={{position:"absolute",left:"68%",top:"40%",fontSize:9,color:"rgba(139,92,246,0.4)",fontWeight:800,letterSpacing:"1px"}}>LEKKI</div>
        <div style={{position:"absolute",left:"82%",top:"48%",fontSize:8,color:"rgba(27,42,74,0.2)",fontWeight:700}}>AJAH</div>
      </>}

      {/* Route lines (pickup → current position for active, or pickup → dropoff) */}
      <svg width="100%" height="100%" style={{position:"absolute",top:0,left:0,pointerEvents:"none",zIndex:4}} viewBox="0 0 100 100" preserveAspectRatio="none">
        {displayPins.filter(p=>!["Delivered","Cancelled","Failed"].includes(p.status)).map(p=>(
          <g key={p.id+"route"}>
            <line x1={p.px} y1={p.py} x2={p.dx} y2={p.dy} stroke={p.color} strokeWidth={highlightOrder===p.id?"0.8":"0.4"} strokeDasharray="2,2" opacity={highlightOrder===p.id?0.8:0.4}/>
            {/* Pickup dot */}
            <circle cx={p.px} cy={p.py} r={highlightOrder===p.id?1.5:1} fill="#fff" stroke={p.color} strokeWidth="0.5"/>
            {/* Dropoff dot */}
            <circle cx={p.dx} cy={p.dy} r={highlightOrder===p.id?1.5:1} fill={p.color} stroke="#fff" strokeWidth="0.4"/>
          </g>
        ))}
      </svg>

      {/* Order pins */}
      {displayPins.map(p => {
        const isH = highlightOrder===p.id || hoverPin===p.id;
        const cx = p.status==="Delivered"?p.dx: p.status==="Pending"?p.px: (p.px+p.dx)/2;
        const cy = p.status==="Delivered"?p.dy: p.status==="Pending"?p.py: (p.py+p.dy)/2;
        return (
          <div key={p.id} onMouseEnter={()=>setHoverPin(p.id)} onMouseLeave={()=>setHoverPin(null)}
            style={{position:"absolute",left:`${cx}%`,top:`${cy}%`,transform:"translate(-50%,-100%)",zIndex:isH?15:5,cursor:"pointer",transition:"transform 0.15s"}}>
            <div style={{width:isH?16:10,height:isH?16:10,borderRadius:"50% 50% 50% 0",transform:"rotate(-45deg)",background:p.color,border:"2px solid #fff",boxShadow:`0 2px 8px ${p.color}50`,transition:"all 0.15s"}}/>
            {isH && (
              <div style={{position:"absolute",top:-40,left:"50%",transform:"translateX(-50%)",background:"#fff",padding:"4px 8px",borderRadius:6,boxShadow:"0 2px 12px rgba(0,0,0,0.15)",whiteSpace:"nowrap",zIndex:20,border:`1px solid ${S.border}`}}>
                <div style={{fontSize:9,fontWeight:800,color:S.navy}}>{p.id.slice(-7)}</div>
                <div style={{fontSize:8,color:p.color,fontWeight:700}}>{p.label}</div>
                {p.rider && <div style={{fontSize:7,color:S.textMuted}}>🏍️ {p.rider}</div>}
              </div>
            )}
            {!small && !isH && <div style={{position:"absolute",top:-14,left:"50%",transform:"translateX(-50%)",fontSize:7,fontWeight:700,color:S.navy,whiteSpace:"nowrap",background:"rgba(255,255,255,0.9)",padding:"1px 4px",borderRadius:3}}>{p.id.slice(-3)}</div>}
          </div>
        );
      })}

      {/* Rider dots */}
      {!highlightOrder && riderDots.map(r => (
        <div key={r.id} style={{position:"absolute",left:`${r.x}%`,top:`${r.y+3}%`,zIndex:6}}>
          <div style={{position:"relative"}}>
            <div style={{width:10,height:10,borderRadius:"50%",background:r.status==="online"?S.green:S.gold,border:"2px solid #fff",boxShadow:"0 1px 6px rgba(0,0,0,0.2)"}}/>
            {r.status==="online" && <div style={{position:"absolute",top:-1,left:-1,width:12,height:12,borderRadius:"50%",border:`2px solid ${S.green}`,animation:"pulse 2s infinite",opacity:0.4}}/>}
            {!small && <div style={{position:"absolute",top:12,left:"50%",transform:"translateX(-50%)",fontSize:7,fontWeight:600,color:S.navy,whiteSpace:"nowrap",background:"rgba(255,255,255,0.85)",padding:"1px 4px",borderRadius:3}}>{r.vehicle} {r.name}</div>}
          </div>
        </div>
      ))}

      {/* Bridge labels */}
      {!small && <>
        <div style={{position:"absolute",left:"40%",top:"45%",fontSize:6,color:"rgba(232,168,56,0.6)",fontWeight:700,transform:"rotate(-35deg)",whiteSpace:"nowrap"}}>3rd Mainland Bridge</div>
        <div style={{position:"absolute",left:"60%",top:"49%",fontSize:6,color:"rgba(232,168,56,0.5)",fontWeight:600,whiteSpace:"nowrap"}}>Lekki-Ikoyi Bridge</div>
      </>}

      {/* Map controls */}
      {!small && (
        <div style={{position:"absolute",top:8,right:8,display:"flex",gap:4,zIndex:20}}>
          {[{id:"live",label:"Live",icon:"📡"},{id:"zones",label:"Zones",icon:"🗺️"},{id:"heatmap",label:"Heat",icon:"🔥"}].map(v=>(
            <button key={v.id} onClick={()=>setMapView(v.id)} style={{
              padding:"4px 8px",borderRadius:6,border:`1px solid ${mapView===v.id?S.gold:S.border}`,
              background:mapView===v.id?"rgba(232,168,56,0.12)":"rgba(255,255,255,0.95)",
              cursor:"pointer",fontSize:8,fontWeight:700,color:mapView===v.id?S.gold:S.textMuted,
              display:"flex",alignItems:"center",gap:3,fontFamily:"inherit",
            }}>{v.icon} {v.label}</button>
          ))}
        </div>
      )}

      {/* Legend */}
      <div style={{position:"absolute",bottom:8,right:8,display:"flex",gap:8,background:"rgba(255,255,255,0.95)",padding:"5px 10px",borderRadius:8,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",zIndex:10}}>
        <span style={{fontSize:8,color:S.textMuted,display:"flex",alignItems:"center",gap:3}}><span style={{width:6,height:6,borderRadius:"50%",background:S.gold}}/> Active</span>
        <span style={{fontSize:8,color:S.textMuted,display:"flex",alignItems:"center",gap:3}}><span style={{width:6,height:6,borderRadius:"50%",background:S.green}}/> Rider</span>
        <span style={{fontSize:8,color:S.textMuted,display:"flex",alignItems:"center",gap:3}}><span style={{width:6,height:6,borderRadius:"50% 50% 50% 0",transform:"rotate(-45deg)",background:S.yellow}}/> Pending</span>
        <span style={{fontSize:8,color:S.textMuted,display:"flex",alignItems:"center",gap:3}}><span style={{width:6,height:6,borderRadius:"50% 50% 50% 0",transform:"rotate(-45deg)",background:S.purple}}/> In Progress</span>
      </div>

      {/* Live stats overlay */}
      {!small && mapView==="live" && (
        <div style={{position:"absolute",bottom:8,left:8,background:"rgba(27,42,74,0.9)",padding:"6px 12px",borderRadius:8,zIndex:10}}>
          <div style={{display:"flex",gap:14}}>
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:14,fontWeight:800,color:S.gold,fontFamily:"'Space Mono',monospace"}}>{activeOrders.length}</div>
              <div style={{fontSize:7,color:"rgba(255,255,255,0.5)",fontWeight:600}}>ACTIVE</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:14,fontWeight:800,color:S.green,fontFamily:"'Space Mono',monospace"}}>{riderDots.filter(r=>r.status==="online").length}</div>
              <div style={{fontSize:7,color:"rgba(255,255,255,0.5)",fontWeight:600}}>ONLINE</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div style={{fontSize:14,fontWeight:800,color:"#fff",fontFamily:"'Space Mono',monospace"}}>{riderDots.filter(r=>r.status==="on_delivery").length}</div>
              <div style={{fontSize:7,color:"rgba(255,255,255,0.5)",fontWeight:600}}>DELIVERING</div>
            </div>
          </div>
        </div>
      )}

      {/* Heatmap overlay */}
      {mapView==="heatmap" && !small && (
        <svg width="100%" height="100%" style={{position:"absolute",top:0,left:0,pointerEvents:"none",zIndex:3}} viewBox="0 0 100 100" preserveAspectRatio="none">
          <defs>
            <radialGradient id="heat1"><stop offset="0%" stopColor="rgba(239,68,68,0.4)"/><stop offset="100%" stopColor="rgba(239,68,68,0)"/></radialGradient>
            <radialGradient id="heat2"><stop offset="0%" stopColor="rgba(245,158,11,0.35)"/><stop offset="100%" stopColor="rgba(245,158,11,0)"/></radialGradient>
            <radialGradient id="heat3"><stop offset="0%" stopColor="rgba(16,185,129,0.25)"/><stop offset="100%" stopColor="rgba(16,185,129,0)"/></radialGradient>
          </defs>
          <circle cx="53" cy="50" r="15" fill="url(#heat1)"/>
          <circle cx="32" cy="35" r="12" fill="url(#heat2)"/>
          <circle cx="72" cy="48" r="14" fill="url(#heat2)"/>
          <circle cx="20" cy="50" r="8" fill="url(#heat3)"/>
          <circle cx="85" cy="50" r="10" fill="url(#heat3)"/>
        </svg>
      )}

      {/* Pulse animation */}
      <style>{`@keyframes pulse { 0%{transform:scale(1);opacity:0.4} 50%{transform:scale(1.8);opacity:0} 100%{transform:scale(1);opacity:0} }`}</style>
    </div>
  );
}
const STS = { Pending:{bg:S.yellowBg,text:S.yellow}, Assigned:{bg:S.blueBg,text:S.blue}, "Picked Up":{bg:S.purpleBg,text:S.purple}, "In Transit":{bg:"rgba(232,168,56,0.1)",text:S.gold}, Delivered:{bg:S.greenBg,text:S.green}, Cancelled:{bg:S.redBg,text:S.red}, Failed:{bg:S.redBg,text:"#F87171"} };

// ─── DELIVERY ROUTE MAP (Google Maps) ───────────────────────────
function DeliveryRouteMap({ order, rider }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const directionsRendererRef = useRef(null);
  const [mapStatus, setMapStatus] = useState('loading');
  const [mapReady, setMapReady] = useState(false);

  // Effect 1: Initialize the Google Map (once)
  useEffect(() => {
    const initializeMap = () => {
      if (!mapRef.current || mapInstanceRef.current) return;
      const map = new window.google.maps.Map(mapRef.current, {
        center: { lat: 6.5244, lng: 3.3792 },
        zoom: 12,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
      });
      mapInstanceRef.current = map;
      directionsRendererRef.current = new window.google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true,
        polylineOptions: {
          strokeColor: '#E8A838',
          strokeWeight: 4,
          strokeOpacity: 0.7,
          icons: [{ icon: { path: window.google.maps.SymbolPath.CIRCLE, scale: 4 }, offset: '0', repeat: '100px' }]
        }
      });
      setMapReady(true);
    };

    let unsubscribe = null;
    if (window.google && window.google.maps) {
      initializeMap();
    } else {
      window.addEventListener('google-maps-loaded', initializeMap);
      unsubscribe = () => window.removeEventListener('google-maps-loaded', initializeMap);
    }

    return () => {
      if (unsubscribe) unsubscribe();
      markersRef.current.forEach(m => m.setMap(null));
      markersRef.current = [];
      if (directionsRendererRef.current) { directionsRendererRef.current.setMap(null); directionsRendererRef.current = null; }
      mapInstanceRef.current = null;
    };
  }, []);

  // Effect 2: Update markers + route whenever order/rider changes
  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current || !window.google) return;
    const map = mapInstanceRef.current;
    const geocoder = new window.google.maps.Geocoder();

    const geocodeAddr = (address) => new Promise((resolve) => {
      geocoder.geocode({ address: address + ', Lagos, Nigeria' }, (results, status) => {
        resolve((status === 'OK' && results[0]) ? results[0].geometry.location : null);
      });
    });

    (async () => {
      // Clear previous markers and route
      markersRef.current.forEach(m => m.setMap(null));
      markersRef.current = [];
      if (directionsRendererRef.current) directionsRendererRef.current.setDirections({ routes: [] });

      const [pickupLoc, dropoffLoc] = await Promise.all([
        geocodeAddr(order.pickup),
        geocodeAddr(order.dropoff),
      ]);
      if (!pickupLoc || !dropoffLoc) { setMapStatus('error'); return; }

      // Pickup marker — navy dot
      markersRef.current.push(new window.google.maps.Marker({
        position: pickupLoc, map,
        title: 'Pickup: ' + order.pickup,
        icon: { path: window.google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#1B2A4A', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
        label: { text: '📦', fontSize: '16px' }
      }));

      // Dropoff marker — green dot
      markersRef.current.push(new window.google.maps.Marker({
        position: dropoffLoc, map,
        title: 'Dropoff: ' + order.dropoff,
        icon: { path: window.google.maps.SymbolPath.CIRCLE, scale: 10, fillColor: '#10B981', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
        label: { text: '🏠', fontSize: '16px' }
      }));

      // Rider marker — gold dot (only if GPS available)
      if (rider && rider.lat && rider.lng) {
        markersRef.current.push(new window.google.maps.Marker({
          position: { lat: rider.lat, lng: rider.lng }, map,
          title: 'Rider: ' + (rider.name || 'Rider'),
          icon: { path: window.google.maps.SymbolPath.CIRCLE, scale: 12, fillColor: '#E8A838', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 3 },
          label: { text: '🏍️', fontSize: '16px' }
        }));
      }

      // Draw route
      new window.google.maps.DirectionsService().route({
        origin: pickupLoc,
        destination: dropoffLoc,
        travelMode: window.google.maps.TravelMode.DRIVING,
      }, (result, status) => {
        if (status === 'OK') {
          directionsRendererRef.current.setDirections(result);
        } else {
          // Route failed — just fit bounds to markers
          const bounds = new window.google.maps.LatLngBounds();
          bounds.extend(pickupLoc);
          bounds.extend(dropoffLoc);
          if (rider && rider.lat && rider.lng) bounds.extend({ lat: rider.lat, lng: rider.lng });
          map.fitBounds(bounds, { padding: 40 });
        }
        setMapStatus('ready');
      });
    })().catch(err => { console.error('DeliveryRouteMap error:', err); setMapStatus('error'); });
  }, [mapReady, order.id, order.pickup, order.dropoff, rider?.id, rider?.lat, rider?.lng]);

  return (
    <div style={{ position:'relative', borderRadius:10, overflow:'hidden', border:`1px solid ${S.border}` }}>
      <div ref={mapRef} style={{ height:230, width:'100%' }} />
      {mapStatus === 'loading' && (
        <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', background:'#EEF2F7', gap:8 }}>
          <div style={{ fontSize:24 }}>🗺️</div>
          <div style={{ fontSize:11, color:S.textMuted }}>Loading map…</div>
        </div>
      )}
      {mapStatus === 'error' && (
        <div style={{ position:'absolute', inset:0, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', background:'#EEF2F7', gap:6 }}>
          <div style={{ fontSize:24 }}>📍</div>
          <div style={{ fontSize:11, color:S.textMuted }}>Could not load map</div>
          <div style={{ fontSize:10, color:S.textMuted }}>Check addresses or connection</div>
        </div>
      )}
    </div>
  );
}

const INIT_RIDERS = [
  { id:"R001",name:"Musa Kabiru",phone:"08034561234",vehicle:"Bike",status:"online",currentOrder:"AX-6158260",todayOrders:8,todayEarnings:14400,rating:4.8,totalDeliveries:1234,completionRate:96,avgTime:"28 min",joined:"Sep 2024" },
  { id:"R002",name:"Ahmed Bello",phone:"09012349876",vehicle:"Bike",status:"online",currentOrder:"AX-6158258",todayOrders:6,todayEarnings:10800,rating:4.6,totalDeliveries:876,completionRate:94,avgTime:"32 min",joined:"Nov 2024" },
  { id:"R003",name:"Chinedu Okoro",phone:"07055667788",vehicle:"Car",status:"on_delivery",currentOrder:"AX-6158261",todayOrders:4,todayEarnings:18000,rating:4.9,totalDeliveries:567,completionRate:98,avgTime:"35 min",joined:"Jan 2025" },
  { id:"R004",name:"Tunde Adewale",phone:"08199887766",vehicle:"Van",status:"offline",currentOrder:null,todayOrders:0,todayEarnings:0,rating:4.5,totalDeliveries:345,completionRate:92,avgTime:"42 min",joined:"Oct 2024" },
  { id:"R005",name:"Ibrahim Suleiman",phone:"08088776655",vehicle:"Bike",status:"online",currentOrder:null,todayOrders:5,todayEarnings:9000,rating:4.7,totalDeliveries:2100,completionRate:97,avgTime:"25 min",joined:"Jun 2024" },
  { id:"R006",name:"Kola Adekunle",phone:"07033445566",vehicle:"Car",status:"on_delivery",currentOrder:"AX-6158263",todayOrders:3,todayEarnings:13500,rating:4.4,totalDeliveries:198,completionRate:91,avgTime:"38 min",joined:"Dec 2024" },
  { id:"R007",name:"Emeka Nwankwo",phone:"09044332211",vehicle:"Bike",status:"online",currentOrder:null,todayOrders:7,todayEarnings:12600,rating:4.8,totalDeliveries:1567,completionRate:95,avgTime:"26 min",joined:"Aug 2024" },
  { id:"R008",name:"Femi Akinola",phone:"08155443322",vehicle:"Bike",status:"offline",currentOrder:null,todayOrders:9,todayEarnings:16200,rating:4.9,totalDeliveries:3200,completionRate:99,avgTime:"22 min",joined:"Mar 2024" },
];
const INIT_ORDERS = [
  { id:"AX-6158260",customer:"Adebayo Johnson",customerPhone:"08034567890",merchant:"Vivid Print",pickup:"24 Harvey Rd, Sabo Yaba",dropoff:"15 Akin Adesola St, VI",rider:"Musa Kabiru",riderId:"R001",status:"In Transit",amount:1210,cod:55000,codFee:500,vehicle:"Bike",created:"Feb 14, 3:42 PM",pkg:"Box" },
  { id:"AX-6158261",customer:"Chidi Obi",customerPhone:"07011223344",merchant:"Mama Nkechi Kitchen",pickup:"8 Bode Thomas, Surulere",dropoff:"22 Ozumba Mbadiwe, VI",rider:"Chinedu Okoro",riderId:"R003",status:"Picked Up",amount:4500,cod:0,codFee:0,vehicle:"Car",created:"Feb 14, 3:28 PM",pkg:"Food" },
  { id:"AX-6158262",customer:"Funke Adeyemi",customerPhone:"09012345678",merchant:"TechZone Gadgets",pickup:"Computer Village, Ikeja",dropoff:"45 Admiralty Way, Lekki",rider:null,riderId:null,status:"Pending",amount:4500,cod:210000,codFee:500,vehicle:"Car",created:"Feb 14, 3:15 PM",pkg:"Fragile" },
  { id:"AX-6158263",customer:"Emeka Eze",customerPhone:"09044332211",merchant:"AutoParts Hub",pickup:"12 Agege Motor Rd, Mushin",dropoff:"33 Allen Avenue, Ikeja",rider:"Kola Adekunle",riderId:"R006",status:"In Transit",amount:4500,cod:45000,codFee:500,vehicle:"Car",created:"Feb 14, 2:55 PM",pkg:"Box" },
  { id:"AX-6158258",customer:"Blessing Nwosu",customerPhone:"08155667788",merchant:"GlowUp Beauty",pickup:"10 Adeola Odeku, VI",dropoff:"7 Admiralty Rd, Lekki Phase 1",rider:"Ahmed Bello",riderId:"R002",status:"Assigned",amount:1210,cod:0,codFee:0,vehicle:"Bike",created:"Feb 14, 2:40 PM",pkg:"Envelope" },
  { id:"AX-6158257",customer:"Ngozi Ibe",customerPhone:"07088990011",merchant:"Vivid Print",pickup:"24 Harvey Rd, Sabo Yaba",dropoff:"5 Karimu Kotun, VI",rider:"Musa Kabiru",riderId:"R001",status:"Delivered",amount:1210,cod:36000,codFee:500,vehicle:"Bike",created:"Feb 14, 1:20 PM",pkg:"Box" },
  { id:"AX-6158256",customer:"Kola Peters",customerPhone:"08144556677",merchant:"TechZone Gadgets",pickup:"Computer Village, Ikeja",dropoff:"14 Toyin St, Ikeja",rider:"Ibrahim Suleiman",riderId:"R005",status:"Delivered",amount:1210,cod:125000,codFee:500,vehicle:"Bike",created:"Feb 14, 12:50 PM",pkg:"Fragile" },
  { id:"AX-6158255",customer:"Aisha Mohammed",customerPhone:"07055443322",merchant:"FreshFit Lagos",pickup:"3 Admiralty Way, Lekki",dropoff:"20 Fola Osibo, Lekki Phase 1",rider:"Emeka Nwankwo",riderId:"R007",status:"Delivered",amount:1210,cod:0,codFee:0,vehicle:"Bike",created:"Feb 14, 11:30 AM",pkg:"Envelope" },
  { id:"AX-6158254",customer:"Adebayo Johnson",customerPhone:"08034567890",merchant:"Vivid Print",pickup:"24 Harvey Rd, Sabo Yaba",dropoff:"15 Akin Adesola St, VI",rider:null,riderId:null,status:"Cancelled",amount:1210,cod:0,codFee:0,vehicle:"Bike",created:"Feb 14, 10:15 AM",pkg:"Document" },
  { id:"AX-6158253",customer:"Chidi Obi",customerPhone:"07011223344",merchant:"Mama Nkechi Kitchen",pickup:"8 Bode Thomas, Surulere",dropoff:"1 Glover Rd, Ikoyi",rider:"Ahmed Bello",riderId:"R002",status:"Delivered",amount:4500,cod:75000,codFee:500,vehicle:"Car",created:"Feb 13, 5:40 PM",pkg:"Food" },
  { id:"AX-6158252",customer:"Emeka Eze",customerPhone:"09044332211",merchant:"AutoParts Hub",pickup:"12 Agege Motor Rd, Mushin",dropoff:"8 Opebi Rd, Ikeja",rider:"Kola Adekunle",riderId:"R006",status:"Failed",amount:4500,cod:18000,codFee:500,vehicle:"Car",created:"Feb 13, 4:10 PM",pkg:"Box" },
  { id:"AX-6158251",customer:"Funke Adeyemi",customerPhone:"09012345678",merchant:"GlowUp Beauty",pickup:"10 Adeola Odeku, VI",dropoff:"25 Adetokunbo Ademola, VI",rider:"Femi Akinola",riderId:"R008",status:"Delivered",amount:1210,cod:8500,codFee:500,vehicle:"Bike",created:"Feb 13, 3:00 PM",pkg:"Box" },
];
const MERCHANTS_DATA = [
  { id:"M001",name:"Vivid Print",contact:"Yetunde Igbene",phone:"08051832508",category:"Printing",totalOrders:234,monthOrders:42,walletBalance:87900,status:"Active",joined:"Nov 2024" },
  { id:"M002",name:"TechZone Gadgets",contact:"Ade Bakare",phone:"09012345678",category:"Electronics",totalOrders:567,monthOrders:89,walletBalance:234500,status:"Active",joined:"Sep 2024" },
  { id:"M003",name:"Mama Nkechi Kitchen",contact:"Nkechi Obi",phone:"07033445566",category:"Food",totalOrders:1203,monthOrders:156,walletBalance:56700,status:"Active",joined:"Jul 2024" },
  { id:"M004",name:"FreshFit Lagos",contact:"Sola Adams",phone:"08055667788",category:"Fashion",totalOrders:89,monthOrders:12,walletBalance:12300,status:"Active",joined:"Jan 2025" },
  { id:"M005",name:"GlowUp Beauty",contact:"Amara Eze",phone:"08022334455",category:"Beauty",totalOrders:445,monthOrders:67,walletBalance:178000,status:"Active",joined:"Aug 2024" },
  { id:"M006",name:"AutoParts Hub",contact:"Bayo Ogun",phone:"08099887766",category:"Auto Parts",totalOrders:312,monthOrders:34,walletBalance:45600,status:"Inactive",joined:"Oct 2024" },
];
const CUSTOMERS_DATA = [
  { id:"C001",name:"Adebayo Johnson",phone:"08034567890",email:"adebayo@gmail.com",totalOrders:15,lastOrder:"Feb 14",totalSpent:182500,favMerchant:"Vivid Print" },
  { id:"C002",name:"Funke Adeyemi",phone:"09012345678",email:"funke.a@yahoo.com",totalOrders:8,lastOrder:"Feb 13",totalSpent:94000,favMerchant:"TechZone Gadgets" },
  { id:"C003",name:"Chidi Obi",phone:"07011223344",email:"chidi.obi@outlook.com",totalOrders:23,lastOrder:"Feb 14",totalSpent:567000,favMerchant:"Mama Nkechi" },
  { id:"C004",name:"Blessing Nwosu",phone:"08155667788",email:"blessing.n@gmail.com",totalOrders:5,lastOrder:"Feb 12",totalSpent:42000,favMerchant:"GlowUp Beauty" },
  { id:"C005",name:"Emeka Eze",phone:"09044332211",email:"emeka.eze@gmail.com",totalOrders:31,lastOrder:"Feb 14",totalSpent:890000,favMerchant:"AutoParts Hub" },
  { id:"C006",name:"Ngozi Ibe",phone:"07088990011",email:"ngozi.ibe@yahoo.com",totalOrders:12,lastOrder:"Feb 13",totalSpent:156000,favMerchant:"Vivid Print" },
  { id:"C007",name:"Kola Peters",phone:"08144556677",email:"kpeters@gmail.com",totalOrders:19,lastOrder:"Feb 14",totalSpent:345000,favMerchant:"TechZone Gadgets" },
  { id:"C008",name:"Aisha Mohammed",phone:"07055443322",email:"aisha.m@outlook.com",totalOrders:7,lastOrder:"Feb 11",totalSpent:78500,favMerchant:"FreshFit Lagos" },
];
const MSG_RIDER = [
  { id:"R001",name:"Musa Kabiru",unread:2,lastMsg:"On my way to pickup now",lastTime:"4:05 PM",messages:[{from:"dispatch",text:"Musa, new order AX-6158260 assigned. Pickup at Sabo Yaba.",time:"3:44 PM"},{from:"rider",text:"Received. Heading there now.",time:"3:45 PM"},{from:"rider",text:"Traffic heavy on Third Mainland. ETA 12 mins.",time:"3:50 PM"},{from:"dispatch",text:"Noted. Customer informed.",time:"3:51 PM"},{from:"rider",text:"On my way to pickup now",time:"4:05 PM"}]},
  { id:"R003",name:"Chinedu Okoro",unread:0,lastMsg:"Package secured, heading out",lastTime:"3:35 PM",messages:[{from:"dispatch",text:"Chinedu, AX-6158261 for you. Car required — food delivery.",time:"3:28 PM"},{from:"rider",text:"Copy. 5 mins from Surulere pickup.",time:"3:30 PM"},{from:"rider",text:"Package secured, heading out",time:"3:35 PM"}]},
  { id:"R005",name:"Ibrahim Suleiman",unread:1,lastMsg:"Free for next dispatch",lastTime:"1:15 PM",messages:[{from:"rider",text:"AX-6158256 delivered. COD collected.",time:"1:10 PM"},{from:"dispatch",text:"Great work! Settle COD via wallet.",time:"1:12 PM"},{from:"rider",text:"Done. Free for next dispatch",time:"1:15 PM"}]},
];
const MSG_CUSTOMER = [
  { id:"C001",name:"Adebayo Johnson",unread:1,lastMsg:"When will my package arrive?",lastTime:"4:08 PM",messages:[{from:"customer",text:"Hi, I placed AX-6158260. Any update?",time:"4:02 PM"},{from:"dispatch",text:"Your rider Musa is en route. ETA ~15 min.",time:"4:04 PM"},{from:"customer",text:"When will my package arrive?",time:"4:08 PM"}]},
  { id:"C003",name:"Chidi Obi",unread:0,lastMsg:"Thank you!",lastTime:"3:40 PM",messages:[{from:"customer",text:"Is my food order on the way?",time:"3:30 PM"},{from:"dispatch",text:"Yes! Chinedu picked it up. Heading to you now.",time:"3:36 PM"},{from:"customer",text:"Thank you!",time:"3:40 PM"}]},
];

const Badge = ({status}) => { const s=STS[status]||{bg:"#f1f5f9",text:"#94A3B8"}; return <span style={{fontSize:10,fontWeight:700,padding:"3px 10px",borderRadius:6,background:s.bg,color:s.text,textTransform:"uppercase",letterSpacing:"0.5px"}}>{status}</span>; };
const StatCard = ({label,value,sub,color}) => (<div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:"16px 18px",flex:1}}><div style={{fontSize:11,color:S.textMuted,fontWeight:600,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:6}}>{label}</div><div style={{fontSize:24,fontWeight:800,color:color||S.text,fontFamily:"'Space Mono', monospace",lineHeight:1}}>{value}</div>{sub&&<div style={{fontSize:11,color:S.textMuted,marginTop:4}}>{sub}</div>}</div>);
const now = () => new Date().toLocaleTimeString("en-US",{hour:"numeric",minute:"2-digit",hour12:true});

// ─── LOGIN SCREEN ───────────────────────────────────────────────
function LoginScreen({ onLogin }) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await AuthAPI.login(phone, password);
      onLogin();
    } catch (err) {
      setError(err.errors?.non_field_errors?.[0] || err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:S.bg,fontFamily:"'DM Sans','Segoe UI',system-ui,sans-serif"}}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
      <div style={{width:380,padding:40,background:S.card,borderRadius:16,boxShadow:"0 4px 24px rgba(0,0,0,0.08)"}}>
        <div style={{textAlign:"center",marginBottom:32}}>
          <div style={{width:56,height:56,borderRadius:12,display:"inline-flex",alignItems:"center",justifyContent:"center",background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,fontWeight:800,fontSize:22,color:S.navy,fontFamily:"'Space Mono',monospace",marginBottom:16}}>AX</div>
          <h1 style={{fontSize:24,fontWeight:700,color:S.text,margin:0}}>Dispatch Portal</h1>
          <p style={{color:S.muted,fontSize:14,marginTop:4}}>Sign in to continue</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{marginBottom:16}}>
            <label style={{display:"block",fontSize:13,fontWeight:500,color:S.text,marginBottom:6}}>Phone Number</label>
            <input type="text" value={phone} onChange={e=>setPhone(e.target.value)} placeholder="+234..." style={{width:"100%",padding:"12px 14px",border:`1px solid ${S.border}`,borderRadius:8,fontSize:14,background:S.bg}} required/>
          </div>
          <div style={{marginBottom:24}}>
            <label style={{display:"block",fontSize:13,fontWeight:500,color:S.text,marginBottom:6}}>Password</label>
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" style={{width:"100%",padding:"12px 14px",border:`1px solid ${S.border}`,borderRadius:8,fontSize:14,background:S.bg}} required/>
          </div>
          {error && <div style={{padding:"10px 14px",background:S.redBg,color:S.red,borderRadius:8,fontSize:13,marginBottom:16}}>{error}</div>}
          <button type="submit" disabled={loading} style={{width:"100%",padding:"14px",background:S.gold,color:"#fff",border:"none",borderRadius:10,fontSize:15,fontWeight:600,cursor:loading?"wait":"pointer",opacity:loading?0.7:1}}>{loading?"Signing in...":"Sign In"}</button>
        </form>
      </div>
    </div>
  );
}

export default function AXDispatchPortal() {
  const [isAuthenticated, setIsAuthenticated] = useState(AuthAPI.isAuthenticated());
  const [loading, setLoading] = useState(true);
  const [screen,setScreen] = useState("dashboard");
  const [selectedOrderId,setSelectedOrderId] = useState(null);
  const [selectedRiderId,setSelectedRiderId] = useState(null);
  const [showCreateOrder,setShowCreateOrder] = useState(false);
  const [orders,setOrders] = useState([]);
  const [riders,setRiders] = useState([]);
  const [merchants,setMerchants] = useState([]);
  const [eventLogs,setEventLogs] = useState({});

  // Initialize event logs when orders change
  const initEventLogs = (ordersList) => {
    const logs = {};
    ordersList.forEach(o => {
      const b = [{time:o.created?.split(", ")[1]||o.created||"N/A",event:"Order created",by:`Merchant Portal (${o.merchant})`,type:"create"}];
      if(o.riderId) b.push({time:"auto",event:`Assigned to ${o.rider}`,by:"Auto-Dispatch",type:"assign"});
      if(["Picked Up","In Transit","Delivered"].includes(o.status)) b.push({time:"auto",event:"Package picked up",by:o.rider,type:"pickup"});
      if(["In Transit","Delivered"].includes(o.status)) b.push({time:"auto",event:"In transit to dropoff",by:"GPS",type:"transit"});
      if(o.status==="Delivered"){ b.push({time:"auto",event:"Delivered — confirmed",by:o.rider,type:"delivered"}); if(o.cod>0) b.push({time:"auto",event:`COD settled: ₦${(o.cod-o.codFee).toLocaleString()}`,by:"System",type:"settlement"}); }
      if(o.status==="Cancelled") b.push({time:"auto",event:"Order cancelled",by:"Dispatch",type:"cancel"});
      if(o.status==="Failed") b.push({time:"auto",event:"Delivery failed",by:o.rider||"System",type:"fail"});
      logs[o.id]=b;
    });
    return logs;
  };

  // Fetch data whenever authenticated becomes true
  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    const fetchData = async () => {
      setLoading(true);
      try {
        const [ridersData, ordersData, merchantsData] = await Promise.all([
          RidersAPI.getAll().catch(() => []),
          OrdersAPI.getAll().catch(() => []),
          MerchantsAPI.getAll().catch(() => [])
        ]);
        setRiders(ridersData);
        setOrders(ordersData);
        setMerchants(merchantsData);
        setEventLogs(initEventLogs(ordersData));
      } catch (error) {
        console.error('Failed to fetch data:', error);
        AuthAPI.logout();
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [isAuthenticated]); // re-run when user logs in

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen onLogin={() => { setIsAuthenticated(true); setLoading(true); }} />;
  }

  // Show loading screen
  if (loading) {
    return (
      <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",background:S.bg,fontFamily:"'DM Sans',sans-serif"}}>
        <div style={{textAlign:"center"}}>
          <div style={{width:48,height:48,border:`3px solid ${S.border}`,borderTopColor:S.gold,borderRadius:"50%",animation:"spin 1s linear infinite",margin:"0 auto 16px"}}></div>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          <div style={{color:S.muted,fontSize:14}}>Loading dispatch data...</div>
        </div>
      </div>
    );
  }

  const addLog = (oid,event,by,type) => setEventLogs(p=>({...p,[oid]:[...(p[oid]||[]),{time:now(),event,by,type}]}));
  const updateOrder = (oid,u) => setOrders(p=>p.map(o=>o.id===oid?{...o,...u}:o));

  const assignRider = async (oid,rid) => {
    const r = riders.find(x=>x.id===rid); if(!r) return;
    try {
      await OrdersAPI.assignRider(oid, rid);
      updateOrder(oid,{rider:r.name,riderId:rid,status:"Assigned"});
      setRiders(p=>p.map(x=>x.id===rid?{...x,currentOrder:oid,status:"on_delivery"}:x));
      addLog(oid,`Assigned to ${r.name}`,"Dispatch","assign");
      addLog(oid,"Status → Assigned","System","status");
    } catch (error) {
      console.error('Failed to assign rider:', error);
      alert('Failed to assign rider. Please try again.');
    }
  };

  const changeStatus = (oid,ns) => {
    const o = orders.find(x=>x.id===oid); if(!o) return;
    updateOrder(oid,{status:ns});
    addLog(oid,`Status → ${ns}`,"Dispatch",ns==="Delivered"?"delivered":ns==="Cancelled"?"cancel":"status");
    if(ns==="Delivered"&&o.cod>0) addLog(oid,`COD settled: ₦${(o.cod-o.codFee).toLocaleString()} to merchant`,"System","settlement");
    if(["Delivered","Cancelled","Failed"].includes(ns)&&o.riderId) setRiders(p=>p.map(r=>r.id===o.riderId?{...r,currentOrder:null,status:"online"}:r));
  };

  const navTo = (s,id) => { if(s==="orders"){setSelectedOrderId(id);setScreen("orders");}else{setSelectedRiderId(id);setScreen("riders");} };
  const navItems = [
    {id:"dashboard",label:"Dashboard",icon:I.dashboard},
    {id:"orders",label:"Orders",icon:I.orders,count:orders.filter(o=>o.status==="Pending").length},
    {id:"riders",label:"Riders",icon:I.riders,count:riders.filter(r=>r.status==="online").length},
    {id:"merchants",label:"Merchants",icon:I.merchants},
    {id:"customers",label:"Customers",icon:I.customers},
    {id:"messaging",label:"Messaging",icon:I.messaging,count:MSG_RIDER.reduce((s,m)=>s+m.unread,0)+MSG_CUSTOMER.reduce((s,m)=>s+m.unread,0)},
    {id:"settings",label:"Settings",icon:I.settings},
  ];

  return (
    <div style={{display:"flex",height:"100vh",background:S.bg,fontFamily:"'DM Sans','Segoe UI',system-ui,sans-serif",color:S.text,overflow:"hidden"}}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
      <style>{`*{box-sizing:border-box;margin:0}button:hover{filter:brightness(1.05)}input:focus,select:focus{outline:2px solid ${S.gold};outline-offset:-1px}::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:${S.border};border-radius:3px}@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}`}</style>

      {/* SIDEBAR — Navy theme matching Merchant Portal */}
      <aside style={{width:240,background:S.navy,display:"flex",flexDirection:"column",flexShrink:0}}>
        <div style={{padding:"22px 18px 18px",borderBottom:"1px solid rgba(255,255,255,0.08)"}}>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{width:36,height:36,borderRadius:8,display:"flex",alignItems:"center",justifyContent:"center",background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,fontWeight:800,fontSize:15,color:S.navy,fontFamily:"'Space Mono',monospace"}}>AX</div>
            <div><div style={{color:"#fff",fontWeight:700,fontSize:15,letterSpacing:"0.5px"}}>ASSURED</div><div style={{color:S.gold,fontSize:11,fontWeight:600,letterSpacing:"2px",marginTop:-2}}>DISPATCH</div></div>
          </div>
        </div>
        <div style={{padding:"12px 14px",borderBottom:"1px solid rgba(255,255,255,0.08)",display:"flex",gap:8}}>
          {[{v:orders.filter(o=>["In Transit","Picked Up","Assigned"].includes(o.status)).length,l:"ACTIVE",c:S.gold,bg:"rgba(232,168,56,0.12)"},{v:riders.filter(r=>r.status==="online").length,l:"ONLINE",c:S.green,bg:"rgba(22,163,74,0.12)"},{v:orders.filter(o=>o.status==="Pending").length,l:"PENDING",c:S.yellow,bg:"rgba(245,158,11,0.12)"}].map(s=>(<div key={s.l} style={{flex:1,padding:8,borderRadius:8,background:s.bg,textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:s.c,fontFamily:"'Space Mono',monospace"}}>{s.v}</div><div style={{fontSize:9,color:"rgba(255,255,255,0.4)",fontWeight:600}}>{s.l}</div></div>))}
        </div>
        <nav style={{flex:1,padding:"10px 8px",display:"flex",flexDirection:"column",gap:2}}>
          {navItems.map(item=>{const a=screen===item.id;return (<button key={item.id} onClick={()=>{setScreen(item.id);setSelectedOrderId(null);setSelectedRiderId(null);}} style={{display:"flex",alignItems:"center",gap:12,padding:"11px 14px",borderRadius:10,border:"none",cursor:"pointer",fontSize:13,fontWeight:a?600:400,fontFamily:"inherit",width:"100%",textAlign:"left",background:a?"rgba(232,168,56,0.12)":"transparent",color:a?S.gold:"rgba(255,255,255,0.6)",transition:"all 0.2s"}}><span style={{opacity:a?1:0.6}}>{item.icon}</span><span style={{flex:1}}>{item.label}</span>{item.count>0&&<span style={{fontSize:10,fontWeight:700,padding:"2px 7px",borderRadius:8,minWidth:18,textAlign:"center",background:a?S.gold:"rgba(255,255,255,0.1)",color:a?"#fff":"rgba(255,255,255,0.5)"}}>{item.count}</span>}</button>);})}
        </nav>
        <div style={{padding:"12px 14px",borderTop:"1px solid rgba(255,255,255,0.08)"}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:10}}>
            <div style={{width:32,height:32,borderRadius:"50%",background:"rgba(232,168,56,0.15)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:800,color:S.gold}}>OI</div>
            <div><div style={{fontSize:12,fontWeight:600,color:"#fff"}}>Otimeyin I.</div><div style={{fontSize:10,color:"rgba(255,255,255,0.4)"}}>Admin</div></div>
          </div>
          <button onClick={()=>{AuthAPI.logout();window.location.reload();}} style={{width:"100%",padding:"8px 12px",background:"rgba(239,68,68,0.15)",color:"#EF4444",border:"none",borderRadius:6,fontSize:12,fontWeight:500,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:6}}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            Logout
          </button>
        </div>
      </aside>

      <main style={{flex:1,display:"flex",flexDirection:"column",overflow:"hidden"}}>
        <header style={{padding:"14px 24px",borderBottom:`1px solid ${S.border}`,background:S.card,display:"flex",alignItems:"center",justifyContent:"space-between",flexShrink:0}}>
          <h1 style={{fontSize:18,fontWeight:700,color:S.navy,margin:0}}>{screen==="dashboard"?"Dashboard":screen==="orders"?(selectedOrderId?`Order ${selectedOrderId}`:"Orders"):screen==="riders"?(selectedRiderId?"Rider Details":"Riders"):screen==="merchants"?"Merchants":screen==="customers"?"Customers":screen==="messaging"?"Messaging":"Settings"}</h1>
          <button onClick={()=>setShowCreateOrder(true)} style={{display:"flex",alignItems:"center",gap:6,padding:"8px 18px",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"inherit",fontWeight:700,fontSize:13,background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,boxShadow:"0 2px 8px rgba(232,168,56,0.25)"}}>{I.plus} New Order</button>
        </header>
        <div style={{flex:1,overflow:"auto",padding:24,animation:"fadeIn 0.3s ease"}}>
          {screen==="dashboard"&&<DashboardScreen orders={orders} riders={riders} onViewOrder={id=>navTo("orders",id)} onViewRider={id=>navTo("riders",id)}/>}
          {screen==="orders"&&<OrdersScreen orders={orders} riders={riders} selectedId={selectedOrderId} onSelect={setSelectedOrderId} onBack={()=>setSelectedOrderId(null)} onViewRider={id=>navTo("riders",id)} onAssign={assignRider} onChangeStatus={changeStatus} onUpdateOrder={updateOrder} addLog={addLog} eventLogs={eventLogs}/>}
          {screen==="riders"&&<RidersScreen riders={riders} orders={orders} selectedId={selectedRiderId} onSelect={setSelectedRiderId} onBack={()=>setSelectedRiderId(null)} onViewOrder={id=>navTo("orders",id)}/>}
          {screen==="merchants"&&<MerchantsScreen data={merchants.length > 0 ? merchants : MERCHANTS_DATA}/>}
          {screen==="customers"&&<CustomersScreen data={CUSTOMERS_DATA}/>}
          {screen==="messaging"&&<MessagingScreen/>}
          {screen==="settings"&&<SettingsScreen/>}
        </div>
      </main>
      {showCreateOrder&&<CreateOrderModal riders={riders} merchants={merchants} onClose={()=>setShowCreateOrder(false)} onOrderCreated={(created)=>{
        const newOrder={
          id: created.id || "N/A",
          customer: created.customer || "Unknown",
          customerPhone: created.customerPhone || "",
          merchant: created.merchant || "Unknown",
          pickup: created.pickup || "",
          dropoff: created.dropoff || "",
          rider: created.rider || null,
          riderId: created.riderId || null,
          status: created.status || "Pending",
          amount: parseFloat(created.amount) || 0,
          cod: parseFloat(created.cod) || 0,
          codFee: parseFloat(created.codFee) || 0,
          vehicle: created.vehicle || "Bike",
          created: created.created || new Date().toLocaleString(),
          pkg: created.pkg || "Box"
        };
        setOrders(p=>[newOrder,...p]);
      }}/>}
    </div>
  );
}

// ─── DASHBOARD ──────────────────────────────────────────────────
function DashboardScreen({ orders, riders, onViewOrder, onViewRider }) {
  const todayStr = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"
  const today = orders.filter(o => {
    if (!o.created) return false;
    // Handle ISO datetime ("2026-02-22T15:42:00Z") or any string containing today's date
    return o.created.startsWith(todayStr) || o.created.includes(todayStr);
  });
  // Fall back to all orders if today filter returns nothing (e.g. older data)
  const displayOrders = today.length > 0 ? today : orders;
  const active = orders.filter(o => ["In Transit","Picked Up","Assigned"].includes(o.status));
  const delivered = displayOrders.filter(o => o.status === "Delivered");
  const revenue = displayOrders.reduce((s,o) => s+o.amount+o.codFee, 0);
  const codTotal = displayOrders.reduce((s,o) => s+o.cod, 0);

  const events = [
    { time:"4:05 PM", text:"AX-6158260 in transit — Musa heading to VI", color:S.gold, oid:"AX-6158260" },
    { time:"3:58 PM", text:"AX-6158260 picked up at Sabo Yaba", color:S.purple, oid:"AX-6158260" },
    { time:"3:44 PM", text:"AX-6158260 assigned to Musa Kabiru", color:S.blue, oid:"AX-6158260" },
    { time:"3:42 PM", text:"New order AX-6158260 from Vivid Print", color:S.gold, oid:"AX-6158260" },
    { time:"3:35 PM", text:"AX-6158261 picked up — Chinedu heading to VI", color:S.purple, oid:"AX-6158261" },
    { time:"3:28 PM", text:"New order AX-6158261 from Mama Nkechi", color:S.gold, oid:"AX-6158261" },
    { time:"3:15 PM", text:"AX-6158262 pending — no rider assigned", color:S.yellow, oid:"AX-6158262" },
    { time:"2:55 PM", text:"AX-6158263 in transit — Kola heading to Ikeja", color:S.gold, oid:"AX-6158263" },
    { time:"1:51 PM", text:"AX-6158257 delivered ✓ COD ₦36,000 settled", color:S.green, oid:"AX-6158257" },
    { time:"1:10 PM", text:"AX-6158256 delivered ✓ COD ₦125,000 settled", color:S.green, oid:"AX-6158256" },
  ];

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:20}}>
        <StatCard label="Today's Orders" value={displayOrders.length} sub={`${delivered.length} delivered`}/>
        <StatCard label="Active Now" value={active.length} sub={`${orders.filter(o=>o.status==="Pending").length} pending`} color={S.gold}/>
        <StatCard label="Online Riders" value={riders.filter(r=>r.status==="online").length} sub={`${riders.filter(r=>r.status==="on_delivery").length} on delivery`} color={S.green}/>
        <StatCard label="Revenue Today" value={`₦${(revenue/1000).toFixed(0)}K`} sub={`₦${(codTotal/1000).toFixed(0)}K COD collected`} color={S.gold}/>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 320px",gap:16}}>
        {/* Live feed */}
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
          <div style={{padding:"14px 18px",borderBottom:`1px solid ${S.border}`,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
            <div style={{display:"flex",alignItems:"center",gap:8}}><div style={{width:8,height:8,borderRadius:"50%",background:S.green,boxShadow:`0 0 8px ${S.green}`}}/><span style={{fontSize:13,fontWeight:700}}>Live Activity</span></div>
            <span style={{fontSize:11,color:S.textMuted}}>{events.length} events</span>
          </div>
          <div style={{maxHeight:420,overflowY:"auto"}}>
            {events.map((ev,i) => (
              <div key={i} onClick={()=>onViewOrder(ev.oid)} style={{padding:"11px 18px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",display:"flex",alignItems:"flex-start",gap:12,transition:"background 0.15s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                <div style={{width:8,height:8,borderRadius:"50%",background:ev.color,marginTop:5,flexShrink:0}}/>
                <div style={{flex:1,fontSize:12,color:S.text,lineHeight:1.4}}>{ev.text}</div>
                <span style={{fontSize:10,color:S.textMuted,fontFamily:"'Space Mono',monospace",flexShrink:0}}>{ev.time}</span>
              </div>
            ))}
          </div>
        </div>
        {/* Right col */}
        <div style={{display:"flex",flexDirection:"column",gap:12}}>
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`}}>
            <div style={{padding:"12px 16px",borderBottom:`1px solid ${S.border}`}}><span style={{fontSize:13,fontWeight:700,color:S.yellow}}>⏳ Pending Assignment</span></div>
            {orders.filter(o=>o.status==="Pending").map(o=>(
              <div key={o.id} onClick={()=>onViewOrder(o.id)} style={{padding:"10px 16px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",transition:"background 0.15s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                <div style={{display:"flex",justifyContent:"space-between"}}><span style={{fontSize:12,fontWeight:700,color:S.gold,fontFamily:"'Space Mono',monospace"}}>{o.id}</span><span style={{fontSize:11,color:S.textMuted}}>{o.vehicle}</span></div>
                <div style={{fontSize:11,color:S.textDim,marginTop:2}}>{o.merchant} → {o.dropoff.split(",")[0]}</div>
                {o.cod>0&&<div style={{fontSize:10,color:S.green,marginTop:2}}>💵 COD ₦{o.cod.toLocaleString()}</div>}
              </div>
            ))}
            {orders.filter(o=>o.status==="Pending").length===0&&<div style={{padding:"20px 16px",textAlign:"center",fontSize:12,color:S.textMuted}}>All orders assigned ✓</div>}
          </div>
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`}}>
            <div style={{padding:"12px 16px",borderBottom:`1px solid ${S.border}`}}><span style={{fontSize:13,fontWeight:700,color:S.green}}>🟢 Online Riders</span></div>
            {riders.filter(r=>r.status==="online"||r.status==="on_delivery").map(r=>(
              <div key={r.id} onClick={()=>onViewRider(r.id)} style={{padding:"10px 16px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"space-between",transition:"background 0.15s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                <div style={{display:"flex",alignItems:"center",gap:10}}>
                  <div style={{width:8,height:8,borderRadius:"50%",background:r.status==="on_delivery"?S.purple:S.green}}/>
                  <div><div style={{fontSize:12,fontWeight:600}}>{r.name}</div><div style={{fontSize:10,color:S.textMuted}}>{r.vehicle} • {r.todayOrders} today</div></div>
                </div>
                {r.currentOrder?<span style={{fontSize:10,fontWeight:700,color:S.purple,fontFamily:"'Space Mono',monospace"}}>{r.currentOrder}</span>:<span style={{fontSize:10,fontWeight:700,color:S.green}}>Available</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ORDERS SCREEN ──────────────────────────────────────────────
function OrdersScreen({ orders, riders, selectedId, onSelect, onBack, onViewRider, onAssign, onChangeStatus, onUpdateOrder, addLog, eventLogs }) {
  const [statusFilter, setStatusFilter] = useState("All");
  const [search, setSearch] = useState("");

  if (selectedId) {
    const order = orders.find(o => o.id === selectedId);
    if (!order) return <div style={{color:S.textMuted}}>Order not found</div>;
    return <OrderDetail order={order} riders={riders} onBack={onBack} onViewRider={onViewRider} onAssign={onAssign} onChangeStatus={onChangeStatus} onUpdateOrder={onUpdateOrder} addLog={addLog} logs={eventLogs[order.id]||[]} />;
  }

  const tabs = ["All","Pending","Assigned","Picked Up","In Transit","Delivered","Cancelled","Failed"];
  const filtered = orders.filter(o => {
    if (statusFilter !== "All" && o.status !== statusFilter) return false;
    if (search) { const s = search.toLowerCase(); return o.id.toLowerCase().includes(s)||o.customer.toLowerCase().includes(s)||o.merchant.toLowerCase().includes(s)||o.customerPhone.includes(s); }
    return true;
  });

  return (
    <div>
      <div style={{display:"flex",gap:4,marginBottom:14,flexWrap:"wrap"}}>
        {tabs.map(t=>{const cnt=t==="All"?orders.length:orders.filter(o=>o.status===t).length; return (
          <button key={t} onClick={()=>setStatusFilter(t)} style={{padding:"7px 14px",borderRadius:8,border:`1px solid ${statusFilter===t?"transparent":S.border}`,cursor:"pointer",fontFamily:"inherit",fontSize:12,fontWeight:600,background:statusFilter===t?(STS[t]?STS[t].bg:S.goldPale):S.card,color:statusFilter===t?(STS[t]?STS[t].text:S.gold):S.textMuted}}>{t} <span style={{fontSize:10,opacity:0.7,marginLeft:4}}>{cnt}</span></button>
        );})}
      </div>
      <div style={{display:"flex",gap:10,marginBottom:14}}>
        <div style={{flex:1,background:S.card,borderRadius:10,border:`1px solid ${S.border}`,display:"flex",alignItems:"center",gap:8,padding:"0 12px"}}>
          <span style={{opacity:0.4}}>{I.search}</span>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search by Order ID, customer, merchant, phone..." style={{flex:1,background:"transparent",border:"none",color:S.text,fontSize:12,fontFamily:"inherit",height:38,outline:"none"}}/>
        </div>
        <button style={{display:"flex",alignItems:"center",gap:6,padding:"0 14px",borderRadius:10,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:12,fontFamily:"inherit"}}>{I.download} Export CSV</button>
      </div>

      <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
        <div style={{display:"grid",gridTemplateColumns:"110px 1fr 1fr 1.2fr 130px 80px 70px 80px",padding:"10px 16px",background:S.borderLight,fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",borderBottom:`1px solid ${S.border}`}}>
          <span>Order ID</span><span>Customer</span><span>Merchant</span><span>Route</span><span>Rider</span><span>Amount</span><span>COD</span><span>Status</span>
        </div>
        <div style={{maxHeight:"calc(100vh - 280px)",overflowY:"auto"}}>
          {filtered.map(o=>(
            <div key={o.id} onClick={()=>onSelect(o.id)} style={{display:"grid",gridTemplateColumns:"110px 1fr 1fr 1.2fr 130px 80px 70px 80px",padding:"12px 16px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",transition:"background 0.12s",alignItems:"center"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:12,fontWeight:700,color:S.gold,fontFamily:"'Space Mono',monospace"}}>{o.id}</span>
              <div><div style={{fontSize:12,fontWeight:600}}>{o.customer}</div><div style={{fontSize:10,color:S.textMuted}}>{o.customerPhone}</div></div>
              <span style={{fontSize:12,color:S.textDim}}>{o.merchant}</span>
              <div style={{fontSize:11,color:S.textMuted,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{o.pickup.split(",")[0]} → {o.dropoff.split(",")[0]}</div>
              <div>{o.rider?<div style={{display:"flex",alignItems:"center",gap:6}}><div style={{width:6,height:6,borderRadius:"50%",background:S.green}}/><span style={{fontSize:12}}>{o.rider}</span></div>:<span style={{fontSize:11,fontWeight:700,color:S.yellow}}>⚠ Unassigned</span>}</div>
              <span style={{fontSize:12,fontWeight:600,fontFamily:"'Space Mono',monospace"}}>₦{o.amount.toLocaleString()}</span>
              <span style={{fontSize:11,color:o.cod>0?S.green:S.textMuted,fontFamily:"'Space Mono',monospace"}}>{o.cod>0?`₦${(o.cod/1000).toFixed(0)}K`:"—"}</span>
              <Badge status={o.status}/>
            </div>
          ))}
          {filtered.length===0&&<div style={{padding:"40px 0",textAlign:"center",fontSize:13,color:S.textMuted}}>No orders match filters</div>}
        </div>
      </div>
    </div>
  );
}

// ─── ORDER DETAIL (all fixes) ───────────────────────────────────
function OrderDetail({ order, riders, onBack, onViewRider, onAssign, onChangeStatus, onUpdateOrder, addLog, logs }) {
  const [showAssign, setShowAssign] = useState(false);
  const [editPickup, setEditPickup] = useState(false);
  const [editDropoff, setEditDropoff] = useState(false);
  const [pickupVal, setPickupVal] = useState(order.pickup);
  const [dropoffVal, setDropoffVal] = useState(order.dropoff);
  const [editPrice, setEditPrice] = useState(false);
  const [priceVal, setPriceVal] = useState(String(order.amount));
  const [showStatusMenu, setShowStatusMenu] = useState(false);

  const rider = order.riderId ? riders.find(r => r.id === order.riderId) : null;
  const isTerminal = ["Delivered","Cancelled","Failed"].includes(order.status);

  // Status flow for progression
  const nextStatuses = () => {
    const flow = ["Pending","Assigned","Picked Up","In Transit","Delivered"];
    const idx = flow.indexOf(order.status);
    const opts = [];
    if (idx >= 0 && idx < flow.length - 1) opts.push(flow[idx + 1]);
    if (!isTerminal) { opts.push("Cancelled"); opts.push("Failed"); }
    return opts;
  };

  const savePickup = () => { onUpdateOrder(order.id, { pickup: pickupVal }); addLog(order.id, `Pickup address changed to: ${pickupVal}`, "Dispatch", "edit"); setEditPickup(false); };
  const saveDropoff = () => { onUpdateOrder(order.id, { dropoff: dropoffVal }); addLog(order.id, `Dropoff address changed to: ${dropoffVal}`, "Dispatch", "edit"); setEditDropoff(false); };
  const savePrice = () => { const n = parseInt(priceVal)||order.amount; onUpdateOrder(order.id, { amount: n }); addLog(order.id, `Price changed to ₦${n.toLocaleString()}`, "Dispatch", "edit"); setEditPrice(false); };

  const logColors = { create:S.gold, payment:S.blue, assign:S.green, status:S.textDim, pickup:S.purple, transit:S.gold, cod:S.green, delivered:S.green, settlement:S.gold, cancel:S.red, fail:S.red, edit:S.blue };

  const iStyle = { width:"100%", border:`1.5px solid ${S.border}`, borderRadius:8, padding:"8px 12px", fontSize:13, fontFamily:"inherit", color:S.navy, background:"#fff" };

  return (
    <div>
      <button onClick={onBack} style={{display:"flex",alignItems:"center",gap:6,padding:0,background:"none",border:"none",cursor:"pointer",color:S.textDim,fontSize:13,fontWeight:600,fontFamily:"inherit",marginBottom:16}}>{I.back} Back to Orders</button>

      {/* Top bar */}
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:"14px 20px",marginBottom:16}}>
        <div style={{display:"flex",alignItems:"center",gap:14,flexWrap:"wrap"}}>
          <span style={{fontSize:18,fontWeight:800,color:S.gold,fontFamily:"'Space Mono',monospace"}}>{order.id}</span>
          <Badge status={order.status}/>
          <span style={{fontSize:12,color:S.textMuted}}>{order.created}</span>
          <span style={{fontSize:10,padding:"3px 8px",borderRadius:6,background:order.vehicle==="Bike"?S.goldPale:order.vehicle==="Car"?S.blueBg:S.purpleBg,color:order.vehicle==="Bike"?S.gold:order.vehicle==="Car"?S.blue:S.purple,fontWeight:700}}>{order.vehicle}</span>
          {order.cod>0&&<span style={{fontSize:10,padding:"3px 8px",borderRadius:6,background:S.greenBg,color:S.green,fontWeight:700}}>💵 COD ₦{order.cod.toLocaleString()}</span>}
        </div>
        <div style={{display:"flex",gap:8}}>
          <button style={{display:"flex",alignItems:"center",gap:5,padding:"7px 14px",borderRadius:8,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:11,fontWeight:600,fontFamily:"inherit"}}>{I.print} Label</button>
          <button style={{display:"flex",alignItems:"center",gap:5,padding:"7px 14px",borderRadius:8,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:11,fontWeight:600,fontFamily:"inherit"}}>{I.download} Receipt</button>
          {!isTerminal&&<button onClick={()=>onChangeStatus(order.id,"Cancelled")} style={{padding:"7px 14px",borderRadius:8,border:"none",background:S.redBg,color:S.red,cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:"inherit"}}>Cancel</button>}
        </div>
      </div>

      {/* STATUS PROGRESSION BAR */}
      {!isTerminal && (
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:"14px 20px",marginBottom:16}}>
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:10}}>
            <span style={{fontSize:11,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px"}}>Status Progression</span>
            <div style={{position:"relative"}}>
              <button onClick={()=>setShowStatusMenu(!showStatusMenu)} style={{padding:"6px 14px",borderRadius:8,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:11,fontWeight:600,fontFamily:"inherit"}}>Change Status ▾</button>
              {showStatusMenu && (
                <div style={{position:"absolute",right:0,top:"100%",marginTop:4,background:S.card,border:`1px solid ${S.border}`,borderRadius:10,boxShadow:"0 8px 24px rgba(0,0,0,0.12)",zIndex:10,minWidth:180,overflow:"hidden"}}>
                  {nextStatuses().map(ns=>(
                    <button key={ns} onClick={()=>{onChangeStatus(order.id,ns);setShowStatusMenu(false);}} style={{display:"block",width:"100%",padding:"10px 16px",border:"none",background:"transparent",cursor:"pointer",fontSize:12,fontWeight:600,fontFamily:"inherit",textAlign:"left",color:STS[ns]?STS[ns].text:S.text,transition:"background 0.12s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      → {ns}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:0}}>
            {["Pending","Assigned","Picked Up","In Transit","Delivered"].map((st,i,arr)=>{
              const idx = arr.indexOf(order.status);
              const done = i <= idx;
              const current = i === idx;
              return (
                <div key={st} style={{display:"flex",alignItems:"center",flex:1}}>
                  <div style={{display:"flex",flexDirection:"column",alignItems:"center",flex:0}}>
                    <div style={{width:current?28:22,height:current?28:22,borderRadius:"50%",background:done?(STS[st]?STS[st].bg:"#eee"):"#f1f5f9",border:`2px solid ${done?(STS[st]?STS[st].text:S.gold):S.border}`,display:"flex",alignItems:"center",justifyContent:"center",transition:"all 0.2s"}}>
                      {done && i<idx ? <span style={{color:STS[st]?STS[st].text:S.green}}>{I.check}</span> : current ? <div style={{width:8,height:8,borderRadius:"50%",background:STS[st]?STS[st].text:S.gold}}/> : null}
                    </div>
                    <span style={{fontSize:9,fontWeight:done?700:500,color:done?(STS[st]?STS[st].text:S.gold):S.textMuted,marginTop:4,whiteSpace:"nowrap"}}>{st}</span>
                  </div>
                  {i<arr.length-1&&<div style={{flex:1,height:2,background:done&&i<idx?S.green:S.border,margin:"0 4px 16px 4px",transition:"background 0.3s"}}/>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"1fr 360px",gap:16}}>
        {/* LEFT */}
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          {/* Customer + Merchant */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
              <div style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:10}}>Customer</div>
              <div style={{fontSize:14,fontWeight:700,marginBottom:2}}>{order.customer}</div>
              <div style={{fontSize:12,color:S.textDim,fontFamily:"'Space Mono',monospace",marginBottom:8}}>{order.customerPhone}</div>
              <div style={{display:"flex",gap:6}}>
                <a href={`tel:${order.customerPhone}`} style={{display:"flex",alignItems:"center",gap:4,padding:"5px 10px",borderRadius:6,background:S.goldPale,color:S.gold,fontSize:10,fontWeight:600,textDecoration:"none"}}>{I.phone} Call</a>
                <a href={`https://wa.me/234${order.customerPhone.slice(1)}`} target="_blank" rel="noreferrer" style={{display:"flex",alignItems:"center",gap:4,padding:"5px 10px",borderRadius:6,background:S.greenBg,color:S.green,fontSize:10,fontWeight:600,textDecoration:"none"}}>💬 WhatsApp</a>
              </div>
            </div>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
              <div style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:10}}>Merchant</div>
              <div style={{fontSize:14,fontWeight:700,marginBottom:2}}>{order.merchant}</div>
              <div style={{fontSize:12,color:S.textDim,marginBottom:8}}>Via Merchant Portal</div>
              <span style={{fontSize:10,padding:"3px 8px",borderRadius:6,background:S.goldPale,color:S.gold,fontWeight:700}}>VERIFIED</span>
            </div>
          </div>

          {/* ADDRESSES — EDITABLE */}
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
            <div style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:12}}>Route</div>
            <div style={{display:"flex",gap:12,alignItems:"stretch"}}>
              <div style={{display:"flex",flexDirection:"column",alignItems:"center",paddingTop:4}}>
                <div style={{width:10,height:10,borderRadius:"50%",background:S.green}}/><div style={{width:2,flex:1,background:S.border,margin:"4px 0"}}/><div style={{width:10,height:10,borderRadius:"50%",background:S.red}}/>
              </div>
              <div style={{flex:1,display:"flex",flexDirection:"column",gap:14}}>
                {/* Pickup */}
                <div>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:4}}>
                    <span style={{fontSize:10,fontWeight:700,color:S.green}}>PICKUP</span>
                    {!isTerminal && !editPickup && <button onClick={()=>setEditPickup(true)} style={{display:"flex",alignItems:"center",gap:3,background:"none",border:"none",color:S.gold,fontSize:10,fontWeight:600,cursor:"pointer",fontFamily:"inherit"}}>{I.edit} Edit</button>}
                  </div>
                  {editPickup ? (
                    <div style={{display:"flex",gap:8}}>
                      <input value={pickupVal} onChange={e=>setPickupVal(e.target.value)} style={{...iStyle,flex:1}} autoFocus/>
                      <button onClick={savePickup} style={{padding:"8px 14px",borderRadius:8,border:"none",background:S.green,color:"#fff",cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:"inherit"}}>Save</button>
                      <button onClick={()=>{setEditPickup(false);setPickupVal(order.pickup);}} style={{padding:"8px 10px",borderRadius:8,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:11,fontFamily:"inherit"}}>Cancel</button>
                    </div>
                  ) : (
                    <div style={{fontSize:13,fontWeight:600}}>{order.pickup}</div>
                  )}
                </div>
                {/* Dropoff */}
                <div>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:4}}>
                    <span style={{fontSize:10,fontWeight:700,color:S.red}}>DROPOFF</span>
                    {!isTerminal && !editDropoff && <button onClick={()=>setEditDropoff(true)} style={{display:"flex",alignItems:"center",gap:3,background:"none",border:"none",color:S.gold,fontSize:10,fontWeight:600,cursor:"pointer",fontFamily:"inherit"}}>{I.edit} Edit</button>}
                  </div>
                  {editDropoff ? (
                    <div style={{display:"flex",gap:8}}>
                      <input value={dropoffVal} onChange={e=>setDropoffVal(e.target.value)} style={{...iStyle,flex:1}} autoFocus/>
                      <button onClick={saveDropoff} style={{padding:"8px 14px",borderRadius:8,border:"none",background:S.green,color:"#fff",cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:"inherit"}}>Save</button>
                      <button onClick={()=>{setEditDropoff(false);setDropoffVal(order.dropoff);}} style={{padding:"8px 10px",borderRadius:8,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:11,fontFamily:"inherit"}}>Cancel</button>
                    </div>
                  ) : (
                    <div style={{fontSize:13,fontWeight:600}}>{order.dropoff}</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Package + Pricing */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
              <div style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:10}}>Package</div>
              <div style={{fontSize:13,marginBottom:4}}>Type: <span style={{fontWeight:700}}>{order.pkg}</span></div>
              <div style={{fontSize:13}}>Vehicle: <span style={{fontWeight:700}}>{order.vehicle}</span></div>
            </div>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:10}}>
                <span style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px"}}>Pricing</span>
                {!isTerminal && !editPrice && <button onClick={()=>setEditPrice(true)} style={{display:"flex",alignItems:"center",gap:3,background:"none",border:"none",color:S.gold,fontSize:10,fontWeight:600,cursor:"pointer",fontFamily:"inherit"}}>{I.edit} Edit</button>}
              </div>
              <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:S.textDim,marginBottom:4}}>
                <span>Delivery fee</span>
                {editPrice ? (
                  <div style={{display:"flex",gap:4,alignItems:"center"}}>
                    <span>₦</span><input value={priceVal} onChange={e=>setPriceVal(e.target.value)} style={{width:80,border:`1px solid ${S.border}`,borderRadius:6,padding:"3px 8px",fontSize:12,fontFamily:"'Space Mono',monospace",textAlign:"right"}}/>
                    <button onClick={savePrice} style={{padding:"3px 8px",borderRadius:6,border:"none",background:S.green,color:"#fff",fontSize:10,fontWeight:700,cursor:"pointer"}}>✓</button>
                    <button onClick={()=>setEditPrice(false)} style={{padding:"3px 6px",borderRadius:6,border:`1px solid ${S.border}`,background:S.card,color:S.textMuted,fontSize:10,cursor:"pointer"}}>✕</button>
                  </div>
                ) : (
                  <span style={{fontWeight:700,fontFamily:"'Space Mono',monospace"}}>₦{order.amount.toLocaleString()}</span>
                )}
              </div>
              {order.cod>0&&<>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:S.textDim,marginBottom:4}}><span>COD collection</span><span style={{fontWeight:700,color:S.green,fontFamily:"'Space Mono',monospace"}}>₦{order.cod.toLocaleString()}</span></div>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:12,color:S.textDim,marginBottom:4}}><span>COD fee</span><span style={{fontWeight:700,fontFamily:"'Space Mono',monospace"}}>₦{order.codFee.toLocaleString()}</span></div>
              </>}
              {!editPrice && <div style={{display:"flex",justifyContent:"space-between",fontSize:13,fontWeight:700,borderTop:`1px solid ${S.border}`,paddingTop:6,marginTop:4}}><span>Wallet charged</span><span style={{fontFamily:"'Space Mono',monospace"}}>₦{(order.amount+order.codFee).toLocaleString()}</span></div>}
            </div>
          </div>

          {/* RIDER ASSIGNMENT — shows availability clearly, persists */}
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
              <span style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px"}}>Assigned Rider</span>
              {!isTerminal && <button onClick={()=>setShowAssign(!showAssign)} style={{padding:"5px 14px",borderRadius:8,border:"none",cursor:"pointer",fontFamily:"inherit",background:rider?S.blueBg:S.yellowBg,color:rider?S.blue:S.yellow,fontSize:11,fontWeight:700}}>{rider?"Reassign":"Assign Rider"}</button>}
            </div>
            {rider ? (
              <div onClick={()=>onViewRider(rider.id)} style={{display:"flex",alignItems:"center",gap:14,padding:"10px 12px",background:S.borderLight,borderRadius:10,cursor:"pointer"}}>
                <div style={{width:40,height:40,borderRadius:10,background:S.goldPale,display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,fontWeight:800,color:S.gold}}>{rider.name.split(" ").map(n=>n[0]).join("")}</div>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:700}}>{rider.name}</div>
                  <div style={{fontSize:11,color:S.textDim}}>{rider.phone} • {rider.vehicle} • ⭐ {rider.rating}</div>
                </div>
                <div style={{textAlign:"right"}}>
                  <div style={{fontSize:10,fontWeight:700,padding:"3px 8px",borderRadius:6,background:rider.status==="on_delivery"?S.purpleBg:S.greenBg,color:rider.status==="on_delivery"?S.purple:S.green}}>
                    {rider.status==="on_delivery"?"ON DELIVERY":"AVAILABLE"}
                  </div>
                  <div style={{fontSize:10,color:S.textMuted,marginTop:2}}>{rider.todayOrders} orders today</div>
                </div>
              </div>
            ) : (
              <div style={{padding:"12px",borderRadius:10,background:S.yellowBg,border:`1px dashed ${S.yellow}`,textAlign:"center",fontSize:12,fontWeight:600,color:S.yellow}}>⚠ No rider assigned — click "Assign Rider" above</div>
            )}

            {/* Rider selector dropdown */}
            {showAssign && (
              <div style={{marginTop:12,borderTop:`1px solid ${S.border}`,paddingTop:12}}>
                <div style={{fontSize:11,fontWeight:700,color:S.textMuted,marginBottom:8}}>SELECT RIDER</div>
                {riders.filter(r=>r.status!=="offline").map(r=>{
                  const busy = !!r.currentOrder && r.currentOrder !== order.id;
                  const available = !r.currentOrder || r.currentOrder === order.id;
                  return (
                    <div key={r.id} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"8px 10px",borderRadius:8,marginBottom:4,background:available?S.borderLight:"transparent",border:`1px solid ${available?S.border:"transparent"}`,opacity:busy?0.5:1}}>
                      <div style={{display:"flex",alignItems:"center",gap:10}}>
                        <div style={{width:8,height:8,borderRadius:"50%",background:r.status==="on_delivery"?S.purple:S.green}}/>
                        <div>
                          <div style={{fontSize:12,fontWeight:600}}>{r.name} <span style={{fontSize:10,color:S.textMuted}}>({r.vehicle})</span></div>
                          <div style={{fontSize:10,color:S.textMuted}}>
                            ⭐ {r.rating} • {r.todayOrders} today
                            {busy && <span style={{color:S.purple,fontWeight:700,marginLeft:6}}>📦 Fulfilling {r.currentOrder}</span>}
                            {available && r.status==="online" && <span style={{color:S.green,fontWeight:700,marginLeft:6}}>✓ Available</span>}
                          </div>
                        </div>
                      </div>
                      {available ? (
                        <button onClick={()=>{onAssign(order.id,r.id);setShowAssign(false);}} style={{padding:"5px 14px",borderRadius:8,border:"none",cursor:"pointer",background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,fontSize:10,fontWeight:800,fontFamily:"inherit"}}>Assign</button>
                      ) : (
                        <span style={{fontSize:10,color:S.textMuted,fontStyle:"italic"}}>Busy</span>
                      )}
                    </div>
                  );
                })}
                {riders.filter(r=>r.status==="offline").length>0 && (
                  <div style={{fontSize:10,color:S.textMuted,marginTop:8,paddingTop:8,borderTop:`1px solid ${S.borderLight}`}}>
                    {riders.filter(r=>r.status==="offline").length} rider(s) offline: {riders.filter(r=>r.status==="offline").map(r=>r.name).join(", ")}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT — Map + Event Log */}
        <div style={{display:"flex",flexDirection:"column",gap:14,alignSelf:"start"}}>
          {/* Delivery Route — real Leaflet map */}
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:12}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:10}}>
              <div style={{fontSize:12,fontWeight:700}}>Delivery Route</div>
              {rider && rider.lat && rider.lng ? (
                <div style={{display:"flex",alignItems:"center",gap:4,fontSize:9,fontWeight:600,color:S.green}}>
                  <span style={{width:6,height:6,borderRadius:"50%",background:S.green,display:"inline-block"}}/>
                  Rider location live
                </div>
              ) : rider ? (
                <div style={{fontSize:9,color:S.textMuted,fontWeight:600}}>GPS unavailable</div>
              ) : null}
            </div>
            <DeliveryRouteMap order={order} rider={rider} />
            <div style={{display:"flex",justifyContent:"space-between",marginTop:10}}>
              <div>
                <div style={{fontSize:9,color:S.textMuted,fontWeight:600}}>📦 PICKUP</div>
                <div style={{fontSize:11,fontWeight:600,color:S.navy}}>{order.pickup.split(",")[0]}</div>
              </div>
              <div style={{fontSize:16,color:S.textMuted,alignSelf:"center"}}>→</div>
              <div style={{textAlign:"right"}}>
                <div style={{fontSize:9,color:S.textMuted,fontWeight:600}}>🏠 DROPOFF</div>
                <div style={{fontSize:11,fontWeight:600,color:S.navy}}>{order.dropoff.split(",")[0]}</div>
              </div>
            </div>
          </div>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
          <div style={{padding:"14px 18px",borderBottom:`1px solid ${S.border}`,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
            <span style={{fontSize:13,fontWeight:700}}>Event Log</span>
            <span style={{fontSize:10,color:S.textMuted}}>{logs.length} events</span>
          </div>
          <div style={{padding:"14px 18px",maxHeight:600,overflowY:"auto"}}>
            {logs.map((log,i)=>(
              <div key={i} style={{display:"flex",gap:12,position:"relative",paddingBottom:i<logs.length-1?16:0}}>
                {i<logs.length-1&&<div style={{position:"absolute",left:5,top:14,bottom:0,width:2,background:S.border}}/>}
                <div style={{width:12,height:12,borderRadius:"50%",background:logColors[log.type]||S.textMuted,flexShrink:0,marginTop:2,position:"relative",zIndex:1,boxShadow:`0 0 6px ${logColors[log.type]||S.textMuted}30`}}/>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
                    <div style={{fontSize:12,fontWeight:500,lineHeight:1.4}}>{log.event}</div>
                    <span style={{fontSize:10,color:S.textMuted,fontFamily:"'Space Mono',monospace",flexShrink:0,marginLeft:8}}>{log.time}</span>
                  </div>
                  <div style={{fontSize:10,color:S.textMuted,marginTop:1}}>{log.by}</div>
                </div>
              </div>
            ))}
            {logs.length===0&&<div style={{textAlign:"center",color:S.textMuted,fontSize:12,padding:20}}>No events yet</div>}
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

// ─── RIDERS SCREEN ──────────────────────────────────────────────
function RidersScreen({ riders, orders, selectedId, onSelect, onBack, onViewOrder }) {
  const [filter, setFilter] = useState("All");
  const [search, setSearch] = useState("");

  if (selectedId) {
    const rider = riders.find(r=>r.id===selectedId);
    if (!rider) return <div style={{color:S.textMuted}}>Rider not found</div>;
    const rOrders = orders.filter(o=>o.riderId===rider.id);
    return (
      <div>
        <button onClick={onBack} style={{display:"flex",alignItems:"center",gap:6,padding:0,background:"none",border:"none",cursor:"pointer",color:S.textDim,fontSize:13,fontWeight:600,fontFamily:"inherit",marginBottom:16}}>{I.back} Back to Riders</button>
        <div style={{display:"grid",gridTemplateColumns:"300px 1fr",gap:16}}>
          <div style={{display:"flex",flexDirection:"column",gap:12}}>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:20,textAlign:"center"}}>
              <div style={{width:64,height:64,borderRadius:16,margin:"0 auto 10px",background:S.goldPale,display:"flex",alignItems:"center",justifyContent:"center",fontSize:22,fontWeight:800,color:S.gold}}>{rider.name.split(" ").map(n=>n[0]).join("")}</div>
              <div style={{fontSize:18,fontWeight:800}}>{rider.name}</div>
              <div style={{fontSize:12,color:S.textDim,fontFamily:"'Space Mono',monospace",marginTop:2}}>{rider.phone}</div>
              <span style={{display:"inline-block",marginTop:8,fontSize:10,fontWeight:700,padding:"3px 10px",borderRadius:6,background:rider.status==="online"?S.greenBg:rider.status==="on_delivery"?S.purpleBg:S.redBg,color:rider.status==="online"?S.green:rider.status==="on_delivery"?S.purple:S.red}}>{rider.status==="online"?"ONLINE":rider.status==="on_delivery"?"ON DELIVERY":"OFFLINE"}</span>
              {rider.currentOrder && <div style={{fontSize:11,color:S.purple,fontWeight:700,fontFamily:"'Space Mono',monospace",marginTop:6}}>📦 {rider.currentOrder}</div>}
              <div style={{display:"flex",gap:6,marginTop:12}}>
                <a href={`tel:${rider.phone}`} style={{flex:1,display:"flex",alignItems:"center",justifyContent:"center",gap:5,padding:"8px 0",borderRadius:8,background:S.goldPale,color:S.gold,fontSize:11,fontWeight:600,textDecoration:"none"}}>{I.phone} Call</a>
                <a href={`https://wa.me/234${rider.phone.slice(1)}`} target="_blank" rel="noreferrer" style={{flex:1,display:"flex",alignItems:"center",justifyContent:"center",gap:5,padding:"8px 0",borderRadius:8,background:S.greenBg,color:S.green,fontSize:11,fontWeight:600,textDecoration:"none"}}>💬 WhatsApp</a>
              </div>
              <div style={{marginTop:14,paddingTop:14,borderTop:`1px solid ${S.border}`,textAlign:"left"}}>
                {[{l:"Vehicle",v:rider.vehicle},{l:"ID",v:rider.id},{l:"Joined",v:rider.joined}].map(f=>(
                  <div key={f.l} style={{display:"flex",justifyContent:"space-between",padding:"6px 0"}}><span style={{fontSize:12,color:S.textMuted}}>{f.l}</span><span style={{fontSize:12,fontWeight:600}}>{f.v}</span></div>
                ))}
              </div>
            </div>
            <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,padding:16}}>
              <div style={{fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:12}}>Performance</div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                {[{l:"Total Deliveries",v:rider.totalDeliveries.toLocaleString(),c:S.text},{l:"Completion",v:`${rider.completionRate}%`,c:rider.completionRate>=95?S.green:S.yellow},{l:"Avg Time",v:rider.avgTime,c:S.text},{l:"Rating",v:`⭐ ${rider.rating}`,c:S.gold},{l:"Today Orders",v:rider.todayOrders,c:S.gold},{l:"Today Earnings",v:`₦${rider.todayEarnings.toLocaleString()}`,c:S.green}].map(s=>(
                  <div key={s.l} style={{padding:10,background:S.borderLight,borderRadius:8,textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:s.c,fontFamily:"'Space Mono',monospace"}}>{s.v}</div><div style={{fontSize:9,color:S.textMuted,marginTop:2}}>{s.l}</div></div>
                ))}
              </div>
            </div>
          </div>
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
            <div style={{padding:"14px 18px",borderBottom:`1px solid ${S.border}`}}><span style={{fontSize:13,fontWeight:700}}>Order History ({rOrders.length})</span></div>
            <div style={{display:"grid",gridTemplateColumns:"100px 1fr 1fr 80px 70px 70px",padding:"8px 16px",fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",borderBottom:`1px solid ${S.border}`}}>
              <span>ID</span><span>Merchant</span><span>Route</span><span>Amount</span><span>COD</span><span>Status</span>
            </div>
            <div style={{maxHeight:400,overflowY:"auto"}}>
              {rOrders.map(o=>(
                <div key={o.id} onClick={()=>onViewOrder(o.id)} style={{display:"grid",gridTemplateColumns:"100px 1fr 1fr 80px 70px 70px",padding:"10px 16px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",alignItems:"center",transition:"background 0.12s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <span style={{fontSize:11,fontWeight:700,color:S.gold,fontFamily:"'Space Mono',monospace"}}>{o.id}</span>
                  <span style={{fontSize:11,color:S.textDim}}>{o.merchant}</span>
                  <span style={{fontSize:11,color:S.textMuted,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{o.pickup.split(",")[0]} → {o.dropoff.split(",")[0]}</span>
                  <span style={{fontSize:11,fontWeight:600,fontFamily:"'Space Mono',monospace"}}>₦{o.amount.toLocaleString()}</span>
                  <span style={{fontSize:11,color:o.cod>0?S.green:S.textMuted,fontFamily:"'Space Mono',monospace"}}>{o.cod>0?`₦${(o.cod/1000).toFixed(0)}K`:"—"}</span>
                  <Badge status={o.status}/>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  const sMap = {"Online":"online","On Delivery":"on_delivery","Offline":"offline"};
  const filtered = riders.filter(r=>{ if(filter!=="All"&&r.status!==sMap[filter]) return false; if(search){const s=search.toLowerCase();return r.name.toLowerCase().includes(s)||r.phone.includes(s);} return true; });
  const sc = (s)=>s==="online"?S.green:s==="on_delivery"?S.purple:S.textMuted;

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16}}>
        <StatCard label="Total Riders" value={riders.length}/>
        <StatCard label="Online" value={riders.filter(r=>r.status==="online").length} color={S.green}/>
        <StatCard label="On Delivery" value={riders.filter(r=>r.status==="on_delivery").length} color={S.purple}/>
        <StatCard label="Deliveries Today" value={riders.reduce((s,r)=>s+r.todayOrders,0)} color={S.gold}/>
      </div>
      <div style={{display:"flex",gap:10,marginBottom:14}}>
        <div style={{display:"flex",gap:4}}>
          {["All","Online","On Delivery","Offline"].map(f=>(<button key={f} onClick={()=>setFilter(f)} style={{padding:"7px 14px",borderRadius:8,border:`1px solid ${filter===f?"transparent":S.border}`,cursor:"pointer",fontFamily:"inherit",fontSize:12,fontWeight:600,background:filter===f?S.goldPale:S.card,color:filter===f?S.gold:S.textMuted}}>{f}</button>))}
        </div>
        <div style={{flex:1,background:S.card,borderRadius:10,border:`1px solid ${S.border}`,display:"flex",alignItems:"center",gap:8,padding:"0 12px"}}>
          <span style={{opacity:0.4}}>{I.search}</span>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search riders..." style={{flex:1,background:"transparent",border:"none",color:S.text,fontSize:12,fontFamily:"inherit",height:38,outline:"none"}}/>
        </div>
      </div>
      <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
        <div style={{display:"grid",gridTemplateColumns:"60px 1fr 100px 80px 90px 110px 100px 70px",padding:"10px 16px",background:S.borderLight,fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",borderBottom:`1px solid ${S.border}`}}>
          <span>ID</span><span>Rider</span><span>Phone</span><span>Vehicle</span><span>Status</span><span>Current Order</span><span>Today</span><span>Rating</span>
        </div>
        <div style={{maxHeight:"calc(100vh - 310px)",overflowY:"auto"}}>
          {filtered.map(r=>(
            <div key={r.id} onClick={()=>onSelect(r.id)} style={{display:"grid",gridTemplateColumns:"60px 1fr 100px 80px 90px 110px 100px 70px",padding:"12px 16px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",transition:"background 0.12s",alignItems:"center"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:11,fontWeight:700,color:S.textDim,fontFamily:"'Space Mono',monospace"}}>{r.id}</span>
              <div style={{display:"flex",alignItems:"center",gap:10}}>
                <div style={{width:32,height:32,borderRadius:8,background:`${sc(r.status)}12`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:800,color:sc(r.status)}}>{r.name.split(" ").map(n=>n[0]).join("")}</div>
                <span style={{fontSize:12,fontWeight:600}}>{r.name}</span>
              </div>
              <span style={{fontSize:11,color:S.textDim,fontFamily:"'Space Mono',monospace"}}>{r.phone}</span>
              <span style={{fontSize:11,color:S.textDim}}>{r.vehicle}</span>
              <span style={{fontSize:10,fontWeight:700,padding:"3px 8px",borderRadius:6,background:`${sc(r.status)}12`,color:sc(r.status)}}>{r.status==="online"?"Online":r.status==="on_delivery"?"On Delivery":"Offline"}</span>
              <span style={{fontSize:11,color:r.currentOrder?S.purple:S.textMuted,fontWeight:r.currentOrder?700:400,fontFamily:"'Space Mono',monospace"}}>{r.currentOrder||"— Available"}</span>
              <div><span style={{fontSize:12,fontWeight:700}}>{r.todayOrders} orders</span><div style={{fontSize:10,color:S.textMuted}}>₦{r.todayEarnings.toLocaleString()}</div></div>
              <span style={{fontSize:12,color:S.gold}}>⭐ {r.rating}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── MERCHANTS ──────────────────────────────────────────────────
function MerchantsScreen({ data }) {
  const [search, setSearch] = useState("");
  const f = data.filter(m=>!search||m.name.toLowerCase().includes(search.toLowerCase())||m.contact.toLowerCase().includes(search.toLowerCase()));
  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16}}>
        <StatCard label="Total Merchants" value={data.length}/>
        <StatCard label="Active" value={data.filter(m=>m.status==="Active").length} color={S.green}/>
        <StatCard label="This Month" value={data.reduce((s,m)=>s+m.monthOrders,0)} color={S.gold}/>
        <StatCard label="Wallet Balance" value={`₦${(data.reduce((s,m)=>s+m.walletBalance,0)/1000).toFixed(0)}K`} color={S.gold}/>
      </div>
      <div style={{marginBottom:14,background:S.card,borderRadius:10,border:`1px solid ${S.border}`,display:"flex",alignItems:"center",gap:8,padding:"0 12px"}}>
        <span style={{opacity:0.4}}>{I.search}</span>
        <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search merchants..." style={{flex:1,background:"transparent",border:"none",color:S.text,fontSize:12,fontFamily:"inherit",height:38,outline:"none"}}/>
      </div>
      <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
        <div style={{display:"grid",gridTemplateColumns:"60px 1fr 1fr 90px 70px 70px 100px 70px 80px",padding:"10px 16px",background:S.borderLight,fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",borderBottom:`1px solid ${S.border}`}}>
          <span>ID</span><span>Business</span><span>Contact</span><span>Category</span><span>Total</span><span>Month</span><span>Wallet</span><span>Status</span><span>Joined</span>
        </div>
        {f.map(m=>(<div key={m.id} style={{display:"grid",gridTemplateColumns:"60px 1fr 1fr 90px 70px 70px 100px 70px 80px",padding:"12px 16px",borderBottom:`1px solid ${S.borderLight}`,alignItems:"center",cursor:"pointer",transition:"background 0.12s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
          <span style={{fontSize:11,color:S.textMuted,fontFamily:"'Space Mono',monospace"}}>{m.id}</span>
          <span style={{fontSize:12,fontWeight:700}}>{m.name}</span>
          <div><div style={{fontSize:12}}>{m.contact}</div><div style={{fontSize:10,color:S.textMuted,fontFamily:"'Space Mono',monospace"}}>{m.phone}</div></div>
          <span style={{fontSize:11,padding:"2px 8px",borderRadius:4,background:S.borderLight,color:S.textDim}}>{m.category}</span>
          <span style={{fontSize:12,fontWeight:600}}>{m.totalOrders}</span>
          <span style={{fontSize:12,fontWeight:700,color:S.gold}}>{m.monthOrders}</span>
          <span style={{fontSize:12,fontWeight:600,color:S.gold,fontFamily:"'Space Mono',monospace"}}>₦{m.walletBalance.toLocaleString()}</span>
          <span style={{fontSize:10,fontWeight:700,padding:"3px 8px",borderRadius:6,background:m.status==="Active"?S.greenBg:S.redBg,color:m.status==="Active"?S.green:S.red}}>{m.status}</span>
          <span style={{fontSize:11,color:S.textMuted}}>{m.joined}</span>
        </div>))}
      </div>
    </div>
  );
}

// ─── CUSTOMERS ──────────────────────────────────────────────────
function CustomersScreen({ data }) {
  const [search, setSearch] = useState("");
  const f = data.filter(c=>!search||c.name.toLowerCase().includes(search.toLowerCase())||c.phone.includes(search)||c.email.toLowerCase().includes(search.toLowerCase()));
  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16}}>
        <StatCard label="Total Customers" value={data.length}/>
        <StatCard label="Total Orders" value={data.reduce((s,c)=>s+c.totalOrders,0)} color={S.gold}/>
        <StatCard label="Revenue" value={`₦${(data.reduce((s,c)=>s+c.totalSpent,0)/1e6).toFixed(1)}M`} color={S.gold}/>
        <StatCard label="Avg Orders" value={(data.reduce((s,c)=>s+c.totalOrders,0)/data.length).toFixed(1)} color={S.green}/>
      </div>
      <div style={{display:"flex",gap:10,marginBottom:14}}>
        <div style={{flex:1,background:S.card,borderRadius:10,border:`1px solid ${S.border}`,display:"flex",alignItems:"center",gap:8,padding:"0 12px"}}>
          <span style={{opacity:0.4}}>{I.search}</span>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search by name, phone, email..." style={{flex:1,background:"transparent",border:"none",color:S.text,fontSize:12,fontFamily:"inherit",height:38,outline:"none"}}/>
        </div>
        <button style={{display:"flex",alignItems:"center",gap:6,padding:"0 14px",borderRadius:10,border:`1px solid ${S.border}`,background:S.card,color:S.textDim,cursor:"pointer",fontSize:12,fontFamily:"inherit"}}>{I.download} Export</button>
      </div>
      <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
        <div style={{display:"grid",gridTemplateColumns:"60px 1fr 110px 1fr 70px 70px 100px 1fr",padding:"10px 16px",background:S.borderLight,fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px",borderBottom:`1px solid ${S.border}`}}>
          <span>ID</span><span>Name</span><span>Phone</span><span>Email</span><span>Orders</span><span>Last</span><span>Spent</span><span>Fav Merchant</span>
        </div>
        {f.map(c=>(<div key={c.id} style={{display:"grid",gridTemplateColumns:"60px 1fr 110px 1fr 70px 70px 100px 1fr",padding:"12px 16px",borderBottom:`1px solid ${S.borderLight}`,alignItems:"center",cursor:"pointer",transition:"background 0.12s"}} onMouseEnter={e=>e.currentTarget.style.background=S.borderLight} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
          <span style={{fontSize:11,color:S.textMuted,fontFamily:"'Space Mono',monospace"}}>{c.id}</span>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{width:30,height:30,borderRadius:8,background:S.goldPale,display:"flex",alignItems:"center",justifyContent:"center",fontSize:10,fontWeight:800,color:S.gold}}>{c.name.split(" ").map(n=>n[0]).join("")}</div>
            <span style={{fontSize:12,fontWeight:600}}>{c.name}</span>
          </div>
          <span style={{fontSize:11,color:S.textDim,fontFamily:"'Space Mono',monospace"}}>{c.phone}</span>
          <span style={{fontSize:11,color:S.textDim}}>{c.email}</span>
          <span style={{fontSize:12,fontWeight:700,color:S.gold}}>{c.totalOrders}</span>
          <span style={{fontSize:11,color:S.textMuted}}>{c.lastOrder}</span>
          <span style={{fontSize:12,fontWeight:700,color:S.gold,fontFamily:"'Space Mono',monospace"}}>₦{c.totalSpent.toLocaleString()}</span>
          <span style={{fontSize:11,color:S.textDim}}>{c.favMerchant}</span>
        </div>))}
      </div>
    </div>
  );
}

// ─── MESSAGING ──────────────────────────────────────────────────
function MessagingScreen() {
  const [tab,setTab]=useState("riders");
  const [activeId,setActiveId]=useState(null);
  const [input,setInput]=useState("");
  const chats=tab==="riders"?MSG_RIDER:MSG_CUSTOMER;
  const active=activeId?chats.find(c=>c.id===activeId):null;
  const templates=["Your order has been picked up. Rider is on the way.","Rider is ~10 minutes away.","Slight delay, we apologize.","Delivered successfully. Thank you!","Please confirm delivery address."];
  return (
    <div style={{display:"grid",gridTemplateColumns:"280px 1fr",gap:0,height:"calc(100vh - 130px)",background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
      <div style={{borderRight:`1px solid ${S.border}`,display:"flex",flexDirection:"column"}}>
        <div style={{display:"flex",borderBottom:`1px solid ${S.border}`}}>
          {[{id:"riders",l:"Riders",c:MSG_RIDER.reduce((s,m)=>s+m.unread,0)},{id:"customers",l:"Customers",c:MSG_CUSTOMER.reduce((s,m)=>s+m.unread,0)}].map(t=>(<button key={t.id} onClick={()=>{setTab(t.id);setActiveId(null);}} style={{flex:1,padding:"12px 0",border:"none",cursor:"pointer",fontFamily:"inherit",fontSize:12,fontWeight:600,borderBottom:tab===t.id?`2px solid ${S.gold}`:"2px solid transparent",color:tab===t.id?S.gold:S.textMuted,background:"transparent"}}>{t.l}{t.c>0&&<span style={{marginLeft:6,fontSize:10,padding:"1px 6px",borderRadius:6,background:S.gold,color:"#fff",fontWeight:700}}>{t.c}</span>}</button>))}
        </div>
        <div style={{flex:1,overflowY:"auto"}}>
          {chats.map(ch=>(<div key={ch.id} onClick={()=>setActiveId(ch.id)} style={{padding:"12px 14px",borderBottom:`1px solid ${S.borderLight}`,cursor:"pointer",background:activeId===ch.id?S.goldPale:"transparent",transition:"background 0.12s"}} onMouseEnter={e=>{if(activeId!==ch.id)e.currentTarget.style.background=S.borderLight;}} onMouseLeave={e=>{if(activeId!==ch.id)e.currentTarget.style.background="transparent";}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><span style={{fontSize:13,fontWeight:ch.unread?700:500}}>{ch.name}</span><span style={{fontSize:10,color:S.textMuted}}>{ch.lastTime}</span></div>
            <div style={{display:"flex",justifyContent:"space-between"}}><span style={{fontSize:11,color:ch.unread?S.text:S.textMuted,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",maxWidth:180}}>{ch.lastMsg}</span>{ch.unread>0&&<span style={{fontSize:9,fontWeight:700,padding:"2px 6px",borderRadius:8,background:S.gold,color:"#fff",minWidth:16,textAlign:"center"}}>{ch.unread}</span>}</div>
          </div>))}
        </div>
      </div>
      {active?(<div style={{display:"flex",flexDirection:"column"}}>
        <div style={{padding:"12px 18px",borderBottom:`1px solid ${S.border}`,display:"flex",alignItems:"center",gap:10}}>
          <div style={{width:34,height:34,borderRadius:10,background:S.goldPale,display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:800,color:S.gold}}>{active.name.split(" ").map(n=>n[0]).join("")}</div>
          <div><div style={{fontSize:14,fontWeight:700}}>{active.name}</div><div style={{fontSize:10,color:S.textMuted}}>{tab==="riders"?"Rider":"Customer"} • {active.id}</div></div>
        </div>
        <div style={{flex:1,overflowY:"auto",padding:"14px 18px",display:"flex",flexDirection:"column",gap:8}}>
          {active.messages.map((m,i)=>{const d=m.from==="dispatch";return (<div key={i} style={{display:"flex",justifyContent:d?"flex-end":"flex-start"}}><div style={{maxWidth:"65%",padding:"10px 14px",borderRadius:12,borderBottomRightRadius:d?4:12,borderBottomLeftRadius:d?12:4,background:d?S.goldPale:S.borderLight,fontSize:12,lineHeight:1.5}}><div>{m.text}</div><div style={{fontSize:9,color:S.textMuted,marginTop:4,textAlign:d?"right":"left"}}>{m.time}</div></div></div>);})}
        </div>
        <div style={{padding:"8px 18px",borderTop:`1px solid ${S.border}`,display:"flex",gap:6,overflowX:"auto"}}>
          {templates.slice(0,3).map((t,i)=>(<button key={i} onClick={()=>setInput(t)} style={{padding:"5px 10px",borderRadius:6,border:`1px solid ${S.border}`,background:S.borderLight,color:S.textDim,cursor:"pointer",fontFamily:"inherit",fontSize:10,whiteSpace:"nowrap"}}>{t.substring(0,30)}...</button>))}
        </div>
        <div style={{padding:"10px 18px",borderTop:`1px solid ${S.border}`,display:"flex",gap:8}}>
          <input value={input} onChange={e=>setInput(e.target.value)} placeholder="Type a message..." style={{flex:1,background:S.borderLight,border:`1px solid ${S.border}`,borderRadius:8,padding:"0 14px",height:40,color:S.text,fontSize:12,fontFamily:"inherit",outline:"none"}}/>
          <button style={{width:40,height:40,borderRadius:8,border:"none",cursor:"pointer",background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,display:"flex",alignItems:"center",justifyContent:"center"}}>{I.send}</button>
        </div>
      </div>):(<div style={{display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",gap:8}}><div style={{fontSize:40,opacity:0.2}}>💬</div><div style={{fontSize:14,color:S.textMuted}}>Select a conversation</div></div>)}
    </div>
  );
}

// ─── SETTINGS ───────────────────────────────────────────────────
function SettingsScreen() {
  // ─── PRICING STATE (Research-based Lagos defaults) ───
  const [bikeBase, setBikeBase] = useState(500);
  const [bikePerKm, setBikePerKm] = useState(150);
  const [bikeMinKm, setBikeMinKm] = useState(3);
  const [bikeMin, setBikeMin] = useState(1200);
  const [carBase, setCarBase] = useState(1000);
  const [carPerKm, setCarPerKm] = useState(250);
  const [carMinKm, setCarMinKm] = useState(3);
  const [carMin, setCarMin] = useState(2500);
  const [vanBase, setVanBase] = useState(2000);
  const [vanPerKm, setVanPerKm] = useState(400);
  const [vanMinKm, setVanMinKm] = useState(3);
  const [vanMin, setVanMin] = useState(5000);
  const [codFee, setCodFee] = useState(500);
  const [codPct, setCodPct] = useState(1.5);
  const [bridgeSurcharge, setBridgeSurcharge] = useState(500);
  const [outerZoneSurcharge, setOuterZoneSurcharge] = useState(800);
  const [islandPremium, setIslandPremium] = useState(300);
  const [weightThreshold, setWeightThreshold] = useState(5);
  const [weightSurcharge, setWeightSurcharge] = useState(200);
  const [weightUnit, setWeightUnit] = useState(5);
  const [surgeEnabled, setSurgeEnabled] = useState(true);
  const [surgeMultiplier, setSurgeMultiplier] = useState(1.5);
  const [surgeMorningStart, setSurgeMorningStart] = useState("07:00");
  const [surgeMorningEnd, setSurgeMorningEnd] = useState("09:30");
  const [surgeEveningStart, setSurgeEveningStart] = useState("17:00");
  const [surgeEveningEnd, setSurgeEveningEnd] = useState("20:00");
  const [rainSurge, setRainSurge] = useState(true);
  const [rainMultiplier, setRainMultiplier] = useState(1.3);
  const [tierEnabled, setTierEnabled] = useState(true);
  const [tier1Km, setTier1Km] = useState(15);
  const [tier1Discount, setTier1Discount] = useState(10);
  const [tier2Km, setTier2Km] = useState(25);
  const [tier2Discount, setTier2Discount] = useState(15);
  const [autoAssign, setAutoAssign] = useState(true);
  const [assignRadius, setAssignRadius] = useState(5);
  const [acceptTimeout, setAcceptTimeout] = useState(120);
  const [maxBike, setMaxBike] = useState(2);
  const [maxCar, setMaxCar] = useState(1);
  const [maxVan, setMaxVan] = useState(1);
  const [notifNew, setNotifNew] = useState(true);
  const [notifUnassigned, setNotifUnassigned] = useState(true);
  const [notifComplete, setNotifComplete] = useState(true);
  const [notifCod, setNotifCod] = useState(true);
  const [settingsTab, setSettingsTab] = useState("pricing");
  const [saved, setSaved] = useState(false);
  const [simKm, setSimKm] = useState(8);
  const [simVehicle, setSimVehicle] = useState("bike");
  const [simZone, setSimZone] = useState("same");
  const [simWeight, setSimWeight] = useState(3);
  const [simSurge, setSimSurge] = useState(false);

  const calcPrice = (base, perKm, minKm, minFee, km, zone, weight) => {
    let price;
    if (km <= minKm) { price = minFee; }
    else {
      price = base + (km * perKm);
      if (tierEnabled && km >= tier2Km) price = price * (1 - tier2Discount / 100);
      else if (tierEnabled && km >= tier1Km) price = price * (1 - tier1Discount / 100);
      price = Math.max(minFee, Math.round(price));
    }
    if (zone === "bridge") price += bridgeSurcharge;
    if (zone === "outer") price += outerZoneSurcharge;
    if (zone === "island") price += islandPremium;
    if (weight > weightThreshold) price += Math.ceil((weight - weightThreshold) / weightUnit) * weightSurcharge;
    return Math.round(price);
  };
  const getVC = () => ({
    bike: { base:bikeBase, perKm:bikePerKm, minKm:bikeMinKm, min:bikeMin },
    car: { base:carBase, perKm:carPerKm, minKm:carMinKm, min:carMin },
    van: { base:vanBase, perKm:vanPerKm, minKm:vanMinKm, min:vanMin },
  });
  const simC = getVC()[simVehicle];
  const simPrice = calcPrice(simC.base, simC.perKm, simC.minKm, simC.min, simKm, simZone, simWeight);
  const simFinal = simSurge ? Math.round(simPrice * surgeMultiplier) : simPrice;
  const handleSave = () => { setSaved(true); setTimeout(()=>setSaved(false),2500); };
  const handleReset = () => { setBikeBase(500);setBikePerKm(150);setBikeMinKm(3);setBikeMin(1200);setCarBase(1000);setCarPerKm(250);setCarMinKm(3);setCarMin(2500);setVanBase(2000);setVanPerKm(400);setVanMinKm(3);setVanMin(5000);setCodFee(500);setCodPct(1.5);setBridgeSurcharge(500);setOuterZoneSurcharge(800);setIslandPremium(300); };

  const inputStyle = {width:"100%",border:`1.5px solid ${S.border}`,borderRadius:10,padding:"0 12px",height:40,fontSize:14,fontFamily:"'Space Mono',monospace",fontWeight:700,color:S.navy,outline:"none"};
  const labelStyle = {display:"block",fontSize:11,fontWeight:600,color:S.textMuted,marginBottom:4,textTransform:"uppercase",letterSpacing:"0.3px"};
  const Toggle = ({on,setOn,size})=>{const w=size==="sm"?36:44;const d=size==="sm"?16:20;return (<div onClick={()=>setOn(!on)} style={{width:w,height:Math.round(w/1.83),borderRadius:w/2,cursor:"pointer",background:on?S.green:S.border,position:"relative",transition:"background 0.2s",flexShrink:0}}><div style={{width:d,height:d,borderRadius:"50%",background:"#fff",position:"absolute",top:Math.round((w/1.83-d)/2),left:on?w-d-Math.round((w/1.83-d)/2):Math.round((w/1.83-d)/2),transition:"left 0.2s",boxShadow:"0 1px 3px rgba(0,0,0,0.2)"}}/></div>)};
  const SC = ({children,title,icon,desc,right})=>(<div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginBottom:14,overflow:"hidden"}}><div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`,display:"flex",alignItems:"center",justifyContent:"space-between"}}><div style={{display:"flex",alignItems:"center",gap:10}}><span style={{fontSize:20}}>{icon}</span><div><div style={{fontSize:15,fontWeight:700,color:S.navy}}>{title}</div>{desc&&<div style={{fontSize:11,color:S.textMuted}}>{desc}</div>}</div></div>{right}</div><div style={{padding:20}}>{children}</div></div>);
  const tabs = [{id:"pricing",label:"Pricing & Fees",icon:"💰"},{id:"zones",label:"Zones & Surcharges",icon:"🗺️"},{id:"simulator",label:"Price Calculator",icon:"🧮"},{id:"dispatch",label:"Dispatch Rules",icon:"⚙️"},{id:"notifications",label:"Notifications",icon:"🔔"},{id:"integrations",label:"API & Integrations",icon:"🔌"}];

  return (
    <div style={{maxWidth:900}}>
      <div style={{display:"flex",gap:4,marginBottom:20,background:S.card,borderRadius:12,padding:4,border:`1px solid ${S.border}`,overflowX:"auto"}}>
        {tabs.map(t=>(<button key={t.id} onClick={()=>setSettingsTab(t.id)} style={{flex:1,padding:"10px 0",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"inherit",fontSize:12,fontWeight:600,transition:"all 0.2s",display:"flex",alignItems:"center",justifyContent:"center",gap:5,whiteSpace:"nowrap",background:settingsTab===t.id?S.navy:"transparent",color:settingsTab===t.id?"#fff":S.textDim}}>{t.icon} {t.label}</button>))}
      </div>

      {/* ═══ PRICING TAB ═══ */}
      {settingsTab==="pricing" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{background:`linear-gradient(135deg, ${S.navy} 0%, ${S.navyLight} 100%)`,borderRadius:14,padding:"18px 22px",marginBottom:18}}>
          <div style={{display:"flex",alignItems:"flex-start",gap:14}}>
            <span style={{fontSize:24,marginTop:2}}>💡</span>
            <div style={{flex:1}}>
              <div style={{fontSize:14,fontWeight:700,color:"#fff",marginBottom:6}}>Lagos Delivery Market Research — Recommended Pricing</div>
              <div style={{fontSize:12,color:"rgba(255,255,255,0.55)",lineHeight:1.7,marginBottom:12}}>Based on analysis of Kwik, Gokada, GIG Logistics, and 50+ independent dispatch riders across Lagos. Defaults below are calibrated for competitive positioning while maintaining healthy margins.</div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10}}>
                {[{label:"Same Area",range:"₦1,200 – ₦3,000",desc:"Within Ikeja, Lekki, etc.",km:"1–5 km"},{label:"Mainland↔Island",range:"₦3,000 – ₦7,000",desc:"Bridge crossing required",km:"10–25 km"},{label:"Outer Lagos",range:"₦5,000 – ₦12,000",desc:"Ikorodu, Ojo, Badagry",km:"20–40 km"}].map(r=>(<div key={r.label} style={{background:"rgba(255,255,255,0.08)",borderRadius:10,padding:"10px 12px"}}><div style={{fontSize:10,fontWeight:700,color:S.gold,marginBottom:3}}>{r.label}</div><div style={{fontSize:14,fontWeight:800,color:"#fff",fontFamily:"'Space Mono',monospace"}}>{r.range}</div><div style={{fontSize:9,color:"rgba(255,255,255,0.4)",marginTop:3}}>{r.desc} • ~{r.km}</div></div>))}
              </div>
            </div>
          </div>
        </div>

        {[{label:"Bike",emoji:"🏍️",color:"#10B981",base:bikeBase,setBase:setBikeBase,perKm:bikePerKm,setPerKm:setBikePerKm,minKm:bikeMinKm,setMinKm:setBikeMinKm,min:bikeMin,setMin:setBikeMin,desc:"Small packages, documents, food. Max 25kg.",mr:"₦100–₦200/km"},
          {label:"Car",emoji:"🚗",color:"#3B82F6",base:carBase,setBase:setCarBase,perKm:carPerKm,setPerKm:setCarPerKm,minKm:carMinKm,setMinKm:setCarMinKm,min:carMin,setMin:setCarMin,desc:"Medium packages, electronics, fragile. Max 100kg.",mr:"₦200–₦350/km"},
          {label:"Van",emoji:"🚐",color:"#8B5CF6",base:vanBase,setBase:setVanBase,perKm:vanPerKm,setPerKm:setVanPerKm,minKm:vanMinKm,setMinKm:setVanMinKm,min:vanMin,setMin:setVanMin,desc:"Bulk orders, furniture, large cargo. Max 500kg.",mr:"₦350–₦500/km"}
        ].map(v=>(<div key={v.label} style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginBottom:14,overflow:"hidden"}}>
          <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
            <div style={{display:"flex",alignItems:"center",gap:10}}><span style={{fontSize:22}}>{v.emoji}</span><div><div style={{fontSize:15,fontWeight:700,color:S.navy}}>{v.label} Delivery</div><div style={{fontSize:11,color:S.textMuted}}>{v.desc}</div></div></div>
            <div style={{display:"flex",alignItems:"center",gap:8}}><div style={{background:"#f8fafc",padding:"4px 10px",borderRadius:6,fontSize:10,color:S.textMuted}}>Market: {v.mr}</div><div style={{background:`${v.color}12`,padding:"6px 14px",borderRadius:8}}><span style={{fontSize:11,fontWeight:700,color:v.color}}>MIN ₦{v.min.toLocaleString()}</span></div></div>
          </div>
          <div style={{padding:20}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:14,marginBottom:16}}>
              <div><label style={labelStyle}>Base Fee (₦)</label><input value={v.base} onChange={e=>v.setBase(Number(e.target.value)||0)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Flat charge per order</div></div>
              <div><label style={labelStyle}>Per KM Rate (₦)</label><input value={v.perKm} onChange={e=>v.setPerKm(Number(e.target.value)||0)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Charged after min distance</div></div>
              <div><label style={labelStyle}>Min Distance (KM)</label><input value={v.minKm} onChange={e=>v.setMinKm(Number(e.target.value)||0)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Covered by minimum fee</div></div>
              <div><label style={labelStyle}>Minimum Fee (₦)</label><input value={v.min} onChange={e=>v.setMin(Number(e.target.value)||0)} style={{...inputStyle,color:v.color,borderColor:`${v.color}40`}}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Floor price for ≤{v.minKm}km</div></div>
            </div>
            <div style={{background:"#f8fafc",borderRadius:10,padding:"12px 16px"}}>
              <div style={{fontSize:11,fontWeight:700,color:S.textMuted,marginBottom:8}}>PRICE PREVIEW (base — no zone/weight surcharges)</div>
              <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                {[1,3,5,8,12,20,30].map(km=>{const price=calcPrice(v.base,v.perKm,v.minKm,v.min,km,"same",0);return (<div key={km} style={{padding:"8px 10px",background:"#fff",borderRadius:8,border:`1px solid ${km<=v.minKm?`${v.color}30`:S.border}`,textAlign:"center",minWidth:68,flex:1}}><div style={{fontSize:10,color:S.textMuted,fontWeight:600}}>{km} KM</div><div style={{fontSize:14,fontWeight:800,color:v.color,fontFamily:"'Space Mono',monospace"}}>₦{price.toLocaleString()}</div>{km<=v.minKm&&<div style={{fontSize:8,color:v.color,fontWeight:700}}>MIN RATE</div>}{tierEnabled&&km>=tier1Km&&<div style={{fontSize:8,color:S.green,fontWeight:700}}>−{km>=tier2Km?tier2Discount:tier1Discount}%</div>}</div>);})}
              </div>
              <div style={{marginTop:8,fontSize:10,color:S.textMuted,lineHeight:1.5}}>Formula: If ≤{v.minKm}km → ₦{v.min.toLocaleString()}. Otherwise: ₦{v.base.toLocaleString()} + (km × ₦{v.perKm}){tierEnabled?`, ${tier1Discount}% off >${tier1Km}km, ${tier2Discount}% off >${tier2Km}km`:""}. Plus zone + weight surcharges.</div>
            </div>
          </div>
        </div>))}

        <SC title="Cash on Delivery (COD) Fee" icon="💵" desc="Deducted from COD amount before merchant settlement">
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
            <div><label style={labelStyle}>Flat Fee per COD (₦)</label><input value={codFee} onChange={e=>setCodFee(Number(e.target.value)||0)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Fixed charge per COD collection. Market: ₦300–₦500</div></div>
            <div><label style={labelStyle}>Percentage Fee (%)</label><input value={codPct} onChange={e=>setCodPct(Number(e.target.value)||0)} step="0.1" type="number" style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>On top of flat fee. 1.5% on ₦50,000 = ₦750</div></div>
          </div>
          <div style={{marginTop:14,background:S.greenBg,borderRadius:10,padding:"12px 16px"}}>
            <div style={{fontSize:11,fontWeight:700,color:S.green,marginBottom:6}}>COD SETTLEMENT PREVIEW</div>
            <div style={{display:"flex",gap:14}}>
              {[10000,50000,150000,500000].map(amt=>{const fee=codFee+Math.round(amt*(codPct/100));return (<div key={amt} style={{flex:1,textAlign:"center"}}><div style={{fontSize:10,color:S.textMuted}}>₦{amt.toLocaleString()}</div><div style={{fontSize:12,fontWeight:700,color:S.red,fontFamily:"'Space Mono',monospace"}}>−₦{fee.toLocaleString()}</div><div style={{fontSize:12,fontWeight:700,color:S.green,fontFamily:"'Space Mono',monospace"}}>→₦{(amt-fee).toLocaleString()}</div><div style={{fontSize:8,color:S.textMuted}}>({((fee/amt)*100).toFixed(1)}%)</div></div>);})}
            </div>
          </div>
        </SC>

        <SC title="Distance Tier Discounts" icon="📏" desc="Reduce per-km rate for longer distances" right={<Toggle on={tierEnabled} setOn={setTierEnabled}/>}>
          {tierEnabled?(<div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:14}}>
            <div><label style={labelStyle}>Tier 1 From (KM)</label><input value={tier1Km} onChange={e=>setTier1Km(Number(e.target.value)||0)} style={inputStyle}/></div>
            <div><label style={labelStyle}>Tier 1 Discount (%)</label><input value={tier1Discount} onChange={e=>setTier1Discount(Number(e.target.value)||0)} style={inputStyle}/></div>
            <div><label style={labelStyle}>Tier 2 From (KM)</label><input value={tier2Km} onChange={e=>setTier2Km(Number(e.target.value)||0)} style={inputStyle}/></div>
            <div><label style={labelStyle}>Tier 2 Discount (%)</label><input value={tier2Discount} onChange={e=>setTier2Discount(Number(e.target.value)||0)} style={inputStyle}/></div>
          </div>):(<div style={{fontSize:12,color:S.textMuted,textAlign:"center",padding:10}}>Disabled — flat per-km rate applies</div>)}
        </SC>

        <div style={{display:"flex",justifyContent:"flex-end",gap:10,marginTop:8}}>
          <button onClick={handleReset} style={{padding:"10px 24px",borderRadius:10,border:`1px solid ${S.border}`,background:S.card,cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:600,color:S.textDim}}>Reset Defaults</button>
          <button onClick={handleSave} style={{padding:"10px 32px",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:700,background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,boxShadow:"0 2px 8px rgba(232,168,56,0.25)"}}>{saved?"✓ Saved!":"Save Pricing"}</button>
        </div>
      </div>)}

      {/* ═══ ZONES & SURCHARGES TAB ═══ */}
      {settingsTab==="zones" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginBottom:14,overflow:"hidden"}}>
          <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><div style={{fontSize:15,fontWeight:700,color:S.navy}}>🗺️ Lagos Delivery Zones</div><div style={{fontSize:11,color:S.textMuted}}>Zone surcharges added on top of base distance pricing</div></div>
          <div style={{padding:20}}><LagosMap small={false} showZones={true}/></div>
        </div>
        <SC title="Zone-Based Surcharges" icon="📍" desc="Additional fees based on delivery route type">
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14,marginBottom:16}}>
            <div style={{background:"rgba(232,168,56,0.06)",borderRadius:10,padding:14,border:"1px solid rgba(232,168,56,0.15)"}}>
              <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:16}}>🌉</span><div style={{fontSize:13,fontWeight:700,color:S.navy}}>Bridge Crossing</div></div>
              <label style={labelStyle}>Surcharge (₦)</label><input value={bridgeSurcharge} onChange={e=>setBridgeSurcharge(Number(e.target.value)||0)} style={inputStyle}/>
              <div style={{fontSize:10,color:S.textMuted,marginTop:4}}>Mainland ↔ Island via 3rd Mainland, Carter, or Eko Bridge</div>
            </div>
            <div style={{background:"rgba(139,92,246,0.05)",borderRadius:10,padding:14,border:"1px solid rgba(139,92,246,0.12)"}}>
              <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:16}}>🏝️</span><div style={{fontSize:13,fontWeight:700,color:S.navy}}>Island Premium</div></div>
              <label style={labelStyle}>Surcharge (₦)</label><input value={islandPremium} onChange={e=>setIslandPremium(Number(e.target.value)||0)} style={inputStyle}/>
              <div style={{fontSize:10,color:S.textMuted,marginTop:4}}>Both pickup & dropoff on Island (VI, Ikoyi, Lekki)</div>
            </div>
            <div style={{background:"rgba(16,185,129,0.05)",borderRadius:10,padding:14,border:"1px solid rgba(16,185,129,0.12)"}}>
              <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:8}}><span style={{fontSize:16}}>🛤️</span><div style={{fontSize:13,fontWeight:700,color:S.navy}}>Outer Lagos</div></div>
              <label style={labelStyle}>Surcharge (₦)</label><input value={outerZoneSurcharge} onChange={e=>setOuterZoneSurcharge(Number(e.target.value)||0)} style={inputStyle}/>
              <div style={{fontSize:10,color:S.textMuted,marginTop:4}}>Ikorodu, Ojo, Badagry, Epe, Agbara</div>
            </div>
          </div>
          <div style={{background:"#f8fafc",borderRadius:10,padding:"14px 16px"}}>
            <div style={{fontSize:11,fontWeight:700,color:S.textMuted,marginBottom:10}}>ZONE EXAMPLES (BIKE, 10KM)</div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:10}}>
              {[{l:"Same Zone",z:"same",d:"Ikeja→Ikeja",i:"🏠"},{l:"Bridge",z:"bridge",d:"Yaba→V.I.",i:"🌉"},{l:"Island",z:"island",d:"V.I.→Lekki",i:"🏝️"},{l:"Outer",z:"outer",d:"Ikeja→Ikorodu",i:"🛤️"}].map(z=>{const p=calcPrice(bikeBase,bikePerKm,bikeMinKm,bikeMin,10,z.z,3);return (<div key={z.z} style={{textAlign:"center",padding:"10px 8px",background:"#fff",borderRadius:8,border:`1px solid ${S.border}`}}><div style={{fontSize:16}}>{z.i}</div><div style={{fontSize:10,fontWeight:700,color:S.navy,marginTop:2}}>{z.l}</div><div style={{fontSize:16,fontWeight:800,color:S.gold,fontFamily:"'Space Mono',monospace",margin:"4px 0"}}>₦{p.toLocaleString()}</div><div style={{fontSize:9,color:S.textMuted}}>{z.d}</div></div>);})}
            </div>
          </div>
        </SC>

        <SC title="Weight-Based Surcharges" icon="⚖️" desc="Extra charge for heavy packages">
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14}}>
            <div><label style={labelStyle}>Free Weight Limit (KG)</label><input value={weightThreshold} onChange={e=>setWeightThreshold(Number(e.target.value)||0)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>No surcharge below this</div></div>
            <div><label style={labelStyle}>Surcharge per Unit (₦)</label><input value={weightSurcharge} onChange={e=>setWeightSurcharge(Number(e.target.value)||0)} style={inputStyle}/></div>
            <div><label style={labelStyle}>Weight Unit (KG)</label><input value={weightUnit} onChange={e=>setWeightUnit(Number(e.target.value)||1)} style={inputStyle}/><div style={{fontSize:10,color:S.textMuted,marginTop:3}}>Each extra {weightUnit}kg = ₦{weightSurcharge}</div></div>
          </div>
          <div style={{marginTop:12,background:"#f8fafc",borderRadius:8,padding:"10px 14px",display:"flex",gap:12}}>
            {[2,5,10,15,25].map(w=>{const e=w>weightThreshold?Math.ceil((w-weightThreshold)/weightUnit)*weightSurcharge:0;return (<div key={w} style={{flex:1,textAlign:"center"}}><div style={{fontSize:10,color:S.textMuted,fontWeight:600}}>{w}kg</div><div style={{fontSize:12,fontWeight:700,color:e>0?S.red:S.green,fontFamily:"'Space Mono',monospace"}}>{e>0?`+₦${e.toLocaleString()}`:"FREE"}</div></div>);})}
          </div>
        </SC>

        <SC title="Surge / Peak Hour Pricing" icon="⚡" desc="Higher rates during peak traffic" right={<Toggle on={surgeEnabled} setOn={setSurgeEnabled}/>}>
          {surgeEnabled?(<div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr 1fr",gap:12,marginBottom:14}}>
              <div><label style={labelStyle}>Multiplier</label><input value={surgeMultiplier} onChange={e=>setSurgeMultiplier(Number(e.target.value)||1)} step="0.1" type="number" style={inputStyle}/></div>
              <div><label style={labelStyle}>AM Start</label><input value={surgeMorningStart} onChange={e=>setSurgeMorningStart(e.target.value)} type="time" style={inputStyle}/></div>
              <div><label style={labelStyle}>AM End</label><input value={surgeMorningEnd} onChange={e=>setSurgeMorningEnd(e.target.value)} type="time" style={inputStyle}/></div>
              <div><label style={labelStyle}>PM Start</label><input value={surgeEveningStart} onChange={e=>setSurgeEveningStart(e.target.value)} type="time" style={inputStyle}/></div>
              <div><label style={labelStyle}>PM End</label><input value={surgeEveningEnd} onChange={e=>setSurgeEveningEnd(e.target.value)} type="time" style={inputStyle}/></div>
            </div>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"12px 16px",background:"rgba(59,130,246,0.04)",borderRadius:10,marginBottom:10}}>
              <div><div style={{fontSize:13,fontWeight:600}}>🌧️ Rain Surge</div><div style={{fontSize:11,color:S.textMuted}}>Auto-apply during rainfall</div></div>
              <div style={{display:"flex",alignItems:"center",gap:10}}>{rainSurge&&<input value={rainMultiplier} onChange={e=>setRainMultiplier(Number(e.target.value)||1)} step="0.1" type="number" style={{...inputStyle,width:80,textAlign:"center"}}/>}<Toggle on={rainSurge} setOn={setRainSurge} size="sm"/></div>
            </div>
            <div style={{padding:"10px 14px",background:S.yellowBg,borderRadius:8,display:"flex",alignItems:"center",gap:8}}><span style={{fontSize:14}}>⚠️</span><span style={{fontSize:11,color:S.yellow,fontWeight:600}}>During {surgeMorningStart}–{surgeMorningEnd} & {surgeEveningStart}–{surgeEveningEnd}, prices × {surgeMultiplier}. ₦1,200 → ₦{Math.round(1200*surgeMultiplier).toLocaleString()}.</span></div>
          </div>):(<div style={{fontSize:12,color:S.textMuted,textAlign:"center",padding:10}}>Surge pricing disabled — flat rates 24/7</div>)}
        </SC>

        <div style={{display:"flex",justifyContent:"flex-end",gap:10,marginTop:8}}>
          <button onClick={handleReset} style={{padding:"10px 24px",borderRadius:10,border:`1px solid ${S.border}`,background:S.card,cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:600,color:S.textDim}}>Reset Defaults</button>
          <button onClick={handleSave} style={{padding:"10px 32px",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:700,background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,boxShadow:"0 2px 8px rgba(232,168,56,0.25)"}}>{saved?"✓ Saved!":"Save Zone Settings"}</button>
        </div>
      </div>)}

      {/* ═══ PRICE CALCULATOR TAB ═══ */}
      {settingsTab==="simulator" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
            <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><div style={{fontSize:15,fontWeight:700,color:S.navy}}>🧮 Price Calculator</div><div style={{fontSize:11,color:S.textMuted}}>Simulate delivery pricing for any route</div></div>
            <div style={{padding:20}}>
              <div style={{marginBottom:16}}><label style={labelStyle}>Vehicle Type</label>
                <div style={{display:"flex",gap:8}}>{[{id:"bike",l:"Bike",i:"🏍️"},{id:"car",l:"Car",i:"🚗"},{id:"van",l:"Van",i:"🚐"}].map(v=>(<button key={v.id} onClick={()=>setSimVehicle(v.id)} style={{flex:1,padding:"10px 0",borderRadius:10,cursor:"pointer",fontFamily:"inherit",border:simVehicle===v.id?`2px solid ${S.gold}`:`1px solid ${S.border}`,background:simVehicle===v.id?S.goldPale:"#fff",textAlign:"center"}}><div style={{fontSize:18}}>{v.i}</div><div style={{fontSize:11,fontWeight:600,color:simVehicle===v.id?S.gold:S.text}}>{v.l}</div></button>))}</div>
              </div>
              <div style={{marginBottom:16}}><label style={labelStyle}>Distance: <span style={{color:S.gold,fontFamily:"'Space Mono',monospace"}}>{simKm} km</span></label><input type="range" min="1" max="50" value={simKm} onChange={e=>setSimKm(Number(e.target.value))} style={{width:"100%",accentColor:S.gold}}/><div style={{display:"flex",justifyContent:"space-between",fontSize:9,color:S.textMuted}}><span>1km</span><span>5km</span><span>15km</span><span>50km</span></div></div>
              <div style={{marginBottom:16}}><label style={labelStyle}>Delivery Zone</label>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6}}>{[{id:"same",l:"Same Area",i:"🏠"},{id:"bridge",l:"Bridge Cross",i:"🌉"},{id:"island",l:"Island Only",i:"🏝️"},{id:"outer",l:"Outer Lagos",i:"🛤️"}].map(z=>(<button key={z.id} onClick={()=>setSimZone(z.id)} style={{padding:"8px 10px",borderRadius:8,cursor:"pointer",fontFamily:"inherit",border:simZone===z.id?`2px solid ${S.gold}`:`1px solid ${S.border}`,background:simZone===z.id?S.goldPale:"#fff",fontSize:11,fontWeight:600,display:"flex",alignItems:"center",gap:6}}><span>{z.i}</span>{z.l}</button>))}</div>
              </div>
              <div style={{marginBottom:16}}><label style={labelStyle}>Weight: <span style={{color:S.gold,fontFamily:"'Space Mono',monospace"}}>{simWeight} kg</span></label><input type="range" min="1" max="30" value={simWeight} onChange={e=>setSimWeight(Number(e.target.value))} style={{width:"100%",accentColor:S.gold}}/></div>
              <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"10px 14px",borderRadius:8,border:`1px solid ${S.border}`}}><div style={{fontSize:12,fontWeight:600}}>⚡ Surge ({surgeMultiplier}x)</div><Toggle on={simSurge} setOn={setSimSurge} size="sm"/></div>
            </div>
          </div>
          <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden",display:"flex",flexDirection:"column"}}>
            <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><div style={{fontSize:15,fontWeight:700,color:S.navy}}>💰 Price Breakdown</div></div>
            <div style={{padding:20,flex:1,display:"flex",flexDirection:"column",justifyContent:"space-between"}}>
              <div>
                {[{l:"Base fee",a:simC.base,s:simKm>simC.minKm},{l:"Distance ("+simKm+"km)",a:simKm>simC.minKm?simKm*simC.perKm:0,s:simKm>simC.minKm},{l:"Minimum fee applied",a:simC.min,s:simKm<=simC.minKm},{l:"Zone surcharge",a:simZone==="bridge"?bridgeSurcharge:simZone==="island"?islandPremium:simZone==="outer"?outerZoneSurcharge:0,s:simZone!=="same"},{l:"Weight surcharge",a:simWeight>weightThreshold?Math.ceil((simWeight-weightThreshold)/weightUnit)*weightSurcharge:0,s:simWeight>weightThreshold}].filter(x=>x.s).map((item,idx)=>(<div key={idx} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid "+S.borderLight}}><span style={{fontSize:12,color:item.a<0?S.green:S.text}}>{item.l}</span><span style={{fontSize:13,fontWeight:700,color:item.a<0?S.green:S.navy,fontFamily:"'Space Mono',monospace"}}>₦{Math.abs(item.a).toLocaleString()}</span></div>))}
                {simSurge&&(<div style={{display:"flex",justifyContent:"space-between",padding:"8px 0",marginTop:4}}><span style={{fontSize:12,color:S.red}}>⚡ Surge ({surgeMultiplier}x)</span><span style={{fontSize:13,fontWeight:700,color:S.red,fontFamily:"'Space Mono',monospace"}}>+₦{(simFinal-simPrice).toLocaleString()}</span></div>)}
              </div>
              <div style={{marginTop:16,padding:"16px 18px",background:`linear-gradient(135deg, ${S.navy}, ${S.navyLight})`,borderRadius:12,textAlign:"center"}}>
                <div style={{fontSize:11,color:"rgba(255,255,255,0.5)",fontWeight:600,marginBottom:4}}>CUSTOMER PAYS</div>
                <div style={{fontSize:32,fontWeight:900,color:S.gold,fontFamily:"'Space Mono',monospace"}}>₦{simFinal.toLocaleString()}</div>
                <div style={{fontSize:10,color:"rgba(255,255,255,0.4)",marginTop:4}}>{simVehicle.toUpperCase()} • {simKm}km • {simZone==="bridge"?"Bridge":simZone==="island"?"Island":simZone==="outer"?"Outer":"Local"} • {simWeight}kg{simSurge?" • SURGE":""}</div>
              </div>
              <div style={{marginTop:12,background:"#f8fafc",borderRadius:8,padding:"10px 14px"}}>
                <div style={{fontSize:10,fontWeight:700,color:S.textMuted,marginBottom:6}}>COMPARE ALL VEHICLES</div>
                <div style={{display:"flex",gap:8}}>{[{id:"bike",i:"🏍️"},{id:"car",i:"🚗"},{id:"van",i:"🚐"}].map(v=>{const c=getVC()[v.id];const p=calcPrice(c.base,c.perKm,c.minKm,c.min,simKm,simZone,simWeight);const f=simSurge?Math.round(p*surgeMultiplier):p;return (<div key={v.id} style={{flex:1,textAlign:"center",padding:6,borderRadius:6,background:simVehicle===v.id?"rgba(232,168,56,0.1)":"transparent",border:simVehicle===v.id?`1px solid ${S.gold}`:"1px solid transparent"}}><div style={{fontSize:14}}>{v.i}</div><div style={{fontSize:14,fontWeight:800,color:S.navy,fontFamily:"'Space Mono',monospace"}}>₦{f.toLocaleString()}</div></div>);})}</div>
              </div>
            </div>
          </div>
        </div>

        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginTop:14,overflow:"hidden"}}>
          <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><div style={{fontSize:14,fontWeight:700,color:S.navy}}>🚀 Common Lagos Routes — Quick Reference</div></div>
          <div style={{padding:16,overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr style={{borderBottom:`2px solid ${S.border}`}}>{["Route","KM","Zone","🏍️ Bike","🚗 Car","🚐 Van"].map(h=>(<th key={h} style={{padding:"8px 10px",textAlign:"left",fontSize:10,fontWeight:700,color:S.textMuted,textTransform:"uppercase"}}>{h}</th>))}</tr></thead>
              <tbody>{[{r:"Ikeja → Allen Ave",km:3,z:"same",d:"Local"},{r:"Yaba → V.I.",km:12,z:"bridge",d:"Bridge"},{r:"Surulere → Lekki Ph1",km:18,z:"bridge",d:"Bridge"},{r:"V.I. → Lekki",km:8,z:"island",d:"Island"},{r:"Ikeja → Ikorodu",km:28,z:"outer",d:"Outer"},{r:"Maryland → Ajah",km:32,z:"bridge",d:"Bridge"},{r:"Apapa → Ojo",km:15,z:"outer",d:"Outer"},{r:"V.I. → Ajah",km:22,z:"island",d:"Island"}].map((r,i)=>(<tr key={i} style={{borderBottom:`1px solid ${S.borderLight}`}}><td style={{padding:"8px 10px",fontWeight:600}}>{r.r}</td><td style={{padding:"8px 10px",fontFamily:"'Space Mono',monospace",fontWeight:700}}>{r.km}</td><td style={{padding:"8px 10px"}}><span style={{fontSize:10,padding:"2px 8px",borderRadius:4,background:r.z==="bridge"?"rgba(232,168,56,0.1)":r.z==="island"?"rgba(139,92,246,0.08)":r.z==="outer"?"rgba(16,185,129,0.08)":"#f1f5f9",color:r.z==="bridge"?S.gold:r.z==="island"?"#8B5CF6":r.z==="outer"?S.green:S.textMuted,fontWeight:700}}>{r.d}</span></td>{["bike","car","van"].map(v=>{const c=getVC()[v];return<td key={v} style={{padding:"8px 10px",fontFamily:"'Space Mono',monospace",fontWeight:700,color:S.navy}}>₦{calcPrice(c.base,c.perKm,c.minKm,c.min,r.km,r.z,3).toLocaleString()}</td>;})}</tr>))}</tbody>
            </table>
          </div>
        </div>
      </div>)}

      {/* ═══ DISPATCH RULES TAB ═══ */}
      {settingsTab==="dispatch" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginBottom:14,overflow:"hidden"}}>
          <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><span style={{fontSize:14,fontWeight:700}}>Auto-Assignment</span></div>
          <div style={{padding:20}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:20}}><div><div style={{fontSize:13,fontWeight:600}}>Auto-assign nearest rider</div><div style={{fontSize:11,color:S.textMuted,marginTop:2}}>Automatically assigns closest available rider</div></div><Toggle on={autoAssign} setOn={setAutoAssign}/></div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14}}>
              <div><label style={labelStyle}>Assignment Radius (KM)</label><input value={assignRadius} onChange={e=>setAssignRadius(Number(e.target.value)||0)} style={inputStyle}/></div>
              <div><label style={labelStyle}>Acceptance Timeout (sec)</label><input value={acceptTimeout} onChange={e=>setAcceptTimeout(Number(e.target.value)||0)} style={inputStyle}/></div>
              <div><label style={labelStyle}>Retry Attempts</label><input value={3} readOnly style={{...inputStyle,background:"#f8fafc",color:S.textMuted}}/></div>
            </div>
          </div>
        </div>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginBottom:14,overflow:"hidden"}}>
          <div style={{padding:"14px 20px",borderBottom:`1px solid ${S.border}`}}><span style={{fontSize:14,fontWeight:700}}>Concurrent Orders per Rider</span></div>
          <div style={{padding:20}}>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:14}}>
              <div><label style={labelStyle}>🏍️ Bike Max</label><input value={maxBike} onChange={e=>setMaxBike(Number(e.target.value)||0)} style={inputStyle}/></div>
              <div><label style={labelStyle}>🚗 Car Max</label><input value={maxCar} onChange={e=>setMaxCar(Number(e.target.value)||0)} style={inputStyle}/></div>
              <div><label style={labelStyle}>🚐 Van Max</label><input value={maxVan} onChange={e=>setMaxVan(Number(e.target.value)||0)} style={inputStyle}/></div>
            </div>
          </div>
        </div>
        <div style={{display:"flex",justifyContent:"flex-end",gap:10,marginTop:8}}><button onClick={handleSave} style={{padding:"10px 32px",borderRadius:10,border:"none",cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:700,background:`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:S.navy,boxShadow:"0 2px 8px rgba(232,168,56,0.25)"}}>{saved?"✓ Saved!":"Save Settings"}</button></div>
      </div>)}

      {/* ═══ NOTIFICATIONS TAB ═══ */}
      {settingsTab==="notifications" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
          {[{label:"New order alert",desc:"Sound + desktop notification when a new order arrives",on:notifNew,set:setNotifNew},{label:"Unassigned order warning",desc:"Alert if an order is unassigned for more than 3 minutes",on:notifUnassigned,set:setNotifUnassigned},{label:"Delivery completion",desc:"Notification when a rider confirms delivery",on:notifComplete,set:setNotifComplete},{label:"COD settlement",desc:"Notification when COD is collected and settled to merchant wallet",on:notifCod,set:setNotifCod}].map((n,i,arr)=>(<div key={n.label} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"16px 20px",borderBottom:i<arr.length-1?`1px solid ${S.borderLight}`:"none"}}><div><div style={{fontSize:13,fontWeight:600}}>{n.label}</div><div style={{fontSize:11,color:S.textMuted,marginTop:2}}>{n.desc}</div></div><Toggle on={n.on} setOn={n.set}/></div>))}
        </div>
      </div>)}

      {/* ═══ INTEGRATIONS TAB ═══ */}
      {settingsTab==="integrations" && (<div style={{animation:"fadeIn 0.3s ease"}}>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,overflow:"hidden"}}>
          {[{label:"Onro API",desc:"Connected — Last sync: 2 min ago",status:"connected"},{label:"LibertyPay",desc:"Connected — Payment processing active",status:"connected"},{label:"WhatsApp Business API",desc:"Not connected",status:"disconnected"},{label:"Google Maps Distance Matrix",desc:"Connected — For accurate KM calculations",status:"connected"}].map((item,i,arr)=>(<div key={item.label} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"16px 20px",borderBottom:i<arr.length-1?`1px solid ${S.borderLight}`:"none"}}><div><div style={{fontSize:13,fontWeight:600}}>{item.label}</div><div style={{fontSize:11,color:S.textMuted,marginTop:2}}>{item.desc}</div></div><span style={{fontSize:10,fontWeight:700,padding:"4px 10px",borderRadius:6,background:item.status==="connected"?S.greenBg:S.redBg,color:item.status==="connected"?S.green:S.red}}>{item.status==="connected"?"CONNECTED":"NOT CONNECTED"}</span></div>))}
        </div>
        <div style={{background:S.card,borderRadius:14,border:`1px solid ${S.border}`,marginTop:14,padding:20}}>
          <label style={labelStyle}>Webhook URL</label><input defaultValue="https://api.axpress.ng/webhooks/onro" style={{...inputStyle,fontFamily:"'Space Mono',monospace",fontSize:12,fontWeight:500}}/><div style={{fontSize:10,color:S.textMuted,marginTop:4}}>Receives real-time order status updates from Onro</div>
        </div>
      </div>)}
    </div>
  );
}
// ─── ADDRESS AUTOCOMPLETE INPUT ─────────────────────────────────
function AddressAutocompleteInput({ value, onChange, placeholder, style }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const debounceTimer = useRef(null);
  const autocompleteService = useRef(null);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const init = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
      }
    };
    if (window.googleMapsLoaded) { init(); }
    else { window.addEventListener('google-maps-loaded', init); return () => window.removeEventListener('google-maps-loaded', init); }
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target) && inputRef.current && !inputRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const fetchSuggestions = (input) => {
    if (!input || input.length < 3) { setSuggestions([]); setShowDropdown(false); return; }
    if (!autocompleteService.current) return;
    setLoading(true);
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      autocompleteService.current.getPlacePredictions({
        input,
        componentRestrictions: { country: 'ng' },
        types: ['address'],
        location: new window.google.maps.LatLng(6.5244, 3.3792),
        radius: 50000,
      }, (predictions, status) => {
        setLoading(false);
        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          const lagos = predictions.filter(p => p.description.toLowerCase().includes('lagos'));
          setSuggestions(lagos.length ? lagos : predictions.slice(0, 5));
          setShowDropdown(true);
        } else { setSuggestions([]); setShowDropdown(false); }
      });
    }, 500);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input ref={inputRef} value={value} onChange={e => { onChange(e.target.value); fetchSuggestions(e.target.value); }}
        placeholder={placeholder} style={style} />
      {loading && <div style={{ position:'absolute', right:12, top:'50%', transform:'translateY(-50%)', fontSize:11, color:'#94a3b8' }}>⏳</div>}
      {showDropdown && suggestions.length > 0 && (
        <div ref={dropdownRef} style={{ position:'absolute', top:'100%', left:0, right:0, background:'#fff', border:`1px solid ${S.border}`, borderRadius:10, boxShadow:'0 8px 24px rgba(0,0,0,0.12)', zIndex:9999, maxHeight:220, overflowY:'auto', marginTop:4 }}>
          {suggestions.map((s, idx) => (
            <div key={s.place_id} onClick={() => { onChange(s.description); setSuggestions([]); setShowDropdown(false); }}
              style={{ padding:'10px 14px', cursor:'pointer', borderBottom: idx < suggestions.length-1 ? `1px solid ${S.border}` : 'none', fontSize:13, color:S.navy }}
              onMouseEnter={e => e.currentTarget.style.background='#f8fafc'}
              onMouseLeave={e => e.currentTarget.style.background='#fff'}>
              <span style={{ color:S.gold, marginRight:8 }}>📍</span>
              {s.structured_formatting?.main_text || s.description}
              {s.structured_formatting?.secondary_text && (
                <div style={{ fontSize:11, color:S.textMuted, marginTop:2 }}>{s.structured_formatting.secondary_text}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── CREATE ORDER MODAL ─────────────────────────────────────────
function CreateOrderModal({ riders, merchants, onClose, onOrderCreated }) {
  const iSt={width:"100%",border:`1.5px solid ${S.border}`,borderRadius:10,padding:"0 14px",height:42,fontSize:13,fontFamily:"inherit",color:S.navy,background:"#fff"};
  const lSt={display:"block",fontSize:11,fontWeight:600,color:S.textMuted,marginBottom:5,textTransform:"uppercase",letterSpacing:"0.5px"};

  // Form state
  const [merchantId, setMerchantId] = useState("");
  const [senderName, setSenderName] = useState("");
  const [senderPhone, setSenderPhone] = useState("");
  const [receiverName, setReceiverName] = useState("");
  const [receiverPhone, setReceiverPhone] = useState("");
  const [pickup, setPickup] = useState("");
  const [dropoff, setDropoff] = useState("");
  const [vehicle, setVehicle] = useState("Bike");
  const [pkg, setPkg] = useState("Box");
  const [riderId, setRiderId] = useState("");
  const [priceOverride, setPriceOverride] = useState("");
  const [codOn, setCodOn] = useState(false);
  const [codAmount, setCodAmount] = useState("");

  // Pricing & route state
  const [vehiclePricing, setVehiclePricing] = useState({
    Bike:{ base_fare:1200, rate_per_km:80, rate_per_minute:5 },
    Car:{ base_fare:4500, rate_per_km:150, rate_per_minute:8 },
    Van:{ base_fare:12000, rate_per_km:250, rate_per_minute:12 }
  });
  const [routeDistance, setRouteDistance] = useState(null);
  const [routeDuration, setRouteDuration] = useState(null);
  const [calculatingRoute, setCalculatingRoute] = useState(false);

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Load vehicle pricing from backend
  useEffect(() => {
    VehiclesAPI.getAll().then(res => {
      if (res.success && res.vehicles) {
        const p = {};
        res.vehicles.forEach(v => { p[v.name] = { base_fare: parseFloat(v.base_fare), rate_per_km: parseFloat(v.rate_per_km), rate_per_minute: parseFloat(v.rate_per_minute) }; });
        setVehiclePricing(p);
      }
    }).catch(() => {});
  }, []);

  // Calculate route when both addresses change
  useEffect(() => {
    if (!pickup || !dropoff) { setRouteDistance(null); setRouteDuration(null); return; }
    setCalculatingRoute(true);
    const tid = setTimeout(() => {
      if (typeof google === 'undefined' || !google.maps) { setCalculatingRoute(false); return; }
      new google.maps.DirectionsService().route({
        origin: pickup, destination: dropoff,
        travelMode: google.maps.TravelMode.DRIVING,
      }, (result, status) => {
        setCalculatingRoute(false);
        if (status === google.maps.DirectionsStatus.OK && result.routes[0]) {
          let dist = 0, dur = 0;
          result.routes[0].legs.forEach(l => { dist += l.distance.value; dur += l.duration.value; });
          setRouteDistance(parseFloat((dist / 1000).toFixed(1)));
          setRouteDuration(Math.ceil(dur / 60));
        }
      });
    }, 800);
    return () => clearTimeout(tid);
  }, [pickup, dropoff]);

  // Calculate price for a given vehicle
  const calcPrice = (vName) => {
    const p = vehiclePricing[vName];
    if (!p) return null;
    if (routeDistance && routeDuration) {
      return Math.round(p.base_fare + routeDistance * p.rate_per_km + routeDuration * p.rate_per_minute);
    }
    return Math.round(p.base_fare);
  };

  const displayPrice = priceOverride ? parseInt(priceOverride) : (calcPrice(vehicle) || 0);

  const handleSubmit = async () => {
    setError(null);
    if (!pickup) { setError("Pickup address is required"); return; }
    if (!dropoff) { setError("Dropoff address is required"); return; }
    if (!senderName) { setError("Sender name is required"); return; }
    if (!receiverName) { setError("Receiver name is required"); return; }
    setSubmitting(true);
    try {
      const payload = {
        pickup, dropoff,
        senderName, senderPhone: senderPhone || "N/A",
        receiverName, receiverPhone: receiverPhone || "N/A",
        vehicle, packageType: pkg,
        price: priceOverride || displayPrice,
        cod: codOn ? (parseFloat(codAmount) || 0) : 0,
        riderId: riderId || "",
        merchantId: merchantId || "",
        distance_km: routeDistance || 0,
        duration_minutes: routeDuration || 0,
      };
      const created = await OrdersAPI.create(payload);
      if (onOrderCreated) onOrderCreated(created);
      onClose();
    } catch (err) {
      const msg = err?.detail || err?.non_field_errors?.[0] || (typeof err === 'string' ? err : "Failed to create order. Check all fields.");
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const vehicleOptions = [
    { id:"Bike", icon:"🏍️" }, { id:"Car", icon:"🚗" }, { id:"Van", icon:"🚐" }
  ];

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,0.5)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:1000}} onClick={onClose}>
      <div onClick={e=>e.stopPropagation()} style={{background:S.card,borderRadius:16,border:`1px solid ${S.border}`,width:540,maxHeight:"90vh",overflowY:"auto",boxShadow:"0 24px 64px rgba(0,0,0,0.15)"}}>
        <div style={{padding:"18px 24px",borderBottom:`1px solid ${S.border}`,display:"flex",justifyContent:"space-between",alignItems:"center",position:"sticky",top:0,background:S.card,zIndex:1}}>
          <div><h2 style={{fontSize:18,fontWeight:800,margin:0}}>Create Order</h2><p style={{fontSize:12,color:S.textMuted,margin:"2px 0 0"}}>Manual dispatch order</p></div>
          <button onClick={onClose} style={{background:"none",border:"none",cursor:"pointer",color:S.textMuted}}>{I.x}</button>
        </div>
        <div style={{padding:"20px 24px"}}>
          {/* Merchant */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Merchant</label>
            <select value={merchantId} onChange={e=>setMerchantId(e.target.value)} style={{...iSt,cursor:"pointer"}}>
              <option value="">Select merchant...</option>
              {merchants.map(m=><option key={m.id} value={m.id}>{m.name} — {m.contact}</option>)}
            </select>
          </div>

          {/* Sender */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Sender</label>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
              <input value={senderName} onChange={e=>setSenderName(e.target.value)} placeholder="Sender name" style={iSt}/>
              <input value={senderPhone} onChange={e=>setSenderPhone(e.target.value)} placeholder="Sender phone" style={iSt}/>
            </div>
          </div>

          {/* Pickup */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Pickup Address</label>
            <AddressAutocompleteInput value={pickup} onChange={setPickup} placeholder="Enter pickup address..." style={iSt}/>
          </div>

          {/* Dropoff */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Dropoff Address</label>
            <AddressAutocompleteInput value={dropoff} onChange={setDropoff} placeholder="Enter delivery address..." style={iSt}/>
          </div>

          {/* Receiver */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Receiver</label>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
              <input value={receiverName} onChange={e=>setReceiverName(e.target.value)} placeholder="Receiver name" style={iSt}/>
              <input value={receiverPhone} onChange={e=>setReceiverPhone(e.target.value)} placeholder="Receiver phone" style={iSt}/>
            </div>
          </div>

          {/* Route info */}
          {(calculatingRoute || routeDistance) && (
            <div style={{marginBottom:16,padding:"10px 14px",borderRadius:10,background:"#fef3c7",border:"1px solid #fbbf24",display:"flex",alignItems:"center",gap:10}}>
              {calculatingRoute ? (
                <><div style={{width:16,height:16,border:"2px solid #f59e0b",borderTopColor:"transparent",borderRadius:"50%",animation:"spin 0.8s linear infinite"}}/><span style={{fontSize:12,color:"#92400e",fontWeight:600}}>Calculating route...</span></>
              ) : (
                <span style={{fontSize:12,color:"#92400e",fontWeight:600}}>📏 {routeDistance} km &nbsp;•&nbsp; 🕐 {routeDuration} min</span>
              )}
            </div>
          )}

          {/* Vehicle */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Vehicle Type</label>
            <div style={{display:"flex",gap:8}}>
              {vehicleOptions.map(v => {
                const price = calcPrice(v.id);
                const isSelected = vehicle === v.id;
                return (
                  <button key={v.id} onClick={()=>setVehicle(v.id)} style={{flex:1,padding:"10px 8px",borderRadius:10,cursor:"pointer",fontFamily:"inherit",border:isSelected?`2px solid ${S.gold}`:`1px solid ${S.border}`,background:isSelected?S.goldPale:S.borderLight,textAlign:"center",transition:"all 0.2s"}}>
                    <div style={{fontSize:20}}>{v.icon}</div>
                    <div style={{fontSize:12,fontWeight:600,color:isSelected?S.gold:S.text,marginTop:2}}>{v.id}</div>
                    <div style={{fontSize:11,fontWeight:700,color:S.gold,fontFamily:"'Space Mono',monospace",marginTop:3}}>
                      {calculatingRoute ? "…" : price != null ? `₦${price.toLocaleString()}` : "—"}
                    </div>
                    <div style={{fontSize:9,color:S.textMuted}}>{routeDistance ? "Est." : "Base"}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Package type */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Package Type</label>
            <select value={pkg} onChange={e=>setPkg(e.target.value)} style={{...iSt,cursor:"pointer"}}>
              {["Box","Envelope","Document","Food","Fragile"].map(p=><option key={p}>{p}</option>)}
            </select>
          </div>

          {/* COD */}
          <div style={{marginBottom:16,padding:"14px 16px",borderRadius:10,border:codOn?`2px solid ${S.green}`:`1px solid ${S.border}`,background:codOn?S.greenBg:"transparent"}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
              <div><div style={{fontSize:13,fontWeight:600}}>💵 Cash on Delivery</div><div style={{fontSize:11,color:S.textMuted}}>Collected at delivery</div></div>
              <div onClick={()=>setCodOn(!codOn)} style={{width:40,height:22,borderRadius:11,cursor:"pointer",background:codOn?S.green:S.border,position:"relative",flexShrink:0}}>
                <div style={{width:18,height:18,borderRadius:"50%",background:"#fff",position:"absolute",top:2,left:codOn?20:2,transition:"left 0.2s",boxShadow:"0 1px 3px rgba(0,0,0,0.2)"}}/>
              </div>
            </div>
            {codOn&&<div style={{marginTop:10}}><input value={codAmount} onChange={e=>setCodAmount(e.target.value)} placeholder="COD amount (₦)" style={{...iSt,fontFamily:"'Space Mono',monospace",fontWeight:700}}/></div>}
          </div>

          {/* Rider */}
          <div style={{marginBottom:16}}>
            <label style={lSt}>Assign Rider (Optional)</label>
            <select value={riderId} onChange={e=>setRiderId(e.target.value)} style={{...iSt,cursor:"pointer"}}>
              <option value="">Auto-assign nearest rider</option>
              {riders.filter(r=>r.status==="online"&&!r.currentOrder).map(r=>(<option key={r.id} value={r.id}>{r.name} — {r.vehicle} • ⭐ {r.rating}</option>))}
              {riders.filter(r=>r.status==="on_delivery").map(r=>(<option key={r.id} value={r.id} disabled>{r.name} — 📦 Busy</option>))}
            </select>
          </div>

          {/* Price summary */}
          <div style={{marginBottom:16,padding:"14px 16px",borderRadius:10,background:S.goldPale,border:`1px solid ${S.gold}`,display:"flex",alignItems:"center",justifyContent:"space-between"}}>
            <div>
              <div style={{fontSize:11,fontWeight:600,color:S.textMuted,textTransform:"uppercase",letterSpacing:"0.5px"}}>Estimated Price</div>
              <div style={{fontSize:22,fontWeight:800,color:S.navy,fontFamily:"'Space Mono',monospace"}}>₦{displayPrice.toLocaleString()}</div>
              {routeDistance && <div style={{fontSize:11,color:S.textMuted,marginTop:2}}>{routeDistance}km • {routeDuration}min</div>}
            </div>
            <div style={{textAlign:"right"}}>
              <label style={{...lSt,marginBottom:4}}>Override</label>
              <input value={priceOverride} onChange={e=>setPriceOverride(e.target.value)} placeholder="Custom ₦" style={{...iSt,width:110,fontFamily:"'Space Mono',monospace",fontSize:13}}/>
            </div>
          </div>

          {/* Error */}
          {error && <div style={{marginBottom:14,padding:"10px 14px",borderRadius:8,background:"#fef2f2",border:"1px solid #fecaca",fontSize:13,color:"#dc2626"}}>{error}</div>}

          {/* Buttons */}
          <div style={{display:"flex",gap:10}}>
            <button onClick={onClose} style={{flex:1,padding:"12px 0",borderRadius:10,border:`1px solid ${S.border}`,background:"transparent",color:S.textDim,cursor:"pointer",fontFamily:"inherit",fontSize:13,fontWeight:600}}>Cancel</button>
            <button onClick={handleSubmit} disabled={submitting} style={{flex:2,padding:"12px 0",borderRadius:10,border:"none",cursor:submitting?"not-allowed":"pointer",fontFamily:"inherit",background:submitting?"#e2e8f0":`linear-gradient(135deg,${S.gold},${S.goldLight})`,color:submitting?S.textMuted:S.navy,fontWeight:800,fontSize:14}}>
              {submitting ? "Creating..." : "Create Order"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
