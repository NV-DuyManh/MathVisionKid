const assert = require('node:assert/strict');
const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.addInitScript(() => sessionStorage.setItem('portal_access_token','isolated-layout-qa'));
    await page.route('**/api/v1/**',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({id:'layout-qa-student',name:'Minh',grade:4,role:'STUDENT'})}));
    for(const width of [320,360,390,768,1440]) {
      await page.setViewportSize({width,height:900});
      await page.goto('http://127.0.0.1:8087/study/login');
      const eye = page.getByRole('button', {name:'Hiện mật khẩu',exact:true});
      await eye.waitFor();
      const field = page.getByLabel('Mật khẩu',{exact:true});
      const sizes = await field.evaluate(input => {
        const wrapper=input.parentElement, button=wrapper.querySelector('[role=button]');
        return {width:innerWidth, inputWidth:input.getBoundingClientRect().width, minWidth:getComputedStyle(input).minWidth, right:button.getBoundingClientRect().right, wrapperRight:wrapper.getBoundingClientRect().right};
      });
      console.log(JSON.stringify(sizes));
      assert(sizes.right<=sizes.wrapperRight, `Password control exceeds its field at ${width}px`);
      await field.fill('layout-only-password');
      await eye.click();
      assert.equal(await field.evaluate(input => input.type),'text');
      await page.getByRole('button',{name:'Ẩn mật khẩu',exact:true}).click();
      assert.equal(await field.evaluate(input => input.type),'password');
    }
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
