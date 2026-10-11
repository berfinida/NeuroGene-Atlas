import { chromium } from '@playwright/test';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const stem=process.env.NEUROGENE_REPORT_STEM || 'NeuroGene_Atlas_Scientific_Report';
const browser=await chromium.launch({headless:true});
try {
  const page=await browser.newPage();
  await page.goto(pathToFileURL(path.join(root,`results/reports/${stem}.html`)).href);
  await page.evaluate(()=>Promise.all(Array.from(document.images).map(i=>i.decode())));
  await page.pdf({path:path.join(root,`results/reports/${stem}.pdf`),format:'A4',printBackground:true,margin:{top:'14mm',bottom:'14mm',left:'12mm',right:'12mm'},displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:8px;width:100%;text-align:center">NeuroGene Atlas / exploratory mouse research / <span class="pageNumber"></span> of <span class="totalPages"></span></div>'});
  console.log('Scientific PDF created from HTML with all figures decoded');
} finally {await browser.close();}
