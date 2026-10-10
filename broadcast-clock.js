/* A deterministic UK wall-clock plan. Media buffering never changes its slots. */
(function(root){
'use strict';
const zone='Europe/London', fmt=new Intl.DateTimeFormat('en-GB',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const parts=ms=>Object.fromEntries(fmt.formatToParts(new Date(ms)).filter(p=>p.type!=='literal').map(p=>[p.type,Number(p.value)]));
function wall(y,m,d,h=0){const target=Date.UTC(y,m-1,d,Math.floor(h),Math.round((h%1)*60));let guess=target;for(let i=0;i<4;i++){const p=parts(guess);const shown=Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second);const delta=target-shown;if(!delta)break;guess+=delta;}return guess;}
const holidayNames={'christmas':'Christmas','valentine':'Valentine’s Day','st-patrick':'St Patrick’s Day','easter':'Easter Sunday','thanksgiving':'US Thanksgiving','new-year':'New Year'};
function easterDate(year){const a=year%19,b=Math.floor(year/100),c=year%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),n=h+l-7*m+114;return [Math.floor(n/31),n%31+1];}
function holidayDates(year){const first=new Date(Date.UTC(year,10,1)).getUTCDay();return {'christmas':[[12,24],[12,25],[12,26]],'valentine':[[2,14]],'st-patrick':[[3,17]],'easter':[easterDate(year)],'thanksgiving':[[11,1+(4-first+7)%7+21]],'new-year':[[1,1],[12,31]]};}
const eventsOn=(year,month,day)=>Object.entries(holidayDates(year)).filter(([,dates])=>dates.some(([m,d])=>month===m&&day===d)).map(([name])=>name);
const holidayEligible=(p,year,month,day)=>(!(/christmas|\bxmas\b/i.test(p.show+' '+p.title)||(['Movie','Special'].includes(p.type)&&(p.seasonal_tags||[]).includes('christmas')))||month===12)&&(!p.holiday_events?.length||p.holiday_events.some(event=>event==='christmas'?month===12:(holidayDates(year)[event]||[]).some(([m,d])=>month===m&&day===d)));
const isClassic=p=>/jetsons|flintstones|tom and jerry|looney tunes|merry melodies|popeye|wacky races/i.test(p.show+' '+p.title);
const isKidsAnime=p=>!/digimon ghost game/i.test(p.show+' '+p.title)&&/shinzo|cardcaptors|mew mew power|pok[eé]mon|hamtaro|digimon|bakugan|jewelpet|precure|pretty cure|parappa|doraemon|yu-gi-oh|beyblade|sonic/i.test(p.show+' '+p.title);
const seriesKey=p=>p.series_id||p.series_key||String(p.show||p.title).toLowerCase().replace(/\s*[-—]?\s*(?:complete |all )?(?:season|seasons|series)\b.*/i,'').replace(/[^a-z0-9]/g,''),
 isAdult=p=>p.daypart==='Evening'||/^monster(?:\s*\(|$)/i.test(p.show)||/80s horror anime|queen.?s blade|high school dxd|desert punk|prison school|maken ki|valkyrie drive|hajimete no gal|to love ru|witchblade|bayonetta|paranoia agent|paprika|cyberpunk|chaos.?head|death parade|another|angels of death|maison ikkoku|great teacher onizuka|black lagoon|cowboy bebop|overlord|welcome to the nhk|urusei yatsura|cromartie|gilgamesh|beastars|berserk|gintama|evangelion|death note|akira|perfect blue|ghost in the shell|elfen lied|higurashi|hellsing|parasyte|ninja scroll|tokyo ghoul|attack on titan|serial experiments|devilman|misery|the thing|creepshow|black christmas|30 days of night|the shining/i.test(p.show+' '+p.title);
function contentKey(p){
 if(p.content_id)return p.content_id;
 const key=seriesKey(p), episode=p.episode_number??p.episode, season=p.season_number??p.season;
 if(p.type==='Episode'&&episode!=null&&Number.isFinite(Number(episode)))return key+':'+(season||1)+':'+Number(episode);
 const title=String(p.title||p.show).toLowerCase().replace(/\.mp4$/,'').replace(/[^a-z0-9]/g,'');
 return p.broadcast_identity||key+':'+title;
}
function plan({year,month,day,channel,items=[],breaks={}}){
 const start=wall(year,month,day),next=new Date(Date.UTC(year,month-1,day+1)),end=wall(next.getUTCFullYear(),next.getUTCMonth()+1,next.getUTCDate());
 if(items.some(p=>!Number.isFinite(p.broadcast_start_seconds)||!Number.isFinite(p.broadcast_end_seconds)))throw new Error('Written timetable missing. Rebuild the monthly schedules.');
 const seed=`written-tv-v1:${year}-${month}-${day}:${channel}`;
 const expanded=[];
 for(const p of items){
  if(p.type!=='Break'){expanded.push(p);continue;}
  const station=breaks.channels?.[channel];if(!station)throw new Error('Missing channel break media.');
  let t=p.broadcast_start_seconds;
  for(const index of p.break_sequence){
   const clip=index===-1?station.ident:station.adverts[index];if(!clip)throw new Error('Invalid channel break index.');
   const finish=Math.min(p.broadcast_end_seconds,t+clip.duration_seconds);
   expanded.push({...clip,block:p.block,broadcast_start_seconds:t,broadcast_end_seconds:finish});t=finish;
  }
 }
 const slots=expanded.map(p=>({...p,start:start+p.broadcast_start_seconds*1000,end:start+p.broadcast_end_seconds*1000,slot_id:seed+':'+p.broadcast_start_seconds}));
 const active=eventsOn(year,month,day);
 return {start,end,slots,version:'written-tv-v1',holiday_events:active,holiday_labels:active.map(e=>holidayNames[e]),date:`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`};
}
function locate(plan,now){const index=plan.slots.findIndex(s=>now>=s.start&&now<s.end);return index<0?null:{index,item:plan.slots[index],offset:(now-plan.slots[index].start)/1000};}
root.BootlegClock={contentKey,seriesKey,parts,wall,plan,locate,isClassic,isKidsAnime,isAdult,easterDate,holidayDates,eventsOn,holidayEligible};
})(globalThis);
