import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { LessonListening } from '../features/tutoring/LessonListening';
import { LessonNarration } from '../features/tutoring/LessonNarration';
import { TutorService } from '../features/tutoring/api/TutorService';

jest.mock('../features/tutoring/LessonNarration', () => ({ LessonNarration: () => null }));
jest.mock('../features/tutoring/api/TutorService', () => ({ TutorService: { askLesson: jest.fn() } }));
const step = { kind: 'MATH' as const, title: 'Gộp hai phần cây', explanation: 'Gộp các phần cùng kích thước.', question: 'Em sẽ gộp thế nào?', expression: '1/3 + 2/5', choices: [], unit: '', workExcerpt: '' };
const props = { scope: 'pupil:session:0', sessionId: 'session-visual-00000001', revision: 0, stepIndex: 0, step, paragraphs: ['Giảng bước đang học.'], onReturn: jest.fn() };
let view: TestRenderer.ReactTestRenderer;
const text = () => view.root.findAllByType('Text' as any).map(n => String(n.props.children)).join(' ');
const button = (label: string) => view.root.findAll(n => n.props.accessibilityLabel === label && n.props.onPress)[0];
const press = async (label: string) => { await act(async () => button(label).props.onPress()); };
const render = async (overrides = {}) => { await act(async () => { view = TestRenderer.create(<LessonListening {...props} {...overrides} />); }); };
beforeEach(() => { jest.clearAllMocks(); (TutorService.askLesson as jest.Mock).mockResolvedValue({ answer: 'Các phần phải cùng kích thước.', spokenExplanation: 'Em tưởng tượng chia lại cùng một hình để các phần bằng nhau rồi mới gộp.', followUp: 'Các phần cần giống nhau ở đâu?', guarded: false }); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('offers a check-in after listening and asks only the selected difficulty on the current owned step', async () => {
  await render();
  expect(button('Em chưa hiểu')).toBeUndefined();
  act(() => view.root.findByType(LessonNarration).props.onFinished());
  await press('Em chưa hiểu');
  expect(text()).toContain('Chọn chỗ em còn vướng');
  expect(TutorService.askLesson).not.toHaveBeenCalled();
  await press('Vì sao phải quy đồng?');
  expect(TutorService.askLesson).not.toHaveBeenCalled();
  expect(button('Vì sao phải quy đồng?').props['aria-pressed']).toBe(true);
  await press('Xem giải thích nhé!');
  expect(TutorService.askLesson).toHaveBeenCalledWith({ sessionId: props.sessionId, revision: 0, stepIndex: 0, question: expect.stringContaining('quy đồng') }, expect.anything());
  expect(text()).toContain('Các phần phải cùng kích thước.');
  const narration = view.root.findByType(LessonNarration);
  expect(narration.props.paragraphs[0]).toContain('cùng một hình');
  expect(text()).not.toContain('cùng một hình');
  act(() => narration.props.onFinished());
  await press('Em đã hiểu');
  expect(props.onReturn).toHaveBeenCalledTimes(1);
});

it('allows reading first, retains retryable choices on failure and never displays private provider errors', async () => {
  (TutorService.askLesson as jest.Mock).mockRejectedValue(new Error('localhost secret-key'));
  await render(); await press('Em đã đọc lời giảng'); await press('Em chưa hiểu');
  await press('Vì sao phải quy đồng?');
  await press('Xem giải thích nhé!');
  expect(text()).toContain('Chưa giải thích được lúc này');
  expect(text()).not.toContain('secret-key');
  await press('Thử giải thích lại');
  expect(TutorService.askLesson).toHaveBeenCalledTimes(2);
});

it('aborts a pending explanation when scope changes and ignores a late response', async () => {
  let resolve!: (value: unknown) => void;
  (TutorService.askLesson as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await render(); await press('Em đã đọc lời giảng'); await press('Em chưa hiểu');
  await press('Vì sao phải quy đồng?');
  act(() => { void button('Xem giải thích nhé!').props.onPress(); });
  const signal = (TutorService.askLesson as jest.Mock).mock.calls[0][1];
  await act(async () => view.update(<LessonListening {...props} scope="other-pupil:step:1" revision={1} stepIndex={1} />));
  expect(signal.aborted).toBe(true);
  await act(async () => resolve({ answer: 'OLD ANSWER', spokenExplanation: 'OLD AUDIO', followUp: '', guarded: false }));
  expect(text()).not.toContain('OLD ANSWER');
});

it('uses reading choices for an understanding step and does not invent a fraction difficulty', async () => {
  await render({ step: { ...step, kind: 'UNDERSTAND', expression: '' } });
  await press('Em đã đọc lời giảng'); await press('Em chưa hiểu');
  expect(button('Vì sao phải quy đồng?')).toBeUndefined();
  expect(button('Đề bài đã cho biết gì?')).toBeDefined();
});
