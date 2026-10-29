// Regression tests for the live, clock-expanded 2026 TV continuity plan.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
require(path.join(root,'continuity-pools.js'));
require(path.join(root,'broadcast-clock.js'));
const breaks=JSON.parse(fs.readFileSync(path.join(root,'channel-breaks.json'),'utf8'));
const months=['january','february','march','april','may','june','july','august','september','october','november','december'];
let channelDays=0,bonusEpisodes=0,adSeconds=0,identCount=0,longBefore=0,largestGroup=0;
for(let m=1;m<=12;m++){
 const data=JSON.parse(fs.readFileSync(path.join(root,'schedules',months[m-1]+'.json'),'utf8'));
 for(const date of data.weeks[0].week)for(const channel of date.channels){
  channelDays++;
  const d=Number(date.date);
  const plan=BootlegClock.plan({year:2026,month:m,day:d,channel:channel.name,items:channel.playlist,breaks});
  const start=BootlegClock.wall(2026,m,d);
  const next=new Date(Date.UTC(2026,m-1,d+1));
  const end=BootlegClock.wall(next.getUTCFullYear(),next.getUTCMonth()+1,next.getUTCDate());
  const expected=(end-start)/1000;
  let position=0,group=0,lastIdent=-Infinity;
  const existing=new Set(channel.playlist.filter(p=>p.type!=='Break'&&p.type!=='Filler').map(p=>p.content_id||p.url));
  const added=new Set();
  for(const p of plan.slots){
   assert(Math.abs(p.broadcast_start_seconds-position)<=.01,'Timeline gap '+months[m-1]+'/'+d+'/'+channel.name);
   assert(p.broadcast_end_seconds>p.broadcast_start_seconds,'Zero airtime '+months[m-1]+'/'+d+'/'+channel.name);
   position=p.broadcast_end_seconds;
   const duration=p.broadcast_end_seconds-p.broadcast_start_seconds;
   if(p.editorial_kind==='continuity-short'){
    const key=p.content_id||p.url;
    assert(/\.mp4(?:[?#]|$)/i.test(p.url||''),'No direct MP4 source for bonus programme: '+p.url);
    assert(!existing.has(key),'Bonus duplicates scheduled programme '+channel.name);
    assert(!added.has(key),'Repeated bonus programme '+channel.name);
    assert(Math.abs(duration-p.duration_seconds)<.005,'Clipped bonus programme '+channel.name);
    added.add(key);bonusEpisodes++;
   }
   if(p.type==='Advert'||p.type==='Ident'){
    group+=duration;
    if(p.type==='Advert'){adSeconds+=duration;assert(!p.station_brand,'Branded loops should not play as adverts');}
    if(p.type==='Ident'){
     assert(p.broadcast_start_seconds-lastIdent>=3599.99,'Station ident repeated too soon '+channel.name);
     lastIdent=p.broadcast_start_seconds;identCount++;
    }
   }else{assert(group<=125.05,'Overlong ad interval '+channel.name+' '+group);largestGroup=Math.max(largestGroup,group);group=0;}
  }
  assert(Math.abs(position-expected)<.05,'Day duration wrong '+months[m-1]+'/'+d+'/'+channel.name);
  for(const p of channel.playlist)if(p.type==='Break'&&p.broadcast_end_seconds-p.broadcast_start_seconds>=600)longBefore++;
 }
}
assert.equal(channelDays,3650,'Expected all 2026 channel-days');
assert(bonusEpisodes>1000,'Long breaks were not replaced with full episodes');
console.log(JSON.stringify({status:'passed',channel_days:channelDays,long_original_breaks:longBefore,bonus_programmes:bonusEpisodes,ident_count:identCount,commercial_hours:Math.round(adSeconds/3600),max_commercial_seconds:largestGroup},null,2));
