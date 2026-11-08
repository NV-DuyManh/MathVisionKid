import { completedNarration, narrationChunks, spokenMath, stepNarration, vietnameseVoices, voiceLabel } from '../features/tutoring/narration';
import type { LessonStep } from '../features/tutoring/api/TutorService';
import type { Voice } from 'expo-speech';

const step: LessonStep = { title: 'Tìm phần còn lại', explanation: 'Cả vườn gồm các phần đã cho và phần còn lại.',
  question: 'Em tìm phần còn lại thế nào?', guidance: ['Đọc lại các phần đã biết.', 'Lấy cả vườn trừ phần đã biết.'],
  choices: [], expression: '1-11/15', unit: 'phần', workExcerpt: 'Không được đọc nguyên ảnh ở đây.', solutionSentence: 'Câu lời giải chưa mở.' };

it('builds richer current narration only from opened teaching, never hidden expression or raw work', () => {
  const paragraphs = stepNarration(step, 'Gợi ý vừa được mở.');
  expect(paragraphs).toEqual([...step.guidance!, 'Gợi ý vừa được mở.', step.question]);
  expect(paragraphs.join(' ')).not.toContain(step.expression);
  expect(paragraphs.join(' ')).not.toContain(step.workExcerpt);
  expect(paragraphs.join(' ')).not.toContain(step.solutionSentence);
  expect(stepNarration({ ...step, guidance: [step.explanation, step.question] })).toEqual([step.explanation, step.question]);
});

it('can narrate the calculation only after the step is earned', () => {
  const completed = { title: 'Tổng số bút', solutionSentence: 'Số bút có tất cả là:', expression: '12+5', answer: '17',
    unit: 'bút', explanation: 'Gộp các nhóm bút.', guidance: ['Em kiểm tra lại tổng.'], calculationDetails: ['Cộng hàng đơn vị: 2 + 5 = 7, giữ nguyên hàng chục.'] };
  expect(completedNarration([completed])).toEqual([completed.solutionSentence, completed.explanation, 'Em kiểm tra lại tổng.', '12+5 = 17 (bút)']);
  expect(completedNarration([completed, { ...completed, answer: '18' }])).toEqual([
    completed.solutionSentence, completed.explanation, 'Em kiểm tra lại tổng.', '12+5 = 17 (bút)',
    completed.solutionSentence, completed.explanation, 'Em kiểm tra lại tổng.', '12+5 = 18 (bút)',
  ]);
});

it('teaches why and how for every finished step, without reading all the written working', () => {
  const steps = [
    { title: 'Tìm giá một quyển vở', solutionSentence: 'Giá một quyển vở là:', expression: '102000/12', answer: '8500', unit: 'đồng',
      explanation: 'Các quyển vở có cùng giá, nên chia tổng tiền cho số quyển.',
      guidance: ['Các quyển vở có cùng giá, nên chia tổng tiền cho số quyển.', 'Lấy 102000 chia 12 để tìm tiền của một quyển.', 'Đoạn hướng dẫn sâu còn lại.'] },
    { title: 'Tìm số tiền đang có', expression: '68000-15000', answer: '53000', unit: 'đồng',
      explanation: 'Đã biết số tiền cần trả. Còn thiếu tiền nên lấy tiền cần trả trừ phần còn thiếu.',
      guidance: ['Lấy 68000 trừ 15000; không cộng phần còn thiếu vào số tiền cần trả.'] },
  ];
  const text = completedNarration(steps).join('\n');
  for (const step of steps) expect(text).toContain(step.explanation);
  expect(text).toContain(steps[0].guidance[1]);
  expect(text).toContain(steps[1].guidance[0]);
  expect(text).not.toContain('Đoạn hướng dẫn sâu còn lại.');
  expect(text.match(/Các quyển vở có cùng giá/g)).toHaveLength(1);
});

it('keeps long completed lessons within the audio limit without clipping a sentence or losing a step', () => {
  const steps = Array.from({ length: 6 }, (_, index) => ({ title: `Bước ${index + 1}`, expression: `${index}+1`, answer: `${index + 1}`, unit: '',
    explanation: `Lý do bước ${index + 1}: ${'🍎'.repeat(200)}`, guidance: ['Hướng dẫn dài. '.repeat(30).trim()] }));
  const parts = completedNarration(steps);
  expect(parts.join('').length).toBeLessThanOrEqual(4000);
  for (const step of steps) expect(parts).toContain(step.explanation);
  expect(parts).not.toContain(steps[0].guidance[0].slice(0, 100));
  expect(completedNarration([])).toEqual([]);
});

it('skips the fallback source-reading paragraph when a solving instruction is available', () => {
  const completed = { title: 'Tìm chiều rộng', expression: '8/2', answer: '4', unit: 'm',
    explanation: 'Chiều rộng bằng một nửa chiều dài.',
    guidance: ['Chiều rộng bằng một nửa chiều dài.', 'Đề cho chiều dài là 8 m. Chiều rộng bằng một nửa chiều dài.',
      'Đọc điều cần tìm: Hỏi chiều rộng bao nhiêu mét?',
      'Chia chiều dài thành hai phần bằng nhau để tìm chiều rộng.'] };
  expect(completedNarration([completed])).toEqual([completed.title, completed.explanation, completed.guidance[3], '8/2 = 4 (m)']);
});

it.each([
  ['Bài 3: (2 điểm), 2 đề-xi-mét', 'Bài 3. 2 đề xi mét'],
  ['32m2 và 4dm^2 và 2cm^{3}', '32 mét vuông và 4 đề xi mét vuông và 2 xăng ti mét khối'],
  ['8 x 4 = 32 (m2)', '8 nhân 4 bằng 32 mét vuông'],
  ['(3,5)/(2,5)', '3,5 phần 2,5'],
  ['3.5/2.5', '3.5 phần 2.5'],
  ['x + 3 = 5', 'x cộng 3 bằng 5'],
  ['Bài 3: (2 điểm). 2 đề-xi-mét', 'Bài 3. 2 đề xi mét'],
  ['2 đề-xi-mét và 30 xăng-ti-mét', '2 đề xi mét và 30 xăng ti mét'],
  ['2 đề-xi-mét-vuông và 30 xăng-ti-mét-khối', '2 đề xi mét vuông và 30 xăng ti mét khối'],
  ['Bài 3: (2 điểm), 2 đề−xi−mét−vuông', 'Bài 3. 2 đề xi mét vuông'],
  ['Diện tích (bỏ qua mạch vữa) là 32 (m²).', 'Diện tích bỏ qua mạch vữa là 32 mét vuông .'],
  ['3 ki-lô-gam và 1 mi-li-lít', '3 ki lô gam và 1 mi li lít'],
  ['2 (đề-xi-mét vuông)', '2 đề xi mét vuông'],
  ['(1)/(3) + (2)/(5) = (11)/(15)', '1 phần 3 cộng 2 phần 5 bằng 11 phần 15'],
  ['1 - 11/15 = 4/15', '1 trừ 11 phần 15 bằng 4 phần 15'],
  ['12 × 2 : 3 = 8 (cm²)', '12 nhân 2 chia 3 bằng 8 xăng ti mét vuông'],
  ['(12 + 8) × 2 = 40', 'nhóm 12 cộng 8, hết nhóm nhân 2 bằng 40'],
  ['12 - (8 - 3)', '12 trừ nhóm 8 trừ 3, hết nhóm'],
  ['(-3) × 2', 'âm 3 nhân 2'],
  ['5 × -2 = -10', '5 nhân âm 2 bằng âm 10'],
  ['5 * -2 = -10', '5 nhân âm 2 bằng âm 10'],
  ['12 ÷ -3 = -4', '12 chia âm 3 bằng âm 4'],
  ['5 + -2 = 3', '5 cộng âm 2 bằng 3'],
  ['3 kg và 15 cm', '3 ki lô gam và 15 xăng ti mét'],
  ['250 ml và 2 l', '250 mi li lít và 2 lít'],
  ['31500 ÷ 10000 = 3,15 (ha)', '31500 chia 10000 bằng 3,15 héc ta'],
  ['Đổi sang héc-ta.', 'Đổi sang héc ta.'],
  ['(1 HA + 2 ha) × 2', 'nhóm 1 héc ta cộng 2 héc ta, hết nhóm nhân 2'],
  ['Ha ha, em đếm được 3 hạt!', 'Ha ha, em đếm được 3 hạt!'],
  ['Điểm (M) nằm trong hình', 'Điểm M nằm trong hình'],
  ['gam, làm, lớp và 3kg', 'gam, làm, lớp và 3 ki lô gam'],
  ['5dm² và 3 mm³', '5 đề xi mét vuông và 3 mi li mét khối'],
  ['-3 + 2 = -1', 'âm 3 cộng 2 bằng âm 1'],
  ['Ngày 12/10/2026.', 'Ngày 12/10/2026.'],
  ['Giữ 3,5 và 20%.', 'Giữ 3,5 và 20 phần trăm .'],
])('pronounces %s without calculating or changing its numbers', (source, expected) => {
  expect(spokenMath(source)).toBe(expected);
});

it('keeps compound fraction operands and separates long speech without losing words', () => {
  expect(spokenMath('(7+44)/(24)')).toBe('phân số có tử số là 7 cộng 44, và mẫu số là 24');
  const text = 'Em đọc kỹ dữ kiện và thử giải thích bằng lời. '.repeat(40).trim();
  const chunks = narrationChunks([text, 'Giữ 3.5 cm.']);
  expect(chunks.every(chunk => chunk.length <= 420)).toBe(true);
  expect(chunks.join(' ')).toBe(text + ' Giữ 3.5 xăng ti mét .');
});

it('selects Vietnamese voices, prefers enhanced quality and never falls back to English', () => {
  const voice = (identifier: string, language: string, quality = 'Default', name = identifier) => ({ identifier, language, quality, name } as Voice);
  const voices = vietnameseVoices([voice('english', 'en-US', 'Enhanced'), voice('a', 'vi_VN'),
    voice('b', 'vi-VN', 'Enhanced', 'Microsoft HoaiMy Natural'), voice('b', 'vi-VN', 'Enhanced')]);
  expect(voices.map(item => item.identifier)).toEqual(['b', 'a']);
  expect(voiceLabel(voices[0], 0)).toBe('Giọng nữ');
  expect(vietnameseVoices([voice('english', 'en-US')])).toEqual([]);
  expect(vietnameseVoices(Array.from({ length: 11 }, (_, i) => voice(`vi-${i}`, 'vi-VN')))).toHaveLength(2);
});
