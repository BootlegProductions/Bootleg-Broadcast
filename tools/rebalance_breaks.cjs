/**
 * Shorten excessive commercial blocks without moving any existing programmes.
 * Reuses measured, channel-approved episodes from source-library.json.
 * An ident is permitted once per commercial block, never on every fourth clip.
 * Run: node tools/rebalance_breaks.cjs
 */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const SHORTS={
 '90s Toons':['Augie Doggie and Doggy Daddy','Wacky Races','Pinky and the Brain'],
 'Cartoons Cartoons':['Regular Show','I Am Weasel','Camp Lazlo','Courage the Cowardly Dog'],
 'Japanime':['Cromartie High School','Neo Ranga'],
 'Off-Licence TV':['Grizzly Tales for Gruesome Kids','The Story of Tracy Beaker'],
 'Star Spangled TV':['Trailer Park Boys The Complete Third Season','Home Improvement','The Osbournes'],
 'AAA':['Aqua Teen Hunger Force','Beavis and Butt-Head','The Maxx'],
 'Dickleodeon':['SpongeBob SquarePants','My Life as a Teenage Robot','The Fairly OddParents'],
 'GirlyPop':['64 Zoo Lane','Pingu','Franny’s Feet'],
 'Dizzy':['Recess','Phineas and Ferb'],
 'What':['jackass the box set','Viva La Bam Complete Seasons 4 & 5','Unsolved Mysteries Ghosts']
};
const KEEP=['type','show','title','url','duration_seconds','duration_evidence','series_id','series_label','content_id','season','episode','episode_number','season_number','episode_part','source_page','language_status','seasonal_tags','holiday_events'];
const round=n=>Math.round(n*1000)/1000;
const id=p=>p.content_id||p.url;
function poolFor(catalogue,channel,month){
 const names=SHORTS[channel]||[];
 const seen=new Set();
 return catalogue.programmes.filter(p=>{
  const seconds=Number(p.duration_seconds);
  if(!names.includes(p.show)||!((p.channels||[p.channel]).includes(channel))||
    p.type!=='Episode'||p.broadcast_held||
    !/^https:\/\/archive\.org\/download\/.+\.mp4$/i.test(p.url||'')||
    /\.ia\.mp4$/i.test(p.url)||!p.duration_evidence||
    !Number.isFinite(seconds)||seconds<295||seconds>950||
    ['non-english','reported-non-english'].includes(p.language_status)||
    p.episode_number===0)return false;
  if(p.seasonal_tags?.includes('christmas')&&month!==12)return false;
  if(p.seasonal_tags?.includes('halloween')&&month!==10)return false;
  if(p.holiday_events?.length)return false;
  const key=id(p);if(seen.has(key))return false;seen.add(key);return true;
 }).sort((a,b)=>String(a.show).localeCompare(String(b.show))||
    (a.season_number||0)-(b.season_number||0)||
    (a.episode_number||0)-(b.episode_number||0)||
    String(a.url).localeCompare(String(b.url)));
}
function pickBridge(available,gap,used,seed){
 if(gap<8*60)return [];
 const budget=gap-75;
 if(budget<300)return [];
 const rotated=available.length?(seed%available.length):0;
 const choices=[...available.slice(rotated),...available.slice(0,rotated)]
    .filter(p=>!used.has(id(p))&&p.duration_seconds<=budget)
    .slice(0,160);
 if(!choices.length)return [];
 let best=[],score=Infinity;
 const consider=(clips)=>{
  const total=clips.reduce((n,p)=>n+p.duration_seconds,0);
  const remain=gap-total;
  if(remain<65||remain>260)return;
  // Aim for approximately two minutes of adverts, and prefer a single
  // cohesive short over two pieces if both fit equally well.
  const value=Math.abs(remain-125)+17*(clips.length-1);
  if(value<score){score=value;best=clips;}
 };
 for(let i=0;i<choices.length;i++){
  const a=choices[i];consider([a]);
  for(let j=i+1;j<choices.length;j++){
   const b=choices[j];
   if(id(a)!==id(b)&&a.duration_seconds+b.duration_seconds<=budget)consider([a,b]);
  }
 }
 return best;
}
function adAllowed(a,month,fromOriginal){
 if(!a||!Number.isFinite(Number(a.duration_seconds))||a.duration_seconds<=0)return false;
 if(!fromOriginal){
  if(a.holiday_events?.length)return false;
  if(a.seasonal_tags?.includes('christmas')&&month!==12)return false;
  if(a.seasonal_tags?.includes('halloween')&&month!==10)return false;
 }
 return true;
}
function rebuildBreak(row,station,month,seed,stats){
 const start=row.broadcast_start_seconds,end=row.broadcast_end_seconds;
 let t=start,remaining=end-start;
 const adpool=station.adverts,ident=Number(station.ident.duration_seconds);
 const old=(row.break_sequence||[]).filter(i=>Number.isInteger(i)&&i>=0&&i<adpool.length);
 const after=adpool.length?seed%adpool.length:0;
 const all=[...new Set([...old,...Array.from({length:adpool.length},(_,i)=>(after+i)%adpool.length)])];
 const originals=new Set(old),used=new Set(),sequence=[];
 while(remaining>ident+0.001){
  let chosen=-1;
  // Leave at most one station ident to close the break.
  // Never cut an advert, and never repeat an advert in a single break.
  for(const i of all){
   if(used.has(i)||!adAllowed(adpool[i],month,originals.has(i)))continue;
   const secs=Number(adpool[i].duration_seconds);
   if(secs<=remaining+0.00001&&
       (remaining-secs<=ident+0.001 || remaining-secs>=4.5)){
    chosen=i;break;
   }
  }
  if(chosen<0)break;
  used.add(chosen);sequence.push(chosen);
  t=round(t+Number(adpool[chosen].duration_seconds));
  remaining=round(end-t);
 }
 if(remaining>0.0005){
  // The ident may be cut by the boundary; adverts never are.
  sequence.push(-1);
  t=round(t+Math.min(ident,remaining));
  remaining=round(end-t);
 }
 stats.identsAfter+=sequence.filter(i=>i===-1).length;
 const result=[];
 if(sequence.length)result.push({...row,break_sequence:sequence,broadcast_end_seconds:t});
 if(remaining>0.0005){
  stats.shortContinuitySeconds+=remaining;
  result.push({type:'Filler',show:row.show,title:row.show+' — Next programme shortly',
    presentation:true,broadcast_start_seconds:t,broadcast_end_seconds:end,block:row.block});
 }
 return result;
}
function rebalanceMonth(schedule,catalogue,channelBreaks,month,stats){
 const byChannel=new Map(Object.keys(SHORTS).map(ch=>[ch,poolFor(catalogue,ch,month)]));
 for(const week of schedule.weeks||[])for(const day of week.week||[])for(const channel of day.channels||[]){
  const station=channelBreaks.channels[channel.name];
  if(!station)throw Error('No commercial/ident catalogue for '+channel.name);
  const used=new Set(channel.playlist.filter(p=>!['Break','Filler','Ident','Advert'].includes(p.type)).map(id));
  const result=[];
  for(const p of channel.playlist){
   if(p.type!=='Break'){result.push(p);continue;}
   stats.breaks++;
   stats.identsBefore+=(p.break_sequence||[]).filter(i=>i===-1).length;
   const duration=p.broadcast_end_seconds-p.broadcast_start_seconds;
   // Bridge only the final 18:00 hour break. The 19:00 programme
   // still starts at exactly 19:00, as authored.
   const prime=p.broadcast_end_seconds>=68400-.001 &&
    p.broadcast_end_seconds<=68400+.001 &&
    p.broadcast_start_seconds>=18*3600 &&duration>=8*60;
   let at=p.broadcast_start_seconds;
   if(prime){
    stats.primeBefore++;stats.primeSecondsBefore+=duration;
    const available=byChannel.get(channel.name)||[];
    const seed=month*1009+Number(day.date)*131+channel.name.length*17;
    const shorts=pickBridge(available,duration,used,seed);
    for(const short of shorts){
     const end=round(at+Number(short.duration_seconds));
     const program=Object.fromEntries(KEEP.filter(k=>short[k]!==undefined).map(k=>[k,short[k]]));
     result.push({...program,block:'Evening short',broadcast_start_seconds:at,broadcast_end_seconds:end});
     at=end;used.add(id(short));stats.shorts++;stats.programmeSeconds+=short.duration_seconds;
    }
    if(shorts.length)stats.primeBridged++;
   }
   if(p.broadcast_end_seconds-at>0.0005){
    const replacement={...p,broadcast_start_seconds:at};
    result.push(...rebuildBreak(replacement,station,month,
      month*7777+Number(day.date)*67+Math.round(at)+channel.name.length,stats));
   }
   if(prime)stats.primeSecondsAfter+=p.broadcast_end_seconds-at;
  }
  // Checks: no original programme was moved; all durations are measured.
  let prior=null;
  for(const p of result){
   if(prior!==null&&Math.abs(p.broadcast_start_seconds-prior)>0.021)
    throw Error('Timeline discontinuity '+month+'/'+day.date+'/'+channel.name+': '+prior+' -> '+p.broadcast_start_seconds);
   if(!(p.broadcast_end_seconds>p.broadcast_start_seconds))
    throw Error('Invalid duration '+channel.name+' '+p.title);
   if(p.type==='Episode'&&Math.abs(p.broadcast_end_seconds-p.broadcast_start_seconds-p.duration_seconds)>0.021)
    throw Error('Episode runtime mismatch '+channel.name+' '+p.title);
   if(p.type==='Break'&&(p.break_sequence.filter(n=>n===-1).length>1||
     new Set(p.break_sequence.filter(n=>n>=0)).size!==p.break_sequence.filter(n=>n>=0).length))
    throw Error('Duplicate ident or commercial '+channel.name);
   prior=p.broadcast_end_seconds;
  }
  channel.playlist=result;
 }
 return schedule;
}
function main(){
 const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
 const catalogue=read('source-library.json'),breaks=read('channel-breaks.json');
 const stats={breaks:0,identsBefore:0,identsAfter:0,shorts:0,programmeSeconds:0,
   primeBefore:0,primeBridged:0,primeSecondsBefore:0,primeSecondsAfter:0,
   shortContinuitySeconds:0};
 const months=['january','february','march','april','may','june','july','august','september','october','november','december'];
 for(let m=1;m<=12;m++){
  const file='schedules/'+months[m-1]+'.json',data=read(file);
  rebalanceMonth(data,catalogue,breaks,m,stats);
  fs.writeFileSync(path.join(ROOT,file),JSON.stringify(data));
  if(m===10)fs.writeFileSync(path.join(ROOT,'schedule.json'),JSON.stringify(data));
 }
 if(stats.identsAfter>stats.breaks||!stats.primeBridged)
  throw Error('Break reform did not reduce ident frequency or bridge evenings');
 fs.writeFileSync(path.join(ROOT,'break-rebalance-report.json'),JSON.stringify({
  version:'2026-10',policy:'One ident per commercial block, no repeated adverts within a block; evening short programmes fill long 18:45–19:00 intervals',
  ...stats},null,2)+'\n');
 console.log(JSON.stringify(stats,null,2));
}
if(require.main===module)main();
module.exports={rebalanceMonth,pickBridge,rebuildBreak,poolFor};
