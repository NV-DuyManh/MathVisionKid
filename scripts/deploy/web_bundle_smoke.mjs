import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM, VirtualConsole } from 'jsdom';

// Execute the actual built entry (including React, renderer and libraries) with HTTP fixtures only.
export async function checkWebBundle(dist, app, { checkLogout = false } = {}) {
  const html = await readFile(new URL('index.html', dist), 'utf8');
  const entry = html.match(/<script\b[^>]*\bsrc="([^"]+)"/)?.[1];
  assert.ok(entry?.startsWith('/assets/'), 'Production HTML must reference its bundled entry.');
  const script = await readFile(new URL(entry.slice(1), dist), 'utf8');
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => {
    if (error.type === 'unhandled exception') errors.push(error.detail || error);
  });
  virtualConsole.on('error', (...args) => errors.push(args.join(' ')));
  const role = app === 'admin' ? 'ADMIN' : app === 'teacher' ? 'TEACHER' : 'STUDENT';
  const profile = { userId: 'production-user', role, displayName: 'Production User', active: true };
  const url = `https://${app}.mathvision.example/login${app === 'portal' ? '' : '#sso=production-ticket'}`;
  const dom = new JSDOM('<div id="root"></div>', {
    url, runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole,
  });
  const calls = [];
  const navigation = [];
  const location = dom.window.location;
  Object.defineProperty(dom.window, 'location', { value: new Proxy({}, {
    get(_target, key) {
      if (key === 'replace' || key === 'assign') return address => navigation.push(address);
      const value = Reflect.get(location, key);
      return typeof value === 'function' ? value.bind(location) : value;
    },
    set(_target, key, value) {
      if (key === 'href') { navigation.push(value); return true; }
      return Reflect.set(location, key, value);
    },
  }) });
  if (app === 'portal') {
    dom.window.sessionStorage.setItem('portal_access_token', 'student-access');
    dom.window.sessionStorage.setItem('portal_refresh_token', 'student-refresh');
  }
  dom.window.XMLHttpRequest = class {
    onloadend = null;
    readyState = 0;
    responseType = '';
    status = 200;
    statusText = 'OK';
    open(method, address) { this.method = method; this.url = address; }
    setRequestHeader() {}
    getAllResponseHeaders() { return 'content-type: application/json\r\n'; }
    abort() { this.onabort?.(); }
    send(body) {
      calls.push({ method: this.method, url: this.url, body });
      let data;
      if (this.url.endsWith('/auth/sso/exchange')) data = { accessToken: 'production-access', refreshToken: 'production-refresh' };
      else if (this.url.endsWith('/me')) data = profile;
      else if (this.url.includes('/admin/audit')) data = { content: [], totalPages: 0, totalElements: 0, number: 0, size: 6 };
      else if (this.url.endsWith('/admin/dashboard')) data = { totalStudents: 0, activeStudents: 0, disabledStudents: 0,
        totalTeachers: 0, activeTeachers: 0, disabledTeachers: 0, totalClasses: 0 };
      else if (this.url.endsWith('/teacher/classes')) data = [];
      else data = { metrics: { totalToday: 0, completed: 0, reviewRequired: 0 }, recentBatches: [] };
      this.responseText = JSON.stringify(data);
      this.readyState = 4;
      dom.window.setTimeout(() => this.onloadend?.(), 0);
    }
  };
  dom.window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  try {
    // jsdom evaluates scripts rather than ESM; preserve only the entry's module URL metadata.
    const metadata = `(${JSON.stringify({ url: new URL(entry, dom.window.location.href).href })})`;
    dom.window.eval(script.replaceAll('import.meta', metadata));
    const expectedPath = app === 'portal' ? '/student' : '/dashboard';
    for (let attempt = 0; attempt < 100 && errors.length === 0; attempt++) {
      if (app === 'portal' ? navigation.some(address => new URL(address, url).pathname === '/study/')
        : dom.window.location.pathname === expectedPath && dom.window.document.body.textContent.includes(profile.displayName)) break;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    assert.deepEqual(errors, [], 'Production rendering must not throw React dispatcher errors.');
    assert.equal(dom.window.location.pathname, expectedPath);
    assert.equal(dom.window.location.hash, '');
    if (app === 'portal') assert.equal(new URL(navigation[0], url).pathname, '/study/', 'Validated student must enter the shared learning app.');
    else assert.ok(dom.window.document.body.textContent.includes(profile.displayName), 'Authenticated application must render the returned profile.');
    assert.ok(calls.some(call => call.url.endsWith('/me')));
    if (app !== 'portal') assert.equal(calls.filter(call => call.url.endsWith('/auth/sso/exchange')).length, 1);
    if (checkLogout) {
      const button = dom.window.document.querySelector('button[aria-label="Đăng xuất"]');
      assert.ok(button, 'Admin logout must be available.');
      button.click();
      for (let attempt = 0; attempt < 100 && navigation.length === 0; attempt++) {
        await new Promise(resolve => setTimeout(resolve, 20));
      }
      // Give auth-route effects time to expose a competing navigation after the first one.
      await new Promise(resolve => setTimeout(resolve, 50));
      assert.equal(navigation.length, 1, 'Logout must issue a single external navigation.');
      assert.equal(new URL(navigation[0]).pathname, '/logout');
      assert.equal(new URL(navigation[0]).searchParams.get('source'), 'admin');
      assert.equal(dom.window.localStorage.getItem('mvk_admin_access_token'), null);
      assert.equal(dom.window.localStorage.getItem('mvk_admin_refresh_token'), null);
      assert.equal(calls.filter(call => call.url.endsWith('/auth/logout')).length, 1);
      assert.deepEqual(errors, []);
    }
  } finally {
    dom.window.close();
  }
}
