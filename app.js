/* Bootleg Broadcast v0.28 — CRT television, seasonal rotation and source recovery. */
'use strict';
const $ = id => document.getElementById(id);
const player = $('player');
const remoteControl = $('remote-control');
const MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december'];
const SETTINGS_KEY = 'bootlegBroadcast.v028';
const NON_PROGRAMME = new Set(['Advert','AdBreak','Ident']);
const ukParts = () => BootlegClock.parts(Broadcast.now());
let settings = {};
try { settings = JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}; } catch {}
let schedule=null, advertPools={}, currentChannel=Number.isInteger(settings.currentChannel)?settings.currentChannel:0, currentIndex=0;
let channelMemory=settings.channelMemory || {}, poweredOn=false, started=false, previewDate=null;
let currentMonth=MONTHS[Number(ukParts().month)-1], scheduleGeneration=0, tuningGeneration=0;
let lastGoodScheduleState=null;
let statusTimer, recoveryTimer, sourceTimer, channelTimer, staticTimer, digitTimer;
let consecutiveFailures=0, sourceIndex=0, sourceRetry=0, stalledAttempts=0, pendingSeek=0, digits='', lastChannel=0;
let guideReturnFocus=null, helpReturnFocus=null, dayStamp=`${ukParts().year}-${ukParts().month}-${ukParts().day}`;
const sounds={on:new Audio('assets/tv on sfx/tv on sfx.mp3'),off:new Audio('assets/tv off sfx/tv off sfx.mp3'),channel:new Audio('assets/static sfx/channel switch static.mp3'),button:new Audio('assets/remote button sfx/remote button sfx.mp3')};
const logos={'90s Toons':'90s Cartoons Logo.png','Cartoons Cartoons':'Cartoons Cartoons Logo.png','AAA':'AAA Logo.png','Off-Licence TV':'Off Licence TV Logo.png','Japanime':'Japanime Logo.png','Star Spangled TV':'Star Spangled TV Logo.png','What':'What Logo.png','Dizzy':'Dizzy Logo.png','Dickleodeon':'Dickleodeon Logo.png','GirlyPop':'Girly Pop Logo.png'};
player.volume=Math.max(0,Math.min(1,Number.isFinite(settings.volume)?settings.volume:0.7));
player.muted=Boolean(settings.muted);
remoteControl.classList.toggle('active',settings.remoteOpen !== false);
function escapeHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function persistSettings(){try{localStorage.setItem(SETTINGS_KEY,JSON.stringify({currentChannel,channelMemory,volume:player.volume,muted:player.muted,remoteOpen:remoteControl.classList.contains('active')}));}catch{}}
function playSound(sound,volume=0.2){if(player.muted)return;sound.pause();sound.currentTime=0;sound.volume=volume;sound.play().catch(()=>{});}
function showStatus(message,duration=1600,className=''){clearTimeout(statusTimer);$('statusOverlay').textContent=message;$('statusOverlay').className=`visible ${className}`;if(duration>0)statusTimer=setTimeout(hideStatus,duration);}
function hideStatus(){clearTimeout(statusTimer);$('statusOverlay').className='';}
function flattenDays(data=schedule){return data?.weeks?data.weeks.flatMap(w=>w.week||[]):data?.week||[];}
function getRotationDay(){const days=flattenDays();if(!days.length)return null;const day=previewDate||Number(ukParts().day);if(schedule?.weeks)return days.find(d=>Number(d.date)===day)||days[(day-1)%days.length];const weekday=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/London',weekday:'long'}).format(new Date());return days.find(d=>d.day===weekday)||days[(day-1)%days.length];}
function getTodaySchedule(){return Broadcast.day()||getRotationDay();}
function getCurrentChannelData(){return getTodaySchedule()?.channels?.[currentChannel]||null;}
function getCurrentItem(){return Broadcast.item();}
function memoryKey(){return `${previewDate?'preview':'calendar'}:${currentMonth}:${getTodaySchedule()?.date||previewDate||ukParts().day}:${getCurrentChannelData()?.name||currentChannel}`;}
function setMemoryForCurrentItem(time=player.currentTime||0){const item=getCurrentItem();if(!item)return;channelMemory[memoryKey()]={episodeIndex:currentIndex,time,url:item.url};const keys=Object.keys(channelMemory);keys.slice(0,Math.max(0,keys.length-100)).forEach(k=>delete channelMemory[k]);persistSettings();}
function saveChannelState(){setMemoryForCurrentItem();}
function getItemSources(item){return Broadcast.sources(item);}
function updateChannelBug(name){const logo=logos[name];$('channelBug').style.display=poweredOn&&logo?'block':'none';if(logo)$('channelBug').src=`assets/channel logos/${logo}`;}
function updateRemote(){Broadcast.remote();const c=getCurrentChannelData(),i=getCurrentItem();$('remote-display').textContent=`${poweredOn?(player.paused?'PAUSED':'ON'):'STANDBY'} · CH ${String(currentChannel+1).padStart(2,'0')} · ${player.muted?'MUTE':Math.round(player.volume*100)+'%'}\n${c?.name||'Loading schedule…'}\n${i?.title||''}`;$('pause-button').textContent=poweredOn&&!player.paused?'PAUSE':'PLAY';$('mute-button').setAttribute('aria-pressed',String(player.muted));$('power-button').setAttribute('aria-pressed',String(poweredOn));$('remote-handle').setAttribute('aria-expanded',String(remoteControl.classList.contains('active')));$('season-label').textContent=`${currentMonth==='october'?'HALLOWEEN':currentMonth==='december'?'CHRISTMAS':currentMonth.toUpperCase()} · ${previewDate?'PREVIEW '+previewDate:'TODAY'}`;}
function updateChannelOverlay(){$('channelNumber').textContent='CH '+String(currentChannel+1).padStart(2,'0');$('channelNameOverlay').textContent=getCurrentChannelData()?.name||'';updateChannelBug(getCurrentChannelData()?.name);}
function showChannelOverlay(){clearTimeout(channelTimer);$('channelOverlay').style.opacity=1;channelTimer=setTimeout(()=>$('channelOverlay').style.opacity=0,2000);}
function showStatic(){clearTimeout(staticTimer);$('static').style.opacity=1;staticTimer=setTimeout(()=>$('static').style.opacity=0,280);}
function cancelRecovery(){clearTimeout(recoveryTimer);clearTimeout(sourceTimer);}
function resetPlayer(){++tuningGeneration;cancelRecovery();player.onloadedmetadata=null;player.pause();player.removeAttribute('src');player.load();}
function armSourceTimeout(delay=22000){clearTimeout(sourceTimer);if(!poweredOn)return;const generation=tuningGeneration;sourceTimer=setTimeout(()=>{if(generation===tuningGeneration&&poweredOn&&!player.paused)recoverSource('SIGNAL TIMED OUT');else if(generation===tuningGeneration&&poweredOn&&player.readyState<2)recoverSource('SIGNAL TIMED OUT');},delay);}
function safePlay(){if(!poweredOn||!player.getAttribute('src'))return;player.play().catch(err=>{if(err.name==='NotAllowedError')showStatus('PRESS PLAY TO START',0);else if(err.name==='NotSupportedError')recoverSource('SOURCE UNSUPPORTED');});}
function loadItemSource(item,index=0,seek=0){cancelRecovery();const sources=getItemSources(item);if(!sources.length)return false;sourceIndex=index;pendingSeek=seek;const generation=++tuningGeneration;player.onloadedmetadata=()=>{if(generation!==tuningGeneration)return;if(Broadcast.mode()==='live')pendingSeek=Broadcast.seek();if(pendingSeek>0&&Number.isFinite(player.duration)){if(pendingSeek>=player.duration&&!item.loop){Broadcast.presentation('Back shortly · '+getCurrentChannelData()?.name);return;}player.currentTime=Math.min(pendingSeek,Math.max(0,player.duration-0.1));}pendingSeek=0;if(poweredOn)safePlay();};player.src=sources[index];player.load();if(poweredOn){showStatus(index?'TRYING BACKUP SOURCE…':'TUNING…',0);armSourceTimeout();safePlay();}updateRemote();return true;}
function tryNextAlternateSource(manual=false){return Broadcast.alternate(manual);}
function recoverSource(reason){return Broadcast.recover(reason);}
function nextProgrammeIndex(items,from,direction=1){for(let step=1;step<=items.length;step++){const n=(from+direction*step+items.length*2)%items.length;if(items[n]?.url&&!NON_PROGRAMME.has(items[n].type)&&items[n].type!=='Filler'&&!items[n].presentation)return n;}return -1;}
function playCurrent(){return Broadcast.play();}
function loadChannel(){return Broadcast.load();}
function tuneChannel(index){const channels=getTodaySchedule()?.channels;if(!channels?.length)return;saveChannelState();lastChannel=currentChannel;currentChannel=((index%channels.length)+channels.length)%channels.length;consecutiveFailures=0;resetPlayer();if(poweredOn)playSound(sounds.channel,0.08);showStatic();loadChannel();showChannelOverlay();persistSettings();}
function nextChannel(){tuneChannel(currentChannel+1);}
function prevChannel(){tuneChannel(currentChannel-1);}
function skipProgramme(direction=1){return Broadcast.skip(direction);}
function restartProgramme(){return Broadcast.restart();}
function togglePower(){if(!schedule){showStatus('LOADING SCHEDULE…',1800);return;}poweredOn=!poweredOn;started=started||poweredOn;document.body.classList.toggle('tv-powered-on',poweredOn);$('power').hidden=poweredOn;cancelRecovery();if(poweredOn){playSound(sounds.on);if(Broadcast.mode()==='live')Broadcast.sync(true);if(!player.getAttribute('src')&&!Broadcast.holding())loadChannel();safePlay();armSourceTimeout();showChannelOverlay();}else{saveChannelState();player.pause();hideStatus();$('channelOverlay').style.opacity=0;playSound(sounds.off);}updateChannelBug(getCurrentChannelData()?.name);updateRemote();}
function togglePause(){return Broadcast.pause();}
function toggleMute(){player.muted=!player.muted;showStatus(player.muted?'MUTED':`VOLUME ${Math.round(player.volume*100)}`);persistSettings();updateRemote();}
function changeVolume(delta){player.volume=Math.max(0,Math.min(1,player.volume+delta));if(delta>0)player.muted=false;showStatus(`VOLUME ${Math.round(player.volume*100)}`);persistSettings();updateRemote();}
function volumeUp(){changeVolume(0.1);}
function volumeDown(){changeVolume(-0.1);}
function toggleVideoFullscreen(){if(document.fullscreenElement){document.exitFullscreen?.().catch(()=>{});return;}if(player.requestFullscreen)player.requestFullscreen().catch(()=>showStatus('FULLSCREEN UNAVAILABLE'));else if(player.webkitEnterFullscreen)player.webkitEnterFullscreen();}
function toggleBigPicture(){if(document.fullscreenElement)document.exitFullscreen?.().catch(()=>{});else document.documentElement.requestFullscreen?.().catch(()=>showStatus('FULLSCREEN UNAVAILABLE'));}
function chooseAdverts(){return [];}
function expandTodayAdBreaks(){}
async function fetchJson(path){const response=await fetch(path);if(!response.ok)throw Error(`Schedule unavailable (${response.status})`);return response.json();}
async function selectSchedule(month,day=null){const generation=++scheduleGeneration;const previous=schedule?{schedule,currentMonth,previewDate,currentChannel}:lastGoodScheduleState;if(schedule)lastGoodScheduleState=previous;saveChannelState();resetPlayer();schedule=null;showStatus('LOADING SCHEDULE…',0);try{const data=await fetchJson(`schedules/${month}.json`);if(generation!==scheduleGeneration)return;schedule=data;currentMonth=month;previewDate=day;lastGoodScheduleState={schedule,currentMonth,previewDate,currentChannel};expandTodayAdBreaks();currentChannel=Math.min(currentChannel,Math.max(0,(getTodaySchedule()?.channels?.length||1)-1));consecutiveFailures=0;loadChannel();if(!poweredOn)hideStatus();syncGuideControls();updateRemote();}catch(e){if(generation!==scheduleGeneration)return;schedule=previous?.schedule||null;currentMonth=previous?.currentMonth||currentMonth;previewDate=previous?.previewDate||null;currentChannel=previous?.currentChannel||0;if(schedule)loadChannel();showStatus('SCHEDULE UNAVAILABLE · TRY AGAIN',0,'error');syncGuideControls();updateRemote();}}
function renderScheduleOverlay(){return Broadcast.mini();}
function toggleScheduleOverlay(){$('scheduleOverlay').classList.toggle('active');renderScheduleOverlay();}
function chooseProgramme(channel,index){return Broadcast.choose(channel,index);}
function openGuide(){guideReturnFocus=document.activeElement;syncGuideControls();renderGuideList();if(!$('guidePanel').open)$('guidePanel').showModal();$('guide-channel').focus();}
function closeGuide(){$('guidePanel').close();guideReturnFocus?.focus();}
function syncGuideControls(){const month=$('guide-month');month.value=currentMonth;const days=flattenDays();$('guide-day').innerHTML=days.map((d,n)=>`<option value="${d.date||n+1}">${d.date||n+1} ${escapeHtml(d.day||'')}</option>`).join('');$('guide-day').value=String(getTodaySchedule()?.date||previewDate||Number(ukParts().day));const channels=getTodaySchedule()?.channels||[];$('guide-channel').innerHTML=channels.map((c,n)=>`<option value="${n}">${String(n+1).padStart(2,'0')} · ${escapeHtml(c.name)}</option>`).join('');$('guide-channel').value=String(currentChannel);$('guide-notice').textContent=`${currentMonth==='october'?'Halloween rotation':currentMonth==='december'?'Christmas rotation':'Monthly rotation'} · ${previewDate?'Previewing '+currentMonth+' '+previewDate:'Today in the UK'}. Shared broadcast slots use UK time. Choose a programme to watch from the start; it returns to the broadcast afterwards.`;}
function sourcePage(url){try{const u=new URL(url,location.href);if(u.hostname==='archive.org'&&u.pathname.startsWith('/download/'))return 'https://archive.org/details/'+encodeURIComponent(u.pathname.split('/')[2]);return null;}catch{return null;}}
function renderGuideList(){return Broadcast.guide();}
function toggleHelp(force){const open=typeof force==='boolean'?force:!$('helpOverlay').classList.contains('active');if(open){helpReturnFocus=document.activeElement;$('helpOverlay').classList.add('active');$('helpClose').focus();}else{$('helpOverlay').classList.remove('active');helpReturnFocus?.focus();}}
function toggleRemote(){remoteControl.classList.toggle('active');persistSettings();updateRemote();}
function enterDigit(digit){digits+=String(digit);showStatus('CHANNEL '+digits,1500);clearTimeout(digitTimer);if(digits.length>=2)commitDigits();else digitTimer=setTimeout(commitDigits,850);}
function commitDigits(){const n=Number(digits);digits='';clearTimeout(digitTimer);if(n>=1&&n<=(getTodaySchedule()?.channels?.length||0))tuneChannel(n-1);else showStatus('CHANNEL NOT FOUND',1500);}
function flashRemoteIR(){$('remote-ir').classList.add('flash');setTimeout(()=>$('remote-ir').classList.remove('flash'),120);}
$('power').addEventListener('click',togglePower);
$('remote-handle').addEventListener('click',toggleRemote);
remoteControl.addEventListener('click',e=>{if(e.target.closest('.remote-btn')){playSound(sounds.button,0.12);flashRemoteIR();}});
$('helpClose').addEventListener('click',()=>toggleHelp(false));
$('helpOverlay').addEventListener('click',e=>{if(e.target===$('helpOverlay'))toggleHelp(false);});
$('guide-close').addEventListener('click',closeGuide);
$('guidePanel').addEventListener('cancel',e=>{e.preventDefault();closeGuide();});
$('guidePanel').addEventListener('click',e=>{if(e.target===$('guidePanel')){const r=$('guidePanel').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeGuide();}});
$('guide-month').addEventListener('change',async e=>{await selectSchedule(e.target.value,1);renderGuideList();});
$('guide-day').addEventListener('change',async e=>{await selectSchedule(currentMonth,Number(e.target.value));renderGuideList();});
$('guide-channel').addEventListener('change',renderGuideList);
$('guide-search').addEventListener('input',renderGuideList);
$('guide-today').addEventListener('click',async()=>{await selectSchedule(MONTHS[Number(ukParts().month)-1],null);renderGuideList();});
$('source-button').addEventListener('click',()=>{if(!tryNextAlternateSource(true)){Broadcast.retry();showStatus('RETRYING CURRENT SOURCE…',1800);}});
player.addEventListener('ended',()=>Broadcast.ended());
player.addEventListener('error',()=>{if(player.getAttribute('src')&&!Broadcast.holding())recoverSource('PROGRAMME UNAVAILABLE');});
player.addEventListener('playing',()=>{cancelRecovery();consecutiveFailures=0;sourceRetry=0;stalledAttempts=0;hideStatus();updateRemote();});
player.addEventListener('pause',updateRemote);
player.addEventListener('waiting',()=>{if(poweredOn&&!Broadcast.holding()){showStatus('BUFFERING…',0);armSourceTimeout(25000);}});
player.addEventListener('stalled',()=>{if(poweredOn&&!Broadcast.holding())armSourceTimeout(18000);});
player.addEventListener('timeupdate',()=>{if(poweredOn&&!player.paused&&player.readyState>=3){clearTimeout(sourceTimer);}});
document.addEventListener('keydown',e=>{const tag=document.activeElement?.tagName;if(['INPUT','TEXTAREA','SELECT'].includes(tag)||e.ctrlKey||e.metaKey||e.altKey)return;if($('guidePanel').open)return;if($('helpOverlay').classList.contains('active')){if(e.key==='Escape')toggleHelp(false);else if(e.key==='Tab'){e.preventDefault();$('helpClose').focus();}return;}const key=e.key.toLowerCase();const actions={'arrowright':nextChannel,'arrowleft':prevChannel,'arrowup':volumeUp,'arrowdown':volumeDown,'m':toggleMute,'s':toggleScheduleOverlay,'g':openGuide,'f':toggleVideoFullscreen,'b':toggleBigPicture,'r':toggleRemote,'p':togglePower,' ':togglePause,'n':()=>skipProgramme(1),'a':()=> $('source-button').click(),'escape':()=>{$('scheduleOverlay').classList.remove('active');},'enter':commitDigits};if(/^\d$/.test(key)){e.preventDefault();enterDigit(key);}else if(actions[key]){if(key===' '&&tag==='BUTTON')return;e.preventDefault();if(!e.repeat||key.startsWith('arrow'))actions[key]();}});
// Swipes retain the physical-TV feel on phones; buttons remain keyboard operable.
let touchStart=null;
$('screen').addEventListener('touchstart',e=>{const t=e.changedTouches[0];touchStart={x:t.clientX,y:t.clientY,time:Date.now()};},{passive:true});
let lastTap=0;
$('screen').addEventListener('touchend',e=>{if(!touchStart)return;const t=e.changedTouches[0],dx=t.clientX-touchStart.x,dy=t.clientY-touchStart.y;if(Math.abs(dx)>55&&Math.abs(dx)>Math.abs(dy)*1.25){dx<0?nextChannel():prevChannel();lastTap=0;}else if(Math.abs(dx)<16&&Math.abs(dy)<16&&Date.now()-touchStart.time<450){if(Date.now()-lastTap<350){toggleVideoFullscreen();lastTap=0;}else lastTap=Date.now();}touchStart=null;},{passive:true});
let remoteY=null;
$('remote-handle').addEventListener('touchstart',e=>remoteY=e.changedTouches[0].clientY,{passive:true});
$('remote-handle').addEventListener('touchend',e=>{if(remoteY===null)return;const delta=e.changedTouches[0].clientY-remoteY;remoteY=null;if(Math.abs(delta)>42){remoteControl.classList.toggle('active',delta<0);persistSettings();updateRemote();}},{passive:true});
$('broadcast-button').addEventListener('click',()=>Broadcast.returnLive());
window.addEventListener('pagehide',saveChannelState);
// Reload the correct calendar schedule after midnight or waking a sleeping tab.
async function checkCalendar(){const p=ukParts(),stamp=`${p.year}-${p.month}-${p.day}`;if(stamp===dayStamp)return;dayStamp=stamp;if(!previewDate&&Broadcast.mode()==='live')await selectSchedule(MONTHS[Number(p.month)-1],null);}
setInterval(checkCalendar,60000);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')checkCalendar();else saveChannelState();});
Broadcast.boot().then(()=>Promise.all([fetchJson('adverts.json').catch(()=>({channels:{}})),fetchJson(`schedules/${currentMonth}.json`).catch(()=>fetchJson('schedule.json'))])).then(([ads,data])=>{advertPools=ads.channels||{};schedule=data;expandTodayAdBreaks();currentChannel=Math.max(0,Math.min(currentChannel,(getTodaySchedule()?.channels?.length||1)-1));loadChannel();hideStatus();syncGuideControls();updateRemote();Broadcast.deepLink();}).catch(()=>{showStatus('SCHEDULE UNAVAILABLE · RELOAD PAGE',0,'error');updateRemote();});
