// Identify visible programme holding intervals after the live continuity planner runs.
// No edits to schedules, and no downloads from Archive.
'use strict';
const fs=require('fs'),path=require('path');
const base=path.resolve(__dirname,'..');
require(path.join(base,'continuity-pools.js'));
require(path.join(base,'holiday-programmes.js'));
require(path.join(base,'broadcast-clock.js'));
const breaks=JSON.parse(fs.readFileSync(path.join(base,'channel-breaks.json'),'utf8'));
const dates=[['october',28,10],['october',29,10],['december',1,12],['december',6,12],['december',24,12],['december',25,12]];
const rows=[],stats={};
for(const [month,day,m] of dates){
 const data=JSON.parse(fs.readFileSync(path.join(base,'schedules',month+'.json'),'utf8'));
 const date=data.weeks[0].week.find(d=>Number(d.date)===day);
 if(!date)continue;
 for(const channel of date.channels){
   const plan=BootlegClock.plan({year:2026,month:m,day,channel:channel.name,items:channel.playlist,breaks});
   const slot=plan.slots.find(p=>p.broadcast_start_seconds<=18*3600+45*60 && 18*3600+45*60<p.broadcast_end_seconds);
   const fillers=plan.slots.filter(p=>p.presentation&&p.type==='Filler');
   const long=fillers.filter(p=>p.broadcast_end_seconds-p.broadcast_start_seconds>180);
   const minutes=fillers.reduce((n,p)=>n+(p.broadcast_end_seconds-p.broadcast_start_seconds)/60,0);
   const key=channel.name;
   stats[key]??={sampled:0,holding_minutes:0,long_holding:0,max_holding_minutes:0};
   stats[key].sampled++;
   stats[key].holding_minutes+=minutes;
   stats[key].long_holding+=long.length;
   stats[key].max_holding_minutes=Math.max(stats[key].max_holding_minutes,...fillers.map(p=>(p.broadcast_end_seconds-p.broadcast_start_seconds)/60),0);
   rows.push({date:month+' '+day,channel:key,at1845:slot?{
     title:slot.title||slot.type,type:slot.type,
     start:+(slot.broadcast_start_seconds/60).toFixed(2),
     end:+(slot.broadcast_end_seconds/60).toFixed(2)
   }:null,holdingMinutes:+minutes.toFixed(1),
   longHolding:long.slice(0,3).map(p=>({start:+(p.broadcast_start_seconds/60).toFixed(1),
      duration:+((p.broadcast_end_seconds-p.broadcast_start_seconds)/60).toFixed(1)}))});
 }
}
const results={dates:dates.map(x=>x[0]+' '+x[1]),stats,examples:rows.filter(p=>p.at1845?.type==='Filler'||p.longHolding.length>0).slice(0,55)};
fs.writeFileSync(path.join(base,'continuity-gap-audit.json'),JSON.stringify(results,null,2)+'\n');
console.log(JSON.stringify({stats,examples:results.examples.slice(0,10)},null,2));
