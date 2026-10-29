// Check 2026 broadcast clocks with measured new idents and seasonal filtering.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
require(path.join(root,'continuity-pools.js'));
require(path.join(root,'holiday-programmes.js'));
require(path.join(root,'channel-idents.js'));
require(path.join(root,'broadcast-clock.js'));
const pool=globalThis.BOOTLEG_IDENT_POOLS.channels;
const breaks=JSON.parse(fs.readFileSync(path.join(root,'channel-breaks.json'),'utf8'));
const dates=[['october',10,28],['october',10,29],['december',12,1],['december',12,25],['january',1,15]];
const report={status:'passed',ident_pool_counts:Object.fromEntries(Object.entries(pool).map(([name,rows])=>[name,rows.length])),checks:[],sampled_ident_total:0,rotated_new_idents:0,incorrect_seasonal:0,max_ident_per_channel_day:0};
for(const [month,m,day] of dates){
 const d=JSON.parse(fs.readFileSync(path.join(root,'schedules',month+'.json'),'utf8'));
 const entry=d.weeks[0].week.find(x=>Number(x.date)===day);
 assert(entry,month+' day '+day+' missing');
 for(const name of Object.keys(pool)){
  const channel=entry.channels.find(x=>x.name===name);
  assert(channel,'Missing channel '+name);
  const out=BootlegClock.plan({year:2026,month:m,day,channel:name,items:channel.playlist,breaks});
  const ids=out.slots.filter(x=>x.type==='Ident');
  let last=-Infinity,rotated=0;
  for(const clip of ids){
   assert(clip.broadcast_start_seconds-last>=3599.99,'Ident spam '+name+' '+month+' '+day);
   last=clip.broadcast_start_seconds;
   const match=pool[name].find(p=>p.url===clip.url);
   if(match){
    assert(!match.months||match.months.includes(m),'Out of season ident '+match.title);
    rotated++;
   }else{
    assert.equal(clip.url,breaks.channels[name].ident.url,'Wrong channel ident for '+name);
   }
   const length=clip.broadcast_end_seconds-clip.broadcast_start_seconds;
   assert(length>0 && length<=35,'Overlong ident '+clip.title);
  }
  assert(ids.length<=24,'More than 24 hourly idents '+name+' '+month+' '+day);
  assert(rotated>0,'Expected newly sourced idents in '+name+' '+month+' '+day);
  report.sampled_ident_total+=ids.length;report.rotated_new_idents+=rotated;
  report.max_ident_per_channel_day=Math.max(report.max_ident_per_channel_day,ids.length);
  report.checks.push({month,day,channel:name,idents:ids.length,new_idents:rotated,examples:ids.filter(p=>pool[name].some(x=>x.url===p.url)).slice(0,3).map(p=>p.title)});
 }
}
for(const [ch,clips] of Object.entries(pool))for(const clip of clips){
 assert(clip.url.startsWith('https://archive.org/download/')&&clip.url.endsWith('.mp4'));
 assert(clip.duration_seconds>=3&&clip.duration_seconds<=22);
 assert(!/\[NO SOUND\]|compilation|full collection/i.test(clip.title));
}
fs.writeFileSync(path.join(root,'channel-ident-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:'passed',counts:report.ident_pool_counts,sampled:report.sampled_ident_total,rotated:report.rotated_new_idents,maxDaily:report.max_ident_per_channel_day},null,2));
