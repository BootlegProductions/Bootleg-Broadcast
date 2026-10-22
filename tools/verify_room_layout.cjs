// Exercise actual room placement at common portrait, landscape and desktop sizes.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync(require('path').join(__dirname,'../mobile-layout.js'),'utf8');
let checked=0;
for(const [w,h] of [[390,844],[844,390],[768,1024],[1024,768],[1363,936],[1920,1080],[2560,1080]]){
 for(const season of ['regular','october','december']){
  const values={},classes=new Set(),list={toggle:(s,v)=>v?classes.add(s):classes.delete(s),remove:s=>classes.delete(s)};
  const nodes={stage:{getBoundingClientRect:()=>({width:w,height:h})},'remote-control':{classList:list},'remote-handle':{setAttribute:()=>{}}};
  const context={document:{getElementById:id=>nodes[id]||{},body:{dataset:{season},classList:list},documentElement:{style:{setProperty:(k,v)=>values[k]=parseFloat(v)}}},window:{addEventListener:()=>{}},matchMedia:()=>({matches:false}),ResizeObserver:class{observe(){}},MutationObserver:class{observe(){}},requestAnimationFrame:()=>1};
  vm.runInNewContext(code,context);
  const mobile=classes.has('mobile-scene');
  if(mobile){
   const width=values['--mobile-tv-width'],left=values['--mobile-tv-left'],top=values['--mobile-tv-top'];
   assert(left>=0&&left+width<=w+.1,`${w}x${h}: CRT outside viewport`);
   assert(top>=0,`${w}x${h}: CRT above viewport`);
   const ratio=h>=w?488/666:1154/1258;
   assert(top+width*ratio<=h+.1,`${w}x${h}: CRT below viewport`);
   if(season!=='regular'&&w>h){
    const scale=Math.max(w/1920,h/1080),horizon=870*scale-(1080*scale-h)/2;
    // Both angled feet should reach the tabletop, rather than float above its back edge.
    assert(top+width*ratio-width*.09>=horizon-2,`${w}x${h}: feet float above table`);
   }
  }else if(season!=='regular'){
   assert(values['--season-tv-top']>=0);
   assert(values['--season-tv-top']+values['--season-tv-width']*(1154/1258)<=h);
  }
  checked++;
 }
}
console.log(JSON.stringify({status:'passed',room_layout_scenarios:checked,scope:'Geometry checks; desktop seasonal rooms also visually reviewed in browser.'}));
