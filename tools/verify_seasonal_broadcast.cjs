// Verify real dated programming after importing three seasonal Archive collections.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
require(path.join(ROOT,'continuity-pools.js'));
require(path.join(ROOT,'holiday-programmes.js'));
require(path.join(ROOT,'nick-uploader-programmes.js'));
require(path.join(ROOT,'seasonal-programmes.js'));
require(path.join(ROOT,'seasonal-commercials.js'));
require(path.join(ROOT,'channel-idents.js'));
require(path.join(ROOT,'broadcast-clock.js'));
const media=globalThis.BOOTLEG_SEASONAL_MEDIA.programmes;
const commercials=globalThis.BOOTLEG_SEASONAL_COMMERCIALS.adverts;
assert(media.length>=100,'Seasonal programme feed unexpectedly empty');
assert(commercials.length>=10,'Retro Christmas advert feed unexpectedly empty');
const valid=new Set();
for(const p of media){
 assert(p.url.startsWith('https://archive.org/download/')&&/\.mp4$/i.test(p.url));
 assert(p.duration_seconds>=150&&Number.isFinite(p.duration_seconds));
 assert(p.seasonal_tags.includes('christmas'));
 assert(!valid.has(p.url),'Repeated video URL '+p.url);
 valid.add(p.url);
}
const breaks=JSON.parse(fs.readFileSync(path.join(ROOT,'channel-breaks.json'),'utf8'));
for(const p of commercials){
 assert(p.seasonal_tags.includes('christmas')&&p.duration_seconds<=61);
 const s=breaks.channels[p.channel];assert(s,'Unknown advert channel');
 if(!s.adverts.some(x=>x.url===p.url))s.adverts.push(p);
}
const report={status:'passed',registered_programmes:media.length,registered_commercials:commercials.length,
 dates_checked:[],new_seasonal_airings:0,non_december_airings:0,christmas_ads_in_december:0,
 christmas_ads_in_october:0,max_intermission_seconds:0,airings_by_channel:{},sample_airings:[]};
for(const [month,m,days] of [['october',10,[28,29]],['december',12,[1,6,12,24,25]]]){
 const archive=JSON.parse(fs.readFileSync(path.join(ROOT,'schedules',month+'.json'),'utf8'));
 for(const day of days){
  const d=archive.weeks[0].week.find(x=>Number(x.date)===day);
  assert(d,'Missing '+month+' '+day);
  const audit={month,day,airings:0,adverts:0,hold_minutes:0};
  for(const ch of d.channels){
   const plan=BootlegClock.plan({year:2026,month:m,day,channel:ch.name,items:ch.playlist,breaks});
   let prev=-Infinity;const active=new Set();
   for(const p of plan.slots){
    assert(p.broadcast_start_seconds>=prev-.001,'Unsorted channel '+ch.name);
    assert(p.broadcast_end_seconds>p.broadcast_start_seconds,'Empty slot '+ch.name);
    prev=p.broadcast_end_seconds;
    const sid=p.content_id||'';
    if(sid.startsWith('archive-seasonal:')){
     const source=media.find(x=>x.content_id===sid);
     assert(source,'Unknown seasonal ID');
     assert(m===12,'Christmas episode leaked into '+month);
     assert(!active.has(sid),'Repeating same Christmas special in one day: '+sid);
     active.add(sid);
     audit.airings++;report.new_seasonal_airings++;
     report.airings_by_channel[ch.name]=(report.airings_by_channel[ch.name]||0)+1;
     if(report.sample_airings.length<24)report.sample_airings.push({day,channel:ch.name,title:p.title,at:Math.round(p.broadcast_start_seconds/60)});
    }
    if(sid.startsWith('archive-xmas-ad:')){
     audit.adverts++;
     if(m===12)report.christmas_ads_in_december++;
     else report.christmas_ads_in_october++;
    }
    if(p.type==='Filler'){
     const secs=p.broadcast_end_seconds-p.broadcast_start_seconds;
     audit.hold_minutes+=secs/60;report.max_intermission_seconds=Math.max(report.max_intermission_seconds,secs);
    }
   }
  }
  report.dates_checked.push(audit);
 }
}
assert.equal(report.non_december_airings,0);
assert.equal(report.christmas_ads_in_october,0);
assert(report.new_seasonal_airings>0,'No new Christmas programmes were ever placed on air');
fs.writeFileSync(path.join(ROOT,'seasonal-broadcast-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,programmes:report.registered_programmes,adverts:report.registered_commercials,
airings:report.new_seasonal_airings,december_ads:report.christmas_ads_in_december,max_holding_seconds:+report.max_intermission_seconds.toFixed(1),
examples:report.sample_airings.slice(0,8)},null,2));
