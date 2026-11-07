import { test as base, expect } from '@playwright/test';
import { sites, apiOrigin } from './sites.mjs';

export { expect, sites };
export const profile = role => ({
  userId: `fixture-${role}`, email: `${role.toLowerCase()}@example.test`,
  displayName: `Kiểm thử ${role}`, role, active: true, gradeLevel: 5,
  createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z',
});
const tokens = role => ({ accessToken: `fixture.${role}.access`, refreshToken: `fixture.${role}.refresh` });
const pageOf = content => ({ content, number: 0, size: 20, totalElements: content.length, totalPages: 1 });

// Production web bundles and browser storage/navigation are real. Only HTTP API
// responses are fixtures; this suite does not claim to verify backend RBAC.
export const test = base.extend({
  app: async ({ context }, use) => {
    const state = { requests: [], unexpected: [], errors: [], expired: false, classesDown: false, assignments: [] };
    const tickets = new Map();
    const watch = page => page.on('pageerror', error => state.errors.push(error.message));
    context.pages().forEach(watch);
    context.on('page', watch);
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const site = Object.values(sites).find(site => site.origin === url.origin);
      if (site && !url.pathname.startsWith('/api/v1/')) {
        const port = state.realStudent && url.pathname.startsWith('/study/') ? 43173 : site.port;
        const response = await route.fetch({ url: `http://127.0.0.1:${port}${url.pathname}${url.search}` });
        return route.fulfill({ response });
      }
      if (url.origin !== apiOrigin && !(site && url.pathname.startsWith('/api/v1/'))) {
        // No third-party calls or credentials: even fonts/social SDKs are offline.
        if (/^https:\/\/fonts\.(?:googleapis|gstatic)\.com\//.test(url.href)) return route.fulfill({ body: '', contentType: 'text/css' });
        state.unexpected.push(url.href);
        return route.abort('blockedbyclient');
      }
      const path = url.pathname.replace(/^\/api\/v1/, '');
      const method = request.method();
      const body = request.postDataJSON();
      const role = request.headers().authorization?.match(/^Bearer fixture\.(STUDENT|TEACHER|ADMIN)\.access$/)?.[1];
      const record = { method, path, body, role, origin: request.headers().origin, query: Object.fromEntries(url.searchParams) };
      state.requests.push(record);
      const json = (value, status = 200) => route.fulfill({ status, json: value,
        headers: { 'access-control-allow-origin': '*' } });
      const reject = (status = 401) => json({ error: { code: 'FIXTURE_REJECTED', message: 'Yêu cầu kiểm thử không hợp lệ.' } }, status);
      if (method === 'OPTIONS') return route.fulfill({ status: 204, headers: {
        'access-control-allow-origin': '*', 'access-control-allow-headers': 'authorization,content-type',
        'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
      } });
      if (path === '/auth/login' && method === 'POST') {
        const loginRole = body.email.split('@')[0].toUpperCase();
        return ['STUDENT', 'TEACHER', 'ADMIN'].includes(loginRole) && body.password === 'synthetic-password'
          ? json(tokens(loginRole)) : reject();
      }
      if (path === '/auth/refresh') return state.expired ? reject() : json(tokens(body.refreshToken.split('.')[1]));
      if (path === '/auth/logout') return json({});
      if (path === '/auth/sso/ticket') {
        if (!role || role !== body.targetApp) return reject(403);
        const code = `ticket-${role}`;
        tickets.set(code, role);
        return json({ code, targetApp: role, expiresIn: 30 });
      }
      if (path === '/auth/sso/exchange') {
        const ticketRole = tickets.get(body.code);
        if (!ticketRole || ticketRole !== body.targetApp) return reject(403);
        tickets.delete(body.code);
        return json(tokens(ticketRole));
      }
      if (state.expired || !role) return reject();
      if (path === '/me') return json(profile(role));
      if (state.realStudent && path === '/student/quizzes/pending-count') return json({ pendingCount: 0, totalStars: 0 });
      if (state.realStudent && path === '/student/quizzes') return json({ items: [], page: 0, totalPages: 0, totalElements: 0 });
      if (path.startsWith('/teacher/') && role !== 'TEACHER') return reject(403);
      if (path.startsWith('/admin/') && role !== 'ADMIN') return reject(403);
      if (path === '/teacher/dashboard') return json({ todayTotal: 0, processedCount: 0, reviewRequiredCount: 0, recentBatches: [] });
      if (path === '/teacher/classes') return state.classesDown ? reject(503) : json([{ classId: 'class-5a', name: '5A', studentCount: 2 }]);
      if (path === '/teacher/assignments' && method === 'POST') {
        const assignment = { ...body, assignmentId: 'assignment-1' };
        state.assignments.push(assignment);
        return json(assignment, 201);
      }
      if (path === '/teacher/assignments') return json(state.assignments);
      if (path === '/teacher/assignments/assignment-1') return json(state.assignments[0]);
      if (path === '/teacher/classes/class-5a') return json({ classId: 'class-5a', name: '5A', students: [profile('STUDENT')] });
      if (path === '/teacher/batches') return json([]);
      if (path === '/admin/dashboard') return json({ totalStudents: 2, activeStudents: 1, disabledStudents: 1,
        totalTeachers: 1, activeTeachers: 1, disabledTeachers: 0, totalClasses: 1 });
      if (path === '/admin/audit') return json(pageOf([]));
      if (path === '/admin/users') {
        let users = [profile('TEACHER'), { ...profile('STUDENT'), displayName: 'An kiểm thử', active: false }];
        if (url.searchParams.has('role')) users = users.filter(user => user.role === url.searchParams.get('role'));
        if (url.searchParams.has('active')) users = users.filter(user => String(user.active) === url.searchParams.get('active'));
        if (url.searchParams.has('query')) users = users.filter(user => user.displayName.includes(url.searchParams.get('query')));
        return json(pageOf(users));
      }
      state.unexpected.push(`${method} ${path}`);
      return reject(404);
    });
    await use(state);
    await context.unrouteAll({ behavior: 'wait' });
    expect(state.unexpected, 'No unhandled fixture API or external network calls').toEqual([]);
    expect(state.errors, 'No uncaught browser errors').toEqual([]);
  },
});

export async function login(page, role) {
  await page.goto(`${sites.portal.origin}/login`);
  await page.getByRole('textbox', { name: 'Email', exact: true }).fill(`${role.toLowerCase()}@example.test`);
  await page.getByLabel(/^Mật khẩu/).fill('synthetic-password');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  if (role !== 'STUDENT') {
    await expect(page).toHaveURL(`${sites[role.toLowerCase()].origin}/dashboard`);
    // URL changes before auth bootstrap and the responsive navigation render.
    await expect(page.getByRole('heading', { name: `Xin chào, Kiểm thử ${role}`, exact: true })).toBeVisible();
  }
}

export async function openNavigation(page, role) {
  const toggle = page.getByRole('button', { name: role === 'TEACHER' ? 'Mở điều hướng giáo viên' : 'Mở điều hướng quản trị' });
  if (await toggle.isVisible()) await toggle.click();
}
