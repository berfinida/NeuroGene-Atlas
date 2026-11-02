import {test, expect} from "@playwright/test";

test.beforeEach(async({page})=>{
  const errors:string[]=[]; page.on("pageerror",e=>errors.push(e.message));
  (page as any).__errors=errors;
  await page.goto("/");
  await expect(page.getByText("Public Research Demo",{exact:true})).toBeVisible();
  await expect(page.getByText("14,359",{exact:true})).toBeVisible();
});
test.afterEach(async({page})=>{
  expect((page as any).__errors).toEqual([]);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
});

test("honest demo scope, study warning and supported downloads",async({page})=>{
  await expect(page.getByText(/local review preview; not approved/)).toBeVisible();
  await expect(page.getByText(/GSE284723: GEO 10/)).toBeVisible();
  await page.getByLabel("Explore dataset").selectOption("GSE284723");
  await expect(page.locator("tbody tr")).toHaveCount(9);
  await expect(page.getByRole("heading",{name:"GSE284723",exact:true})).toBeVisible();
  await expect(page.locator('a[href$="/download/counts"]')).toHaveCount(0);
  const pending=page.waitForEvent("download");
  await page.getByRole("link",{name:"distances",exact:true}).click();
  expect(await (await pending).failure()).toBeNull();
  await page.screenshot({path:test.info().outputPath("study.png"),fullPage:true});
});

test("real interactive volcano and expression navigation",async({page})=>{
  await page.getByRole("button",{name:"Differential Expression",exact:true}).click();
  const plot=page.getByLabel("Interactive DESeq2 volcano plot");
  await expect(plot).toHaveAttribute("data-points","14358");
  await expect(plot.locator("svg.recharts-surface")).toBeVisible();
  await expect(plot.locator(".recharts-scatter-symbol")).toHaveCount(14358);
  await plot.screenshot({path:test.info().outputPath("volcano.png")});
  await page.getByLabel("Search genes").fill("Dmd");
  await page.getByRole("button",{name:"Dmd",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Dmd",exact:true})).toBeVisible();
  await expect(page.locator('option[value="raw"]')).toHaveJSProperty("disabled",true);
  await expect(page.locator(".recharts-bar-rectangle")).toHaveCount(6);
});

test("pathways, cross-study and exploratory candidates use real data",async({page})=>{
  await page.getByRole("button",{name:"Pathways",exact:true}).click();
  await expect(page.getByRole("heading",{name:"48 pathways"})).toBeVisible();
  await page.getByRole("button",{name:"Cross-Dataset Validation",exact:true}).click();
  await expect(page.locator(".stats strong").filter({hasText:/^976$/})).toBeVisible();
  await page.getByRole("button",{name:"Candidates",exact:true}).click();
  await expect(page.locator("tbody tr")).toHaveCount(50);
});

test("precomputed STRING scene is rendered and downloadable",async({page})=>{
  await page.getByRole("button",{name:"Network",exact:true}).click();
  const network=page.getByRole("img",{name:"Interactive STRING mouse protein-association network"});
  await expect(network).toHaveAttribute("data-node-count","100");
  await expect(page.getByText("4,646",{exact:true})).toBeVisible();
  await expect.poll(()=>network.locator("canvas").evaluateAll(canvases=>canvases.some(canvas=>{
    const c=canvas as HTMLCanvasElement;
    const rgba=c.getContext("2d")?.getImageData(0,0,c.width,c.height).data;
    if(!rgba)return false;
    for(let i=0;i<rgba.length;i+=4){if(rgba[i+3]>0&&Math.min(rgba[i],rgba[i+1],rgba[i+2])<240)return true;}
    return false;
  }))).toBeTruthy();
  const pending=page.waitForEvent("download"); await page.getByTitle("Download network nodes").click();
  expect(await (await pending).failure()).toBeNull();
  await page.screenshot({path:test.info().outputPath("network.png"),fullPage:true});
});

test("restricted pages avoid offering forbidden artifacts",async({page})=>{
  for(const name of ["Publication","Reports"]){
    await page.getByRole("button",{name,exact:true}).click();
    await expect(page.getByText(new RegExp(`${name} bulk artifacts are not included`))).toBeVisible();
    await expect(page.locator('a[href^="/api/research/report"],a[href="/api/download/report"]')).toHaveCount(0);
  }
  expect((await page.request.get("/api/download/report")).status()).toBe(403);
  expect((await page.request.get("/api/expression/ENSMUSG00000045103?scale=raw")).status()).toBe(403);
});
