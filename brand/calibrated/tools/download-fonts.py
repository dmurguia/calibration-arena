"""Download original OFL fonts and upstream webfonts; no account required."""
import hashlib, json, re, urllib.request, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    'archivoblack': ['ArchivoBlack-Regular.ttf'],
    'ibmplexsans': ['IBMPlexSans[wdth,wght].ttf'],
    'ibmplexmono': ['IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf'],
}
WEB = [
    ('Archivo+Black', 'ArchivoBlack-Regular'),
    ('IBM+Plex+Sans:wght@400;500;600', 'IBMPlexSans'),
    ('IBM+Plex+Mono:wght@400;500', 'IBMPlexMono'),
]
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
    return urllib.request.urlopen(req,timeout=45).read()
records=[]
for family,names in FAMILIES.items():
    folder=ROOT/'fonts'/family;folder.mkdir(parents=True,exist_ok=True)
    for name in names+['OFL.txt','METADATA.pb']:
        url='https://raw.githubusercontent.com/google/fonts/main/ofl/'+family+'/'+urllib.parse.quote(name)
        data=get(url);out=folder/name;out.write_bytes(data)
        records.append({'file':str(out.relative_to(ROOT)),'source':url,'sha256':hashlib.sha256(data).hexdigest(),'license':'SIL Open Font License 1.1'})
web=ROOT/'fonts'/'web';web.mkdir(parents=True,exist_ok=True)
css=[]
for query,name in WEB:
    url='https://fonts.googleapis.com/css2?family='+query+'&display=swap'
    text=get(url).decode();(web/(name+'-upstream.css')).write_text(text)
    blocks=re.findall(r'/\* latin \*/\s*(@font-face\s*\{.*?\})',text,re.S)
    if not blocks: blocks=re.findall(r'(@font-face\s*\{.*?\})',text,re.S)
    for block in blocks:
        weight=re.search(r'font-weight:\s*([^;]+);',block).group(1)
        source=re.search(r'src:\s*url\(([^)]+)\)',block).group(1)
        data=get(source);ext='.woff2' if data[:4]==b'wOF2' else '.ttf';filename=name+'-'+weight.replace(' ','-')+ext;out=web/filename;out.write_bytes(data)
        records.append({'file':str(out.relative_to(ROOT)),'source':source,'css_source':url,'sha256':hashlib.sha256(data).hexdigest(),'license':'SIL Open Font License 1.1','coverage':'Latin subset; desktop TTF files carry broader coverage'})
        css.append(re.sub(r'src:\s*url\([^)]+\)',"src: url('./web/"+filename+"')",block))
(ROOT/'fonts'/'fonts.css').write_text('/* Upstream Latin webfonts. Keep accompanying OFL notices. */\n'+'\n'.join(css)+'\n')
(ROOT/'fonts'/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
print('Saved',len(records),'font/license/source files')
