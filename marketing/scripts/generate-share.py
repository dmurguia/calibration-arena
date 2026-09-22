"""Render the share card as outlined SVG using the approved local brand fonts.
Requires fonttools. Rasterize the SVG with any standard SVG renderer.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import re

root=Path(__file__).resolve().parents[1]
brand=root.parent/'brand/calibrated'
font=TTFont(brand/'fonts/ibmplexsans/IBMPlexSans[wdth,wght].ttf')
glyphs=font.getGlyphSet(); cmap=font.getBestCmap(); units=font['head'].unitsPerEm

def text(content,x,y,size,color='#464643'):
    scale=size/units; xpos=0; paths=[]
    for char in content:
        name=cmap.get(ord(char),'space'); glyph=glyphs[name]; pen=SVGPathPen(glyphs); glyph.draw(pen)
        paths.append(f'<path transform="translate({xpos} 0)" d="{pen.getCommands()}"/>'); xpos+=glyph.width
    return f'<g fill="{color}" transform="translate({x} {y}) scale({scale} {-scale})">'+''.join(paths)+'</g>'

def asset(name,x,y,width,height):
    raw=(brand/'logos/svg'/name).read_text(); view=re.search(r'viewBox="([^"]+)"',raw).group(1)
    inside=raw[raw.index('>')+1:raw.rindex('</svg>')]
    return f'<svg x="{x}" y="{y}" width="{width}" height="{height}" viewBox="{view}">{inside}</svg>'
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#F4F1E9"/>'
svg+=asset('calibrated-wordmark-ink.svg',64,60,295,42)
svg+='<path d="M64 145H1136M64 548H1136" stroke="#CCC9C0"/>'
svg+=text('Hone your',64,277,80)+text('agents.',64,365,80)
svg+=text('Evaluations. Training data. RL environments.',67,449,24)

svg+=asset('calibrated-mark-ink.svg',894,252,160,160)
svg+=text('calibrated.co',64,587,19)+text('Your expertise. Your models.',790,587,16)
svg+='</svg>'
(root/'public/assets/share-card.svg').write_text(svg)
print('Created outlined share-card.svg')
