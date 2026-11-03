// No network requests: test the generated initialization against a Leaflet API mock.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
(async()=>{
for(const filename of ['Budapest_Road_Map.html','Budapest_Hard_Stop_Map.html']){
 const html=fs.readFileSync(__dirname+'/'+filename,'utf8');assert(!/\bsvg\s*\{/.test(html),'global SVG styling must not affect map overlays');
 const js=html.match(/<script>([\s\S]*?)<\/script>/)[1];let pending;const elements={},calls=[],layers=new Set();
 const map={fitBounds:(points)=>{assert.equal(points.length,251);assert(points.every(p=>p[0]>47.49&&p[0]<47.51&&p[1]>19.07&&p[1]<19.09));calls.push('fit');},invalidateSize:()=>calls.push('resize'),hasLayer:l=>layers.has(l),removeLayer:l=>layers.delete(l)};
 const layer=()=>({on(){return this;},addTo(parent){if(parent===map)layers.add(this);return this;},bindPopup(){return this;}});
 const ctx={location:{protocol:'http:'},requestAnimationFrame:cb=>cb(),L:{map:(el,options)=>{assert(options.preferCanvas);return map;},polyline:(p,o)=>{assert(p.length>=2);calls.push(o.weight===3?'route':'road');return layer();},tileLayer:layer,layerGroup:layer,circleMarker:layer,control:{layers:()=>layer()}},document:{getElementById:id=>(elements[id]??={disabled:false,style:{},open:true}),createElement:type=>({type}),head:{appendChild:el=>{if(el.type==='link')el.onload();else pending=el.onload();}}}};
 ctx.window=ctx;vm.createContext(ctx);vm.runInContext(js,ctx);assert.equal(calls.length,0);ctx.enableStreetMap();await pending;
 assert.equal(Object.keys(ctx.vehicleLayers).length,5);assert(calls.filter(x=>x==='route').length>=10);assert.equal(elements['offline-fallback'].open,false);assert(calls.includes('resize'));
 const v=ctx.vehicleLayers['Vehicle 1'];ctx.toggleVehicle(0,false);assert(!layers.has(v));ctx.toggleVehicle(0,true);assert(layers.has(v));console.log(filename+': route overlays, bounds, CSS isolation and switches passed');
}
})().catch(e=>{console.error(e);process.exit(1);});
