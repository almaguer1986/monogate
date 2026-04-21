import { useState, useRef, useEffect, useCallback } from "react";

const eml = (x, y) => y <= 0 ? Math.exp(x) : Math.exp(x) - Math.log(y);

const STRATA = [
  { depth: 0, name: "Arithmetic", color: "#64748B", y: 0.82 },
  { depth: 1, name: "Growth", color: "#06B6D4", y: 0.65 },
  { depth: 2, name: "Measurement", color: "#8B5CF6", y: 0.48 },
  { depth: 3, name: "Oscillation", color: "#EC4899", y: 0.28 },
  { depth: "∞", name: "The Depths", color: "#FDE68A", y: 0.08 },
];

const OBJECTS = [
  { id: "one", name: "1", depth: 0, x: 0.15, size: 3, formula: "eml(0, 1) = exp(0) - ln(1) = 1", nodes: 1, compute: (x) => 1, desc: "The constant. The seed of everything." },
  { id: "zero", name: "0", depth: 0, x: 0.35, size: 3, formula: "eml(0, e) = exp(0) - ln(e) = 0", nodes: 2, compute: (x) => 0, desc: "Nothing. But eml needs 2 nodes to make it." },
  { id: "int", name: "integers", depth: 0, x: 0.55, size: 3, formula: "eml(0,1) composed n times", nodes: "n", compute: (x) => Math.round(x), desc: "Counting. Discrete. The foundation of arithmetic." },
  { id: "exp", name: "exp(x)", depth: 1, x: 0.2, size: 6, formula: "eml(x, 1) = exp(x) - ln(1) = exp(x)", nodes: 1, compute: (x) => Math.exp(x), desc: "One EML node. The simplest possible expression. Growth itself." },
  { id: "e", name: "e", depth: 1, x: 0.45, size: 5, formula: "eml(1, 1) = exp(1) - ln(1) = e", nodes: 1, compute: (x) => Math.E, desc: "Euler's number. eml(1,1). The growth constant." },
  { id: "poly", name: "x²", depth: 1, x: 0.7, size: 4, formula: "exp(2·ln(x)) via EML composition", nodes: 5, compute: (x) => x * x, desc: "Polynomial. Requires nesting EML nodes." },
  { id: "ln", name: "ln(x)", depth: 2, x: 0.15, size: 6, formula: "eml(1, eml(eml(1,x), 1))", nodes: 4, compute: (x) => x > 0 ? Math.log(x) : 0, desc: "Four EML nodes. Measuring the rate of growth. EML-2." },
  { id: "entropy", name: "entropy", depth: 2, x: 0.38, size: 5, formula: "H = -Σ p·ln(p)", nodes: "n+4", compute: (x) => x > 0 && x < 1 ? -(x * Math.log(x) + (1-x) * Math.log(1-x)) : 0, desc: "Information content. How surprised you are. Logarithmic measurement." },
  { id: "kl", name: "KL divergence", depth: 2, x: 0.6, size: 4, formula: "D_KL = Σ p·ln(p/q)", nodes: "2n+4", compute: (x) => x > 0 && x < 1 ? x * Math.log(x / 0.5) + (1-x) * Math.log((1-x) / 0.5) : 0, desc: "Distance between distributions. EML-2: measuring measurement." },
  { id: "tanh", name: "tanh(x)", depth: 3, x: 0.68, size: 4, formula: "(e^{2x}−1)/(e^{2x}+1)", nodes: "EML-3", compute: (x) => Math.tanh(x), desc: "Hyperbolic tangent. EML-3. Appears in neural activations, statistical mechanics." },
  { id: "sin", name: "sin(x)", depth: 3, x: 0.18, size: 7, formula: "Im(eml(ix, 1))", nodes: "1 complex / ∞ real", compute: (x) => Math.sin(x), desc: "T01: no finite real EML tree equals sin(x). T03: Im(eml(ix,1)) = sin(x) over ℂ. 1 node." },
  { id: "cos", name: "cos(x)", depth: 3, x: 0.35, size: 5, formula: "Re(eml(ix, 1))", nodes: "1 complex / ∞ real", compute: (x) => Math.cos(x), desc: "T03 Euler Gateway. Re(eml(ix,1)) = cos(x) over ℂ in 1 node." },
  { id: "fourier", name: "Fourier", depth: 3, x: 0.52, size: 6, formula: "F̂(ξ) = ∫f·e^{-2πixξ}dx", nodes: "∞", compute: (x) => Math.sin(x) + 0.5 * Math.sin(3*x) + 0.33 * Math.sin(5*x), desc: "Fourier transform. EML-3 → EML-3. EML-3 Closure Theorem: stratum is algebraically sealed." },
  { id: "erf", name: "erf(x)", depth: 3, x: 0.84, size: 4, formula: "2/√π ∫₀ˣ e^{-t²}dt", nodes: "EML-3", compute: (x) => { const s = x >= 0 ? 1 : -1; const t = 1/(1+0.3275911*Math.abs(x)); const p = t*(0.254829592+t*(-0.284496736+t*(1.421413741+t*(-1.453152027+t*1.061405429)))); return s*(1-p*Math.exp(-x*x)); }, desc: "Error function. EML-3. EML Fourier density theorem (§36): converges to machine precision." },
  { id: "abs_sin", name: "|sin(x)|", depth: "∞", x: 0.18, size: 6, formula: "EML-∞ (non-constructible)", nodes: "—", compute: null, desc: "T01 variant: |sin(x)| has infinitely many zeros AND non-analytic kinks. No finite real EML tree can represent it. EML-∞ open problem." },
  { id: "abs_x", name: "|x|", depth: "∞", x: 0.38, size: 5, formula: "EML-∞ (non-analytic)", nodes: "—", compute: null, desc: "|x| has a non-analytic kink at x=0. Finite EML trees are real-analytic. EML-∞ by T01 extension." },
  { id: "sawtooth", name: "sawtooth", depth: "∞", x: 0.55, size: 5, formula: "Σ (−1)^{n+1}·sin(nx)/n", nodes: "—", compute: null, desc: "Sawtooth wave. Non-smooth, Gibbs phenomenon. Requires infinite Fourier terms. EML-∞." },
  { id: "heaviside", name: "Heaviside", depth: "∞", x: 0.72, size: 4, formula: "H(x) = 0 (x<0), 1 (x≥0)", nodes: "—", compute: null, desc: "Step function. Non-analytic discontinuity. Cannot be a finite real EML tree. EML-∞." },
  { id: "floor", name: "⌊x⌋", depth: "∞", x: 0.85, size: 4, formula: "EML-∞ (piecewise constant)", nodes: "—", compute: null, desc: "Floor function. Countably many discontinuities. Finite EML trees are continuous. EML-∞." },
];

function getDepthY(depth, h) {
  const s = STRATA.find(st => String(st.depth) === String(depth));
  return s ? s.y * h : h * 0.5;
}

function LiveGraph({ compute, color, label }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    let t = 0, fr;
    const draw = () => {
      t += 0.03;
      ctx.fillStyle = "rgba(6,2,14,0.15)"; ctx.fillRect(0, 0, w, h);
      // Axes
      ctx.strokeStyle = "rgba(255,255,255,0.05)"; ctx.lineWidth = 0.5;
      ctx.beginPath(); ctx.moveTo(0, h/2); ctx.lineTo(w, h/2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(w/2, 0); ctx.lineTo(w/2, h); ctx.stroke();
      // Function curve
      ctx.beginPath();
      for (let px = 0; px < w; px++) {
        const x = ((px / w) - 0.5) * 8 + t * 0.5;
        let y = compute(x);
        if (!isFinite(y)) y = 0;
        y = Math.max(-3, Math.min(3, y));
        const screenY = h/2 - (y / 3) * (h/2 - 10);
        if (px === 0) ctx.moveTo(px, screenY); else ctx.lineTo(px, screenY);
      }
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
      // Label
      ctx.fillStyle = `${color}80`; ctx.font = "9px monospace"; ctx.textAlign = "left";
      ctx.fillText(label, 6, 14);
      fr = requestAnimationFrame(draw);
    };
    ctx.fillStyle = "#06020E"; ctx.fillRect(0, 0, w, h); draw();
    return () => cancelAnimationFrame(fr);
  }, [compute, color, label]);
  return <canvas ref={ref} width={240} height={120} style={{ width: "100%", height: 120, display: "block", borderRadius: 8 }} />;
}

export default function MonogateCosmos() {
  const canvasRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [combining, setCombining] = useState(null);
  const [comboResult, setComboResult] = useState(null);
  const [hovered, setHovered] = useState(null);
  const timeRef = useRef(0);
  const frameRef = useRef(null);
  const starsRef = useRef([]);

  useEffect(() => {
    const s = [];
    for (let i = 0; i < 150; i++) s.push({ x: Math.random(), y: Math.random(), size: Math.random() * 1.2 + 0.3, brightness: Math.random() * 0.2 + 0.05 });
    starsRef.current = s;
  }, []);

  useEffect(() => {
    const c = canvasRef.current; if (!c) return;
    const ctx = c.getContext("2d"); const w = c.width, h = c.height;
    const draw = () => {
      timeRef.current += 0.008; const t = timeRef.current;
      const bg = ctx.createLinearGradient(0,0,0,h);
      bg.addColorStop(0,"#0a0118"); bg.addColorStop(0.5,"#06020e"); bg.addColorStop(1,"#04010a");
      ctx.fillStyle = bg; ctx.fillRect(0,0,w,h);
      starsRef.current.forEach(star => {
        ctx.beginPath(); ctx.arc(star.x*w, star.y*h, star.size, 0, Math.PI*2);
        ctx.fillStyle = `rgba(200,200,255,${star.brightness + Math.sin(t*3+star.x*100)*0.03})`; ctx.fill();
      });
      STRATA.forEach(stratum => {
        const sy = stratum.y * h;
        const [r,g,b] = [parseInt(stratum.color.slice(1,3),16), parseInt(stratum.color.slice(3,5),16), parseInt(stratum.color.slice(5,7),16)];
        const neb = ctx.createRadialGradient(w*0.5,sy,0,w*0.5,sy,w*0.5);
        neb.addColorStop(0,`rgba(${r},${g},${b},0.025)`); neb.addColorStop(1,"rgba(0,0,0,0)");
        ctx.fillStyle = neb; ctx.fillRect(0,sy-h*0.08,w,h*0.16);
        ctx.beginPath();
        for (let x=0;x<w;x+=3){ const wave=Math.sin(x*0.005+t+stratum.depth*2)*2; if(x===0)ctx.moveTo(x,sy+wave);else ctx.lineTo(x,sy+wave); }
        ctx.strokeStyle=`rgba(${r},${g},${b},0.05)`; ctx.lineWidth=1; ctx.stroke();
        ctx.fillStyle=`rgba(${r},${g},${b},0.1)`; ctx.font="8px monospace"; ctx.textAlign="left";
        ctx.fillText(`${stratum.depth==="∞"?"EML-∞":`EML-${stratum.depth}`}`,6,sy+3);
      });
      // Gap
      const g3=STRATA.find(s=>s.depth===3).y*h, gi=STRATA.find(s=>s.depth==="∞").y*h, gm=(g3+gi)/2;
      ctx.fillStyle=`rgba(239,68,68,${0.03+Math.sin(t*2)*0.01})`; ctx.font="7px monospace"; ctx.textAlign="center";
      ctx.fillText("EML-4 ∅",w/2,gm);
      // Shadows
      OBJECTS.filter(o=>o.shadow).forEach(obj=>{
        const fy=getDepthY(obj.depth,h), ty=getDepthY(obj.shadow,h), ox=obj.x*w;
        const sc=STRATA.find(s=>s.depth===obj.shadow);
        const [sr,sg,sb]=[parseInt(sc.color.slice(1,3),16),parseInt(sc.color.slice(3,5),16),parseInt(sc.color.slice(5,7),16)];
        const isSelected = selected?.id === obj.id;
        const alpha = isSelected ? 0.15 : 0.04;
        const beamW = isSelected ? 4 : 1;
        ctx.beginPath(); ctx.moveTo(ox-beamW,fy); ctx.lineTo(ox+beamW,fy); ctx.lineTo(ox+beamW+2,ty); ctx.lineTo(ox-beamW-2,ty); ctx.closePath();
        const grd=ctx.createLinearGradient(ox,fy,ox,ty);
        grd.addColorStop(0,`rgba(253,230,138,${alpha+Math.sin(t+obj.x*10)*0.02})`);
        grd.addColorStop(1,`rgba(${sr},${sg},${sb},${alpha*0.3})`);
        ctx.fillStyle=grd; ctx.fill();
        if(isSelected){ ctx.beginPath();ctx.arc(ox,ty,4+Math.sin(t*3)*1,0,Math.PI*2);ctx.fillStyle=`rgba(${sr},${sg},${sb},0.3)`;ctx.fill(); }
      });
      // Objects
      OBJECTS.forEach(obj=>{
        const ox=obj.x*w+Math.sin(t*0.3+obj.x*20)*3;
        const oy=getDepthY(obj.depth,h)+Math.cos(t*0.4+obj.x*15)*2;
        const sc=STRATA.find(s=>String(s.depth)===String(obj.depth));
        const [r,g,b]=[parseInt(sc.color.slice(1,3),16),parseInt(sc.color.slice(3,5),16),parseInt(sc.color.slice(5,7),16)];
        const isSel=selected?.id===obj.id;
        const isComb=combining?.id===obj.id;
        const isHov=hovered?.id===obj.id;
        const glowR=isSel?obj.size*8:isComb?obj.size*6:isHov?obj.size*5:obj.size*3;
        const glowA=isSel?0.25:isComb?0.2:isHov?0.15:0.1;
        const glow=ctx.createRadialGradient(ox,oy,0,ox,oy,glowR);
        glow.addColorStop(0,`rgba(${r},${g},${b},${glowA+Math.sin(t+obj.x*10)*0.03})`);
        glow.addColorStop(1,"rgba(0,0,0,0)");
        ctx.fillStyle=glow; ctx.beginPath(); ctx.arc(ox,oy,glowR,0,Math.PI*2); ctx.fill();
        ctx.beginPath(); ctx.arc(ox,oy,isSel?obj.size+2:obj.size,0,Math.PI*2);
        ctx.fillStyle=`rgba(${r},${g},${b},${isSel?0.9:0.5+Math.sin(t*2+obj.x*5)*0.1})`;ctx.fill();
        if(isSel){ctx.strokeStyle=`rgba(${r},${g},${b},0.6)`;ctx.lineWidth=1.5;ctx.stroke();}
        ctx.fillStyle=`rgba(${r},${g},${b},${isSel?0.7:0.25})`;
        ctx.font=`${isSel?10:Math.max(7,obj.size+2)}px monospace`;ctx.textAlign="center";
        ctx.fillText(obj.name,ox,oy+obj.size+(isSel?14:10));
      });
      ctx.fillStyle=`rgba(167,139,250,${0.05+Math.sin(t*1.5)*0.015})`;
      ctx.font="11px monospace";ctx.textAlign="center";
      ctx.fillText("eml(x, y) = exp(x) − ln(y)",w/2,h-12);
      frameRef.current=requestAnimationFrame(draw);
    };
    draw(); return ()=>cancelAnimationFrame(frameRef.current);
  },[selected,combining,hovered]);

  const handleClick = useCallback((e) => {
    const c=canvasRef.current;if(!c)return;
    const rect=c.getBoundingClientRect();
    const mx=(e.clientX-rect.left)*(c.width/rect.width);
    const my=(e.clientY-rect.top)*(c.height/rect.height);
    let nearest=null,dist=25;
    OBJECTS.forEach(obj=>{
      const ox=obj.x*c.width, oy=getDepthY(obj.depth,c.height);
      const d=Math.sqrt(Math.pow(mx-ox,2)+Math.pow(my-oy,2));
      if(d<dist){nearest=obj;dist=d;}
    });
    if(!nearest){setSelected(null);setCombining(null);setComboResult(null);return;}
    if(selected && selected.id!==nearest.id){
      // Combine!
      setCombining(nearest);
      const d1=selected.depth, d2=nearest.depth;
      let resultDepth;
      if(d1==="∞"||d2==="∞") resultDepth="∞";
      else resultDepth=Math.max(Number(d1),Number(d2));
      const isClosure=Number(d1)===3&&Number(d2)===3;
      setComboResult({
        a: selected, b: nearest, depth: resultDepth, isClosure,
        formula: `eml(${selected.name}, ${nearest.name})`,
      });
      // After showing combo, set the new one as selected for next combo
      setTimeout(() => { setSelected(nearest); setCombining(null); }, 0);
    } else {
      setSelected(nearest);
      setCombining(null);
      setComboResult(null);
    }
  },[selected]);

  const handleMouseMove = useCallback((e)=>{
    const c=canvasRef.current;if(!c)return;
    const rect=c.getBoundingClientRect();
    const mx=(e.clientX-rect.left)*(c.width/rect.width);
    const my=(e.clientY-rect.top)*(c.height/rect.height);
    let nearest=null,dist=20;
    OBJECTS.forEach(obj=>{
      const ox=obj.x*c.width,oy=getDepthY(obj.depth,c.height);
      const d=Math.sqrt(Math.pow(mx-ox,2)+Math.pow(my-oy,2));
      if(d<dist){nearest=obj;dist=d;}
    });
    setHovered(nearest);
  },[]);

  const selData=selected?OBJECTS.find(o=>o.id===selected.id):null;
  const selStratum=selData?STRATA.find(s=>String(s.depth)===String(selData.depth)):null;

  return (
    <div style={{fontFamily:"var(--font-sans,system-ui,sans-serif)",maxWidth:780,margin:"0 auto",padding:"0 0 2rem"}}>
      <div style={{textAlign:"center",padding:"1rem 1rem 0.4rem"}}>
        <div style={{fontSize:11,letterSpacing:3,textTransform:"uppercase",color:"#A78BFA",fontWeight:500,marginBottom:3}}>monogate.dev</div>
        <h1 style={{fontSize:24,fontWeight:600,margin:"0 0 4px",color:"var(--color-text-primary,#1a1a2e)"}}>The Cosmos</h1>
        <p style={{fontSize:13,color:"var(--color-text-secondary,#6b7280)",margin:0}}>
          Click any object to inspect it. Click a second object to combine them with eml().{selected?" Click another object to combine with "+selected.name+".":""}
        </p>
      </div>

      <div style={{position:"relative",borderRadius:16,overflow:"hidden",border:"1px solid rgba(167,139,250,0.1)"}}>
        <canvas ref={canvasRef} width={780} height={520} onClick={handleClick} onMouseMove={handleMouseMove} onMouseLeave={()=>setHovered(null)}
          style={{width:"100%",display:"block",borderRadius:14,cursor:hovered?"pointer":"default"}} />
      </div>

      {/* Legend */}
      <div style={{display:"flex",gap:4,justifyContent:"center",margin:"8px 0"}}>
        {STRATA.map(s=>(<div key={s.depth} style={{display:"flex",alignItems:"center",gap:3,padding:"3px 7px",borderRadius:5,background:`${s.color}08`}}>
          <div style={{width:6,height:6,borderRadius:3,background:s.color}} />
          <span style={{fontSize:8,color:s.color,fontFamily:"var(--font-mono)",fontWeight:600}}>{s.depth==="∞"?"∞":s.depth}</span>
        </div>))}
      </div>

      <div style={{display:"grid",gridTemplateColumns:selData?.compute?"1fr 240px":"1fr",gap:10,marginTop:6}}>
        {/* Info panel */}
        {selData && selStratum && (
          <div style={{padding:"14px 18px",borderRadius:12,background:`${selStratum.color}06`,border:`1.5px solid ${selStratum.color}20`,animation:"fadeIn 0.2s ease"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:6}}>
              <div style={{fontSize:18,fontWeight:700,color:selStratum.color}}>{selData.name}</div>
              <div style={{fontSize:12,fontFamily:"var(--font-mono)",color:selStratum.color,fontWeight:600}}>{selStratum.depth==="∞"?"EML-∞":`EML-${selStratum.depth}`} · {selStratum.name}</div>
            </div>
            <div style={{fontSize:12,color:"var(--color-text-secondary,#666)",lineHeight:1.6,marginBottom:8}}>{selData.desc}</div>
            <div style={{padding:"8px 12px",borderRadius:8,background:"var(--color-background-primary,white)",border:"0.5px solid var(--color-border-tertiary,rgba(0,0,0,0.06))"}}>
              <div style={{fontSize:10,fontWeight:600,color:selStratum.color,marginBottom:3}}>EML Expression</div>
              <div style={{fontSize:12,fontFamily:"var(--font-mono)",color:"var(--color-text-primary,#444)"}}>{selData.formula}</div>
              {selData.nodes&&<div style={{fontSize:10,color:"var(--color-text-secondary,#999)",marginTop:3}}>Node count: {selData.nodes}</div>}
            </div>
            {selData.shadow&&(
              <div style={{marginTop:8,padding:"6px 10px",borderRadius:6,background:"rgba(253,230,138,0.04)",border:"1px solid rgba(253,230,138,0.1)",fontSize:11,color:"#D97706"}}>
                Shadow beam → EML-{selData.shadow}. This object casts a {selData.shadow===2?"real exponential":"complex exponential"} shadow. (Shadow Depth Theorem)
              </div>
            )}
            <div style={{fontSize:10,color:"var(--color-text-secondary,#aaa)",marginTop:6,fontStyle:"italic"}}>
              Click another object to combine with eml({selData.name}, ?)
            </div>
          </div>
        )}

        {/* Live graph */}
        {selData?.compute && (
          <div style={{borderRadius:12,overflow:"hidden",border:`1px solid ${selStratum.color}20`}}>
            <LiveGraph compute={selData.compute} color={selStratum.color} label={selData.name} />
          </div>
        )}
      </div>

      {/* Combination result */}
      {comboResult && (
        <div style={{
          marginTop:10,padding:"14px 18px",borderRadius:12,
          background:comboResult.isClosure?"rgba(236,72,153,0.06)":"rgba(167,139,250,0.04)",
          border:comboResult.isClosure?"2px solid rgba(236,72,153,0.2)":"1.5px solid rgba(167,139,250,0.15)",
          animation:"fadeIn 0.3s ease",
        }}>
          <div style={{fontSize:14,fontFamily:"var(--font-mono)",color:comboResult.isClosure?"#EC4899":"#A78BFA",fontWeight:700,marginBottom:6}}>
            {comboResult.formula} → EML-{comboResult.depth}
          </div>
          {comboResult.isClosure?(
            <div style={{fontSize:12,color:"var(--color-text-secondary,#666)",lineHeight:1.6}}>
              <span style={{color:"#EC4899",fontWeight:600}}>Closure!</span> Both objects are EML-3. Their combination stays at EML-3.
              eml(EML-3, EML-3) = EML-3. The stratum is algebraically closed. You can't escape depth 3 by combining depth-3 objects.
              This is why the room in the Closure game has no door — only categorification (Δd=∞) escapes.
            </div>
          ):(
            <div style={{fontSize:12,color:"var(--color-text-secondary,#666)",lineHeight:1.6}}>
              {String(comboResult.depth)==="∞"
                ?"Any combination involving an EML-∞ object remains at EML-∞. Infinity absorbs everything."
                :`The combination takes the maximum depth of the two inputs: max(EML-${comboResult.a.depth}, EML-${comboResult.b.depth}) = EML-${comboResult.depth}.`
              }
            </div>
          )}
          <button onClick={()=>{setSelected(null);setCombining(null);setComboResult(null);}} style={{
            marginTop:8,padding:"6px 14px",borderRadius:6,border:"none",cursor:"pointer",
            background:"rgba(167,139,250,0.08)",color:"#A78BFA",fontSize:11,fontWeight:500,
          }}>Clear selection</button>
        </div>
      )}

      {!selected&&!comboResult&&(
        <div style={{textAlign:"center",padding:"10px",color:"var(--color-text-secondary,#aaa)",fontSize:12}}>
          Click any glowing object to inspect it and see the live EML computation.
        </div>
      )}

      <div style={{padding:"0.6rem 1rem",marginTop:10,background:"var(--color-background-secondary,#faf5ff)",borderRadius:10,border:"0.5px solid var(--color-border-tertiary,rgba(0,0,0,0.06))"}}>
        <p style={{fontSize:11,color:"var(--color-text-secondary,#555)",margin:0,lineHeight:1.6}}>
          The Cosmos shows the EML Atlas as a living universe. Objects float at their mathematically determined depth.
          Golden shadow beams connect EML-∞ objects to their finite projections. The void between EML-3 and EML-∞
          is the gap where depth 4 does not exist. Click any object to see its EML formula and live computation.
          Click two objects to combine them — and discover that EML-3 × EML-3 = EML-3. Closure. The room has no door.
        </p>
      </div>

      <div style={{textAlign:"center",marginTop:8,fontSize:11,color:"var(--color-text-secondary,#999)"}}>
        <a href="https://monogate.org" target="_blank" rel="noopener noreferrer" style={{color:"#A78BFA",textDecoration:"none",fontWeight:500}}>monogate.org</a>
        {" · "}<a href="https://monogate.dev" target="_blank" rel="noopener noreferrer" style={{color:"#06B6D4",textDecoration:"none"}}>monogate.dev</a>
      </div>

      <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}`}</style>
    </div>
  );
}
