import { test, expect, sites, login } from '../browser/fixtures.mjs';

async function prepare(page,app) {
  app.realStudent=true;
  await login(page,'STUDENT');
  await expect(page.getByRole('heading',{name:'Tiện ích nhanh',exact:true})).toBeVisible();
}
async function inside(page,locator) {
  const box=await locator.boundingBox(), viewport=page.viewportSize();
  expect(box).not.toBeNull();
  expect(box.x).toBeGreaterThanOrEqual(-1);
  expect(box.x+box.width).toBeLessThanOrEqual(viewport.width+1);
  expect(box.y).toBeGreaterThanOrEqual(-1);
  expect(box.y+box.height).toBeLessThanOrEqual(viewport.height+1);
}
for(const [width,height] of [[1280,660],[1366,768],[1920,1080]]) {
  test(`home panels and race setup fit the real viewport at ${width}x${height}`,async({page,app,isMobile},info)=>{
    test.skip(isMobile,'Desktop layout regression.');
    await page.setViewportSize({width,height});
    await prepare(page,app);
    expect(await page.locator('.student-workspace-sidebar').evaluate(el=>el.scrollWidth<=el.clientWidth+1),'The sidebar must not have its own horizontal scrollbar').toBe(true);
    for(const id of ['home-hero','learning-streak']) {
      const box=await page.getByTestId(id).boundingBox();
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x+box.width).toBeLessThanOrEqual(width+1);
    }
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
    await info.attach('home width',{body:await page.screenshot({path:info.outputPath('home.png')}),contentType:'image/png'});
    await expect.poll(() => Boolean(app.studentProfile)).toBe(true);
    app.studentProfile.gradeLevel = 1;
    await page.goto(`${sites.portal.origin}/study/games/race-to-finish`);
    await expect(page.getByText('Giải toán lớp 1 và đua qua khu rừng diệu kỳ',{exact:true})).toBeVisible();
    await expect(page.getByText(/Tung xúc xắc, giải toán lớp 1:/)).toBeVisible();
    await expect(page.getByTestId('start-race-button')).toBeEnabled();
    await inside(page,page.getByTestId('start-race-button'));
    await inside(page,page.getByTestId('race-setup-exit'));
    await info.attach('race setup fits',{body:await page.screenshot({path:info.outputPath('race-setup.png')}),contentType:'image/png'});
  });
}
