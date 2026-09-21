"""Build deterministic vectors, palette files and artwork metadata.
Existing image masters and prompts.json must be present.
Requires fonttools. Run from any directory with python3 tools/build-kit.py.
Raster derivatives are produced separately with export-assets.cjs (requires sharp).
"""
from pathlib import Path
import json, shutil, html, csv, hashlib
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = Path(__file__).resolve().parents[1]
for d in ['logos/svg','logos/png','images/masters','images/web','colors','motion','previews']:
    (ROOT/d).mkdir(parents=True,exist_ok=True)

COLORS = {
 'ink':('#464643','Charcoal','Primary text and the identity'),
 'paper':('#F4F1E9','Notebook paper','Main canvas; lightly warm off-white'),
 'graphite':('#656460','Graphite','Secondary text and pencil-like marks'),
 'steel':('#929698','Brushed steel','Material accent and non-text details'),
 'leather':('#70543E','Leather brown','Restrained warmth; a timeless watch strap'),
 'white':('#FAF9F6','Chalk white','Light reading surface')
}
def luminance(h):
    values=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in values]
    return sum(x*w for x,w in zip(v,(.2126,.7152,.0722)))
def contrast(a,b):
    x,y=sorted([luminance(a),luminance(b)])
    return (y+.05)/(x+.05)
palette={k:{'hex':v[0],'name':v[1],'role':v[2]} for k,v in COLORS.items()}
tokens={'brand':'Calibrated Co.','version':'3.0','colors':palette,'typography':{
 'identity':{'family':'Archivo Black','weight':400,'use':'Logo and rare emphatic moments only'},
 'display':{'family':'IBM Plex Sans','weight':400,'tracking':'0','lineHeight':1.15,'use':'Conservative headings and short notes'},
 'body':{'family':'IBM Plex Sans','weights':[400,500],'lineHeight':1.55},
 'technical':{'family':'IBM Plex Mono','weights':[400],'lineHeight':1.5}},
 'semantic':{'background':'paper','text':'ink','textSecondary':'graphite','action':'ink','actionText':'paper','focus':'graphite'}}
(ROOT/'colors/tokens.json').write_text(json.dumps(tokens,indent=2)+'\n')
css='/* Calibrated Co. v3 — sRGB screen colors */\n:root {\n'+''.join(f'  --cal-{k}: {v[0]};\n' for k,v in COLORS.items())+'''  --cal-font-identity: 'Archivo Black', sans-serif;\n  --cal-font-display: 'IBM Plex Sans', sans-serif;
  --cal-font-body: 'IBM Plex Sans', sans-serif;
  --cal-font-mono: 'IBM Plex Mono', monospace;
  --cal-font-editorial: 'IBM Plex Sans', sans-serif;
  --cal-background: var(--cal-paper);
  --cal-text: var(--cal-ink);
  --cal-text-secondary: var(--cal-graphite);
  --cal-action: var(--cal-ink);
  --cal-action-text: var(--cal-paper);
}
'''
(ROOT/'colors/tokens.css').write_text(css)
with (ROOT/'colors/palette.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['token','name','hex','red','green','blue','role'])
    for k,(h,n,r) in COLORS.items():w.writerow([k,n,h,*[int(h[i:i+2],16) for i in (1,3,5)],r])
pairs=[('ink','paper'),('graphite','paper'),('paper','ink'),('paper','leather'),('ink','white'),('graphite','white')]
rows=[{'foreground':a,'background':b,'ratio':round(contrast(COLORS[a][0],COLORS[b][0]),2),'WCAG_AA_normal_text':contrast(COLORS[a][0],COLORS[b][0])>=4.5} for a,b in pairs]
(ROOT/'colors/contrast.json').write_text(json.dumps(rows,indent=2)+'\n')

C='M180 48 C154 16 121 10 96 15 C51 22 20 57 13 102 C5 146 30 184 68 197 C110 214 153 194 179 164 L165 150 C142 176 111 188 81 177 C51 167 38 140 38 114 C37 76 64 39 99 31 C126 24 151 33 169 59 Z'
DASH='M151 106 L205 105 L205 122 L141 121 Z'
MARK=f'<path d="{C}"/><path d="{DASH}"/>'

def lettering(text,fontfile,tracking=0):
    f=TTFont(ROOT/fontfile);g=f.getGlyphSet();cmap=f.getBestCmap();metrics=f['hmtx'].metrics
    pen=SVGPathPen(g);bounds=BoundsPen(g);x=0
    for char in text:
        glyph=cmap[ord(char)]
        transform=(1,0,0,-1,x,0)
        g[glyph].draw(TransformPen(pen,transform));g[glyph].draw(TransformPen(bounds,transform))
        x+=metrics[glyph][0]+tracking
    x0,y0,x1,y1=bounds.bounds
    return pen.getCommands(),(x0,y0,x1-x0,y1-y0)

WORD,WB=lettering('CALIBRATED CO.','fonts/archivoblack/ArchivoBlack-Regular.ttf',-22)
TAG,TB=lettering('The art of better.','fonts/ibmplexsans/IBMPlexSans[wdth,wght].ttf',0)
def place(d,b,x,y,width):
    bx,by,bw,bh=b;s=width/bw
    return f'<g transform="translate({x:.3f} {y:.3f}) scale({s:.6f}) translate({-bx:.3f} {-by:.3f})"><path d="{d}"/></g>'
def svg(name,content,w,h,color,bg=None):
    background=f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(name)}"><title>{html.escape(name)}</title>{background}<g fill="{color}">{content}</g></svg>\n'
wordh=WB[3]/WB[2]*1200
shapes={
 'mark':(MARK,220,220),
 'wordmark':(place(WORD,WB,12,12,1200),1224,round(wordh+24,3)),
 'horizontal':(f'<g transform="translate(0 2) scale(.8)">{MARK}</g>'+place(WORD,WB,213,55,1040),1275,182),
 'stacked':(f'<g transform="translate(485 0)">{MARK}</g>'+place(WORD,WB,20,260,1150),1190,round(280+WB[3]/WB[2]*1150,3)),
 'signature':(f'<g transform="translate(485 0)">{MARK}</g>'+place(WORD,WB,20,260,1150)+place(TAG,TB,395,395,400),1190,510),
 'tagline':(place(TAG,TB,12,12,720),744,round(24+TB[3]/TB[2]*720,3))
}
for variant in ['ink','paper','graphite']:
    for name,(content,w,h) in shapes.items():
        (ROOT/f'logos/svg/calibrated-{name}-{variant}.svg').write_text(svg(f'Calibrated Co. {name}',content,w,h,COLORS[variant][0]))
for name,bg,fg in [('app-icon',COLORS['ink'][0],COLORS['paper'][0])]:
    (ROOT/f'logos/svg/calibrated-{name}.svg').write_text(svg('Calibrated Co.',f'<g transform="translate(36 36) scale(2)">{MARK}</g>',512,512,fg,bg))
(ROOT/'logos/svg/calibrated-favicon.svg').write_text(svg('Calibrated Co.',MARK,220,220,COLORS['ink'][0]))

# A vector-only overview for quick viewing and sharing.
sheet='<rect width="1600" height="1000" fill="#F4F1E9"/>'
sheet+='<rect x="72" y="70" width="264" height="264" fill="#464643"/>'
sheet+=f'<g fill="#F4F1E9" transform="translate(72 70) scale(1.2)">{MARK}</g>'
sheet+=f'<g fill="#464643">{place(WORD,WB,390,135,1130)}{place(TAG,TB,390,275,480)}</g>'
sheet+='<path d="M72 405H1528" stroke="#464643" stroke-width="2"/>'
for i,key in enumerate(['ink','graphite','steel','leather','paper','white']):
    x=72+i*246;h,n,r=COLORS[key]
    sheet+=f'<rect x="{x}" y="460" width="226" height="340" fill="{h}"/>'
    fg=COLORS['paper'][0] if i in [0,1,3] else COLORS['ink'][0]
    if key!='leather':
        sheet+=f'<g transform="translate({x+66} 570) scale(.43)" fill="{fg}">{MARK}</g>'
    label,lb=lettering(n.upper(),'fonts/ibmplexmono/IBMPlexMono-Medium.ttf')
    sheet+=f'<g fill="#464643">{place(label,lb,x,830,min(205,lb[2]*.017))}</g>'
    label,lb=lettering(h,'fonts/ibmplexmono/IBMPlexMono-Regular.ttf')
    sheet+=f'<g fill="#656460">{place(label,lb,x,865,105)}</g>'
(ROOT/'previews/identity-and-colors.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000">{sheet}</svg>')

jobs=json.loads((ROOT/'images/prompts.json').read_text())
descriptions={
 'open-sketch':('Open sketch','Loose graphite lines curl and overlap on warm paper.','Signature hero, motion starting frame; retain open edges and overshoots.'),
 'graphite-pressure':('Graphite pressure','Broad dark graphite strokes cross pale textured paper.','Editorial background; paper wordmark over the darkest area, verify contrast.'),
 'working-notation':('Working notation','Fine pencil loops, private shorthand and faint structured marks on off-white paper.','Human thinking and revision; leave annotations spacious and recognizably drawn.'),
 'instrument-steel':('Instrument steel','A close study of neutral brushed steel, a slotted screw and machined curves.','Precision and craft; silver stays a material, not a decorative color accent.'),
 'paper-and-cloth':('Paper and cloth','Off-white paper, charcoal book cloth and a narrow steel edge.','Quiet material background or editorial crop; no colored cover accents.')

}
manifest=[]
for job in jobs:
    name=job['name'];master=ROOT/f'images/masters/{name}.png'
    if not master.exists():raise FileNotFoundError(f'Restore original artwork master: {master}')
    title,alt,use=descriptions[name]
    manifest.append({'id':name,'title':title,'master':f'masters/{name}.png','web':f'web/{name}.webp','thumbnail':f'web/{name}-768.webp','alt':alt,'recommended_use':use,'origin':'AI-generated original illustration / material study','generator':'OpenAI built-in image generation','date':job['created'],'not_documentary_photography':True,'sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'prompt':job['prompt'],'prompt_note':job.get('prompt_note'),'rights_note':'See RIGHTS.md. No third-party stock image license is included or required for these generated originals; applicable service terms govern use. No exclusivity or trademark clearance is asserted.'})
(ROOT/'images/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Keep the portable prompt record free of machine-specific paths.
clean=[{k:v for k,v in row.items() if k!='source'} for row in jobs]
(ROOT/'images/prompts.json').write_text(json.dumps(clean,indent=2)+'\n')
print('Built neutral identity, notebook typography, contrast report and current artwork manifest.')
