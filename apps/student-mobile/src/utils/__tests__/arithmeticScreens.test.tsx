import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Text, View } from 'react-native';
import ProcessingScreen from '../../app/processing';
import TokenConfirmationScreen from '../../app/results/token-confirmation';
import CorrectScreen from '../../app/results/correct';
import ErrorHintScreen from '../../app/results/error-hint';
import { TokenConfirmationCard } from '../../components/domain/TokenConfirmationCard';
import { MathExpression } from '../../components/domain/MathExpression';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';
import { SubmissionStatus } from '../../types';
import { COLORS } from '../../constants/theme';

const mockRouter = { replace: jest.fn(), back: jest.fn() };
let mockParams: Record<string, string> = {};
const mockService = { uploadImage: jest.fn(), retrySubmission: jest.fn(), getSubmission: jest.fn(), confirmToken: jest.fn() };
jest.mock('expo-router', () => ({ useRouter: () => mockRouter, useLocalSearchParams: () => mockParams }));
jest.mock('../../services/api/SubmissionServiceFactory', () => ({ getSubmissionService: () => mockService }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: 'Icon' }));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
jest.mock('../../features/recognition/components/RecognitionProgress', () => ({ RecognitionProgress: 'RecognitionProgress' }));

let renderer: TestRenderer.ReactTestRenderer | undefined;
const valid = { id: 'actual-submission', status: SubmissionStatus.FEEDBACK_READY, validation: { isValid: true, diagnosisState: 'VALID' } };
const invalid = { ...valid, validation: { isValid: false, diagnosisState: 'INVALID' } };
const pending = { id: valid.id, status: SubmissionStatus.PROCESSING };
beforeEach(() => {
  jest.useFakeTimers();
  jest.spyOn(console, 'log').mockImplementation(() => {});
  recognitionDraftStore.setDraft({ rawUri: 'file:///raw.jpg', uri: 'file:///masked-crop.jpg', width: 200, height: 300, mimeType: 'image/jpeg', filename: 'crop.jpg', source: 'GALLERY', mode: 'ARITHMETIC' });
  mockParams = {};
  Object.values(mockService).forEach(mock => mock.mockReset());
  mockService.uploadImage.mockResolvedValue(pending);
  mockService.getSubmission.mockResolvedValue(valid);
});
afterEach(() => { act(() => renderer?.unmount()); renderer = undefined; jest.clearAllTimers(); jest.useRealTimers(); jest.restoreAllMocks(); jest.clearAllMocks(); recognitionDraftStore.clearDraft(); });
async function mount(Screen: React.ComponentType) { await act(async () => { renderer = TestRenderer.create(<Screen />); }); }
async function advance(ms = 2000) { await act(async () => { jest.advanceTimersByTime(ms); }); }
const text = () => renderer!.root.findAllByType(Text).map(node => String(node.props.children)).join(' ');

test.each([[invalid, '/results/error-hint'], [{ ...valid, validation: { isValid: false, diagnosisState: 'UNCERTAIN' } }, '/results/review-required']])('immediate FEEDBACK_READY uses actual validation, not unconditional success', async (returned, route) => {
  mockService.uploadImage.mockResolvedValue(returned);
  await mount(ProcessingScreen);
  expect(mockRouter.replace).toHaveBeenCalledWith(expect.objectContaining({ pathname: route }));
  expect(mockService.getSubmission).not.toHaveBeenCalled();
});

test('sequential processing stops at 45 attempts and retry reads the same submission without another upload', async () => {
  mockService.getSubmission.mockResolvedValue(pending);
  await mount(ProcessingScreen);
  for (let count = 0; count < 45; count++) await advance();
  expect(mockService.getSubmission).toHaveBeenCalledTimes(45);
  expect(text()).toContain('Bài vẫn đang được xử lý');
  await advance(180000);
  expect(mockService.getSubmission).toHaveBeenCalledTimes(45);
  mockService.getSubmission.mockResolvedValue(invalid);
  const retry = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Xem lại kết quả' && typeof node.props.onPress === 'function')[0];
  await act(async () => retry.props.onPress());
  expect(mockService.uploadImage).toHaveBeenCalledTimes(1);
  expect(mockRouter.replace).toHaveBeenCalledWith(expect.objectContaining({ pathname: '/results/error-hint' }));
});

test('cancellation aborts HTTP and suppresses navigation from a late upload response', async () => {
  let finish!: (value: typeof valid) => void;
  mockService.uploadImage.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await mount(ProcessingScreen);
  const signal = mockService.uploadImage.mock.calls[0][1];
  act(() => renderer!.root.findByType('RecognitionProgress' as any).props.onCancel());
  expect(signal.aborted).toBe(true);
  await act(async () => finish(valid));
  expect(mockRouter.back).toHaveBeenCalledTimes(1);
  expect(mockRouter.replace).not.toHaveBeenCalled();
});

test.each([CorrectScreen, ErrorHintScreen])('missing result never fabricates a calculation or grading claim', async Screen => {
  mockParams = { data: '{bad JSON' };
  await mount(Screen);
  expect(text()).toContain('Chưa có kết quả');
  expect(text()).not.toMatch(/458|276|734|724|Làm tốt lắm|đã phát hiện/);
});

test('confirmation selects one of two identical digits by tokenId, sends current job and safely routes a revalidated invalid result', async () => {
  mockParams = { id: 'actual-submission' };
  mockService.getSubmission.mockResolvedValue({ id: 'actual-submission', jobId: 'actual-job', status: SubmissionStatus.NEEDS_CONFIRMATION,
    recognizedExercise: { expression: '17 + 17 = 34', tokens: [{ tokenId: 'first-seven', value: '7', ambiguity: true, row: 0 }, { tokenId: 'second-seven', value: '7', ambiguity: true, row: 1 }] } });
  mockService.confirmToken.mockResolvedValue(invalid);
  await mount(TokenConfirmationScreen);
  const second = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Ký hiệu 2: 7' && typeof node.props.onPress === 'function')[0];
  act(() => second.props.onPress());
  await act(async () => renderer!.root.findByType(TokenConfirmationCard).props.onConfirm('3'));
  expect(mockService.confirmToken).toHaveBeenCalledWith('actual-submission', { jobId: 'actual-job', tokenId: 'second-seven', newClass: '3' }, expect.anything());
  expect(mockRouter.replace).toHaveBeenCalledWith(expect.objectContaining({ pathname: '/results/error-hint' }));
});

test('missing token identity does not display invented seven or offer confirmation', async () => {
  mockParams = { id: 'actual-submission' };
  mockService.getSubmission.mockResolvedValue({ id: 'actual-submission', status: SubmissionStatus.NEEDS_CONFIRMATION, ambiguousToken: { value: '7' } });
  await mount(TokenConfirmationScreen);
  expect(renderer!.root.findAllByType(TokenConfirmationCard)).toHaveLength(0);
  expect(mockRouter.replace).toHaveBeenCalledWith(expect.objectContaining({ pathname: '/results/review-required' }));
});

test('validator column zero highlights the rightmost units digit of a full-string result', () => {
  act(() => { renderer = TestRenderer.create(<MathExpression exercise={{ expression: '45 + 27 = 62' }} highlightIndex={0} />); });
  const units = renderer!.root.findAllByType(Text).find(node => node.props.children === '2')!;
  const tens = renderer!.root.findAllByType(Text).find(node => node.props.children === '6')!;
  expect(units.props.style).toEqual(expect.arrayContaining([expect.objectContaining({ color: COLORS.error })]));
  expect(tens.props.style.filter(Boolean)).toHaveLength(1);
});
