// Exercise the actual app tuning functions, including rapid channel changes and mute.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const app=fs.readFileSync(path.join(__dirname,'..','app.js'),'utf8');
const functions=app.split('\n').filter(l=>/^function (?:stopChannelNoise|playChannelNoise|toggleMute)\(/.test(l)).join('\n');
const timers=new Map();let nextTimer=0,plays=0,pauses=0;
const context={player:{muted:false,volume:.7},poweredOn:true,sounds:{channel:{volume:1,currentTime:9,pause(){pauses++},play(){plays++;return Promise.resolve()}}},setTimeout:(f,ms)=>{timers.set(++nextTimer,{f,ms});return nextTimer},clearTimeout:id=>timers.delete(id),showStatus:()=>{},persistSettings:()=>{},updateRemote:()=>{}};
vm.createContext(context);vm.runInContext('let channelNoiseTimer;\n'+functions+'\nglobalThis.api={playChannelNoise,stopChannelNoise,toggleMute};',context);
context.api.playChannelNoise();assert.equal(plays,1);assert(Math.abs(context.sounds.channel.volume-.0315)<1e-6);assert.equal(context.sounds.channel.currentTime,0);assert.equal([...timers.values()][0].ms,140);
context.api.playChannelNoise();assert.equal(plays,2);assert.equal(timers.size,1,'Rapid retunes must replace the stop timer');
[...timers.values()][0].f();assert.equal(timers.size,0);assert(pauses>=3);
context.api.playChannelNoise();context.api.toggleMute();assert(context.player.muted);assert.equal(timers.size,0);context.api.playChannelNoise();assert.equal(plays,3);
context.player.muted=false;context.poweredOn=false;context.api.playChannelNoise();assert.equal(plays,3);
console.log(JSON.stringify({version:'0.36',status:'passed',checks:['Tuning volume follows player volume','Stop timer caps burst at 140 ms','Rapid changes leave one timer','Muting stops sound and blocks playback','Power-off blocks tuning sound']}));
