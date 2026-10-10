// Exercise the actual clock and recovery code without downloading Archive videos.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');require(path.join(root,'broadcast-clock.js'));
const breaks=JSON.parse(fs.readFileSync(path.join(root,'channel-breaks.json')));
let plans=0;
for(let month=1;month<=12;month++){
 const name=new Intl.DateTimeFormat('en',{month:'long',timeZone:'UTC'}).format(new Date(Date.UTC(2026,month-1,1))).toLowerCase();
 const data=JSON.parse(fs.readFileSync(path.join(root,'schedules',name+'.json')));
 for(const d of data.weeks[0].week)for(const c of d.channels){
  const plan=BootlegClock.plan({year:2026,month,day:Number(d.date),channel:c.name,items:c.playlist,breaks});let end=plan.start;
  for(const p of plan.slots){assert(Math.abs(end-p.start)<11,`${name} ${d.date} ${c.name} timeline gap`);assert(p.end>p.start);end=p.end;}
  assert(Math.abs(end-plan.end)<11,'UK midnight');assert(BootlegClock.locate(plan,plan.start));assert(BootlegClock.locate(plan,plan.end-1));plans++;
 }
}
assert.equal(plans,3650);
const storage=new Map(),nodes={};let perf=0;const initial=Date.UTC(2026,9,8,12,0),loads=[];
const channel='90s Toons',ident=breaks.channels[channel].ident;
const first={type:'Episode',show:'X-Men',title:'X-Men — S01E01',url:'https://archive.org/download/example/episode.mp4',start:initial,end:initial+1800000,slot_id:'one'};
const second={...first,title:'Spider-Man — S01E01',url:'https://archive.org/download/example/spider.mp4',start:first.end,end:initial+3600000,slot_id:'two'};
const c={name:channel,playlist:[first,second],plan:{slots:[first,second]}};
const context={BootlegClock,Date:class extends Date{static now(){return initial;}},performance:{now:()=>perf},crypto:{randomUUID:()=> 'test'},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},sessionStorage:{getItem:()=> 'test'},BOOTLEG_HOSTING:{backend:false},document:{body:{dataset:{}},addEventListener:()=>{}},setInterval:()=>{},setTimeout:()=>1,clearTimeout:()=>{},fetchJson:async()=>breaks,fetch:async()=>{throw Error('Backend should not be called');},$:id=>nodes[id]||= {hidden:true,open:false,setAttribute:()=>{},textContent:''},schedule:{},MONTHS:['january','february','march','april','may','june','july','august','september','october','november','december'],currentMonth:'october',previewDate:null,currentIndex:0,currentChannel:0,player:{duration:1200,currentTime:0,paused:false,readyState:4,pause:()=>{}},poweredOn:true,sourceIndex:0,sourceRetry:0,stalledAttempts:0,tuningGeneration:0,pendingSeek:0,getCurrentChannelData:()=>c,resetPlayer:()=>{},cancelRecovery:()=>{},hideStatus:()=>{},showStatus:()=>{},updateRemote:()=>{},updateChannelOverlay:()=>{},renderScheduleOverlay:()=>{},renderGuideList:()=>{},loadItemSource:(p,i,seek)=>loads.push({p,i,seek})};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'broadcast-ui.js'),'utf8')+'\nglobalThis.test=Broadcast;',context);
(async()=>{
 const b=context.test;await b.boot();b.load();assert.equal(loads.at(-1).p.url,first.url);
 perf=1200000;b.ended();assert.equal(loads.at(-1).p.url,ident.url);assert(b.item().loop);assert(!b.holding(),'Early ending must play ident, not wait card');
 context.player.duration=ident.duration_seconds;perf=1212000;assert(b.seek()<ident.duration_seconds);b.ended();assert.equal(loads.at(-1).p.url,ident.url);
 perf=1801000;b.sync();assert.equal(loads.at(-1).p.url,second.url);assert(!b.item().loop);
 context.sourceRetry=1;b.recover('TEST BROKEN SOURCE');assert.equal(loads.at(-1).p.url,ident.url);assert(JSON.parse(storage.get('bootleg.source.flags'))[second.url]);
 const listeners={},reportNodes={};const reportContext={Date,JSON,URL,Blob,localStorage:context.localStorage,BOOTLEG_HOSTING:{backend:false},document:{getElementById:id=>reportNodes[id]||= {value:'',disabled:true,addEventListener:(name,f)=>listeners[id+':'+name]=f},querySelector:()=>({}),createElement:()=>({click:()=>{}})}};
 vm.createContext(reportContext);vm.runInContext(fs.readFileSync(path.join(root,'reports.js'),'utf8'),reportContext);
 assert(reportNodes['report-message'].textContent.includes('1 saved local flags'));assert(!reportNodes['export-reports'].disabled);
 await listeners['report-list:click']({target:{closest:()=>({dataset:{action:'clear-local',index:'0'}})}});assert.equal(Object.keys(JSON.parse(storage.get('bootleg.source.flags'))).length,0);
 console.log(JSON.stringify({status:'passed',expanded_channel_days:plans,checks:['Measured break expansion and UK midnight coverage','Early video end plays own channel ident','Ident loops seek within actual duration','Next scheduled programme resumes at fixed time','Exhausted retries flag source durably and play ident','Static reports show and clear saved source flags without a backend']}));
})().catch(e=>{console.error(e);process.exitCode=1;});
