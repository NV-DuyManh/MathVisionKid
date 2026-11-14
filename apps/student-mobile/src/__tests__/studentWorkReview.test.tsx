import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StudentWorkReview } from '../features/tutoring/StudentWorkReview';
import { TutorService } from '../features/tutoring/api/TutorService';

let mockBlur: (() => void) | undefined;
let mockRefocus: (() => void) | undefined;
let mockDeferFocus = false;
jest.mock('expo-router', () => ({ useRouter: () => ({ push: jest.fn(), replace: jest.fn() }), useFocusEffect: (fn: () => (() => void)) => require('react').useEffect(() => {
  mockRefocus = () => { mockBlur = fn(); };
  if (!mockDeferFocus) mockRefocus();
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
beforeEach(() => { mockDeferFocus = false; jest.clearAllMocks(); (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => makeResult(sourceId)); });
afterEach(() => { if (view) act(() => view.unmount()); });

it('starts the confirmed review when navigation focus arrives after mounting', async () => {
  mockDeferFocus = true;
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} autoStart />); });
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
  await act(async () => mockRefocus?.());
  expect(TutorService.reviewWork).toHaveBeenCalledTimes(1);
  expect(text()).toContain('Kết quả bài em làm');
});

it('requires both confirmations and never starts a review automatically', async () => {
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} enabled={false} />); });
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
  expect(button('Nhận xét bài em làm').props.disabled).toBe(true);
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(TutorService.reviewWork).not.toHaveBeenCalled();
});

it('shows missing work in orange without presenting a wording correction', async () => {
  const missing = 'Em còn thiếu bước tìm tổng số cây trong vườn từ số cây cam và phần tương ứng.';
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId),
    complete: false, missingPart: missing,
    rows: [
      { lineIndex: 0, sourceText: 'Số cây trong vườn là:', status: 'FIX', errorKind: 'EXPLANATION',
        feedback: 'Em mới tìm phần cây táo và xoài, chưa phải tổng số cây.', hints: ['Em sửa tên đại lượng.'] },
      { lineIndex: 1, sourceText: '1/3 + 2/5 = 11/15', status: 'OK', errorKind: 'NONE', feedback: 'Phép cộng phù hợp.', hints: [] },
    ] }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props}
    workText={'Số cây trong vườn là:\n1/3 + 2/5 = 11/15'} autoStart />); });
  expect(text()).toContain('Bài làm thiếu · Chưa làm xong');
  expect(text()).toContain(missing);
  expect(text()).not.toContain('Cần xem lại lời dẫn');
  expect(button('Em nhập dòng vừa sửa')).toBeUndefined();
  expect(text()).not.toContain('60');
  const evidence = view.root.findAllByType('WorkPhotoEvidence' as any);
  expect(evidence[0].props.incompleteInfo.isIncomplete).toBe(true);
});

it('keeps work after a quota response without starting a retry loop or inventing a verdict', async () => {
  (TutorService.reviewWork as jest.Mock).mockRejectedValue({ response: { status: 503, data: { error: { code: 'TUTOR_RATE_LIMITED' } } } });
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} autoStart />); });
  expect(text()).toContain('Mình cần chờ một chút');
  expect(text()).not.toContain('Em làm tốt rồi');
  expect(TutorService.reviewWork).toHaveBeenCalledTimes(1);
  expect(button('Nhận xét bài em làm')).toBeDefined();
});

it('offers a retry when every row is unverified without asking the pupil to rewrite a heading', async () => {
  const workText = 'Bài giải:\n45 x 3/5 = 28 (học sinh)';
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId, 'NEEDS_REVIEW'),
    rows: workText.split('\n').map((sourceText, lineIndex) => ({ sourceText, lineIndex, status: 'UNSURE', feedback: 'Cần đối chiếu.', hints: [] })),
  }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} workText={workText} autoStart />); });
  expect(button('Thử nhận xét lại')).toBeDefined();
  expect(button('Em nhập dòng vừa sửa')).toBeUndefined();
  expect(button('Gợi ý sửa dòng này')).toBeUndefined();
  expect(text()).not.toContain('Bài giải:');
});

it('reports verified calculations without showing unverified prose as an error or celebrating the whole solution', async () => {
  const workText = 'Bài giải:\nSố bút là:\n12 + 5 = 17';
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId, 'NEEDS_REVIEW'),
    arithmeticVerified: true, rows: workText.split('\n').map((sourceText, lineIndex) => ({ sourceText, lineIndex,
      status: 'UNSURE', feedback: 'Cần đối chiếu.', hints: [] })),
  }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} workText={workText} autoStart />); });
  expect(text()).toContain('Các phép tính em viết đều đúng');
  expect(text()).not.toContain('Cần đối chiếu');
  expect(button('Em nhập dòng vừa sửa')).toBeUndefined();
  expect(view.root.findAllByProps({ testID: 'correct-answer-feedback' })).toHaveLength(0);
});

it('starts a review once after explicit confirmation, without asking for a second review click', async () => {
  let resolve: (value: any) => void = () => {};
  (TutorService.reviewWork as jest.Mock).mockImplementation(() => new Promise(done => { resolve = done; }));
  await act(async () => { view = TestRenderer.create(<React.StrictMode><StudentWorkReview {...props} autoStart /></React.StrictMode>); });
  expect(TutorService.reviewWork).toHaveBeenCalledTimes(1);
  const request = (TutorService.reviewWork as jest.Mock).mock.calls[0][0];
  expect(request).toEqual(expect.objectContaining({ problemConfirmed: true, workConfirmed: true, problemText: props.problemText, workText: props.workText }));
  expect(button('Nhận xét bài em làm')).toBeUndefined();
  await act(async () => resolve(makeResult(request.sourceId, 'CORRECT')));
  expect(button('Hoàn tất nhận xét')).toBeDefined();
  expect(button('Chụp lại bài em đã sửa')).toBeUndefined();
  expect(button('Gợi ý sửa dòng này')).toBeUndefined();
  expect(button('Hoàn tất xem nhận xét')).toBeUndefined();
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
  act(() => button('Nhận xét lại bài').props.onPress());
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
  expect(view.root.findAllByType('WorkPhotoEvidence' as any)).toHaveLength(0);
});

it.each(['11/15', '(11)/(15)', '\\frac{11}{15}', '11⁄15'])('shows stacked inputs for %s and saves all affected rows in one confirmation', async fraction => {
  const work = ['1/3 + 2/5 = 11/15', `1 - ${fraction} = (3)/(15) (số cây)`, '16 : (3)/(15) = 80 (cây)'];
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId),
    rows: work.map((sourceText, lineIndex) => ({ sourceText, lineIndex, status: lineIndex === 0 ? 'OK' : 'FIX',
      errorKind: ['NONE', 'CALCULATION', 'DEPENDENT'][lineIndex], feedback: 'Em đối chiếu lại bước này.', hints: [] })),
  }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} workText={work.join('\n')}
    lines={work.map(text => ({ text, uncertain: false, box: null }))} autoStart />); });
  const evidence = view.root.findAllByType('WorkPhotoEvidence' as any).find(item => item.props.presentation === 'lines');
  expect(evidence?.props).toMatchObject({ issuesOnly: true, showFeedback: true });
  expect(button('Xem tất cả các dòng')).toBeUndefined();
  act(() => button('Em nhập các dòng vừa sửa').props.onPress());
  const field = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onChangeText)[0];
  expect(field('Dòng 1 em vừa sửa')).toBeUndefined();
  expect(field('Dòng 2 em vừa sửa')).toBeUndefined();
  const expressions = view.root.findAll(node => node.type === 'View' && node.props.testID === 'work-line-expression');
  const fractionsIn = (expression: TestRenderer.ReactTestInstance) =>
    expression.findAll(node => node.type === 'View' && node.props.testID === 'work-line-fraction');
  expect(expressions.map(expression => fractionsIn(expression).length)).toEqual([2, 1]);
  expect(field('Dòng 2 em vừa sửa, tử số 1').props.value).toBe('11');
  expect(field('Dòng 2 em vừa sửa, mẫu số 1').props.value).toBe('15');
  expect(field('Dòng 2 em vừa sửa, mẫu số 2').props.value).toBe('15');
  act(() => field('Dòng 2 em vừa sửa, mẫu số 2').props.onChangeText(''));
  expect(field('Dòng 2 em vừa sửa, mẫu số 2').props.value).toBe('');
  act(() => field('Dòng 2 em vừa sửa, tử số 2').props.onChangeText('4'));
  act(() => field('Dòng 2 em vừa sửa, mẫu số 2').props.onChangeText('15'));
  expect(button('Nhận xét lại bài').props.disabled).toBe(true);
  act(() => field('Dòng 3 em vừa sửa, tử số 1').props.onChangeText('4'));
  act(() => field('Dòng 3 em vừa sửa, phần 2').props.onChangeText(' = 60 (cây)'));
  act(() => button('Nhận xét lại bài').props.onPress());
  expect(props.onReviseWork).toHaveBeenCalledTimes(1);
  expect(props.onReviseWork).toHaveBeenCalledWith(`${work[0]}\n1 - ${fraction} = 4/15 (số cây)\n16 : 4/15 = 60 (cây)`);
  expect(TutorService.reviewWork).toHaveBeenCalledTimes(1);
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
  expect(text()).not.toContain('Các phép tính em cần sửa');
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
  expect(text()).toContain('Các phép tính em cần sửa');
});

it('keeps unchanged BOM source unchanged and rejects invisible whitespace as a rewrite', async () => {
  const workText = '\ufeff12 + 5 = 18\ufeff';
  (TutorService.reviewWork as jest.Mock).mockImplementation(async ({ sourceId }) => ({ ...makeResult(sourceId), rows: [{
    sourceText: workText, lineIndex: 0, status: 'FIX', feedback: 'Em kiểm tra phép cộng nhé.', hints: [] }] }));
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} workText={workText} />); });
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  act(() => button('Em nhập dòng vừa sửa').props.onPress());
  expect(button('Nhận xét lại bài').props.disabled).toBe(true);
  act(() => button('Nhận xét lại bài').props.onPress());
  expect(props.onReviseWork).not.toHaveBeenCalled();
  const input = view.root.findAll(node => node.props.accessibilityLabel === 'Dòng em vừa sửa' && node.props.onChangeText)[0];
  act(() => input.props.onChangeText('\u001f\u0085'));
  expect(button('Nhận xét lại bài').props.disabled).toBe(true);
});

it('never presents an old photo as the current source after a text-only correction', async () => {
  await act(async () => { view = TestRenderer.create(<StudentWorkReview {...props} photoCurrent={false} />); });
  expect(text()).not.toContain('Ảnh trước khi sửa vẫn được giữ');
  await act(async () => button('Nhận xét bài em làm').props.onPress());
  expect(view.root.findByType('WorkPhotoEvidence' as any).props.imageUri).toBe('');
  expect(button('Chụp lại bài em đã sửa')).toBeDefined();
  expect(props.onCaptureWork).not.toHaveBeenCalled();
});
