/* A deterministic UK wall-clock plan. Media buffering never changes its slots. */
(function(root){
'use strict';
const zone='Europe/London', fmt=new Intl.DateTimeFormat('en-GB',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
const parts=ms=>Object.fromEntries(fmt.formatToParts(new Date(ms)).filter(p=>p.type!=='literal').map(p=>[p.type,Number(p.value)]));
function wall(y,m,d,h=0){const target=Date.UTC(y,m-1,d,Math.floor(h),Math.round((h%1)*60));let guess=target;for(let i=0;i<4;i++){const p=parts(guess);const shown=Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second);const delta=target-shown;if(!delta)break;guess+=delta;}return guess;}
const hash=s=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0;};
const isCourage=p=>/courage.*cowardly dog/i.test(p.show+' '+p.title)||/^courage$/i.test(p.show);
const inWindow=(p,h)=>{const w=p.broadcast_window||(isCourage(p)?{start_hour:18,end_hour:7}:null);if(!w)return true;return w.start_hour>w.end_hour?(h>=w.start_hour||h<w.end_hour):(h>=w.start_hour&&h<w.end_hour);};
const octoberWeight=p=>Number(p.seasonal_priority?.october)||(isCourage(p)?4:0)||((p.seasonal_tags||[]).includes('halloween')?3:1);
const holidayNames={'christmas':'Christmas','valentine':'Valentine’s Day','st-patrick':'St Patrick’s Day','easter':'Easter Sunday','thanksgiving':'US Thanksgiving','new-year':'New Year'};
function easterDate(year){const a=year%19,b=Math.floor(year/100),c=year%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),n=h+l-7*m+114;return [Math.floor(n/31),n%31+1];}
function holidayDates(year){const first=new Date(Date.UTC(year,10,1)).getUTCDay();return {'christmas':[[12,24],[12,25],[12,26]],'valentine':[[2,14]],'st-patrick':[[3,17]],'easter':[easterDate(year)],'thanksgiving':[[11,1+(4-first+7)%7+21]],'new-year':[[1,1],[12,31]]};}
const eventsOn=(year,month,day)=>Object.entries(holidayDates(year)).filter(([,dates])=>dates.some(([m,d])=>month===m&&day===d)).map(([name])=>name);
const holidayEligible=(p,year,month,day)=>!p.holiday_events?.length||p.holiday_events.some(event=>event==='christmas'?month===12:(holidayDates(year)[event]||[]).some(([m,d])=>month===m&&day===d));
const seasonalWeight=(p,month,active)=>{if(active.some(event=>[...(p.holiday_events||[]),...(p.holiday_priority||[]),...(p.seasonal_tags||[])].includes(event)))return 6;if(month===10)return octoberWeight(p);if(month===12)return (p.seasonal_tags||[]).includes('christmas')?3:(p.seasonal_tags||[]).some(t=>['winter','snow'].includes(t))?2:1;return 1;};
const isClassic=p=>/jetsons|flintstones|tom and jerry|looney tunes|merry melodies|popeye|wacky races/i.test(p.show+' '+p.title);
const isKidsAnime=p=>!/digimon ghost game/i.test(p.show+' '+p.title)&&/pok[eé]mon|hamtaro|digimon|bakugan|jewelpet|precure|pretty cure|parappa|doraemon|yu-gi-oh|beyblade|sonic/i.test(p.show+' '+p.title);
const isAdult=p=>p.daypart==='Evening'||/^monster(?:\s*\(|$)/i.test(p.show)||/beastars|berserk|gintama|evangelion|death note|akira|perfect blue|ghost in the shell|elfen lied|higurashi|hellsing|parasyte|ninja scroll|tokyo ghoul|attack on titan|serial experiments|devilman|misery|the thing|creepshow|black christmas|30 days of night|the shining/i.test(p.show+' '+p.title);
function seconds(p){if(p.type==='Ident')return 12;const duration=Number(p.duration_seconds);if(duration>0)return Math.ceil(duration);if(p.type==='Advert')return 30;return 1800;}
function clean(items){const seen=new Set();return items.filter(p=>!p?.broadcast_held&&p?.url&&!['Ident','Advert','AdBreak'].includes(p.type)&&!seen.has(p.broadcast_identity||p.url)&&seen.add(p.broadcast_identity||p.url));}
function plan({year,month,day,channel,items=[],pools={},breaks={}}){
 const start=wall(year,month,day),nextDate=new Date(Date.UTC(year,month-1,day+1)),end=wall(nextDate.getUTCFullYear(),nextDate.getUTCMonth()+1,nextDate.getUTCDate());
 const known=new Map((pools[channel]||[]).map(p=>[p.url,p]));
 const candidates=clean([...items.map(p=>known.has(p.url)?{...p,...known.get(p.url)}:p),...(pools[channel]||[])]).filter(p=>(!p.schedule_months?.length||p.schedule_months.includes(month))&&(p.type!=='Movie'||p.duration_seconds>0)&&holidayEligible(p,year,month,day));
 const bounds=[0,2.5,7,12,18,21,24];if(channel==='Cartoons Cartoons')bounds.push(8);if(month===12)bounds.push(3,4);bounds.sort((a,b)=>a-b);
 const slots=[],seed=`v4:${year}-${month}-${day}:${channel}`;
 const activeEvents=eventsOn(year,month,day);
 const season=month===10?'october':month===12?'december':'regular';
 const ident={type:'Ident',title:month===10?'Halloween on Bootleg Broadcast':month===12?'Christmas on Bootleg Broadcast':channel+' · Stay tuned',show:channel,url:breaks[season]?.ident||breaks.regular?.ident||items.find(p=>p.type==='Ident'&&p.url)?.url||'',duration_seconds:12};
 function append(item,t,len,label){slots.push({...item,start:t,end:t+len*1000,block:label,slot_id:seed+':'+t});}
 for(let b=0;b<bounds.length-1;b++){
  const h=bounds[b],bh=bounds[b+1];let t=h===24?end:wall(year,month,day,h);const stop=bh===24?end:wall(year,month,day,bh);
  const fireplace=month===12&&h===3&&breaks.fireplace;
  if(fireplace){append({...breaks.fireplace,type:'Filler',title:'Christmas overnight fireplace',loop:true},t,(stop-t)/1000,'Holiday hearth');continue;}
  const afterHours=h>=2.5&&h<7;
  let label=afterHours?'After hours':h<2.5?'Late night':h<12?'Morning':h<18?'Afternoon':h<21?'Evening':'Late night';
  let eligible=candidates;
  if(channel==='Cartoons Cartoons'&&h>=8&&h<12){eligible=candidates.filter(p=>isClassic(p)&&p.duration_seconds>200);label='Classic cartoon mornings';}
  else if(channel==='Japanime'){
   if(h>=7&&h<12){eligible=candidates.filter(isKidsAnime);label='Kids anime mornings';}
   else if(h>=12&&h<21){eligible=candidates.filter(p=>!isAdult(p));label=h<18?'Anime afternoons':'Anime evenings';}
   else{eligible=candidates.filter(isAdult);label=afterHours?'After hours':'Anime after dark';}
  }else if(h>=7&&h<21)eligible=candidates.filter(p=>!isAdult(p));
  eligible=eligible.filter(p=>inWindow(p,h));
  if(!eligible.length){append({...ident,title:label+' · Intermission',presentation:true},t,(stop-t)/1000,label);continue;}
  // Extra rounds increase October airtime without making these year-round shows exclusive to October.
  const rotation=[];const weighted=eligible.map(p=>({p,weight:Math.min(6,Math.max(1,seasonalWeight(p,month,activeEvents))),current:0}));
  const totalWeight=weighted.reduce((n,x)=>n+x.weight,0);
  for(let i=0;i<totalWeight;i++){for(const x of weighted)x.current+=x.weight;const next=weighted.reduce((a,b)=>b.current>a.current?b:a);next.current-=totalWeight;rotation.push(next.p);}
  const courage=month===10&&channel==='Cartoons Cartoons'&&h===18?eligible.filter(isCourage):[];
  const event=activeEvents[0]||(month===12?'christmas':null);
  const holidayFeature=event&&[12,18,21].includes(h)?eligible.filter(p=>[...(p.holiday_events||[]),...(p.holiday_priority||[]),...(p.seasonal_tags||[])].includes(event)):[];
  const featurePool=courage.length?courage:holidayFeature;
  const featureLabel=courage.length?'Courage · October evening double bill':(holidayNames[event]||'Holiday')+' · '+(activeEvents.length?'holiday spotlight':'seasonal spotlight');
  const featured=featurePool.length?Array.from({length:Math.min(activeEvents.length?3:2,featurePool.length)},(_,i)=>featurePool[(hash(year+':'+month+':'+(courage.length?'courage':event))+(day-1)*2+i)%featurePool.length]):[];
  const offset=hash(seed+':'+h)%rotation.length;let n=0;const recent=[];
  while(t<stop){
   let chosen=featured.shift()||null;if(chosen&&seconds(chosen)*1000>stop-t-12000)chosen=null;const isFeatured=Boolean(chosen);
   if(!chosen)for(let j=0;j<rotation.length;j++){const p=rotation[(offset+n+j)%rotation.length];if(!recent.includes(p.url)&&seconds(p)*1000<=stop-t-12000){chosen=p;n+=j+1;break;}}
   if(!chosen)for(const p of eligible){if(seconds(p)*1000<=stop-t-12000){chosen=p;break;}}
   if(!chosen){append({...ident,title:'Back shortly · '+channel,presentation:true},t,(stop-t)/1000,label);break;}
   recent.push(chosen.url);if(recent.length>2)recent.shift();
   const len=seconds(chosen);append(chosen,t,len,isFeatured?featureLabel:label);t+=len*1000;
   // Every programme is followed by a station ident and a short themed break.
   if(stop-t>=12000){append(ident,t,12,label);t+=12000;}
   const adPool=breaks[season]?.adverts||[];
   if(adPool.length){const safeAds=adPool.filter(p=>(h<7||h>=21)||!p.daypart||p.daypart!=='Evening');if(safeAds.length){const ad=safeAds[hash(seed+':ad:'+t)%safeAds.length];const len=Math.min(seconds(ad),60);if(len*1000<=stop-t){append({...ad,type:'Advert'},t,len,label);t+=len*1000;}}}
   if(channel==='Cartoons Cartoons'&&breaks.city?.length&&stop-t>=30000){const bumper=breaks.city[hash(seed+':city:'+t)%breaks.city.length],len=Math.min(seconds(bumper),30);append({...bumper,type:'Ident'},t,len,label);t+=len*1000;}
  }
 }
 return {start,end,slots,version:'v4',holiday_events:activeEvents,holiday_labels:activeEvents.map(e=>holidayNames[e]),date:`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`};
}
function locate(plan,now){const index=plan.slots.findIndex(s=>now>=s.start&&now<s.end);return index<0?null:{index,item:plan.slots[index],offset:(now-plan.slots[index].start)/1000};}
root.BootlegClock={parts,wall,hash,plan,locate,isClassic,isKidsAnime,isAdult,easterDate,holidayDates,eventsOn,holidayEligible};
})(globalThis);
