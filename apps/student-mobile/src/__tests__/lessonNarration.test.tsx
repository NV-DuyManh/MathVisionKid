import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { AppState } from 'react-native';
import * as Speech from '../features/tutoring/speechOutput';
import { LessonNarration } from '../features/tutoring/LessonNarration';
import { voicePreferences } from '../features/tutoring/voicePreferences';
import { readSpeechPreferences } from '../features/tutoring/speechPreferences';
import { warmSpeechSegments } from '../features/tutoring/speechCache';

jest.mock('expo-router', () => ({ useFocusEffect: (callback: () => void) => require('react').useEffect(callback, [callback]) }));
jest.mock('../features/tutoring/speechOutput', () => ({ speak: jest.fn(), stop: jest.fn().mockResolvedValue(undefined), getAvailableVoicesAsync: jest.fn() }));
jest.mock('../features/tutoring/speechCache', () => ({ warmSpeechSegments: jest.fn().mockResolvedValue(new Uint8Array()) }));
jest.mock('../features/tutoring/voicePreferences', () => ({ voicePreferences: { get: jest.fn().mockResolvedValue(null), set: jest.fn().mockResolvedValue(undefined) } }));
const VI = { identifier: 'vi-good', name: 'HoaiMy Natural', language: 'vi-VN', quality: 'Enhanced' };
const paragraphs = ['Em cần chia các phần bằng nhau.', 'Vì các phần cùng kích thước nên mới có thể gộp lại.', 'Em tự thực hiện nhé.'];
let view: TestRenderer.ReactTestRenderer;
let appState: (state: string) => void;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const render = async (props = {}) => {
  await act(async () => { view = TestRenderer.create(<LessonNarration scope="owner:session:step:hint" paragraphs={paragraphs} {...props} />); });
};
beforeEach(() => {
  jest.clearAllMocks();
  (voicePreferences.get as jest.Mock).mockReset().mockResolvedValue(null);
  (Speech.getAvailableVoicesAsync as jest.Mock).mockResolvedValue([VI]);
  jest.spyOn(AppState, 'addEventListener').mockImplementation((_, callback: any) => { appState = callback; return { remove: jest.fn() }; });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('never autoplays, keeps writing concise and exposes the longer matching transcript on request', async () => {
  await render();
  expect(Speech.speak).not.toHaveBeenCalled();
  expect(text()).not.toContain(paragraphs[1]);
  act(() => button('Đọc lời giảng chi tiết').props.onPress());
  expect(text()).toContain(paragraphs[1]);
  expect(button('Đọc lời giảng chi tiết').props['aria-expanded']).toBe(true);
  expect(button('Đọc lời giảng chi tiết').props['aria-controls']).toBeTruthy();
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  expect(Speech.speak).toHaveBeenCalledWith(paragraphs.join(' '), expect.objectContaining({ voice: VI.identifier, language: 'vi-VN', rate: 1.15 }));
  expect(text()).toContain('Đang chuẩn bị lời đọc tiếng Việt');
  act(() => (Speech.speak as jest.Mock).mock.calls[0][1].onStart());
  expect(text()).toContain('Đang đọc lời giảng');
  act(() => (Speech.speak as jest.Mock).mock.calls[0][1].onDone());
  expect(Speech.speak).toHaveBeenCalledTimes(1);
  expect(button('Nghe lại lời giảng')).toBeTruthy();
});

it('advances the audio look-ahead as a long narration moves to its next clip', async () => {
  await render({ paragraphs: ['Em đọc kỹ dữ kiện trong đề rồi tự chọn phép tính phù hợp. '.repeat(45)] });
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  const initial = (warmSpeechSegments as jest.Mock).mock.calls[0][0];
  expect(initial.length).toBeGreaterThan(4);
  act(() => (Speech.speak as jest.Mock).mock.calls[0][1].onDone());
  expect(warmSpeechSegments).toHaveBeenLastCalledWith(initial.slice(1), VI.identifier);
});

it('reports completed explanation only after the final utterance, never a preview or cancelled callback', async () => {
  const onFinished = jest.fn();
  await render({ onFinished });
  act(() => button('Giọng đọc và tốc độ').props.onPress());
  act(() => button('Nghe thử giọng').props.onPress());
  act(() => (Speech.speak as jest.Mock).mock.calls.at(-1)![1].onDone());
  expect(onFinished).not.toHaveBeenCalled();
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  act(() => (Speech.speak as jest.Mock).mock.calls.at(-1)![1].onDone());
  expect(onFinished).toHaveBeenCalledTimes(1);
  act(() => button('Nghe lại lời giảng').props.onPress());
  const stale = (Speech.speak as jest.Mock).mock.calls.at(-1)![1];
  act(() => button('Dừng nghe').props.onPress());
  act(() => stale.onDone());
  expect(onFinished).toHaveBeenCalledTimes(1);
});

it('stops immediately and ignores old speech callbacks when scope or opened content changes', async () => {
  await render(); act(() => button('Nghe giảng kỹ hơn').props.onPress());
  const old = (Speech.speak as jest.Mock).mock.calls[0][1];
  await act(async () => { view.update(<LessonNarration scope="owner:session:step:next-hint" paragraphs={['Nội dung mới đã mở.']} />); });
  expect(Speech.stop).toHaveBeenCalledTimes(1);
  act(() => { old.onDone(); old.onError(new Error('private details')); });
  expect(Speech.speak).toHaveBeenCalledTimes(1);
  expect(text()).not.toContain('private details');
  expect(text()).not.toContain('Chưa phát được');
});

it.each(['background', 'inactive'])('stops when the app becomes %s and does not resume automatically', async state => {
  await render(); act(() => button('Nghe giảng kỹ hơn').props.onPress());
  const old = (Speech.speak as jest.Mock).mock.calls[0][1];
  act(() => appState(state));
  expect(Speech.stop).toHaveBeenCalledTimes(1);
  act(() => old.onDone());
  expect(Speech.speak).toHaveBeenCalledTimes(1);
});

it('stops when busy or unmounted and does not queue repeated taps', async () => {
  await render();
  act(() => { button('Nghe giảng kỹ hơn').props.onPress(); button('Nghe giảng kỹ hơn').props.onPress(); });
  expect(Speech.speak).toHaveBeenCalledTimes(1);
  await act(async () => { view.update(<LessonNarration scope="owner:session:step:hint" paragraphs={paragraphs} disabled />); });
  expect(Speech.stop).toHaveBeenCalledTimes(1);
  await act(async () => { view.update(<LessonNarration scope="owner:session:step:hint" paragraphs={paragraphs} />); });
  await act(async () => button('Nghe giảng kỹ hơn').props.onPress());
  act(() => view.unmount());
  expect(Speech.stop).toHaveBeenCalledTimes(2);
});

it('keeps the full text usable with no Vietnamese voice and allows an inventory retry', async () => {
  (Speech.getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ ...VI, language: 'en-US' }]);
  await render();
  expect(button('Nghe giảng kỹ hơn').props.disabled).toBe(true);
  act(() => button('Đọc lời giảng chi tiết').props.onPress());
  expect(text()).toContain(paragraphs[2]);
  (Speech.getAvailableVoicesAsync as jest.Mock).mockResolvedValue([VI]);
  await act(async () => button('Tìm lại giọng đọc').props.onPress());
  expect(button('Nghe giảng kỹ hơn').props.disabled).toBe(false);
});

it('offers voice preview and pace changes without exposing any lesson answer', async () => {
  await render(); act(() => button('Giọng đọc và tốc độ').props.onPress());
  act(() => button('Tốc độ Chậm').props.onPress());
  act(() => button('Nghe thử giọng').props.onPress());
  expect(Speech.speak).toHaveBeenCalledWith(expect.stringContaining('Chào em'), expect.objectContaining({ rate: 1 }));
  expect((Speech.speak as jest.Mock).mock.calls[0][0]).not.toContain(paragraphs[0]);
  act(() => button('Dừng nghe').props.onPress());
  expect(Speech.stop).toHaveBeenCalled();
});

it('offers all three faster paces and stores the selected rate', async () => {
  await render(); act(() => button('Giọng đọc và tốc độ').props.onPress());
  for (const [label, rate] of [['Chậm', 1], ['Vừa', 1.15], ['Nhanh', 1.3]] as const) {
    act(() => button(`Tốc độ ${label}`).props.onPress());
    expect(voicePreferences.set).toHaveBeenLastCalledWith(JSON.stringify({ voiceId: VI.identifier, rate }));
    act(() => button('Nghe thử giọng').props.onPress());
    expect(Speech.speak).toHaveBeenLastCalledWith(expect.any(String), expect.objectContaining({ rate }));
    act(() => (Speech.speak as jest.Mock).mock.calls.at(-1)![1].onDone());
  }
});

it.each([[.75, 1], [.9, 1.15], [1.05, 1.3], [1, 1], [1.15, 1.15], [1.3, 1.3]])(
  'restores saved rate %s as %s for narration and preparation', async (saved, expected) => {
    (voicePreferences.get as jest.Mock).mockResolvedValue(JSON.stringify({ voiceId: 'vi-VN-HoaiMyNeural', rate: saved }));
    expect(await readSpeechPreferences()).toEqual({ voiceId: 'vi-VN-HoaiMyNeural', rate: expected });
  },
);

it.each(['not-json', '{}', 'null', '{"voiceId":"en-US-other","rate":2}', '{"rate":"1.3"}'])(
  'uses the same Vietnamese defaults for invalid saved preferences: %s', async saved => {
    (voicePreferences.get as jest.Mock).mockResolvedValue(saved);
    expect(await readSpeechPreferences()).toEqual({ voiceId: 'vi-VN-NamMinhNeural', rate: 1.15 });
  },
);

it('waits for saved preferences before enabling playback so it matches prepared audio', async () => {
  let restore!: (value: string) => void;
  (voicePreferences.get as jest.Mock).mockImplementation(() => new Promise(resolve => { restore = resolve; }));
  (Speech.getAvailableVoicesAsync as jest.Mock).mockResolvedValue([{ ...VI, identifier: 'vi-VN-HoaiMyNeural' }]);
  await render();
  expect(button('Nghe giảng kỹ hơn').props.disabled).toBe(true);
  await act(async () => restore(JSON.stringify({ voiceId: 'vi-VN-HoaiMyNeural', rate: 1.3 })));
  expect(button('Nghe giảng kỹ hơn').props.disabled).toBe(false);
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  expect(Speech.speak).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ voice: 'vi-VN-HoaiMyNeural', rate: 1.3 }));
});

it('hides provider errors and invalidates callbacks so a failed utterance cannot continue', async () => {
  await render(); act(() => button('Nghe giảng kỹ hơn').props.onPress());
  const old = (Speech.speak as jest.Mock).mock.calls[0][1];
  act(() => old.onError(new Error('localhost private error')));
  expect(text()).toContain('Chưa phát được lời giảng');
  expect(text()).not.toContain('localhost');
  act(() => old.onDone()); expect(Speech.speak).toHaveBeenCalledTimes(1);
});

it('waits for a previous native cancellation before starting another narration', async () => {
  let finishStop!: () => void;
  (Speech.stop as jest.Mock).mockImplementationOnce(() => new Promise<void>(resolve => { finishStop = resolve; }));
  await render(); act(() => button('Nghe giảng kỹ hơn').props.onPress());
  act(() => button('Dừng nghe').props.onPress());
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  expect(Speech.speak).toHaveBeenCalledTimes(1);
  await act(async () => finishStop());
  expect(Speech.speak).toHaveBeenCalledTimes(2);
});

it('does not start queued native speech after the source changes during cancellation', async () => {
  let finishStop!: () => void;
  (Speech.stop as jest.Mock).mockImplementationOnce(() => new Promise<void>(resolve => { finishStop = resolve; }));
  await render(); act(() => button('Nghe giảng kỹ hơn').props.onPress());
  act(() => button('Dừng nghe').props.onPress());
  act(() => button('Nghe giảng kỹ hơn').props.onPress());
  await act(async () => view.update(<LessonNarration scope="new-owner:session" paragraphs={['Bài học khác.']} />));
  await act(async () => finishStop());
  expect(Speech.speak).toHaveBeenCalledTimes(1);
});
it('offers exactly two ranked voices and a compact single-control reply player', async () => {
  (Speech.getAvailableVoicesAsync as jest.Mock).mockResolvedValue(Array.from({ length: 11 }, (_, index) => ({
    identifier: `vi-${index}`, name: `Vietnamese ${index}`, language: 'vi-VN', quality: index < 2 ? 'Enhanced' : 'Default',
  })));
  await render(); act(() => button('Giọng đọc và tốc độ').props.onPress());
  expect(view.root.findAll(node => typeof node.props.onPress === 'function' && /^Chọn Giọng Việt/.test(node.props.accessibilityLabel || ''))).toHaveLength(2);
  act(() => view.unmount()); await render({ compact: true });
  expect(button('Giọng đọc và tốc độ')).toBeUndefined();
  act(() => button('Nghe giải thích').props.onPress());
  expect(button('Dừng nghe giải thích')).toBeDefined();
});
