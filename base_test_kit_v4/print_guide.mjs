import fs from 'node:fs/promises';import path from 'node:path';
process.env.TMPDIR=await fs.mkdtemp('/dev/shm/base-guide-');
const {chromium}=await import('../.qa/node_modules/playwright/index.mjs');
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const root=path.resolve('output/armature-base-test-v4');
try{const page=await browser.newPage({viewport:{width:1100,height:900}});await page.goto('file://'+root+'/START_HERE.html');await page.evaluate(()=>document.fonts.ready);await page.pdf({path:root+'/PRINT_AND_ASSEMBLY.pdf',format:'A4',printBackground:true,displayHeaderFooter:true,headerTemplate:'<div></div>',footerTemplate:'<div style="font-size:9px;width:100%;text-align:center;color:#657480">Armature base test kit · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});console.log('PDF guide exported');}finally{await browser.close();await fs.rm(process.env.TMPDIR,{recursive:true,force:true});}
