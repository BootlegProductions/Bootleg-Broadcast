/**
 * Build a channel-specific shortlist from exact Archive metadata filenames.
 * No unverified media is automatically aired.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const review=JSON.parse(fs.readFileSync(path.join(ROOT,'archive-candidate-review.json'),'utf8'));
const library=JSON.parse(fs.readFileSync(path.join(ROOT,'source-library.json'),'utf8'));
const picks=[["laika-studios-films","Coraline.mp4",["Cartoons Cartoons"],"Halloween film"],["laika-studios-films","Paranorman.mp4",["Cartoons Cartoons"],"Halloween film"],["laika-studios-films","The Boxtrolls.mp4",["Dizzy","Cartoons Cartoons"],"Family film"],["laika-studios-films","Kubo And The Two Strings.mp4",["Dizzy","Cartoons Cartoons"],"Family film"],["laika-studios-films","Missing Link.mp4",["Dizzy","Cartoons Cartoons"],"Family film"],["media-preservation-chamber_626","9.mp4",["AAA"],"Animated feature"],["media-preservation-chamber_626","A Goofy Movie.mp4",["Dizzy"],"Family film"],["media-preservation-chamber_626","An Extremely Goofy Movie.mp4",["Dizzy"],"Family film"],["media-preservation-chamber_626","Ed, Edd n Eddy's Big Picture Show.mp4",["Cartoons Cartoons"],"Animated feature"],["media-preservation-chamber_626","Codename Kids Next Door Operation Z.E.R.O.mp4",["Cartoons Cartoons"],"Animated feature"],["media-preservation-chamber_626","Dragon Ball Super; Broly (English Dub).mp4",["Japanime"],"Anime film"],["media-preservation-chamber_626","Dragon Ball Super; Super Hero (English Dub).mp4",["Japanime"],"Anime film"],["media-preservation-chamber_626","The Day The Earth Blew Up  A Looney Tunes Movie.mp4",["Cartoons Cartoons"],"Animated feature"],["media-preservation-chamber_626","A Boy Named Charlie Brown.mp4",["90s Toons","Cartoons Cartoons"],"Animation film"],["media-preservation-chamber_626","Animaniacs; Wakko's Wish.mp4",["90s Toons"],"Animated feature"],["halloween-media-preservation-chamber_626","Adventure Time; The Creeps.mp4",["Cartoons Cartoons"],"Halloween short"],["halloween-media-preservation-chamber_626","Camp Lazlo - Hallobeanies.mp4",["Cartoons Cartoons"],"Halloween short"],["halloween-media-preservation-chamber_626","Ed, Edd n Eddy’s Boo Haw Haw.mp4",["Cartoons Cartoons"],"Halloween special"],["halloween-media-preservation-chamber_626","Garfield's Halloween Adventure.mp4",["Cartoons Cartoons"],"Halloween special"],["halloween-media-preservation-chamber_626","Gravity Falls; Summerween.mp4",["Dizzy"],"Halloween special"],["halloween-media-preservation-chamber_626","Gravity Falls; Little Gift Shop Of Horrors.mp4",["Dizzy"],"Halloween special"],["halloween-media-preservation-chamber_626","Hey Arnold!; Arnold’s Halloween.mp4",["Dickleodeon"],"Halloween special"],["halloween-media-preservation-chamber_626","Invader Zim; Halloween Spectacular of Spooky Doom.mp4",["Dickleodeon"],"Halloween special"],["halloween-media-preservation-chamber_626","Regular Show; Terror Tales of the Park.mp4",["Cartoons Cartoons"],"Halloween special"],["halloween-media-preservation-chamber_626","Scary Godmother; Halloween Spooktacular.mp4",["Cartoons Cartoons"],"Halloween special"],["halloween-media-preservation-chamber_626","Scary Godmother; The Revenge of Jimmy.mp4",["Cartoons Cartoons"],"Halloween special"],["halloween-media-preservation-chamber_626","SpongeBob SquarePants; The Legend of Boo-kini Bottom.mp4",["Dickleodeon"],"Halloween special"],["halloween-media-preservation-chamber_626","Kim Possible; October 31st.mp4",["Dizzy"],"Halloween special"],["halloween-media-preservation-chamber_626","The Amazing World of Gumball; Halloween.mp4",["Cartoons Cartoons"],"Halloween short"],["christmas-media-preservation-chamber_626","A Chipmunk Christmas.mp4",["90s Toons"],"Christmas special"],["christmas-media-preservation-chamber_626","A Scooby-Doo Christmas.mp4",["Cartoons Cartoons"],"Christmas special"],["christmas-media-preservation-chamber_626","A Phineas and Ferb Family Christmas.mp4",["Dizzy"],"Christmas special"],["christmas-media-preservation-chamber_626","Arthur's Perfect Christmas.mp4",["GirlyPop"],"Christmas special"],["christmas-media-preservation-chamber_626","Bah, Humduck! - A Looney Tunes Christmas.mp4",["Cartoons Cartoons"],"Christmas special"],["christmas-media-preservation-chamber_626","Doctor Who; A Christmas Carol.mp4",["Off-Licence TV"],"Christmas special"],["christmas-media-preservation-chamber_626","Ed, Edd n Eddy’s; Jingle Jingle Jangle.mp4",["Cartoons Cartoons"],"Christmas special"],["christmas-media-preservation-chamber_626","Hey Arnold!; Arnold's Christmas.mp4",["Dickleodeon"],"Christmas special"],["christmas-media-preservation-chamber_626","Mickey's Once Upon A Christmas.mp4",["Dizzy"],"Christmas special"],["christmas-media-preservation-chamber_626","Moral Orel; The Best Christmas Ever.mp4",["AAA"],"Christmas special"],["christmas-media-preservation-chamber_626","Regular Show; The Christmas Special.mp4",["Cartoons Cartoons"],"Christmas special"],["christmas-media-preservation-chamber_626","Pokemon; Pikachu's Winter Vacation.mp4",["Japanime"],"Christmas special"],["christmas-media-preservation-chamber_626","Invader Zim; The Most Horrible X-Mas Ever.mp4",["Dickleodeon"],"Christmas special"]];
const knownURLs=new Set(library.programmes.map(p=>p.url));
const normalize=s=>String(s||'').toLowerCase().replace(/\.mp4$/,'').replace(/\.ia$/,'').replace(/[^a-z0-9]/g,'');
const existingNames=new Set(library.programmes.flatMap(p=>[p.title,p.show,p.filename].filter(Boolean).map(normalize)));
const entries=[],missing=[];
for(const [identifier,filename,channels,slot] of picks){
 const group=review.collections.find(c=>c.identifier===identifier);
 const file=group?.candidates.find(f=>f.filename===filename&&f.kind==='video-candidate');
 if(!file){missing.push({identifier,filename});continue;}
 const title=filename.replace(/\.mp4$/i,'').replace(/[;]+/g,' — ').replace(/\s+/g,' ').trim();
 entries.push({
  title,identifier,filename,url:file.url,
  source_page:group.details_url,channels,slot,
  duration_seconds:file.duration_seconds,
  duplicate_url_in_library:knownURLs.has(file.url),
  possible_existing_title:existingNames.has(normalize(title)),
  audio_video_verified:false,playback_verified:false,rights_verified:false,
  status:'candidate — metadata checked, playback pending'
 });
}
if(missing.length)throw Error('Listed files absent from scanned Archive metadata: '+JSON.stringify(missing));
const groups=Object.fromEntries([...new Set(entries.flatMap(e=>e.channels))].map(ch=>[ch,entries.filter(e=>e.channels.includes(ch)).map(e=>e.title)]));
const report={
 version:1,generated_at:new Date().toISOString(),
 note:'Metadata-only source candidates. Do not automatically schedule or play until source, audio and rights checks pass.',
 count:entries.length,duplicate_urls:entries.filter(e=>e.duplicate_url_in_library).length,
 possible_existing_titles:entries.filter(e=>e.possible_existing_title).length,
 by_channel:groups,entries
};
fs.writeFileSync(path.join(ROOT,'archive-curated-additions.json'),JSON.stringify(report,null,2)+'\n');
const lines=[
 '# Proposed Archive additions by channel','',
 'Only exact original MP4 filenames found in Archive metadata are listed. Not in the live schedule yet; playback, audio and usage rights still need checking.','',
 ...Object.entries(groups).flatMap(([ch,titles])=>['## '+ch,'',...titles.map(t=>'- '+t),'']),
 '## Duplicate checking','',
 'Candidate files: '+entries.length,
 'Exact URLs already in source library: '+report.duplicate_urls,
 'Possible matching titles in source library: '+report.possible_existing_titles,
 '',
 'Full file URLs and measured durations: archive-curated-additions.json'
];
fs.writeFileSync(path.join(ROOT,'ARCHIVE-CHANNEL-ADDITIONS.md'),lines.join('\n')+'\n');
console.log(JSON.stringify({candidate_count:entries.length,duplicate_urls:report.duplicate_urls,possible_existing_titles:report.possible_existing_titles,by_channel:Object.fromEntries(Object.entries(groups).map(([ch,v])=>[ch,v.length]))},null,2));
