/**
 * Audit the supplied Internet Archive collections without treating ZIP bundles
 * or a collection description as a playable movie. Node 20, no dependencies.
 * Writes review candidates ONLY. Playback and rights must be checked separately.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const COLLECTIONS=[
 {identifier:'laika-studios-films',label:'Laika Studios films',suggestedChannels:['Cartoons Cartoons','Dizzy']},
 {identifier:'media-preservation-chamber_626',label:'Media Preservation Chamber',suggestedChannels:['Cartoons Cartoons','Dizzy','GirlyPop','AAA','90s Toons']},
 {identifier:'halloween-media-preservation-chamber_626',label:'Halloween Media Preservation Chamber',suggestedChannels:['Cartoons Cartoons','AAA','Dickleodeon','Dizzy']},
 {identifier:'christmas-media-preservation-chamber_626',label:'Christmas Media Preservation Chamber',suggestedChannels:['Dizzy','Cartoons Cartoons','GirlyPop','90s Toons']}
];
const USER='m3dia_l0aner_626';
const BASE='https://archive.org';
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function json(url){
 let err;
 for(let attempt=0;attempt<3;attempt++){
  try{
   const response=await fetch(url,{headers:{'User-Agent':'BootlegBroadcastArchiveReview/1.0 (metadata-only)'},signal:AbortSignal.timeout(45000)});
   if(!response.ok)throw new Error('HTTP '+response.status+' '+url);
   return await response.json();
  }catch(e){err=e;if(attempt<2)await sleep((attempt+1)*1200);}
 }
 throw err;
}
function direct(id,name){return BASE+'/download/'+encodeURIComponent(id)+'/'+name.split('/').map(encodeURIComponent).join('/');}
function classify(name,collection){
 const v=(name+' '+collection).toLowerCase();
 if(/coraline|paranorman|boxtrolls|kubo and the two strings|missing link|laika/.test(v))
  return {channels:['Cartoons Cartoons','Dizzy'],category:'animated-family-film'};
 if(/christmas|xmas|santa|snowman|rudolph|grinch|noel/.test(v))
  return {channels:['Dizzy','Cartoons Cartoons','GirlyPop'],category:'christmas-review'};
 if(/halloween|spooky|ghost|monster|horror|pumpkin/.test(v))
  return {channels:['Cartoons Cartoons','AAA'],category:'halloween-review'};
 if(/anime|japanese/.test(v))
  return {channels:['Japanime'],category:'anime-review'};
 return {channels:[],category:'requires-manual-classification'};
}
async function audit(item){
 const data=await json(BASE+'/metadata/'+encodeURIComponent(item.identifier));
 const metadata=data.metadata||{};
 const files=(Array.isArray(data.files)?data.files:[]).filter(f=>f&&typeof f.name==='string');
 const movieExtensions=/\.(mp4|m4v|webm|mkv|mov|avi)$/i;
 const bundles=/\.(zip|7z|rar|tar|iso)$/i;
 const candidates=[];
 for(const f of files){
  if(!movieExtensions.test(f.name)&&!bundles.test(f.name))continue;
  const kind=bundles.test(f.name)?'bundle-needs-inspection':/\.ia\.mp4$/i.test(f.name)?'archive-generated-mp4':'video-candidate';
  const route=classify(f.name,metadata.title||item.label);
  candidates.push({
   filename:f.name,kind,format:f.format||null,source:f.source||null,
   size_bytes:Number(f.size)||null,duration_seconds:Number(f.length)||null,
   url:direct(item.identifier,f.name),suggested_channels:route.channels,
   category:route.category,
   review_status:'unverified-file-metadata',
   notes:kind==='bundle-needs-inspection'?'Check internal titles; do not treat bundle as an MP4':null
  });
 }
 return {
  identifier:item.identifier,
  details_url:BASE+'/details/'+encodeURIComponent(item.identifier),
  label:item.label,title:metadata.title||null,creator:metadata.creator||null,
  mediatype:metadata.mediatype||null,files_listed:files.length,
  candidates_total:candidates.length,
  videos:candidates.filter(f=>f.kind!=='bundle-needs-inspection').length,
  bundles:candidates.filter(f=>f.kind==='bundle-needs-inspection').length,
  suggested_channels:item.suggestedChannels,
  candidates
 };
}
async function uploaderSearch(){
 const queries=['uploader:'+USER,'creator:'+USER];
 const found=new Map(),queriesRun=[];
 for(const query of queries){
  try{
   const params=new URLSearchParams({q:query,rows:'100',page:'1',output:'json'});
   for(const f of ['identifier','title','mediatype','date'])params.append('fl[]',f);
   const url=BASE+'/advancedsearch.php?'+params.toString();
   const answer=await json(url);
   const docs=answer.response?.docs||[];
   queriesRun.push({query,total:answer.response?.numFound||0});
   for(const doc of docs)if(doc.identifier)found.set(doc.identifier,{
    identifier:doc.identifier,title:doc.title||null,mediatype:doc.mediatype||null,
    details_url:BASE+'/details/'+encodeURIComponent(doc.identifier)
   });
  }catch(e){queriesRun.push({query,error:String(e)});}
 }
 return {profile_url:BASE+'/details/@'+USER+'/uploads',queries:queriesRun,items:[...found.values()]};
}
async function main(){
 const results=[],errors=[];
 for(const entry of COLLECTIONS){
  try{results.push(await audit(entry));}
  catch(e){errors.push({identifier:entry.identifier,error:String(e)});}
 }
 const uploader=await uploaderSearch();
 const report={
  generated_at:new Date().toISOString(),scope:'Metadata inventory only; no streaming or rights verification',
  collection_count:results.length,collections:results,uploader,errors
 };
 fs.writeFileSync(path.join(ROOT,'archive-candidate-review.json'),JSON.stringify(report,null,2)+'\n');
 const lines=['# Internet Archive additions — source inventory','',
 'Candidate sources only. Do not broadcast until the individual files, lengths, codec/audio and rights have been checked.','',
 'Uploader: '+uploader.profile_url,'',
 ...uploader.queries.map(q=>'- Search '+q.query+': '+(q.total??q.error)), '',
 ...results.flatMap(c=>[
  '## '+c.label,'',
  'Collection: '+c.details_url,'',
  'Title: '+(c.title||'Unknown')+' · Files: '+c.files_listed+' · Video candidates: '+c.videos+' · Bundles: '+c.bundles,'',
  ...c.candidates.slice(0,110).map(f=>'- ['+f.filename+']('+f.url+') — '+f.kind+(f.duration_seconds?' · '+Math.round(f.duration_seconds/60)+' min':'')+(f.suggested_channels.length?' · '+f.suggested_channels.join(', '):'')),
  ...(c.candidates.length>110?['- Additional files are in archive-candidate-review.json.']:[]),''
 ]),
 '## Other uploader items','','These need their own file-level inspection:',
 ...uploader.items.slice(0,100).map(i=>'- ['+(i.title||i.identifier)+']('+i.details_url+')'),
 '',...(errors.length?['## Errors','',...errors.map(e=>'- '+e.identifier+': '+e.error)]:[])
 ];
 fs.writeFileSync(path.join(ROOT,'ARCHIVE-ADDITIONS-REVIEW.md'),lines.join('\n')+'\n');
 console.log(JSON.stringify({collections:results.map(c=>({identifier:c.identifier,videos:c.videos,bundles:c.bundles,files:c.files_listed})),uploader_items:uploader.items.length,errors},null,2));
 if(!results.length)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
