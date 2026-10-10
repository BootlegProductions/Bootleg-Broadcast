"""Apply title evidence/aliases to legacy film entries without altering their source URLs."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];cat=json.loads((R/'source-library.json').read_text());count=0
for p in cat['programmes']:
 if p.get('type')!='Movie':continue
 title=p.get('source_title','');show=p.get('source_show','');new=None
 if 'Commentary' in title or 'commentary' in p.get('filename','').lower():p['broadcast_held']=True;p['notes']='Commentary version held; needs a standard film copy.'
 if 'Secret of the Omnitrix' in title:new='Ben 10: Secret of the Omnitrix'
 elif 'Big Picture Show' in title:new="Ed, Edd n Eddy’s Big Picture Show"
 elif 'Kikis Delivery' in show:new="Kiki’s Delivery Service"
 elif show=='My Neighbour Totoro':new='My Neighbour Totoro'
 elif 'Nausica' in title:new='Nausicaä of the Valley of the Wind'
 elif show=='Rango':new='Rango'
 elif show=='The Boy And The Heron':new='The Boy and the Heron'
 elif show=='Recess':new='Recess: '+title.replace('Recess ','').replace('Schools Out',"School’s Out")
 elif 'Aqua Teen Forever' in title:new='Aqua Teen Forever: Plantasm'
 elif 'Atlantis 1;' in title or 'Atlantis The Lost Empire' in title:new='Atlantis: The Lost Empire (2001)'
 elif 'Atlantis 2;' in title:new='Atlantis: Milo’s Return'
 elif title.startswith('Toy Story 01') or title=='Toy Story (1995)':new='Toy Story (1995)'
 elif title.startswith('Toy Story 02') or title=='Toy Story 2 (1999)':new='Toy Story 2 (1999)'
 elif title.startswith('Toy Story 03') or title=='Toy Story 3 (2010)':new='Toy Story 3 (2010)'
 elif 'Madagascar 2 Escape' in title or 'Madagascar Escape 2 Africa' in title:new='Madagascar: Escape 2 Africa (2008)'
 elif 'Home Alone 2' in title:new='Home Alone 2: Lost in New York (1992)'
 elif 'Pokémon The First Movie' in title:new='Pokemon Movie 01 Mewtwo Strikes Back'
 elif title.startswith('1) '):new=title[3:]
 elif re.match(r'^[2-7] Leprechaun',title):new=title[2:]
 if new:p['title_override']=new;count+=1
(R/'source-library.json').write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':')));print('Film title overrides:',count)
