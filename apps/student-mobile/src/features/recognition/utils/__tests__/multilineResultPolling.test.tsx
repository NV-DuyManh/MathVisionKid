import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Alert, TextInput } from 'react-native';
import MultilineResultScreen from '../../../../app/recognition/multiline-result';
import { RecognitionService, MultilineTrialResult } from '../../api/RecognitionService';

const mockRouter = { replace: jest.fn(), push: jest.fn(), back: jest.fn() };
let mockTrialId = 'poll-trial';
jest.mock('expo-router', () => ({ useRouter: () => mockRouter, useLocalSearchParams: () => ({ trialId: mockTrialId }) }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Icon' }));
jest.mock('../../state/recognitionDraftStore', () => ({ logFlowDomain: jest.fn() }));
jest.mock('../../analytics/recognitionAnalyticsStore', () => ({ recognitionAnalyticsStore: { computeTrialAnalytics: jest.fn(), setCurrentTrialAnalytics: jest.fn() } }));
jest.mock('../../../../utils/mathSolutionEvaluator', () => ({ evaluateMathSolution: () => null }));
jest.mock('../../components/RecognitionProgress', () => ({ RecognitionProgress: () => null }));
jest.mock('../../api/RecognitionService', () => ({ RecognitionService: { getCachedTrial: jest.fn(), getMultilineTrial: jest.fn(), submitLineFeedback: jest.fn() }, normalizeOcrError: () => ({ message: 'Nội dung đã thay đổi. Em hãy kiểm tra lại.' }) }));

const pending = {
  trialId: 'poll-trial', lines: [{ lineId: 'first', lineOrder: 1, predictedText: 'Em yêu mùa hè', rawOcrText: 'Em yêu mùa hè', verdict: 'UNVERIFIED', groqStatus: null, geminiStatus: null, suggestions: [] }],
} as unknown as MultilineTrialResult;
const settled = { ...pending, lines: [{ ...pending.lines[0], predictedText: 'Em yêu mùa hè.', groqStatus: 'SUCCESS', geminiStatus: 'SUCCESS', groqSuggestion: 'Em yêu mùa hè.', geminiSuggestion: 'Em yêu mùa hè.' }] } as MultilineTrialResult;

let renderer: TestRenderer.ReactTestRenderer;
async function mount() {
  await act(async () => { renderer = TestRenderer.create(<MultilineResultScreen />); });
}
async function advance(ms = 3000) {
  await act(async () => { jest.advanceTimersByTime(ms); });
}
function text() {
  return renderer.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
}
function button(label: string) {
  return renderer.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
}

beforeEach(() => {
  jest.useFakeTimers();
  mockTrialId = pending.trialId;
  jest.spyOn(console, 'log').mockImplementation(() => {});
  (RecognitionService.getCachedTrial as jest.Mock).mockReturnValue(pending);
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValue(pending);
  (RecognitionService.submitLineFeedback as jest.Mock).mockReset();
});
afterEach(() => {
  act(() => renderer?.unmount());
  jest.clearAllTimers();
  jest.useRealTimers();
  jest.restoreAllMocks();
  jest.clearAllMocks();
});

test('pending payload refreshes stop after 24 attempts even when state and editing change', async () => {
  await mount();
  expect(text()).toContain('trong khi chờ gợi ý');
  for (let i = 0; i < 24; i++) {
    if (i === 8) {
      act(() => button('Tự sửa chữ của dòng này').props.onPress());
      act(() => renderer.root.findByType(TextInput).props.onChangeText('Em tự viết lại'));
    }
    await advance();
  }
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(25); // Initial load + 24 refreshes.
  await advance(180000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(25);
  expect(renderer.root.findByType(TextInput).props.value).toBe('Em tự viết lại');
});

test('a delayed settled advisor response keeps active human text and stops polling', async () => {
  let resolve!: (value: MultilineTrialResult) => void;
  await mount();
  (RecognitionService.getMultilineTrial as jest.Mock).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
  await advance();
  act(() => button('Tự sửa chữ của dòng này').props.onPress());
  act(() => renderer.root.findByType(TextInput).props.onChangeText('Bài em đang tự sửa'));
  await advance(30000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(2); // No overlapping GET while one is pending.
  await act(async () => { resolve(settled); });
  expect(renderer.root.findByType(TextInput).props.value).toBe('Bài em đang tự sửa');
  expect(text()).not.toContain('trong khi chờ gợi ý');
  expect(text()).toContain('Gợi ý 1');
  await advance(90000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(2);
});

test('changing trial or unmounting discards a late response and schedules no further requests', async () => {
  let resolve!: (value: MultilineTrialResult) => void;
  await mount();
  (RecognitionService.getMultilineTrial as jest.Mock).mockImplementationOnce(() => new Promise(r => { resolve = r; }));
  await advance();
  const other = { ...pending, trialId: 'next-trial', lines: [{ ...pending.lines[0], groqStatus: 'SUCCESS', geminiStatus: 'SUCCESS' }] } as MultilineTrialResult;
  mockTrialId = other.trialId;
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValue(other);
  await act(async () => { renderer.update(<MultilineResultScreen />); });
  await act(async () => { resolve(settled); });
  await advance(90000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(3);
  expect(text()).not.toContain('Gợi ý 1');
  act(() => renderer.unmount());
  await advance(90000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(3);
});

test('CORRECT sends the exact visible text and a late pending feedback response cannot erase settled advisors', async () => {
  const staleFinal = { ...pending, lines: [{ ...pending.lines[0], finalText: 'Nội dung lưu cũ chưa được chọn' }] } as MultilineTrialResult;
  (RecognitionService.getCachedTrial as jest.Mock).mockReturnValue(staleFinal);
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValueOnce(staleFinal).mockResolvedValue(settled);
  let resolveFeedback!: (value: typeof pending.lines[0]) => void;
  (RecognitionService.submitLineFeedback as jest.Mock).mockImplementationOnce(() => new Promise(resolve => { resolveFeedback = resolve; }));
  await mount();
  await act(async () => { button('Xác nhận dòng này đúng').props.onPress(); });
  expect(RecognitionService.submitLineFeedback).toHaveBeenCalledWith(pending.trialId, 'first', 'CORRECT', 'Em yêu mùa hè');
  expect(text()).toContain('Đã xác nhận');
  await advance();
  expect(text()).toContain('Gợi ý 1');
  await act(async () => { resolveFeedback({ ...pending.lines[0], verdict: 'CORRECT', verifiedTextRaw: 'Em yêu mùa hè', predictedText: 'Em yêu mùa hè' }); });
  expect(text()).toContain('Gợi ý 1');
  act(() => button('Tự sửa chữ của dòng này').props.onPress());
  expect(renderer.root.findByType(TextInput).props.value).toBe('Em yêu mùa hè');
  await advance(90000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(2);
});

test('a rejected stale CORRECT rolls back its verdict while retaining advisor results received during the request', async () => {
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValueOnce(pending).mockResolvedValue(settled);
  let rejectFeedback!: (reason: unknown) => void;
  (RecognitionService.submitLineFeedback as jest.Mock).mockImplementationOnce(() => new Promise((_, reject) => { rejectFeedback = reject; }));
  await mount();
  await act(async () => { button('Xác nhận dòng này đúng').props.onPress(); });
  expect(RecognitionService.submitLineFeedback).toHaveBeenCalledWith(pending.trialId, 'first', 'CORRECT', 'Em yêu mùa hè');
  await advance();
  expect(text()).toContain('Gợi ý 1');
  await act(async () => { rejectFeedback({ response: { status: 400, data: { error: { code: 'DATA_INTEGRITY_ERROR' } } } }); });
  expect(text()).toContain('Chưa xác nhận');
  expect(text()).not.toContain('Đúng ✓');
  expect(text()).toContain('Gợi ý 1');
  expect(Alert.alert).toHaveBeenCalledWith('Chưa thể lưu phản hồi', 'Dòng chữ vừa có gợi ý mới. Em hãy chọn nội dung đúng hoặc tự sửa rồi xác nhận.');
  await advance(90000);
  expect(RecognitionService.getMultilineTrial).toHaveBeenCalledTimes(2);
});

test('an empty visible line requires editing before CORRECT can be submitted', async () => {
  const empty = { ...pending, lines: [{ ...pending.lines[0], rawOcrText: '', predictedText: '' }] } as MultilineTrialResult;
  (RecognitionService.getCachedTrial as jest.Mock).mockReturnValue(empty);
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValue(empty);
  jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  await mount();
  await act(async () => { button('Xác nhận dòng này đúng').props.onPress(); });
  expect(RecognitionService.submitLineFeedback).not.toHaveBeenCalled();
  expect(Alert.alert).toHaveBeenCalledWith('Chưa có nội dung', 'Em hãy tự sửa dòng chữ trước khi xác nhận nhé.');
});

test('confirming a displayed suggestion differing from the server prediction submits it as a correction', async () => {
  const suggested = { ...pending, lines: [{ ...pending.lines[0],
    selectedSource: 'SUGGESTION_1', groqStatus: 'SUCCESS', geminiStatus: 'UNAVAILABLE',
    groqSuggestion: 'Nội dung em đang đọc',
  }] } as MultilineTrialResult;
  (RecognitionService.getCachedTrial as jest.Mock).mockReturnValue(suggested);
  (RecognitionService.getMultilineTrial as jest.Mock).mockResolvedValue(suggested);
  (RecognitionService.submitLineFeedback as jest.Mock).mockResolvedValue({ ...suggested.lines[0],
    verdict: 'CORRECTED', verifiedTextRaw: 'Nội dung em đang đọc',
  });
  await mount();
  await act(async () => { button('Xác nhận dòng này đúng').props.onPress(); });
  expect(RecognitionService.submitLineFeedback).toHaveBeenCalledWith(pending.trialId, 'first', 'CORRECTED', 'Nội dung em đang đọc');
});
