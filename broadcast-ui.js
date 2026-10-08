/* Shared broadcast playback and durable, provisional source feedback. */
const Broadcast=(()=>{
 let pools={},breaks={},cache=null,cacheSchedule=null,cacheKey='',mode='live',selected=null,holding=false,slotKey='',syncing=false,clockSynced=false;
 let anchor=Date.now(),anchorPerf=performance.now();
 const failed=new Set();try{for(const url of Object.keys(JSON.parse(localStorage.getItem('bootleg.source.flags')||'{}')))failed.add(url);}catch{}const repairs=new Map(),queued=new Map();
 let client;try{client=sessionStorage.getItem('bootleg.report.client');if(!client){client=crypto.randomUUID();sessionStorage.setItem('bootleg.report.client',client);}}catch{client=crypto.randomUUID();}
 const now=()=>anchor+(performance.now()-anchorPerf);
 async function clock(){if(globalThis.BOOTLEG_HOSTING?.backend===false){anchor=Date.now();anchorPerf=performance.now();clockSynced=false;return;}const before=performance.now();try{const r=await fetch('/api/time',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();if(!Number.isFinite(data.server_time))throw Error();anchor=data.server_time+(performance.now()-before)/2;anchorPerf=performance.now();clockSynced=true;}catch{clockSynced=false;}}
 async function health(){if(globalThis.BOOTLEG_HOSTING?.backend===false){$('feedback-state').textContent='Failed sources skipped for this visit';return;}try{const r=await fetch('/api/health',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();repairs.clear();for(const fix of data.repairs||[]){repairs.set(fix.url,fix);if(['restored','replaced'].includes(fix.status))failed.delete(fix.url);}$('feedback-state').textContent='Source feedback connected';for(const [id,body] of queued)sendReport(id,body);}catch{$('feedback-state').textContent='Feedback unavailable · failed sources held for this visit';}}
 async function sendReport(id,body){if(globalThis.BOOTLEG_HOSTING?.backend===false){$('feedback-state').textContent='Failed source skipped for this visit';return;}try{const r=await fetch('/api/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw Error();queued.delete(id);}catch{queued.set(id,body);$('feedback-state').textContent='Report waiting to save · keep this TV open';}}
 function report(url,reason){if(!/^https:\/\/archive\.org\/download\//.test(url||''))return;failed.add(url);const body={url,title:item()?.title,channel:getCurrentChannelData()?.name,client,slot:mode==='live'?item()?.slot_id||slotKey:'ondemand:'+Math.floor(now()/3600000),reason};const id=url+body.slot;if(!queued.has(id))sendReport(id,body);}
 function blocked(url){return failed.has(url)||repairs.get(url)?.status==='quarantined';}
 function sources(p){return [...new Set([p?.url,...p?.alternates||[]].filter(Boolean).map(u=>repairs.get(u)?.status==='replaced'?repairs.get(u).replacement:u))];}
 function day(){
  const raw=getRotationDay();if(!raw)return null;const p=BootlegClock.parts(now()),month=MONTHS.indexOf(currentMonth)+1,d=previewDate||p.day,y=p.year,key=`${y}:${month}:${d}`;
  if(cache&&cacheSchedule===schedule&&cacheKey===key)return cache;
  cache={...raw,channels:raw.channels.map(c=>{const plan=BootlegClock.plan({year:y,month,day:d,channel:c.name,items:c.playlist,pools,breaks});return {...c,playlist:plan.slots,plan};})};cacheSchedule=schedule;cacheKey=key;return cache;
 }
 function viewingTime(){if(!previewDate)return now();const p=BootlegClock.parts(now());return BootlegClock.wall(p.year,MONTHS.indexOf(currentMonth)+1,previewDate,p.hour)+p.minute*60000+p.second*1000;}
 function livePosition(){const c=getCurrentChannelData();return c?.plan?BootlegClock.locate(c.plan,viewingTime()):null;}
 function item(){return selected||getCurrentChannelData()?.playlist?.[currentIndex]||null;}
 const time=ms=>new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/London',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(ms));
 function seek(){if(mode==='live'){const pos=livePosition();let offset=pos?.offset||0;if(pos?.item.loop&&Number.isFinite(player.duration)&&player.duration>0)offset%=player.duration;return offset;}return player.currentTime||pendingSeek;}
 function presentation(message){holding=true;player.pause();cancelRecovery();$('broadcast-card').hidden=false;$('broadcast-card-channel').textContent=getCurrentChannelData()?.name||'BOOTLEG BROADCAST';$('broadcast-card-title').textContent=message||item()?.title||'Stay tuned';$('broadcast-card-next').textContent=mode==='live'&&item()?.end?'Scheduled broadcast resumes at '+time(item().end)+' UK':'Returning to scheduled broadcast…';hideStatus();updateRemote();}
 function clearCard(){holding=false;$('broadcast-card').hidden=true;}
 function load(){
  const c=getCurrentChannelData();if(!c?.playlist?.length)return;selected=null;mode='live';const pos=livePosition();if(!pos)return;currentIndex=pos.index;slotKey=pos.item.slot_id;play();
 }
 function play(){
  const p=item();if(!p)return;sourceRetry=0;stalledAttempts=0;clearCard();updateChannelOverlay();
  const urls=sources(p),index=urls.findIndex(u=>!blocked(u));
  if(p.presentation||index<0){resetPlayer();presentation(index<0&&!p.presentation?'Signal unavailable · source flagged for review':p.title);}
  else loadItemSource(p,index,mode==='live'?seek():0);
  renderScheduleOverlay();updateRemote();if($('guidePanel').open)renderGuideList();
 }
 async function returnLive(){
  selected=null;mode='live';clearCard();const month=MONTHS[BootlegClock.parts(now()).month-1];
  if(previewDate||currentMonth!==month)await selectSchedule(month,null);else{resetPlayer();load();}
  if(!poweredOn)togglePower();else{safePlay();armSourceTimeout();}showChannelOverlay();
 }
 function choose(channel,index){const p=getTodaySchedule()?.channels?.[channel]?.playlist?.[index];if(!p||NON_PROGRAMME.has(p.type)||p.type==='Filler'||p.presentation)return;resetPlayer();currentChannel=channel;currentIndex=index;selected={...p};mode='ondemand';slotKey='ondemand:'+p.url;play();if(!poweredOn)togglePower();showChannelOverlay();closeGuide();}
 function chooseItem(p){if(p.broadcast_held||failed.has(p.url)){showStatus('SOURCE HELD FOR REVIEW',3000);return;}resetPlayer();const index=getTodaySchedule()?.channels?.findIndex(c=>c.name===p.channel);if(index>=0)currentChannel=index;selected={...p};mode='ondemand';slotKey='ondemand:'+p.url;play();if(!poweredOn)togglePower();showChannelOverlay();}
 function skip(direction){const c=getCurrentChannelData();if(!c)return;const next=nextProgrammeIndex(c.playlist,currentIndex,direction);if(next>=0)choose(currentChannel,next);}
 function restart(){const p=item();if(!p)return;resetPlayer();selected={...p};mode='ondemand';play();if(!poweredOn)togglePower();}
 function alternate(manual=false){const p=item(),urls=sources(p);let next=sourceIndex+1;while(next<urls.length&&blocked(urls[next]))next++;if(next>=urls.length){if(!manual)return false;next=urls.findIndex(u=>!blocked(u));if(next<0)return false;}sourceRetry=0;stalledAttempts=0;clearCard();loadItemSource(p,next,seek());return true;}
 function retry(){const p=item();if(!p)return;const urls=sources(p),index=Math.min(sourceIndex,Math.max(0,urls.length-1));failed.delete(urls[index]);clearCard();sourceRetry=0;stalledAttempts=0;loadItemSource(p,index,seek());}
 function recover(reason){if(!poweredOn||holding)return;cancelRecovery();const p=item();if(!p)return;
  if(sourceRetry<1){sourceRetry++;const gen=tuningGeneration;showStatus('RE-TUNING SIGNAL…',0);const offset=seek();recoveryTimer=setTimeout(()=>{if(gen===tuningGeneration&&poweredOn)loadItemSource(p,sourceIndex,mode==='live'?seek():offset);},700);return;}
  report(sources(p)[sourceIndex],reason+(player.error?.code?' · media code '+player.error.code:''));
  if(alternate())return;resetPlayer();presentation('Signal unavailable · source flagged for review');
  if(mode!=='live'){const gen=tuningGeneration;recoveryTimer=setTimeout(()=>{if(gen===tuningGeneration&&poweredOn)returnLive();},1800);}
 }
 function ended(){if(!poweredOn)return;if(mode!=='live'){returnLive();return;}const p=item();if(p?.loop){loadItemSource(p,sourceIndex,seek());return;}if(viewingTime()>=p.end-1000){sync(true);return;}presentation(p.type==='Ident'?'Stay tuned · '+getCurrentChannelData()?.name:'Back shortly · '+getCurrentChannelData()?.name);}
 function pause(){if(!poweredOn){togglePower();return;}if(holding){returnLive();return;}if(player.paused){safePlay();armSourceTimeout();}else{selected={...item()};mode='timeshift';player.pause();cancelRecovery();showStatus('PAUSED · RETURN TO BROADCAST TO REJOIN',0);}updateRemote();}
 function sync(force=false){if(!schedule||syncing)return;const p=BootlegClock.parts(now());
  if(mode==='live'&&!previewDate&&MONTHS[p.month-1]!==currentMonth){syncing=true;selectSchedule(MONTHS[p.month-1],null).finally(()=>syncing=false);return;}
  const pos=livePosition();if(!pos)return;
  if(mode==='live'&&(pos.item.slot_id!==slotKey||force)){resetPlayer();load();}
  else if(mode==='live'&&poweredOn&&!holding&&!player.paused&&player.readyState>=2&&performance.now()-lastDriftCheck>12000){lastDriftCheck=performance.now();const target=seek();if(target>=player.duration-0.3&&!pos.item.loop)presentation('Back shortly · '+getCurrentChannelData()?.name);else if(Math.abs(player.currentTime-target)>4&&Number.isFinite(player.duration))try{player.currentTime=Math.min(target,player.duration-0.1);}catch{}}
  const next=$('broadcast-card-next');if(holding&&pos.item.end)next.textContent='Scheduled broadcast resumes at '+time(pos.item.end)+' UK';
 }
 let lastDriftCheck=0;
 function remote(){const c=getCurrentChannelData(),p=item();$('broadcast-button').textContent=mode==='live'&&!previewDate?'LIVE · '+(clockSynced?'UK':'DEVICE CLOCK'):'RETURN TO BROADCAST';$('broadcast-button').setAttribute('aria-pressed',String(mode==='live'&&!previewDate));$('broadcast-mode').textContent=previewDate?'DATE PREVIEW':mode==='live'?(clockSynced?'SHARED UK BROADCAST':'BROADCAST · DEVICE CLOCK'):'WATCHING A SELECTION · RETURNS TO BROADCAST';document.body.dataset.season=currentMonth==='october'?'october':currentMonth==='december'?'december':'regular';}
 function mini(){const c=getCurrentChannelData();if(!c)return;const pos=livePosition(),start=pos?.index||0;const upcoming=c.playlist.map((p,n)=>({p,n})).filter(({p,n})=>n>=start&&!NON_PROGRAMME.has(p.type)).slice(0,8);$('scheduleOverlay').innerHTML=`<div class="mini-guide-header"><h3>${escapeHtml(c.name)}</h3><button type="button" onclick="toggleScheduleOverlay()" aria-label="Close mini guide">×</button></div><div class="schedule-status">${escapeHtml(previewDate?'DATE PREVIEW':'UK BROADCAST')} · ${escapeHtml(pos?.item.block||'')}</div>${upcoming.map(({p,n})=>`<button type="button" class="schedule-item ${n===pos?.index?'now-playing':''}" onclick="chooseProgramme(${currentChannel},${n})"><span class="schedule-marker">${time(p.start)}</span><span class="schedule-title">${escapeHtml(p.title)}${n===pos?.index?' · ON AIR':''}</span></button>`).join('')}<button type="button" class="guide-expand" onclick="openGuide()">FULL DAY GUIDE</button>`;}
 function guide(){const c=getTodaySchedule()?.channels?.[Number($('guide-channel').value)],query=$('guide-search').value.trim().toLowerCase();if(!c){$('guide-list').textContent='No schedule loaded.';return;}const pos=BootlegClock.locate(c.plan,viewingTime());const list=c.playlist.map((p,n)=>({p,n})).filter(({p})=>!NON_PROGRAMME.has(p.type)&&(!query||`${p.title} ${p.show} ${p.block}`.toLowerCase().includes(query)));$('guide-count').textContent=`${list.length} slots · ${c.plan.holiday_labels?.length?c.plan.holiday_labels.join(' / ')+' · ':''}all times UK`;$('guide-list').innerHTML=list.length?list.map(({p,n})=>{const src=sourcePage(p.url);return `<article class="guide-programme ${n===pos?.index?'selected':''}"><button type="button" class="programme-play" onclick="chooseProgramme(${Number($('guide-channel').value)},${n})" ${p.type==='Filler'||p.presentation?'disabled':''}><span class="programme-type">${time(p.start)}–${time(p.end)} UK · ${escapeHtml(p.block)}${n===pos?.index?' · ON AIR':''}</span><strong>${escapeHtml(p.title)}</strong><span>${escapeHtml(p.show||'')}</span></button>${src?`<a href="${escapeHtml(src)}" target="_blank" rel="noopener noreferrer">SOURCE</a>`:''}</article>`;}).join(''):'<p class="guide-empty">No matching scheduled slots. Search the source library for more.</p>';}
 async function boot(){const data=await Promise.all([fetchJson('broadcast-pools.json?v=0341'),fetchJson('seasonal-breaks.json'),clock(),health()]);pools=data[0].channels;breaks=data[1];currentMonth=MONTHS[BootlegClock.parts(now()).month-1];setInterval(sync,1000);setInterval(clock,300000);setInterval(health,60000);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'){clock().then(()=>sync());health();}});}
 async function deepLink(){const url=new URLSearchParams(location.search).get('watch');if(!url)return;try{const data=await fetchJson('source-library.json?v=0341');const p=data.programmes.find(p=>p.url===url);if(p){chooseItem(p);history.replaceState(null,'',location.pathname);}}catch{showStatus('SELECTED PROGRAMME UNAVAILABLE',3000);}}
 return {boot,now,day,item,sources,seek,load,play,returnLive,choose,skip,restart,alternate,retry,recover,ended,pause,sync,remote,mini,guide,deepLink,mode:()=>mode,holding:()=>holding,presentation};
})();
