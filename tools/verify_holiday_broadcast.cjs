// Verify real, metadata-backed holiday additions against the full December channel plan.
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
require(path.join(root,'continuity-pools.js'));
require(path.join(root,'holiday-programmes.js'));
require(path.join(root,'broadcast-clock.js'));
const media=globalThis.BOOTLEG_HOLIDAY_MEDIA.programmes;
assert(media.length>40,'Expected a substantive seasonal film and special library');
const seen=new Set();
for(const p of media){
 assert(!seen.has(p.url),'Duplicate Archive source: '+p.url);seen.add(p.url);
 assert(p.duration_seconds>60&&p.url.startsWith('https://archive.org/download/')&&p.url.endsWith('.mp4'),'Invalid MP4 record '+p.title);
 assert(p.channel&&p.content_id,'Missing channel metadata '+p.title);
}
const breaks=JSON.parse(fs.readFileSync(path.join(root,'channel-breaks.json')));
const report={status:'passed',on_demand_titles:media.length,channels:{},december_short_airings:0,holiday_airings:[],non_december_christmas_slots:0};
const dec=JSON.parse(fs.readFileSync(path.join(root,'schedules/december.json'),'utf8'));
for(const d of dec.weeks[0].week)for(const ch of d.channels){
 const plan=BootlegClock.plan({year:2026,month:12,day:Number(d.date),channel:ch.name,items:ch.playlist,breaks});
 const holiday=plan.slots.filter(p=>p.content_id?.startsWith('archive-holiday:'));
 const summary=report.channels[ch.name]||={library:media.filter(p=>p.channel===ch.name).length,december_airings:0,examples:[]};
 summary.december_airings+=holiday.length;
 for(const p of holiday){
  assert(p.duration_seconds<=3000,'Full-length feature unexpectedly scheduled as continuity');
  assert(p.seasonal_tags.includes('christmas'),'Nonseasonal movie incorrectly inserted as holiday');
  assert(!plan.slots.some(q=>q!==p&&q.url===p.url),'Repeated holiday video in same channel-day');
  if(summary.examples.length<5&&!summary.examples.includes(p.title))summary.examples.push(p.title);
  if(report.holiday_airings.length<18)report.holiday_airings.push({date:'2026-12-'+String(d.date).padStart(2,'0'),channel:ch.name,title:p.title});
 }
 report.december_short_airings+=holiday.length;
}
const oct=JSON.parse(fs.readFileSync(path.join(root,'schedules/october.json'),'utf8'));
for(const d of oct.weeks[0].week.slice(0,3))for(const ch of d.channels){
 const plan=BootlegClock.plan({year:2026,month:10,day:Number(d.date),channel:ch.name,items:ch.playlist,breaks});
 report.non_december_christmas_slots+=plan.slots.filter(p=>p.content_id?.startsWith('archive-holiday:')&&(p.seasonal_tags||[]).includes('christmas')).length;
}
assert.equal(report.non_december_christmas_slots,0,'December media inserted into October');
assert(report.december_short_airings>0,'No holiday programmes replace any December breaks');
fs.writeFileSync(path.join(root,'holiday-broadcast-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
