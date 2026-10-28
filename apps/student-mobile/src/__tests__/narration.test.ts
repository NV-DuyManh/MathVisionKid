import { completedNarration, narrationChunks, spokenMath, stepNarration, vietnameseVoices, voiceLabel } from '../features/tutoring/narration';
import type { LessonStep } from '../features/tutoring/api/TutorService';
import type { Voice } from 'expo-speech';

const step: LessonStep = { title: 'Tìm phần còn lại', explanation: 'Cả vườn gồm các phần đã cho và phần còn lại.',
  question: 'Em tìm phần còn lại thế nào?', guidance: ['Đọc lại các phần đã biết.', 'Lấy cả vườn trừ phần đã biết.'],
  choices: [], expression: '1-11/15', unit: 'phần', workExcerpt: 'Không được đọc nguyên ảnh ở đây.', solutionSentence: 'Câu lời giải chưa mở.' };

it('builds richer current narration only from opened teaching, never hidden expression or raw work', () => {
  const paragraphs = stepNarration(step, 'Gợi ý vừa được mở.');
  expect(paragraphs).toEqual([step.explanation, ...step.guidance!, 'Gợi ý vừa được mở.', step.question]);
  expect(paragraphs.join(' ')).not.toContain(step.expression);
  expect(paragraphs.join(' ')).not.toContain(step.workExcerpt);
  expect(paragraphs.join(' ')).not.toContain(step.solutionSentence);
  expect(stepNarration({ ...step, guidance: [step.explanation, step.question] })).toEqual([step.explanation, step.question]);
});

it('can narrate the calculation only after the step is earned', () => {
  const completed = { title: 'Tổng số bút', solutionSentence: 'Số bút có tất cả là:', expression: '12+5', answer: '17',
    unit: 'bút', explanation: 'Gộp các nhóm bút.', guidance: ['Em kiểm tra lại tổng.'], calculationDetails: ['Cộng hàng đơn vị: 2 + 5 = 7, giữ nguyên hàng chục.'] };
  expect(completedNarration([completed])).toEqual([completed.solutionSentence, '12+5 = 17 (bút)', completed.explanation]);
});

it.each([
  ['(1)/(3) + (2)/(5) = (11)/(15)', '1 phần 3 cộng 2 phần 5 bằng 11 phần 15'],
  ['1 - 11/15 = 4/15', '1 trừ 11 phần 15 bằng 4 phần 15'],
  ['12 × 2 : 3 = 8 (cm²)', '12 nhân 2 chia 3 bằng 8 xăng ti mét vuông'],
  ['(12 + 8) × 2 = 40', 'mở ngoặc 12 cộng 8 đóng ngoặc nhân 2 bằng 40'],
  ['5 × -2 = -10', '5 nhân âm 2 bằng âm 10'],
  ['5 * -2 = -10', '5 nhân âm 2 bằng âm 10'],
  ['12 ÷ -3 = -4', '12 chia âm 3 bằng âm 4'],
  ['5 + -2 = 3', '5 cộng âm 2 bằng 3'],
  ['3 kg và 15 cm', '3 ki lô gam và 15 xăng ti mét'],
  ['250 ml và 2 l', '250 mi li lít và 2 lít'],
  ['Điểm (M) nằm trong hình', 'Điểm mở ngoặc M đóng ngoặc nằm trong hình'],
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
  expect(voiceLabel(voices[0], 0)).toBe('Hoài My');
  expect(vietnameseVoices([voice('english', 'en-US')])).toEqual([]);
  expect(vietnameseVoices(Array.from({ length: 11 }, (_, i) => voice(`vi-${i}`, 'vi-VN')))).toHaveLength(2);
});
