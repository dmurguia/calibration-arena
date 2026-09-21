"""Render the six-page designer brief. Requires reportlab and pypdf."""
from pathlib import Path
import json,re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('Archivo',str(ROOT/'fonts/archivoblack/ArchivoBlack-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Plex',str(ROOT/'fonts/ibmplexsans/IBMPlexSans[wdth,wght].ttf')))
pdfmetrics.registerFont(TTFont('Mono',str(ROOT/'fonts/ibmplexmono/IBMPlexMono-Regular.ttf')))
pages=json.loads((ROOT/'tools/design-brief-content.json').read_text())
out=ROOT/'Calibrated-Co-Design-Brief.pdf'
c=canvas.Canvas(str(out),pagesize=(612,792))
c.setTitle('Calibrated Co. - Designer brief')
c.setAuthor('Calibrated Co.')
c.setSubject('The art of better: inspiration, visual identity and designer handoff')
paper=HexColor('#F4F1E9');ink=HexColor('#464643');green=HexColor('#464643');gray=HexColor('#656460')
def para(text,x,y,w,size=10.5,leading=14.5,font='Plex',color=ink):
    # Use simple hyphens consistently in the exported PDF.
    text=text.replace('—','-').replace('–','-').replace('→','>').replace('¼','1/4')
    p=Paragraph(escape(text),ParagraphStyle('p',fontName=font,fontSize=size,leading=leading,textColor=color))
    _,height=p.wrap(w,720);p.drawOn(c,x,y-height)
    return y-height
def height(text,w,size,leading,font='Plex'):
    p=Paragraph(escape(text),ParagraphStyle('m',fontName=font,fontSize=size,leading=leading))
    return p.wrap(w,720)[1]
layout=[]
for page in pages:
    c.setFillColor(paper);c.rect(0,0,612,792,fill=1,stroke=0)
    c.setFillColor(green);c.rect(0,789,612,3,fill=1,stroke=0)
    c.setFillColor(ink);c.setFont('Mono',8);c.drawString(48,747,'CALIBRATED CO. / DESIGNER BRIEF');c.drawRightString(564,747,page['number']+' / '+page['label'])
    title_size=32
    while pdfmetrics.stringWidth(page['title'],'Plex',title_size)>516:title_size-=1
    y=para(page['title'],48,718,516,title_size,title_size*1.08,'Plex')
    y=para(page['intro'],48,y-15,506,12,16,'Plex',green)-21
    bottom=190 if page.get('image') else 158 if page.get('palette') else 105 if page.get('note') else 70
    size=11
    while size>=9.75:
        total=sum(height(t,516,11.5,15,'Plex')+5+height(b,516,size,size*1.35)+14 for t,b in page['sections'])
        if y-total>=bottom:break
        size-=.25
    if size<9.75:raise RuntimeError('Page too dense: '+page['number'])
    for title,body in page['sections']:
        y=para(title,48,y,516,11.5,15,'Plex')-5
        y=para(body,48,y,516,size,size*1.35)-14
    layout.append({'page':page['number'],'body_size':size,'text_bottom':round(y,1),'reserved_bottom':bottom})
    if page.get('image'):
        c.setStrokeColor(gray);c.setLineWidth(.4);c.line(48,177,564,177)
        c.drawImage(str(ROOT/page['image']),48,63,width=220,height=104,preserveAspectRatio=True,anchor='c',mask='auto')
        para(page['caption'],293,151,245,12,16,'Plex',green)
        para('SUPPLIED WORKING MATERIAL\nSee the brand folder for full-resolution assets.'.replace('\n',' / '),293,108,242,8.5,12,'Mono',gray)
    if page.get('palette'):
        palette=json.loads((ROOT/'colors/tokens.json').read_text())['colors']
        for i,(key,v) in enumerate(palette.items()):
            x=48+i*86
            c.setFillColor(HexColor(v['hex']));c.rect(x,96,80,44,fill=1,stroke=0)
            c.setFont('Mono',6.4);c.setFillColor(ink);c.drawString(x,85,v['hex'])
        para('Full color roles, screen tokens and contrast combinations are supplied in colors/.',48,73,516,8,11,'Plex',gray)
    if page.get('note'):para(page['note'],48,94,516,8,11,'Plex',gray)
    c.setStrokeColor(gray);c.setLineWidth(.4);c.line(48,43,564,43)
    c.setFillColor(gray);c.setFont('Mono',7);c.drawString(48,28,'THE ART OF BETTER.');c.drawRightString(564,28,'REV 3 / 21 SEP 2026 / '+page['number']+' OF 06')
    c.showPage()
c.save()
reader=PdfReader(str(out));assert len(reader.pages)==6
assert all(len(p.extract_text())>600 for p in reader.pages)
print(json.dumps({'pdf':str(out),'pages':len(reader.pages),'layout':layout},indent=2))

