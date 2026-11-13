// Keep test listeners below Linux's ephemeral range; a main CI runner collided on 43170.
const firstPort = Number(process.env.MATHVISION_BROWSER_PORT_BASE ?? 23170);
if (!Number.isInteger(firstPort) || firstPort < 1024 || firstPort > 65532) {
  throw new Error('MATHVISION_BROWSER_PORT_BASE must leave room for four unprivileged TCP ports.');
}

export const sites = {
  portal: { origin: 'https://portal.mathvision.test', port: firstPort, workspace: 'portal-web' },
  teacher: { origin: 'https://teacher.mathvision.test', port: firstPort + 1, workspace: 'teacher-web' },
  admin: { origin: 'https://admin.mathvision.test', port: firstPort + 2, workspace: 'admin-web' },
};
export const studentPort = firstPort + 3;
export const apiOrigin = 'https://api.mathvision.test';
