import { test, expect } from "@playwright/test";

test.beforeEach(async ({page}) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  (page as any).__errors = errors;
  const consoleErrors: string[] = [];
  page.on("console", message => {if(message.type()==="error")consoleErrors.push(message.text())});
  (page as any).__consoleErrors = consoleErrors;
  await page.goto("/");
  await expect(page.getByText("14,359", {exact:true})).toBeVisible();
});
test.afterEach(async ({page}) => {
  expect((page as any).__errors).toEqual([]);
  const expected503 = Boolean((page as any).__expected503);
  expect((page as any).__consoleErrors.filter((m:string)=>!(expected503&&m.includes("503")))).toEqual([]);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth + 1)).toBeTruthy();
});

test("dataset switching preserves study-specific controls and QC",async({page})=>{
  for(const [study,libraries,tested,degs] of [["GSE132741",15,"14,494","2,419"],["GSE284723",9,"15,009","1,817"]] as const){
    await page.getByLabel("Explore dataset").selectOption(study);
    await expect(page.getByRole("heading",{name:study,exact:true})).toBeVisible();
    await expect(page.locator(".stats strong").filter({hasText:tested})).toBeVisible();
    await expect(page.locator(".stats strong").filter({hasText:degs})).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(libraries);
    await expect(page.locator(".recharts-scatter-symbol")).toHaveCount(libraries);
  }
  await expect(page.getByText("Dmd flox52/Y (not WT)",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:"QC",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Sample distances",exact:true})).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(9);
  const pending=page.waitForEvent("download");await page.getByRole("link",{name:"Download sample-distance matrix"}).click();
  const download=await pending;expect(await download.failure()).toBeNull();expect(download.suggestedFilename()).toContain("GSE284723");
  await page.screenshot({path:`test-results/study-switch-${test.info().project.name}.png`,fullPage:true});
  await page.getByLabel("Explore dataset").selectOption("GSE156496");
  await expect(page.locator("tbody tr")).toHaveCount(6);
});

test("study loading error and retry states",async({page})=>{
  (page as any).__expected503=true;
  let release:()=>void=()=>{};
  const delayed=new Promise<void>(resolve=>{release=resolve});
  await page.route("**/api/studies/GSE284723",async route=>{await delayed;await route.fulfill({status:503,contentType:"application/json",body:JSON.stringify({detail:"Test-only simulated server outage"})})});
  await page.getByLabel("Explore dataset").selectOption("GSE284723");
  await expect(page.getByRole("status")).toHaveText("Loading study...");
  release();await expect(page.getByRole("alert").filter({hasText:"Study unavailable (503)"})).toBeVisible();
  await page.unroute("**/api/studies/GSE284723");
  await page.getByTitle("Retry study request").click();
  await expect(page.getByRole("heading",{name:"GSE284723",exact:true})).toBeVisible();
});

test("keyboard navigation accessible labels and scientific content",async({page})=>{
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link",{name:"Skip to scientific content"})).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main-content$/);
  await expect(page.locator("h1")).toHaveCount(1);
  const unlabelled=await page.locator("button,input,select").evaluateAll(elements=>elements.filter(e=>{
    if(e.hasAttribute("aria-label")||e.hasAttribute("title")||e.closest("label"))return false;
    return !(e.textContent||"").trim();
  }).map(e=>e.outerHTML));
  expect(unlabelled).toEqual([]);
  await expect(page.getByRole("navigation",{name:"Scientific dashboard views"})).toBeVisible();
});

test("dataset registry and real PCA", async ({page}) => {
  await expect(page.getByText("1,499", {exact:true})).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(6);
  await expect(page.locator(".recharts-scatter-symbol")).toHaveCount(6);
  await expect(page.getByRole("link", {name:"NCBI GEO source record"})).toHaveAttribute("href", /GSE156496/);
  await page.screenshot({path:`test-results/dataset-${test.info().project.name}.png`,fullPage:true});
});
test("QC figures and validation", async ({page}) => {
  await page.getByRole("button", {name:"QC",exact:true}).click();
  await expect(page.getByRole("heading",{name:"VST principal components"})).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(6);
  await expect(page.locator("img")).toHaveCount(2);
  await expect.poll(()=>page.locator("img").evaluateAll(imgs=>imgs.every(i=>(i as HTMLImageElement).naturalWidth>0))).toBeTruthy();
});
test("DEG pagination filters search and CSV", async ({page}) => {
  await page.getByRole("button", {name:"Differential Expression",exact:true}).click();
  await expect(page.getByRole("heading",{name:"1,499 genes"})).toBeVisible();
  await expect(page.locator("tbody tr")).toHaveCount(50);
  await page.getByTitle("Next page").click();
  await expect(page.getByText("51-100 of 1,499",{exact:true})).toBeVisible();
  await page.getByLabel("Search genes").fill("Dmd");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await expect(page.getByRole("button",{name:"Dmd",exact:true})).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByTitle("Download filtered CSV").click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/filtered.csv/);
  await page.getByRole("button",{name:"Dmd",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Gene Expression",exact:true})).toBeVisible();
});
test("expression search and scales", async ({page}) => {
  await page.getByRole("button",{name:"Gene Expression",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Dmd",exact:true})).toBeVisible();
  await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(6);
  await page.locator("select").selectOption("vst");
  await expect(page.getByText("VST expression",{exact:true})).toBeVisible();
  await page.getByLabel("Find gene").fill("Chrna1");
  await page.getByRole("button",{name:/^Chrna1 ENSMUSG/}).click();
  await expect(page.getByRole("heading",{name:"Chrna1",exact:true})).toBeVisible();
});
test("pathway search and empty downregulated set", async ({page}) => {
  await page.getByRole("button",{name:"Pathways",exact:true}).click();
  await expect(page.getByRole("heading",{name:"48 pathways"})).toBeVisible();
  await page.getByLabel("Search pathways").fill("matrix");
  await expect.poll(()=>page.locator("tbody tr").count()).toBeGreaterThan(0);
  await page.locator("select").selectOption("down");
  await expect(page.getByText("No pathways match these thresholds.")).toBeVisible();
});
test("reports and scientific downloads", async ({page}) => {
  await page.getByRole("button",{name:"Reports",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Software versions"})).toBeVisible();
  await expect(page.locator(".downloads a")).toHaveCount(11);
  for (const url of ["/api/download/report","/api/download/provenance","/api/download/pathways","/api/research/report/html","/api/research/report/pdf"]) {
    const response = await page.request.get(url);
    expect(response.status()).toBe(200);
    expect((await response.body()).length).toBeGreaterThan(100);
  }
});

test("STRING canvas search confidence evidence and download", async ({page})=>{
  await page.getByRole('button',{name:'Network',exact:true}).click();
  await expect(page.locator('.network-canvas')).toHaveAttribute('data-node-count','100');
  await expect.poll(()=>page.locator('.network-canvas canvas').count()).toBeGreaterThan(0);
  const pixels=await page.locator('.network-canvas canvas').last().evaluate((el)=>{
    const canvas=el as HTMLCanvasElement;const data=canvas.getContext('2d')?.getImageData(0,0,canvas.width,canvas.height).data;
    return data?Array.from(data).filter((v,i)=>i%4===3&&v>0).length:0;
  });
  expect(pixels).toBeGreaterThan(100);
  await page.screenshot({path:`test-results/network-full-${test.info().project.name}.png`,fullPage:true});
  await page.getByLabel('Network node color').selectOption('community');
  await expect(page.locator('.network-canvas')).toHaveAttribute('data-node-count','100');
  await page.getByTitle('Zoom in').click();await page.getByTitle('Fit network').click();
  await page.getByLabel('Network confidence').selectOption('0.9');
  await expect(page.locator('.network-canvas')).toHaveAttribute('data-node-count','100');
  await page.getByLabel('Search network genes').fill('ENSMUSG00000030789');
  await expect(page.getByLabel('Select network gene').locator('option').filter({hasText:'Itgax'})).toHaveCount(1);
  await page.getByLabel('Select network gene').selectOption('ENSMUSG00000030789');
  await expect(page.getByRole('heading',{name:'Itgax',exact:true})).toBeVisible();
  await page.getByLabel('Select network association').selectOption({index:1});
  await expect(page.getByRole('heading',{name:'Association evidence'})).toBeVisible();
  const pending=page.waitForEvent('download');await page.getByTitle('Download network edges').click();
  expect((await pending).suggestedFilename()).toContain('edges.csv');
  await page.screenshot({path:`test-results/network-${test.info().project.name}.png`,fullPage:true});
});

test("cross-dataset comparison outliers discordance and pagination",async({page})=>{
  await page.getByRole('button',{name:'Cross-Dataset Validation',exact:true}).click();
  await expect(page.locator('.stats strong').filter({hasText:/^976$/})).toBeVisible();
  await expect(page.getByText('1-50 of 976',{exact:true})).toBeVisible();
  await page.getByTitle('Next page').click();await expect(page.getByText('51-100 of 976',{exact:true})).toBeVisible();
  await page.getByLabel('Comparison subset').selectOption('discordant');
  await expect(page.getByText('1-3 of 3',{exact:true})).toBeVisible();
  await page.getByLabel('Comparison subset').selectOption('overlap');
  await page.getByLabel('External outlier setting').selectOption('no_replacement');
  await expect(page.getByText('1-50 of 896',{exact:true})).toBeVisible();
  await page.getByLabel('Search comparison genes').fill('NO_SUCH_GENE');await expect(page.getByText('0 genes',{exact:true})).toBeVisible();
  await expect.poll(()=>page.locator('img').evaluateAll(imgs=>imgs.every(i=>(i as HTMLImageElement).naturalWidth>0))).toBeTruthy();
  await page.screenshot({path:`test-results/replication-${test.info().project.name}.png`,fullPage:true});
});

test("candidate evidence weighting pagination and sensitivity",async({page})=>{
  await page.getByRole('button',{name:'Candidates',exact:true}).click();
  await expect(page.getByRole('heading',{name:'1,499 exploratory candidates'})).toBeVisible();
  await page.getByTitle('Next page').click();await expect(page.getByText('51-100 of 1,499',{exact:true})).toBeVisible();
  await page.getByLabel('Candidate weighting').selectOption('no_network');
  await expect(page.getByText('1-50 of 1,499',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Evidence',exact:true}).first().click();await expect(page.getByText(/evidence contributions/)).toBeVisible();
  await page.getByLabel('Search candidates').fill('ENSMUSG00000030789');await expect(page.getByText('1-1 of 1',{exact:true})).toBeVisible();
  await expect(page.locator('.recharts-bar-rectangle')).toHaveCount(8);
  expect(await page.locator('.recharts-bar-rectangle path').first().evaluate(e=>e.getBoundingClientRect().width)).toBeGreaterThan(5);
  await page.screenshot({path:`test-results/candidates-${test.info().project.name}.png`,fullPage:true});
});

test("three-study evidence search stability pagination and candidate comparison",async({page})=>{
  await page.getByRole('button',{name:'Study Evidence',exact:true}).click();
  await expect(page.getByRole('heading',{name:'1,499 evidence profiles'})).toBeVisible();
  await page.getByTitle('Next evidence page').click();
  await expect(page.getByText('26-50 of 1,499',{exact:true})).toBeVisible();
  await page.getByRole('checkbox',{name:'Stable across three studies and alternatives'}).check();
  await expect(page.getByRole('heading',{name:'572 evidence profiles'})).toBeVisible();
  await page.getByRole('checkbox',{name:'Stable across three studies and alternatives'}).uncheck();
  await page.getByLabel('Search study evidence').fill('ENSMUSG00000030789');
  await expect(page.getByRole('heading',{name:'1 evidence profiles'})).toBeVisible();
  await page.getByRole('button',{name:'Compare Itgax',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Candidate comparison'})).toBeVisible();
  await expect(page.getByText('Unshrunken log2FC +/- 1.96*lfcSE, approximate within-study Wald; no pooling')).toBeVisible();
  await page.getByLabel('Search study evidence').fill('Tyrobp');
  await page.getByRole('button',{name:'Compare Tyrobp',exact:true}).click();
  await expect(page.getByTitle('Remove Tyrobp')).toBeVisible();
  await page.getByText('Itgax: evidence and uncertainty',{exact:true}).click();
  await expect(page.locator('details').filter({has:page.getByText('Itgax: evidence and uncertainty',{exact:true})}).getByText(/Approximate betweenness:/)).toBeVisible();
  await page.getByTitle('Remove Tyrobp').click();
  await page.screenshot({path:`test-results/study-evidence-${test.info().project.name}.png`,fullPage:true});
});

test("statistical sensitivity study pair FDR and real plot",async({page})=>{
  await page.getByRole('button',{name:'Sensitivity',exact:true}).click();
  await expect(page.getByRole('heading',{name:'DEG overlap sensitivity'})).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(9);
  await page.getByLabel('Sensitivity study pair').selectOption('GSE156496,GSE284723');
  await expect(page.locator('tbody tr')).toHaveCount(12);
  await page.getByLabel('Sensitivity FDR').selectOption('0.01');
  await expect(page.locator('.recharts-bar-rectangle')).toHaveCount(12);
  expect(await page.locator('.recharts-bar-rectangle path').first().evaluate(e=>e.getBoundingClientRect().height)).toBeGreaterThan(5);
  await page.getByLabel('Sensitivity study pair').selectOption('GSE132741,GSE284723');
  await expect(page.locator('tbody tr')).toHaveCount(15);
  await expect.poll(()=>page.locator('img').evaluateAll(imgs=>imgs.every(i=>(i as HTMLImageElement).naturalWidth>0))).toBeTruthy();
  await page.screenshot({path:`test-results/statistical-sensitivity-${test.info().project.name}.png`,fullPage:true});
});

test("publication provenance verified vector downloads and documents",async({page})=>{
  await page.getByRole('button',{name:'Publication',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Final audit / Phase 5',exact:true})).toBeVisible();
  await expect(page.getByText(/24 stored CSV tables matched/)).toBeVisible();
  for(const ext of ['html','pdf'])expect((await page.request.get(`/api/final/download/NeuroGene_Atlas_Scientific_Report_FINAL.${ext}`)).status()).toBe(200);
  await expect(page.getByRole('heading',{name:'Scientific provenance'})).toBeVisible();
  await expect(page.getByLabel('Publication figure').locator('option')).toHaveCount(14);
  await expect(page.getByText(/Original GSE156496 sample metadata states age: 1 month/)).toBeVisible();
  await page.getByLabel('Publication figure').selectOption('gene_forest');
  await expect.poll(()=>page.locator('img').evaluateAll(imgs=>imgs.every(i=>(i as HTMLImageElement).naturalWidth>0))).toBeTruthy();
  for (const name of ['gene_forest.pdf','gene_forest.svg','gene_forest.csv','figure_manifest.json','NeuroGene_Atlas_Publication_Figures.zip']){
    const r=await page.request.get(`/api/publication/download/${name}`);expect(r.status()).toBe(200);expect((await r.body()).length).toBeGreaterThan(100);
  }
  for (const artifact of ['audit','manuscript','provenance','evidence','sensitivity','pathways'])expect((await page.request.get(`/api/phase4/download/${artifact}`)).status()).toBe(200);
  await page.screenshot({path:`test-results/publication-${test.info().project.name}.png`,fullPage:true});
});
