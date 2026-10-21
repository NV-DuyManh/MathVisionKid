import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StudentWorkReview } from '../features/tutoring/StudentWorkReview';
import { TutorService } from '../features/tutoring/api/TutorService';

let mockBlur: (() => void) | undefined;
let mockRefocus: (() => void) | undefined;
jest.mock('expo-router', () => ({ useFocusEffect: (fn: () => (() => void)) => require('react').useEffect(() => {
  mockRefocus = () => { mockBlur = fn(); };
  mockRefocus();
  return () => mockBlur?.();
}, [fn]) }));
jest.mock('../features/tutoring/api/TutorService', () => ({ ...jest.requireActual('../features/tutoring/api/TutorService'), TutorService: { reviewWork: jest.fn() } }));
jest.mock('../features/tutoring/WorkPhotoEvidence', () => ({ WorkPhotoEvidence: 'WorkPhotoEvidence' }));
const props = { problemText: 'Lan có 12 bút, thêm 5 bút. Hỏi có tất cả bao nhiêu bút?', workText: 'Số bút là:\n12 + 5 = 18',
  imageUri: 'file:///masked-work.jpg', lines: [], enabled: true, onReviseWork: jest.fn(), onCaptureWork: jest.fn() };
const makeResult = (sourceId: string, status = 'NEEDS_REVISION') => ({ sourceId, status, summary: 'Cùng xem phép tính em đã viết.',
  praise: status === 'CORRECT' ? 'Em đã dùng phép cộng phù hợp và giữ đơn vị.' : '', nextAction: 'Em đọc lại dòng đã chọn.',
  alternative: status === 'CORRECT' ? 'Em thử giải thích cách gộp nhóm bằng lời nhé.' : '',
  rows: props.workText.split('\n').map((sourceText, lineIndex) => ({ sourceText, lineIndex,
    status: status === 'CORRECT' ? 'OK' : lineIndex === 1 ? 'FIX' : 'UNSURE', feedback: 'Đối chiếu hai nhóm với phép tính nhé.',
    hints: status !== 'CORRECT' && lineIndex === 1 ? ['Cộng hàng đơn vị trước.', 'Kiểm tra lại bằng cách tách nhóm.'] : [] })) });
let view: TestRenderer.ReactTestRenderer;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
beforeEach(() => { jest.clearAllMocks(); (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => makeResult(sourceId)); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('requires both confirmations and never starts a review automatically', async () => {
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} enabled={false} />); });
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
  expect(button('Nhận xét bài em làm').props.disabled).toBe(true);
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
});

it('shows progressive correction hints, asks for the pupil rewrite and keeps photo unchanged', async () => {
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(text()).toContain('Dòng 2');
  expect(text()).not.toContain('Cộng hàng đơn vị trước.');
  act(() => button('Gợi ý sửa dòng này').props.onPress());
  expect(text()).toContain('Cộng hàng đơn vị trước.');
  act(() => button('Gợi ý rõ hơn').props.onPress());
  expect(text()).toContain('Kiểm tra lại bằng cách tách nhóm.');
  expect(button('Đã mở đủ gợi ý dòng này').props.disabled).toBe(true);
  expect(TutorService.reviewWork).toHaveBeenCalledTimes(1);
  act(() => button('Em nhập dòng vừa sửa').props.onPress());
  const input = view.root.findAll(node => node.props.accessibilityLabel === 'Dòng em vừa sửa' && node.props.onChangeText)[0];
  expect(input.props.value).toBe('12 + 5 = 18');
  act(() => input.props.onChangeText('12 + 5 = 17'));
  act(() => button('Dùng dòng em đã sửa').props.onPress());
  expect(props.onReviseWork).toHaveBeenCalledWith('Số bút là:\n12 + 5 = 17');
  expect(props.onCaptureWork).not.toHaveBeenCalled();
});

it('offers source-grounded praise and opens alternative reasoning only on request', async () => {
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => makeResult(sourceId, 'CORRECT'));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(text()).toContain('Em đã dùng phép cộng phù hợp và giữ đơn vị.');
  expect(text()).not.toContain('Em thử giải thích cách gộp nhóm bằng lời nhé.');
  expect(button('Khám phá thêm một cách nghĩ')).toBeUndefined();
  act(() => button('Xem nhận xét chi tiết').props.onPress());
  act(() => button('Khám phá thêm một cách nghĩ').props.onPress());
  expect(text()).toContain('Em thử giải thích cách gộp nhóm bằng lời nhé.');
});

it('aborts an old-source request and does not attach its review to new text', async () => {
  let resolve: (value: any) => void = () => {};
  (TutorService.reviewWork as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  const [request, signal] = (TutorService.reviewWork as jest.Mock).mock.calls[0];
  await act(async () => view.update(<StudentWorkReview {...props} workText="12 + 5 = 17" />));
  expect(signal.aborted).toBe(true);
  await act(async () => resolve(makeResult(request.sourceId)));
  expect(text()).not.toContain('Cùng xem phép tính em đã viết.');
});

it('keeps a safe retry and recapture path after provider failure without a verdict', async () => {
  (TutorService.reviewWork as jest.Mock).mockRejectedValue({ response: { status: 503, data: 'private backend detail' } });
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(text()).toContain('Chưa nhận xét được lúc này');
  expect(text()).not.toContain('private backend detail');
  expect(text()).not.toContain('Em làm đúng rồi');
  act(() => button('Chụp lại bài em đã sửa').props.onPress());
  expect(props.onCaptureWork).toHaveBeenCalledTimes(1);
});

it('can retry after a retained screen loses focus and ignores its old response', async () => {
  let resolve: (value: any) => void = () => {};
  (TutorService.reviewWork as jest.Mock).mockImplementationOnce(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  const [request, signal] = (TutorService.reviewWork as jest.Mock).mock.calls[0];
  act(() => mockBlur?.());
  act(() => mockRefocus?.());
  expect(signal.aborted).toBe(true);
  expect(button('Nhận xét bài em làm').props.disabled).toBe(false);
  await act(async () => resolve(makeResult(request.sourceId)));
  expect(text()).not.toContain('Cùng xem phép tính em đã viết.');
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(text()).toContain('Cùng xem phép tính em đã viết.');
});

it('keeps unchanged BOM source unchanged and rejects invisible whitespace as a rewrite', async () => {
  const workText = '\ufeff12 + 5 = 18\ufeff';
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId), rows: [{
    sourceText: workText, lineIndex: 0, status: 'FIX', feedback: 'Em kiểm tra phép cộng nhé.', hints: [] }] }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} workText={workText} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  act(() => button('Em nhập dòng vừa sửa').props.onPress());
  expect(button('Dùng dòng em đã sửa').props.disabled).toBe(true);
  act(() => button('Dùng dòng em đã sửa').props.onPress());
  expect(props.onReviseWork).not.toHaveBeenCalled();
  const input = view.root.findAll(node => node.props.accessibilityLabel === 'Dòng em vừa sửa' && node.props.onChangeText)[0];
  act(() => input.props.onChangeText('\u001f\u0085'));
  expect(button('Dùng dòng em đã sửa').props.disabled).toBe(true);
});

it('never presents an old photo as the current source after a text-only correction', async () => {
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} photoCurrent={false} />); });
  expect(text()).toContain('Ảnh trước khi sửa vẫn được giữ');
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(view.root.findByType('WorkPhotoEvidence' as any).props.imageUri).toBe('');
  expect(props.onCaptureWork).not.toHaveBeenCalled();
});
