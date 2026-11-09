import { test, expect, sites, login } from '../browser/fixtures.mjs';

const tutor = '/student/tutor/lesson';
const problem = 'An có 12 chiếc bút. An cho bạn 3 chiếc. Hỏi An còn bao nhiêu chiếc bút?';
const voices = { male: 'vi-VN-NamMinhNeural', female: 'vi-VN-HoaiMyNeural' };
const steps = [
  { kind: 'UNDERSTAND', title: 'Tìm dữ kiện', question: 'Ban đầu An có bao nhiêu bút?', answer: '12 chiếc', choices: ['12 chiếc', '3 chiếc'] },
  { kind: 'UNDERSTAND', title: 'Tìm câu hỏi', question: 'Đề bài muốn tìm gì?', answer: 'Số bút còn lại', choices: ['Số bút còn lại', 'Số bút đã cho'] },
  { kind: 'UNDERSTAND', title: 'Kiểm tra đề', question: 'An cho bạn bao nhiêu bút?', answer: '3 chiếc', choices: ['3 chiếc', '9 chiếc'] },
  { kind: 'MATH', title: 'Tìm số bút của An', question: 'Tính 12 trừ 3.', answer: '9', choices: [], expression: '12-3', unit: 'chiếc' },
].map(step => ({ expression: '', unit: '', explanation: step.question, workExcerpt: '', ...step }));

function wav(frequency) {
  const rate = 16000;
  const count = rate * 6;
  const audio = Buffer.alloc(44 + count * 2);
  audio.write('RIFF', 0);
  audio.writeUInt32LE(audio.length - 8, 4);
  audio.write('WAVEfmt ', 8);
  audio.writeUInt32LE(16, 16);
  audio.writeUInt16LE(1, 20);
  audio.writeUInt16LE(1, 22);
  audio.writeUInt32LE(rate, 24);
  audio.writeUInt32LE(rate * 2, 28);
  audio.writeUInt16LE(2, 32);
  audio.writeUInt16LE(16, 34);
  audio.write('data', 36);
  audio.writeUInt32LE(count * 2, 40);
  for (let i = 0; i < count; i++) audio.writeInt16LE(Math.round(1000 * Math.sin(2 * Math.PI * frequency * i / rate)), 44 + i * 2);
  return audio;
}

test('Student recovers lesson preparation and narration and finishes the guided exercise', async ({ page, app }) => {
  app.realStudent = true;
  const sessionId = 'test_student_lesson_session';
  const audioByVoice = { [voices.male]: wav(440), [voices.female]: wav(540) };
  const fallbackAudio = wav(640);
  let femaleAvailable = false;
  const preparedAudio = { phase: 'ready', mode: 'online', percent: 100, completedChunks: 1, totalChunks: 1, elapsedMs: 50 };
  const put = (path, handler) => app.responses.set('POST ' + path, handler);
  const response = (stepIndex, status, preparingMath, step = steps[stepIndex] ?? null) => ({
    sessionId, revision: stepIndex, stepIndex, status, preparingMath, understandingSteps: 3, step,
    topic: 'Phép trừ', goal: 'Tìm số bút còn lại', feedback: 'Em đã đối chiếu đúng dữ kiện.',
    outline: steps.slice(0, preparingMath ? 3 : 4).map(item => item.title),
    completed: steps.slice(0, stepIndex),
  });
  put(tutor + '/prepare', ({ json }) => json({ phase: 'preparing' }));
  put(tutor, ({ body, json }) => {
    expect(body.problemConfirmed).toBe(true);
    return json(response(0, 'READY', true));
  });
  put(tutor + '/answer', ({ body, json }) => {
    expect(body.sessionId).toBe(sessionId);
    const index = body.revision;
    if (body.answer !== steps[index].answer) return json({ ...response(index, 'TRY_AGAIN', index < 3), feedback: 'Em thử tính lại nhé.' });
    if (index === 2) return json(response(3, 'PREPARING', true, null));
    if (index === 3) return json({ ...response(4, 'COMPLETE', false), conclusion: 'An còn 9 chiếc bút.' });
    return json(response(index + 1, 'CORRECT', true));
  });
  put(tutor + '/preparation', ({ body, json }) => json(body.retry ? response(3, 'READY', false) : response(3, 'RETRYABLE', true, null)));
  put(tutor + '/media/prepare', ({ json }) => json(preparedAudio));
  put(tutor + '/narration/prepare', ({ body, json, reject }) => {
    if (!body.useFallback && body.voice === voices.female && !femaleAvailable) return reject(422);
    return json({ ...preparedAudio, mode: body.useFallback ? 'offline' : 'online' });
  });
  put(tutor + '/narration/status', ({ json }) => json(preparedAudio));
  put(tutor + '/narration', ({ body, route }) => route.fulfill({
    contentType: 'audio/wav', body: body.useFallback ? fallbackAudio : audioByVoice[body.voice],
    headers: { 'access-control-allow-origin': '*' },
  }));
  put('/student/quizzes/prepare', ({ json }) => json({ status: 'READY' }));
  put('/student/quizzes/from-learning', ({ json }) => json({ offered: false }));

  await login(page, 'STUDENT');
  await expect(page.getByText('Tiện ích nhanh', { exact: true })).toBeVisible();
  await page.goto(sites.portal.origin + '/study/learning/math-guide?' + new URLSearchParams({ problemText: problem }));
  await expect.poll(() => app.requests.some(request => request.path === tutor + '/prepare')).toBe(true);
  await expect(page.getByRole('button', { name: 'Bắt đầu từng bước' })).toBeDisabled();
  await page.getByRole('checkbox', { name: 'Em đã kiểm tra đề bài và các số' }).click();
  await page.getByRole('button', { name: 'Bắt đầu từng bước' }).click();
  await expect(page.getByRole('heading', { name: 'Tìm dữ kiện' })).toBeVisible();
  await page.getByRole('button', { name: 'Nghe giảng', exact: true }).click();
  const play = page.getByRole('button', { name: 'Phát lời giảng' });
  const pause = page.getByRole('button', { name: 'Tạm dừng lời giảng' });
  await play.click();
  await expect(pause).toBeVisible();
  await pause.click();
  await page.getByRole('radio', { name: 'Giọng nữ' }).click();
  await expect(page.getByRole('radio', { name: 'Giọng nữ' })).toBeChecked();
  await page.getByRole('button', { name: 'Dùng giọng Việt dự phòng' }).click();
  await expect(page.getByText('Đang dùng giọng Việt dự phòng.')).toBeVisible();
  await play.click();
  await expect(pause).toBeVisible();
  expect(app.requests.some(request => request.path === tutor + '/narration' && request.body.useFallback === true)).toBe(true);
  femaleAvailable = true;
  await page.getByRole('button', { name: 'Quay lại giọng đã chọn' }).click();
  await play.click();
  await expect(pause).toBeVisible();
  await expect.poll(() => [...new Set(app.requests.filter(request => request.path === tutor + '/narration' && !request.body.useFallback)
    .map(request => request.body.voice))].sort()).toEqual(Object.values(voices).sort());
  await page.getByRole('button', { name: 'Đọc lời giảng chi tiết' }).click();
  await page.getByRole('button', { name: 'Đóng Nghe giảng' }).click();

  for (const [index, step] of steps.slice(0, 3).entries()) {
    await page.getByRole('button', { name: step.answer, exact: true }).click();
    if (index < 2) await page.getByRole('button', { name: 'Tiếp tục bước tiếp theo' }).click();
  }
  await page.getByRole('button', { name: 'Thử chuẩn bị lại' }).click();
  await expect(page.getByRole('heading', { name: 'Tìm số bút của An' })).toBeVisible();
  const answer = page.getByRole('textbox', { name: 'Câu trả lời của em' });
  await answer.fill('8');
  await page.getByRole('button', { name: 'Kiểm tra bước này' }).click();
  await expect(page.getByText('Em thử tính lại nhé.')).toBeVisible();
  await answer.fill('9');
  await page.getByRole('button', { name: 'Kiểm tra bước này' }).click();
  await page.getByRole('button', { name: 'Xem bài giải' }).click();
  await expect(page.getByRole('heading', { name: 'Bài giải', exact: true })).toBeVisible();
  expect(app.requests.filter(request => request.path === tutor + '/answer' && request.body.revision === 2)).toHaveLength(1);
});
