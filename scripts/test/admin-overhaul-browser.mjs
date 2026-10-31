import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { createReadStream, existsSync, mkdirSync, statSync, writeFileSync } from 'node:fs';
import { resolve, dirname, extname, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes } from 'node:crypto';
import net from 'node:net';
import { createServer } from 'vite';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, process.env.MVK_BROWSER_REPORT_DIR || 'report/admin-overhaul');
const study = resolve(root, 'infra/local-runtime/admin-overhaul/student-web');
const password = randomBytes(24).toString('base64url');
const secrets = [password];
const api = 'http://127.0.0.1:18080/api/v1';
const portalOrigin = 'http://localhost:15172';
const adminOrigin = 'http://localhost:15174';
const teacherOrigin = 'http://localhost:15173';
const results = [];
const consoles = [];
const network = [];
const screenshots = [];
let pageState = null;
let browser, backend, page;
const servers = [];
let currentStep = 'startup';
function safe(message) {
  let text = String(message).split('\n')[0];
  for (const value of secrets) if (value) text = text.replaceAll(value, '[REDACTED]');
  return text.replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[REDACTED]');
}
async function freePort(port) {
  await new Promise((yes, no) => {
    const server = net.createServer();
    server.once('error', () => no(new Error('Test port ' + port + ' is already occupied; existing services were preserved.')));
    server.listen(port, '127.0.0.1', () => server.close(yes));
  });
}
async function step(name, action) {
  currentStep = name;
  try { await action(); results.push({ name, status: 'passed' }); console.log('PASS ' + name); }
  catch (error) { results.push({ name, status: 'failed', error: safe(error.message) }); throw new Error('Browser verification failed at: ' + name); }
}
async function shot(name) {
  await page.screenshot({ path: resolve(output, name + '.png'), fullPage: !/^(navigation|user-create)/.test(name), animations: 'disabled' });
  screenshots.push(name + '.png');
}
async function fits() {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), true, 'Page has horizontal overflow');
}
async function directLogin(email, supplied = password) {
  const response = await page.request.post(api + '/auth/login', { data: { email, password: supplied } });
  assert.equal(response.headers()['x-mathvision-test-database'], 'h2-memory', 'Mutations require the isolated H2 harness marker.');
  assert.equal(response.status(), 200);
  const data = await response.json();
  return data.accessToken;
}
async function apiRequest(path, token, method = 'GET', data) {
  const response = await page.request.fetch(api + path, { method, headers: { Authorization: 'Bearer ' + token }, data });
  return response;
}
async function portalLogin(email) {
  await page.goto(portalOrigin + '/logout');
  await page.waitForFunction(() => !sessionStorage.getItem('portal_access_token') && !sessionStorage.getItem('portal_refresh_token'));
  await page.goto(portalOrigin + '/login');
  await page.getByLabel(new RegExp('^Email')).fill(email);
  await page.getByLabel(new RegExp('^Mật\ khẩu')).fill(password);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
}
async function selectMui(label, option, scope = page) {
  await scope.getByRole('combobox', { name: new RegExp('^' + label) }).click();
  await page.getByRole('option', { name: option, exact: true }).click();
}
function studyPlugin() {
  const mime = { '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ttf': 'font/ttf', '.woff2': 'font/woff2', '.html': 'text/html' };
  return { name: 'isolated-student-export', configureServer(server) {
    server.middlewares.use('/study', (request, response, next) => {
      if (!existsSync(study)) { next(); return; }
      const pathname = decodeURIComponent(new URL(request.url || '/', portalOrigin).pathname);
      let target = resolve(study, '.' + pathname);
      if (!target.startsWith(study + sep) && target !== study) { response.statusCode = 403; response.end(); return; }
      if (!existsSync(target) || statSync(target).isDirectory()) {
        if (extname(pathname) && !pathname.endsWith('.html')) { response.statusCode = 404; response.end(); return; }
        target = resolve(study, 'index.html');
      }
      response.setHeader('Content-Type', mime[extname(target)] || 'application/octet-stream');
      createReadStream(target).pipe(response);
    });
  } };
}
try {
  for (const port of [18080, 15172, 15173, 15174]) await freePort(port);
  mkdirSync(output, { recursive: true });
  const command = 'gradlew.bat -I ../../scripts/test/admin-overhaul.init.gradle adminOverhaulPreview --no-daemon --console=plain';
  backend = spawn(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', command], {
    cwd: resolve(root, 'backend/business-api'), env: { ...process.env, MVK_OVERHAUL_PASSWORD: password }, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'],
  });
  await new Promise((yes, no) => {
    const timeout = setTimeout(() => no(new Error('Isolated backend startup timed out')), 240000);
    let buffer = '';
    const inspect = data => {
      buffer = (buffer + String(data)).slice(-16000);
      if (buffer.includes('ADMIN_OVERHAUL_TEST_READY')) { clearTimeout(timeout); yes(); }
    };
    backend.stdout.on('data', inspect); backend.stderr.on('data', inspect);
    backend.once('exit', code => { clearTimeout(timeout); if (!buffer.includes('ADMIN_OVERHAUL_TEST_READY')) no(new Error('Isolated backend exited with code ' + code + ': ' + buffer.split('\n').filter(line => /error:|ERROR|Caused by:|Exception|What went wrong|Could not|FAILED/.test(line)).slice(-8).map(safe).join(' | '))); });
  });
  Object.assign(process.env, { VITE_API_BASE_URL: api, VITE_ADMIN_URL: adminOrigin, VITE_PORTAL_URL: portalOrigin, VITE_TEACHER_URL: teacherOrigin, VITE_USE_MOCK: 'false', VITE_SHOW_DEV_TOOLS: 'false' });
  for (const [app, port] of [['portal-web', 15172], ['admin-web', 15174], ['teacher-web', 15173]]) {
    const server = await createServer({ root: resolve(root, 'apps', app), configFile: resolve(root, 'apps', app, 'vite.config.ts'), cacheDir: resolve(root, 'infra/local-runtime/admin-ui-env-vite', app), server: { port, host: '127.0.0.1', strictPort: true }, plugins: app === 'portal-web' ? [studyPlugin()] : [] });
    await server.listen(); servers.push(server);
  }
  const require = process.env.MVK_PLAYWRIGHT_ROOT ? createRequire(resolve(process.env.MVK_PLAYWRIGHT_ROOT, 'package.json')) : createRequire(import.meta.url);
  const { chromium } = require('playwright');
  const executablePath = process.env.MVK_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
  browser = await chromium.launch({ executablePath, headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.route('https://overhaul-api.mathvision.example/**', async route => {
    const original = new URL(route.request().url());
    const response = await route.fetch({ url: 'http://127.0.0.1:18080' + original.pathname + original.search });
    await route.fulfill({ response });
  });
  page = await context.newPage();
  page.setDefaultTimeout(60000);
  page.on('pageerror', error => consoles.push({ type: 'pageerror', message: safe(error.message) }));
  page.on('console', event => { if (event.type() === 'error') consoles.push({ type: 'console', message: safe(event.text()) }); });
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.pathname.startsWith('/api/')) network.push({ path: url.pathname, status: response.status() });
  });
  let adminToken, studentId, teacherId, classroomId, replayTicket;
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame() && frame.url().includes('#sso=')) replayTicket = new URLSearchParams(new URL(frame.url()).hash.slice(1)).get('sso');
  });
  await step('A: Portal ADMIN login completes SSO into Admin Dashboard', async () => {
    await portalLogin('admin.demo@mathvision.local');
    await page.waitForURL(adminOrigin + '/dashboard');
    await page.getByRole('heading', { name: 'Tổng quan vận hành', level: 1 }).waitFor();
    assert.equal(await page.getByText('Trang chủ', { exact: true }).count(), 0);
    adminToken = await directLogin('admin.demo@mathvision.local');
    await fits();
  });
  await step('UI creates a Student account and validates detail editing', async () => {
    await page.getByRole('link', { name: 'Người dùng', exact: true }).click();
    await page.getByRole('button', { name: 'Tạo người dùng', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel(new RegExp('^Họ\ và\ tên')).fill('Học sinh kiểm chứng');
    await dialog.getByLabel(new RegExp('^Email\ đăng\ nhập')).fill('overhaul.student@validation.test');
    await dialog.getByLabel(new RegExp('^Mật\ khẩu\ khởi\ tạo')).fill(password);
    await dialog.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('link', { name: 'Xem chi tiết Học sinh kiểm chứng', exact: true }).click();
    studentId = new URL(page.url()).pathname.split('/').at(-1);
    await page.getByRole('button', { name: 'Chỉnh sửa hồ sơ', exact: true }).click();
    await dialog.getByLabel(new RegExp('^Họ\ và\ tên')).fill('Học sinh kiểm chứng đã cập nhật');
    await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('heading', { name: 'Học sinh kiểm chứng đã cập nhật', exact: true }).waitFor();
  });
  await step('UI disables/enables a user; issued access is rejected while disabled', async () => {
    const issued = await directLogin('overhaul.student@validation.test');
    await page.getByRole('button', { name: 'Khóa tài khoản', exact: true }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Xác nhận', exact: true }).click();
    await page.getByRole('button', { name: 'Mở tài khoản', exact: true }).waitFor();
    assert.equal((await apiRequest('/me', issued)).status(), 401);
    await page.getByRole('button', { name: 'Mở tài khoản', exact: true }).click();
    await page.getByRole('dialog').getByRole('button', { name: 'Xác nhận', exact: true }).click();
    await page.getByRole('button', { name: 'Khóa tài khoản', exact: true }).waitFor();
  });
  await step('UI password reset reveals a valid result once and clears it on close', async () => {
    await page.getByRole('button', { name: 'Đặt lại mật khẩu', exact: true }).click();
    const responsePromise = page.waitForResponse(response => response.url().endsWith('/reset-password') && response.request().method() === 'POST');
    await page.getByRole('dialog').getByRole('button', { name: 'Tạo mật khẩu tạm thời', exact: true }).click();
    const response = await responsePromise;
    assert.equal(response.status(), 200);
    const reset = await response.json(); secrets.push(reset.temporaryPassword);
    assert.equal(reset.userId, studentId);
    await page.getByRole('button', { name: 'Sao chép mật khẩu', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Sao chép mật khẩu', exact: true }).click();
    await page.getByRole('button', { name: 'Đóng và xóa khỏi màn hình', exact: true }).click();
    assert.equal((await page.locator('body').innerText()).includes(reset.temporaryPassword), false);
    await directLogin('overhaul.student@validation.test', reset.temporaryPassword);
  });
  await step('UI creates a Teacher account without a student grade', async () => {
    await page.goto(adminOrigin + '/users?create=true');
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel(new RegExp('^Họ\ và\ tên')).fill('Cô Mai kiểm chứng');
    await dialog.getByLabel(new RegExp('^Email\ đăng\ nhập')).fill('overhaul.teacher@validation.test');
    await dialog.getByLabel(new RegExp('^Mật\ khẩu\ khởi\ tạo')).fill(password);
    await selectMui('Vai trò', 'Giáo viên', dialog);
    await dialog.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('link', { name: 'Xem chi tiết Cô Mai kiểm chứng', exact: true }).click();
    teacherId = new URL(page.url()).pathname.split('/').at(-1);
  });
  await step('UI creates and edits a classroom using an active teacher', async () => {
    await page.goto(adminOrigin + '/classes?create=true');
    const dialog = page.getByRole('dialog');
    await dialog.getByLabel(new RegExp('^Tên\ lớp\ học')).fill('Lớp 3A kiểm chứng');
    await dialog.getByLabel(new RegExp('^Năm\ học')).fill('2026–2027');
    await dialog.getByRole('combobox', { name: /^Chọn giáo viên phụ trách/ }).click();
    await page.getByRole('option', { name: /Cô Lan/ }).click();
    await dialog.getByRole('button', { name: 'Tạo lớp học', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('link', { name: 'Xem chi tiết Lớp 3A kiểm chứng', exact: true }).click();
    classroomId = new URL(page.url()).pathname.split('/').at(-1);
    await page.getByRole('button', { name: 'Chỉnh sửa lớp học', exact: true }).click();
    await dialog.getByLabel(new RegExp('^Tên\ lớp\ học')).fill('Lớp 3A đã cập nhật');
    await dialog.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('heading', { level: 1, name: 'Lớp 3A đã cập nhật' }).waitFor();
  });
  await step('UI reassigns the teacher and adds/removes the student roster', async () => {
    const dialog = page.getByRole('dialog');
    await page.getByRole('button', { name: 'Thay đổi giáo viên', exact: true }).click();
    await dialog.getByRole('combobox', { name: /^Chọn giáo viên phụ trách/ }).click();
    await page.getByRole('option', { name: /Cô Mai kiểm chứng/ }).click();
    await dialog.getByRole('button', { name: 'Xác nhận phân công', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('button', { name: 'Thêm học sinh', exact: true }).click();
    await dialog.getByRole('combobox', { name: /^Chọn học sinh/ }).click();
    await page.getByRole('option', { name: /Học sinh kiểm chứng đã cập nhật/ }).click();
    await dialog.getByRole('button', { name: 'Thêm vào lớp', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    await page.getByRole('button', { name: 'Xóa Học sinh kiểm chứng đã cập nhật khỏi lớp', exact: true }).click();
    await dialog.getByRole('button', { name: 'Xóa khỏi lớp', exact: true }).click();
    await dialog.waitFor({ state: 'hidden' });
    const data = await (await apiRequest('/admin/classes/' + classroomId, adminToken)).json();
    assert.equal(data.studentCount, 0); assert.equal(data.teacher.userId, teacherId);
    const add = await apiRequest('/admin/classes/' + classroomId + '/students/' + studentId, adminToken, 'POST');
    assert.equal(add.status(), 200);
  });
  await step('UI search, role/status filters and pagination use real API data', async () => {
    for (let i = 0; i < 11; i++) {
      const response = await apiRequest('/admin/users', adminToken, 'POST', { email: 'page' + i + '@validation.test', displayName: 'Học sinh trang ' + (i + 1), role: 'STUDENT', gradeLevel: 3, initialPassword: password });
      assert.equal(response.status(), 201);
    }
    await page.goto(adminOrigin + '/users');
    await page.getByRole('button', { name: /next page|trang tiếp/i }).click();
    await page.getByRole('button', { name: /previous page|trang trước/i }).waitFor();
    await selectMui('Vai trò', 'Học sinh');
    await selectMui('Trạng thái', 'Đang hoạt động');
    await page.getByLabel(new RegExp('^Tìm\ theo\ tên\ hoặc\ email')).fill('overhaul.student');
    await page.getByRole('button', { name: 'Tìm kiếm', exact: true }).click();
    await page.getByRole('link', { name: 'Xem chi tiết Học sinh kiểm chứng đã cập nhật', exact: true }).waitFor();
    await fits(); await shot('users-1440');
  });
  await step('UI audit filters and metadata dialog work without secrets', async () => {
    await page.goto(adminOrigin + '/audit');
    await selectMui('Loại sự kiện', 'Tạo lớp học');
    await page.getByRole('button', { name: /^Xem sự kiện/ }).first().click();
    await page.getByRole('heading', { name: 'Chi tiết sự kiện', exact: true }).waitFor();
    assert.equal((await page.getByRole('dialog').innerText()).includes(password), false);
    await page.getByRole('button', { name: 'Đóng', exact: true }).click();
    await shot('audit-1440');
  });
  await step('Recognition empty state and 404 route are honest and usable', async () => {
    await page.goto(adminOrigin + '/recognition/analytics');
    await page.getByRole('heading', { name: 'Chưa có nguồn thống kê tổng hợp' }).waitFor();
    await shot('recognition-1440');
    await page.goto(adminOrigin + '/unknown-overhaul-route');
    await page.getByRole('heading', { name: 'Không tìm thấy trang' }).waitFor();
  });
  await step('Responsive 390/768/1024/1440 layouts, drawer and collapsed sidebar', async () => {
    await page.goto(adminOrigin + '/dashboard');
    await page.getByRole('button', { name: 'Thu gọn thanh bên', exact: true }).click();
    await page.getByRole('button', { name: 'Mở rộng thanh bên', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Mở rộng thanh bên', exact: true }).click();
    for (const width of [1440, 1024, 768, 390]) {
      await page.goto(adminOrigin + '/dashboard');
      await page.getByRole('heading', { name: 'Tổng quan vận hành', level: 1 }).waitFor();
      await page.locator('.metric-grid .MuiTypography-h4').first().filter({ hasText: /\d/ }).waitFor();
      await page.setViewportSize({ width, height: 1000 });
      await fits(); await shot('dashboard-' + width);
      if (width < 900) {
        await page.getByRole('button', { name: 'Mở điều hướng quản trị', exact: true }).click();
        await page.getByRole('link', { name: 'Người dùng', exact: true }).waitFor();
        await shot('navigation-' + width);
        await page.getByRole('link', { name: 'Người dùng', exact: true }).click();
        await page.getByRole('heading', { name: 'Quản lý người dùng', level: 1 }).waitFor();
        await fits();
        if (width === 390) {
          await page.getByRole('button', { name: 'Tạo người dùng', exact: true }).click();
          await page.getByRole('dialog').waitFor();
          await fits(); await shot('user-create-390');
          await page.keyboard.press('Escape');
          await page.getByRole('dialog').waitFor({ state: 'hidden' });
        }
        await page.getByRole('button', { name: 'Mở điều hướng quản trị', exact: true }).click();
        await page.getByRole('link', { name: 'Tổng quan', exact: true }).click();
        await page.getByRole('heading', { name: 'Tổng quan vận hành', level: 1 }).waitFor();
      }
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(adminOrigin + '/classes/' + classroomId);
    await page.getByRole('heading', { level: 1, name: 'Lớp 3A đã cập nhật' }).waitFor();
    await shot('class-detail-1440');
  });
  await step('Keyboard navigation and honest network error/retry work', async () => {
    await page.goto(adminOrigin + '/dashboard');
    await page.getByRole('heading', { name: 'Tổng quan vận hành', level: 1 }).waitFor();
    await page.getByRole('link', { name: 'Đến nội dung chính', exact: true }).focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'workspace-main');
    await page.getByRole('link', { name: 'Người dùng', exact: true }).focus();
    await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: 'Quản lý người dùng', level: 1 }).waitFor();
    const pattern = api + '/admin/dashboard';
    let aborted = 0;
    const fault = route => aborted++ < 2 ? route.abort('failed') : route.continue();
    await page.route(pattern, fault);
    try {
      await page.goto(adminOrigin + '/dashboard');
      const error = page.getByRole('alert').filter({ hasText: 'Không thể kết nối máy chủ' });
      await error.waitFor();
      assert.equal((await page.locator('.metric-grid .MuiTypography-h4').allTextContents()).every(value => value === '—'), true);
      const restored = page.waitForResponse(response => response.url() === pattern && response.status() === 200);
      await error.getByRole('button', { name: 'Thử lại', exact: true }).click();
      await restored;
      await error.waitFor({ state: 'hidden' });
      assert.equal((await page.locator('.metric-grid .MuiTypography-h4').allTextContents()).every(value => value !== '—'), true);
    } finally { await page.unroute(pattern, fault); }
  });
  await step('C/D: Student and Teacher cannot enter Admin UI or Admin API', async () => {
    for (const email of ['minh.student@mathvision.local', 'lan.teacher@mathvision.local']) {
      const token = await directLogin(email);
      assert.equal((await apiRequest('/admin/dashboard', token)).status(), 403);
      await page.evaluate(() => { localStorage.removeItem('mvk_admin_access_token'); localStorage.removeItem('mvk_admin_refresh_token'); });
      await page.goto(adminOrigin + '/login');
      await page.getByLabel(new RegExp('^Email\ quản\ trị')).fill(email);
      await page.getByLabel(new RegExp('^Mật\ khẩu')).fill(password);
      await page.getByRole('button', { name: 'Đăng nhập quản trị', exact: true }).click();
      await page.waitForURL(adminOrigin + '/403');
    }
  });
  await step('F/G: replayed/invalid SSO fails safely and logout clears the session', async () => {
    assert.ok(replayTicket);
    await page.goto(adminOrigin + '/login#sso=' + encodeURIComponent(replayTicket));
    await page.getByText(/Mã chuyển tiếp không hợp lệ/).waitFor();
    assert.equal(await page.evaluate(() => localStorage.getItem('mvk_admin_access_token')), null);
    await portalLogin('admin.demo@mathvision.local');
    await page.waitForURL(adminOrigin + '/dashboard');
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await page.waitForURL(url => url.origin === portalOrigin && url.pathname === '/logout');
    await page.goto(adminOrigin + '/dashboard');
    await page.waitForURL(adminOrigin + '/login');
    assert.equal(await page.evaluate(() => localStorage.getItem('mvk_admin_access_token')), null);
  });
  await step('E: rejected access/refresh cannot restore a protected session', async () => {
    await page.evaluate(() => { localStorage.setItem('mvk_admin_access_token', 'invalid-access'); localStorage.setItem('mvk_admin_refresh_token', 'invalid-refresh'); });
    await page.goto(adminOrigin + '/dashboard');
    await page.waitForURL(adminOrigin + '/login');
    assert.equal(await page.evaluate(() => localStorage.getItem('mvk_admin_access_token')), null);
  });
  if (existsSync(resolve(study, 'index.html'))) await step('B: exported Student Web rejects ADMIN and accepts STUDENT', async () => {
    const admin = await directLogin('admin.demo@mathvision.local');
    await page.goto(portalOrigin + '/');
    await page.evaluate(access => sessionStorage.setItem('portal_access_token', access), admin);
    await page.goto(portalOrigin + '/study/');
    await page.waitForURL(url => url.pathname === '/access-denied');
    const student = await directLogin('minh.student@mathvision.local');
    await page.evaluate(access => sessionStorage.setItem('portal_access_token', access), student);
    await page.goto(portalOrigin + '/study/');
    await page.getByRole('tab', { name: 'Trang chủ', exact: true }).waitFor();
    assert.equal(await page.getByRole('heading', { name: 'Tổng quan vận hành' }).count(), 0);
  });
  else results.push({ name: 'B: exported Student Web browser check', status: 'not-run', reason: 'Run admin-overhaul-export.mjs first; native/web provider regressions are separate.' });
  assert.equal(consoles.filter(item => item.type === 'console' && !/Failed to load resource|ERR_FAILED/.test(item.message)).length, 0, 'Unexpected browser console errors were recorded');
  assert.equal(consoles.filter(item => item.type === 'pageerror').length, 0, 'Browser runtime errors were recorded');
} catch (error) {
  if (page) {
    pageState = {
      path: new URL(page.url()).pathname,
      body: safe((await page.locator('body').innerText().catch(() => '')).slice(0, 1200)),
      inputs: await page.locator('input').evaluateAll(nodes => nodes.map(node => ({ id: node.id, type: node.type, labels: [...(node.labels || [])].map(label => label.textContent) }))).catch(() => []),
    };
  }
  console.error('FAIL ' + currentStep + ': ' + safe(error.message));
  process.exitCode = 1;
} finally {
  if (existsSync(output)) writeFileSync(resolve(output, 'browser-results.json'), JSON.stringify({ database: 'isolated H2 memory', realHttp: true, results, screenshots, pageState, console: consoles, network }, null, 2));
  if (browser) await browser.close();
  await Promise.allSettled(servers.map(server => server.close()));
  if (backend?.pid) {
    if (process.platform === 'win32') spawnSync('taskkill', ['/PID', String(backend.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    else backend.kill('SIGTERM');
  }
}
