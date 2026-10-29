/* Shared broadcast playback and durable, provisional source feedback. */
const Broadcast=(()=>{
 let pools={},breaks={},gapMedia=null,cache=null,cacheSchedule=null,cacheKey='',mode='live',selected=null,holding=false,slotKey='',syncing=false,clockSynced=false;
 let anchor=Date.now(),anchorPerf=performance.now();
 // Playback interruptions are temporary, not proof that an Archive file is dead.
 // Keep diagnostic reports, but never preload historical reports as a blacklist.
 const failed=new Map(),repairs=new Map(),queued=new Map();
 const FAILURE_COOLDOWN_MS=45000;
 // Local HTTP previews and older browsers may not expose randomUUID.
 const clientId=()=>globalThis.crypto?.randomUUID?.()||'device-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2);
 let client;try{client=sessionStorage.getItem('bootleg.report.client');if(!client){client=clientId();sessionStorage.setItem('bootleg.report.client',client);}}catch{client=clientId();}
 const now=()=>anchor+(performance.now()-anchorPerf);
 async function clock(){if(globalThis.BOOTLEG_HOSTING?.backend===false){anchor=Date.now();anchorPerf=performance.now();clockSynced=false;return;}const before=performance.now();try{const r=await fetch('/api/time',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();if(!Number.isFinite(data.server_time))throw Error();anchor=data.server_time+(performance.now()-before)/2;anchorPerf=performance.now();clockSynced=true;}catch{clockSynced=false;}}
 async function health(){if(globalThis.BOOTLEG_HOSTING?.backend===false){$('feedback-state').textContent='Failed sources held on this browser';return;}try{const r=await fetch('/api/health',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();repairs.clear();for(const fix of data.repairs||[]){repairs.set(fix.url,fix);if(['restored','replaced'].includes(fix.status))failed.delete(fix.url);}$('feedback-state').textContent='Source feedback connected';for(const [id,body] of queued)sendReport(id,body);}catch{$('feedback-state').textContent='Feedback unavailable · failed sources held for this visit';}}
 async function sendReport(id,body){if(globalThis.BOOTLEG_HOSTING?.backend===false){$('feedback-state').textContent='Failed source held on this browser';return;}try{const r=await fetch('/api/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw Error();queued.delete(id);}catch{queued.set(id,body);$('feedback-state').textContent='Report waiting to save · keep this TV open';}}
 function report(url,reason){if(!/^https:\/\/archive\.org\/download\//.test(url||''))return;failed.set(url,Date.now()+FAILURE_COOLDOWN_MS);try{const flags=JSON.parse(localStorage.getItem('bootleg.source.flags')||'{}');flags[url]={url,title:item()?.title,channel:getCurrentChannelData()?.name,reason:'Playback interruption (not a confirmed dead link): '+reason,reported_at:new Date().toISOString()};localStorage.setItem('bootleg.source.flags',JSON.stringify(flags));}catch{}const body={url,title:item()?.title,channel:getCurrentChannelData()?.name,client,slot:mode==='live'?item()?.slot_id||slotKey:'ondemand:'+Math.floor(now()/3600000),reason};const id=url+body.slot;if(!queued.has(id))sendReport(id,body);}
 function blocked(url){const until=failed.get(url)||0;if(until&&until<=Date.now())failed.delete(url);return until>Date.now()||repairs.get(url)?.status==='quarantined';}
 function activeUrl(urls){return player.getAttribute?.('src')||player.currentSrc||urls[sourceIndex]||'';}
 // Ed, Edd n Eddy catalogue entries pointed to Archive auto-derived .ia.mp4.
 // The exact original .mp4 is present for all 130 affected episode filenames.
 const edArchive=/^https:\/\/archive\.org\/download\/ed-edd-n-eddy-full-series-1999-2009\//i;
 const edCollection='ed-edd-n-eddy-full-series-1999-2009';
 let edFiles=[];
 function edCode(text){
   const m=String(text||'').match(/S(\d{1,2})[\s._-]*E(\d{1,2})/i)
     ||String(text||'').match(/(?:^|[^\d])(\d{1,2})x(\d{1,2})(?!\d)/i);
   return m?String(Number(m[1]))+':'+String(Number(m[2])):null;
 }
 function edEpisodeCode(p){
   const inputs=[p?.url,...p?.alternates||[],p?.title,p?.show];
   return inputs.map(s=>{try{return decodeURIComponent(String(s||''));}catch{return String(s||'');}})
     .map(edCode).find(Boolean);
 }
 async function prepareEdFiles(){
   try{
     const response=await fetch('https://archive.org/metadata/'+edCollection);
     if(!response.ok)return;
     const metadata=await response.json();
     if(!Array.isArray(metadata.files))return;
     edFiles=metadata.files.filter(f=>typeof f.name==='string'&&/\.mp4$/i.test(f.name)&&!/\.ia\.mp4$/i.test(f.name));
   }catch{}
 }
 function originalEdSource(p){
   const code=edEpisodeCode(p);
   if(!code||!edFiles.length)return null;
   const matches=edFiles.filter(f=>edCode(f.name)===code);
   if(matches.length!==1)return null;
   const path=matches[0].name.split('/').map(encodeURIComponent).join('/');
   return 'https://archive.org/download/'+edCollection+'/'+path;
 }
 function sources(p){
   const urls=[p?.url,...p?.alternates||[]].filter(Boolean).map(u=>repairs.get(u)?.status==='replaced'?repairs.get(u).replacement:u);
   const ed=urls.some(u=>edArchive.test(u))||/ed,\s*edd\s*n\s*eddy/i.test(String(p?.show||'')+' '+String(p?.title||''));
   const original=ed?originalEdSource(p):null;
   const expanded=urls.flatMap(u=>edArchive.test(u)&&/\.ia\.mp4(?:[?#]|$)/i.test(u)
    ?[u.replace(/\.ia\.mp4(?=[?#]|$)/i,'.mp4')]:[u]);
   const key=String(p?.title||'').toLowerCase().replace(/[^a-z0-9]+/g,'');
   const holidayAlternates=globalThis.BOOTLEG_HOLIDAY_ALTERNATES?.[key]||[];
   return [...new Set([original,...expanded,...holidayAlternates].filter(Boolean))];
 }
 function day(){
  const raw=getRotationDay();if(!raw)return null;const p=BootlegClock.parts(now()),month=MONTHS.indexOf(currentMonth)+1,d=previewDate||p.day,y=p.year,key=`${y}:${month}:${d}`;
  if(cache&&cacheSchedule===schedule&&cacheKey===key)return cache;
  cache={...raw,channels:raw.channels.map(c=>{const plan=BootlegClock.plan({year:y,month,day:d,channel:c.name,items:c.playlist,pools,breaks});return {...c,playlist:plan.slots,plan};})};cacheSchedule=schedule;cacheKey=key;return cache;
 }
 function viewingTime(){if(!previewDate)return now();const p=BootlegClock.parts(now());return BootlegClock.wall(p.year,MONTHS.indexOf(currentMonth)+1,previewDate,p.hour)+p.minute*60000+p.second*1000;}
 function livePosition(){const c=getCurrentChannelData();return c?.plan?BootlegClock.locate(c.plan,viewingTime()):null;}
 function item(){return selected||gapMedia||getCurrentChannelData()?.playlist?.[currentIndex]||null;}
 const time=ms=>new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/London',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(ms));
 function seek(){if(mode==='live'){const pos=livePosition();let offset=gapMedia ? Math.max(0,(viewingTime()-gapMedia.start)/1000) : pos?.offset||0;if(item()?.loop&&Number.isFinite(player.duration)&&player.duration>0)offset%=player.duration;return offset;}return player.currentTime||pendingSeek;}
 function fillGap(message){
  if(mode!=='live'){returnLive();return;}
  const c=getCurrentChannelData(),original=c?.playlist?.[currentIndex],ident=breaks.channels?.[c?.name]?.ident;
  if(!original||!ident||gapMedia){presentation('Signal unavailable · channel ident could not load');return;}
  gapMedia={...ident,start:viewingTime(),end:original.end,slot_id:original.slot_id,loop:false,gap_ident:true};
  resetPlayer();clearCard();sourceRetry=0;stalledAttempts=0;loadItemSource(gapMedia,0,seek());
  if(message)showStatus(message,2000);updateRemote();
 }

 function updateIntermission(){
  const p=item();if(!p||p.type!=='Filler'||!holding)return;
  const timeRemaining=Math.max(0,Math.ceil((p.end||viewingTime())-viewingTime()));
  const next=getCurrentChannelData()?.playlist?.find(q=>q.start>=p.end-0.01&&
    !NON_PROGRAMME.has(q.type)&&q.type!=='Filler'&&!q.presentation);
  const phase=Math.floor(viewingTime()/12)%3;
  $('broadcast-card-title').textContent=['STATION BREAK','UP NEXT ON '+(getCurrentChannelData()?.name||'BOOTLEG TV'),'TRANSMISSION RESUMING'][phase];
  const count=Math.floor(timeRemaining/60)+':'+String(timeRemaining%60).padStart(2,'0');
  $('broadcast-card-next').textContent=next?
    'NEXT · '+next.title+' · '+time(next.start)+' UK  |  '+count+' TO GO':
    'RETURNING TO SCHEDULED BROADCAST  |  '+count+' TO GO';
 }
 function presentation(message){holding=true;player.pause();cancelRecovery();$('broadcast-card').hidden=false;$('broadcast-card').classList.toggle('intermission',item()?.type==='Filler');$('broadcast-card-channel').textContent=getCurrentChannelData()?.name||'BOOTLEG BROADCAST';$('broadcast-card-title').textContent=message||item()?.title||'Stay tuned';const next=getCurrentChannelData()?.playlist?.find(p=>p.start>viewingTime()&&!NON_PROGRAMME.has(p.type)&&p.type!=='Filler'&&!p.presentation);$('broadcast-card-next').textContent=mode==='live'&&next?'Next: '+next.title+' · '+time(next.start)+' UK':'Returning to scheduled broadcast…';hideStatus();updateIntermission();updateRemote();}
 function clearCard(){holding=false;$('broadcast-card').hidden=true;$('broadcast-card').classList.remove('intermission');}
 function load(){
  gapMedia=null;
  const c=getCurrentChannelData();if(!c?.playlist?.length)return;selected=null;mode='live';const pos=livePosition();if(!pos)return;currentIndex=pos.index;slotKey=pos.item.slot_id;play();
 }
 function play(){
  const p=item();if(!p)return;sourceRetry=0;stalledAttempts=0;clearCard();updateChannelOverlay();
  const urls=sources(p);let index=urls.findIndex(u=>!blocked(u));
  // Never let transient interruptions suppress a source indefinitely.
  if(index<0&&urls.some(u=>repairs.get(u)?.status!=='quarantined')){
   urls.forEach(u=>failed.delete(u));index=urls.findIndex(u=>!blocked(u));
  }
  if(p.presentation){presentation(p.type==='Filler'?'CHANNEL INTERMISSION · NEXT PROGRAMME TO FOLLOW':p.title);}else if(index<0){fillGap('SIGNAL UNAVAILABLE · CHANNEL IDENT BREAK');}
  else loadItemSource(p,index,mode==='live'?seek():0);
  renderScheduleOverlay();updateRemote();if($('guidePanel').open)renderGuideList();
 }
 async function returnLive(){
  selected=null;mode='live';clearCard();const month=MONTHS[BootlegClock.parts(now()).month-1];
  if(previewDate||currentMonth!==month)await selectSchedule(month,null);else{resetPlayer();load();}
  if(!poweredOn)togglePower();else{safePlay();armSourceTimeout();}showChannelOverlay();
 }
 function choose(channel,index){gapMedia=null;const p=getTodaySchedule()?.channels?.[channel]?.playlist?.[index];if(!p||NON_PROGRAMME.has(p.type)||p.type==='Filler'||p.presentation)return;resetPlayer();currentChannel=channel;currentIndex=index;selected={...p};mode='ondemand';slotKey='ondemand:'+p.url;play();if(!poweredOn)togglePower();showChannelOverlay();closeGuide();}
 function chooseItem(p){gapMedia=null;if(p.broadcast_held||(sources(p).length>0&&sources(p).every(u=>repairs.get(u)?.status==='quarantined'))){showStatus('SOURCE HELD FOR REVIEW',3000);return;}resetPlayer();const index=getTodaySchedule()?.channels?.findIndex(c=>c.name===p.channel);if(index>=0)currentChannel=index;selected={...p};mode='ondemand';slotKey='ondemand:'+p.url;play();if(!poweredOn)togglePower();showChannelOverlay();}
 function skip(direction){const c=getCurrentChannelData();if(!c)return;const next=nextProgrammeIndex(c.playlist,currentIndex,direction);if(next>=0)choose(currentChannel,next);}
 function restart(){gapMedia=null;const p=item();if(!p)return;resetPlayer();selected={...p};mode='ondemand';play();if(!poweredOn)togglePower();}
 function alternate(manual=false){const p=item(),urls=sources(p),active=activeUrl(urls);
  // Archive metadata can arrive after playback begins and prepend a new source.
  // Select by the URL actually playing, not by its stale numeric index.
  let next=urls.findIndex(u=>u!==active&&!blocked(u));
  if(next<0&&manual){next=urls.findIndex(u=>u!==active);if(next>=0)failed.delete(urls[next]);}
  if(next<0)return false;
  sourceRetry=0;stalledAttempts=0;clearCard();loadItemSource(p,next,seek());return true;
 }
 function retry(){const p=item();if(!p)return;const urls=sources(p);if(!urls.length)return;
  const current=urls.indexOf(activeUrl(urls));const index=current>=0?current:Math.min(sourceIndex,urls.length-1);
  failed.delete(urls[index]);clearCard();sourceRetry=0;stalledAttempts=0;loadItemSource(p,index,seek());
 }
 function recover(reason){if(!poweredOn||holding)return;cancelRecovery();const p=item();if(!p)return;
  if(gapMedia){presentation('Signal unavailable · returning at the next scheduled programme');return;}
  if(sourceRetry<1){sourceRetry++;const gen=tuningGeneration;showStatus('RE-TUNING SIGNAL…',0);const offset=seek();recoveryTimer=setTimeout(()=>{if(gen===tuningGeneration&&poweredOn)loadItemSource(p,sourceIndex,mode==='live'?seek():offset);},700);return;}
  // Log the URL in the video element, never a different source shifted by late metadata.
  report(activeUrl(sources(p)),reason+(player.error?.code?' · media code '+player.error.code:''));
  if(alternate())return;fillGap('SIGNAL INTERRUPTED · CHANNEL IDENT BREAK');
  if(mode!=='live'){const gen=tuningGeneration;recoveryTimer=setTimeout(()=>{if(gen===tuningGeneration&&poweredOn)returnLive();},1800);}
 }
 function ended(){
  if(!poweredOn)return;
  if(mode!=='live'){returnLive();return;}
  const p=item(),pos=livePosition();if(!p)return;
  // An early media end must never force a reload of the same clock slot.
  if(pos&&pos.item.slot_id!==slotKey){sync();return;}
  if(p.loop){player.currentTime=0;safePlay();return;}
  if(gapMedia||NON_PROGRAMME.has(p.type)||viewingTime()>=p.end-1000){presentation(gapMedia?'Source unavailable · waiting for the next scheduled programme':'Next programme starts shortly');return;}
  fillGap('PROGRAMME ENDED EARLY · CHECK SOURCE RUNTIME');
 }
 function pause(){if(!poweredOn){togglePower();return;}if(holding){returnLive();return;}if(player.paused){safePlay();armSourceTimeout();}else{selected={...item()};mode='timeshift';player.pause();cancelRecovery();showStatus('PAUSED · RETURN TO BROADCAST TO REJOIN',0);}updateRemote();}
 function sync(force=false){if(!schedule||syncing)return;const p=BootlegClock.parts(now());
  if(mode==='live'&&!previewDate&&MONTHS[p.month-1]!==currentMonth){syncing=true;selectSchedule(MONTHS[p.month-1],null).finally(()=>syncing=false);return;}
  const pos=livePosition();if(!pos)return;
  if(mode==='live'&&(pos.item.slot_id!==slotKey||force)){resetPlayer();load();}
  else if(mode==='live'&&poweredOn&&!holding&&!player.paused&&!player.seeking&&player.readyState>=3&&performance.now()-lastDriftCheck>12000){lastDriftCheck=performance.now();const target=seek();if(target>=player.duration-0.3&&!item()?.loop){if(gapMedia||NON_PROGRAMME.has(item()?.type))presentation('Next programme starts shortly');else fillGap();}else if(Math.abs(player.currentTime-target)>4&&Number.isFinite(player.duration))try{player.currentTime=Math.min(target,player.duration-0.1);}catch{}}
  if(holding){if(item()?.type==='Filler')updateIntermission();else{const next=getCurrentChannelData()?.playlist?.find(p=>p.start>viewingTime()&&!NON_PROGRAMME.has(p.type)&&p.type!=='Filler'&&!p.presentation);if(next)$('broadcast-card-next').textContent='Next: '+next.title+' · '+time(next.start)+' UK';}}
 }
 let lastDriftCheck=0;
 function remote(){const c=getCurrentChannelData(),p=item();$('broadcast-button').textContent=mode==='live'&&!previewDate?'LIVE · '+(clockSynced?'UK':'DEVICE CLOCK'):'RETURN TO BROADCAST';$('broadcast-button').setAttribute('aria-pressed',String(mode==='live'&&!previewDate));$('broadcast-mode').textContent=previewDate?'DATE PREVIEW':mode==='live'?(clockSynced?'SHARED UK BROADCAST':'BROADCAST · DEVICE CLOCK'):'WATCHING A SELECTION · RETURNS TO BROADCAST';document.body.dataset.season=currentMonth==='october'?'october':currentMonth==='december'?'december':'regular';}
 function mini(){const c=getCurrentChannelData();if(!c)return;const pos=livePosition(),start=pos?.index||0;const upcoming=c.playlist.map((p,n)=>({p,n})).filter(({p,n})=>n>=start&&!NON_PROGRAMME.has(p.type)&&p.type!=='Filler'&&!p.presentation).slice(0,8);$('scheduleOverlay').innerHTML=`<div class="mini-guide-header"><h3>TV GUIDE <small>${escapeHtml(c.name)}</small></h3><button type="button" onclick="toggleScheduleOverlay()" aria-label="Close mini guide">×</button></div><div class="schedule-status">${escapeHtml(previewDate?'DATE PREVIEW':'UK BROADCAST')} · ${escapeHtml(pos?.item.block||'')}</div>${upcoming.map(({p,n})=>`<button type="button" class="schedule-item ${n===pos?.index?'now-playing':''}" onclick="chooseProgramme(${currentChannel},${n})"><span class="schedule-marker">${time(p.start)}</span><span class="schedule-title">${escapeHtml(p.title)}${n===pos?.index?' · ON AIR':''}</span></button>`).join('')}<button type="button" class="guide-expand" onclick="openGuide()">FULL DAY GUIDE</button>`;}
 function guide(){const c=getTodaySchedule()?.channels?.[Number($('guide-channel').value)],query=$('guide-search').value.trim().toLowerCase();if(!c){$('guide-list').textContent='No schedule loaded.';return;}const pos=BootlegClock.locate(c.plan,viewingTime());const list=c.playlist.map((p,n)=>({p,n})).filter(({p})=>!NON_PROGRAMME.has(p.type)&&p.type!=='Filler'&&!p.presentation&&(!query||`${p.title} ${p.show} ${p.block}`.toLowerCase().includes(query)));$('guide-count').textContent=`${list.length} slots · ${c.plan.holiday_labels?.length?c.plan.holiday_labels.join(' / ')+' · ':''}all times UK`;$('guide-list').innerHTML=list.length?list.map(({p,n})=>{const src=sourcePage(p.url);return `<article class="guide-programme ${n===pos?.index?'selected':''}"><button type="button" class="programme-play" onclick="chooseProgramme(${Number($('guide-channel').value)},${n})" ${p.type==='Filler'||p.presentation?'disabled':''}><span class="programme-type">${time(p.start)}–${time(p.end)} UK · ${escapeHtml(p.block)}${n===pos?.index?' · ON AIR':''}</span><strong>${escapeHtml(p.title)}</strong><span>${escapeHtml(p.show||'')}</span></button>${src?`<a href="${escapeHtml(src)}" target="_blank" rel="noopener noreferrer">SOURCE</a>`:''}</article>`;}).join(''):'<p class="guide-empty">No matching scheduled slots. Search the source library for more.</p>';}
 async function boot(){const metadata=prepareEdFiles();const data=await Promise.all([fetchJson('channel-breaks.json?v=0370'),clock(),health(),Promise.race([metadata,new Promise(resolve=>setTimeout(resolve,2500))])]);breaks=data[0];
  // Extra Archive Christmas commercials enter the normal December ad rotation.
  // Append so compiled schedule indexes still point to their original clips.
  for(const clip of globalThis.BOOTLEG_SEASONAL_COMMERCIALS?.adverts||[]){
   const station=breaks.channels?.[clip.channel];if(!station)continue;
   if(!station.adverts.some(p=>p.url===clip.url))station.adverts.push(clip);
  }
currentMonth=MONTHS[BootlegClock.parts(now()).month-1];setInterval(sync,1000);setInterval(clock,300000);setInterval(health,60000);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'){clock().then(()=>sync());health();}});}
 async function deepLink(){const url=new URLSearchParams(location.search).get('watch');if(!url)return;try{const data=await fetchJson('source-library.json?v=0370');const p=data.programmes.find(p=>p.url===url);if(p){chooseItem(p);history.replaceState(null,'',location.pathname);}}catch{showStatus('SELECTED PROGRAMME UNAVAILABLE',3000);}}
 return {boot,now,day,item,sources,seek,load,play,returnLive,choose,chooseItem,skip,restart,alternate,retry,recover,ended,pause,sync,remote,mini,guide,deepLink,mode:()=>mode,holding:()=>holding,fillGap,presentation};
})();
