/* Requires sharp. Run: node tools/export-assets.cjs */
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
(async()=>{
  for (const name of fs.readdirSync(path.join(root,'logos/svg')).filter(x=>x.endsWith('.svg'))) {
    const width = name.includes('mark-')&&!name.includes('wordmark') ? 1024 : name.includes('icon')?512:name.includes('favicon')?64:2400;
    await sharp(path.join(root,'logos/svg',name),{density:300}).resize({width}).png().toFile(path.join(root,'logos/png',name.replace('.svg','.png')));
  }
  for (const size of [16,32,48,180,192,512]) {
    await sharp(path.join(root,'logos/svg/calibrated-app-icon.svg')).resize(size,size).png().toFile(path.join(root,'logos/png',`calibrated-icon-${size}.png`));
  }
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'images/manifest.json'),'utf8'));
  for(const item of manifest){
    const input=path.join(root,'images',item.master);
    const meta=await sharp(input).metadata();
    item.width=meta.width;item.height=meta.height;
    await sharp(input).webp({quality:88,effort:6}).toFile(path.join(root,'images',item.web));
    await sharp(input).resize({width:768,withoutEnlargement:true}).webp({quality:82,effort:6}).toFile(path.join(root,'images',item.thumbnail));
    item.web_bytes=fs.statSync(path.join(root,'images',item.web)).size;
  }
  fs.writeFileSync(path.join(root,'images/manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  await sharp(path.join(root,'previews/identity-and-colors.svg')).resize({width:1600}).png().toFile(path.join(root,'previews/identity-and-colors.png'));
  console.log('Exported transparent logo PNGs, app icons, WebP artwork and identity preview.');
})();
