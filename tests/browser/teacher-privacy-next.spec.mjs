import { readFile } from 'node:fs/promises';
import { test, expect, login, sites } from './fixtures.mjs';

const image = await readFile(new URL('../../apps/teacher-web/public/ui/mathvision-star.png', import.meta.url));

test('each image requires its own privacy confirmation when advancing', async ({ page, app }) => {
  app.assignments.push({ assignmentId: 'assignment-1', classId: 'class-5a', title: 'Bài kiểm thử', operationType: 'ADDITION' });
  await login(page, 'TEACHER');
  await page.goto(`${sites.teacher.origin}/batches/create?assignmentId=assignment-1`);
  const picker = page.getByRole('button', { name: 'Chọn ảnh từ máy tính' });
  await expect(picker).toBeEnabled();
  await picker.focus();
  const chooser = page.waitForEvent('filechooser');
  await page.keyboard.press('Enter');
  await (await chooser).setFiles([1, 2, 3].map(index => ({
    name: `work-${index}.png`, mimeType: 'image/png', buffer: image,
  })));
  await page.getByRole('button', { name: 'Che thông tin cá nhân', exact: true }).first().click();
  const editor = page.getByRole('dialog', { name: 'Che thông tin cá nhân' });
  const next = editor.getByRole('button', { name: 'Lưu và mở ảnh tiếp theo' });
  const noInfo = editor.getByRole('checkbox', { name: 'Ảnh không có thông tin cá nhân cần che' });
  await expect(next).toBeDisabled();
  await noInfo.check();
  await next.click();
  await expect(editor.getByText('Ảnh 2/3: work-2.png', { exact: true })).toBeVisible();
  await expect(noInfo).not.toBeChecked();
  await expect(next).toBeDisabled();
  await editor.getByRole('button', { name: 'Thêm vùng che' }).click();
  await expect(next).toBeEnabled();
  await next.click();
  await expect(editor.getByText('Ảnh 3/3: work-3.png', { exact: true })).toBeVisible();
  await expect(noInfo).not.toBeChecked();
  await expect(editor.getByRole('button', { name: 'Lưu ảnh đã che' })).toBeDisabled();
  await expect(editor.getByRole('button', { name: 'Lưu và mở ảnh tiếp theo' })).toHaveCount(0);
  await noInfo.check();
  await editor.getByRole('button', { name: 'Lưu ảnh đã che' }).click();
  await expect(editor).toBeHidden();
  const readiness = page.getByRole('region', { name: 'Kiểm tra trước khi gửi' });
  await expect(readiness.getByRole('listitem').filter({ hasText: 'Đã che thông tin' })).toContainText('3/3');
});
