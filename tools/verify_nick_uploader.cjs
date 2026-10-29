// Validate individually named uploader episodes, selectable movies and actual airtimes.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
require(path.join(root,'continuity-pools.js'));
require(path.join(root,'holiday-programmes.js'));
require(path.join(root,'nick-uploader-programmes.js'));
require(path.join(root,'channel-idents.js'));
require(path.join(root,'broadcast-clock.js'));
const programmes=globalThis.BOOTLEG_UPLOADER_PROGRAMMES.programmes;
const breaks=JSON.parse(fs.readFileSync(path.join(root,'channel-breaks.json'),'utf8'));
const seenIds=new Set(),seenUrls=new Set(),series={};
for(const p of programmes){
 assert(p.url.startsWith('https://archive.org/download/')&&/\.mp4$/i.test(p.url),'Bad direct file '+p.title);
 assert(p.duration_seconds>=240,'Invalid runtime '+p.title);
 assert(!seenIds.has(p.content_id),'Repeated episode identity '+p.content_id);
 assert(!seenUrls.has(p.url),'Repeated source URL '+p.url);
 seenIds.add(p.content_id);seenUrls.add(p.url);
 if(p.type==='Episode'){
  assert(Number.isInteger(p.season_number)&&Number.isInteger(p.episode_number),'Missing episode identity '+p.title);
  series[p.show]=(series[p.show]||0)+1;
 }
}
assert.equal(series['Figure It Out'],159);
assert.equal(series['I Spy'],26);
assert.equal(series['Splatalot'],53);
const summary={status:'passed',series,films:programmes.filter(x=>x.type!=='Episode').map(x=>x.title),
 starter_count:programmes.filter(x=>x.continuity_candidate).length,dates_checked:0,actual_broadcast_airings:0,
 broadcasts:[],max_same_day:0};
for(const month of ['january','april','october','december']){
 const m=({january:1,april:4,october:10,december:12})[month];
 const schedule=JSON.parse(fs.readFileSync(path.join(root,'schedules',month+'.json'),'utf8'));
 for(const d of schedule.weeks[0].week.slice(0,14)){
  const ch=d.channels.find(c=>c.name==='Dickleodeon');
  const plan=BootlegClock.plan({year:2026,month:m,day:Number(d.date),channel:ch.name,items:ch.playlist,breaks});
  const slots=plan.slots.filter(p=>p.content_id?.startsWith('nick-uploader:'));
  const ids=new Set();
  for(const p of slots){
   assert(p.editorial_kind==='continuity-short','Unexpected placement type: '+p.title);
   assert(p.type==='Episode','Only measured episodes can enter the short pool');
   assert(!ids.has(p.content_id),'Duplicate episode same channel/day');
   ids.add(p.content_id);
  }
  summary.dates_checked++;summary.actual_broadcast_airings+=slots.length;
  summary.max_same_day=Math.max(summary.max_same_day,slots.length);
  if(summary.broadcasts.length<15)summary.broadcasts.push(...slots.slice(0,15-summary.broadcasts.length).map(p=>({month,day:d.date,title:p.title,time:Math.round(p.broadcast_start_seconds/60)})));
 }
}
fs.writeFileSync(path.join(root,'nick-uploader-validation.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify(summary,null,2));
