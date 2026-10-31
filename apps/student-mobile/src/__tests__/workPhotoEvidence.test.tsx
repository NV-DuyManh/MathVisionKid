import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Image, Platform, StyleSheet } from 'react-native';
import { MathText } from '../components/domain/MathText';
import { COLORS } from '../constants/theme';
import type { NotebookLine } from '../features/tutoring/api/TutorService';
import { WorkPhotoEvidence, WorkPhotoEvidenceRow } from '../features/tutoring/WorkPhotoEvidence';

const URI = 'file:///my-work.jpg';
const lines: NotebookLine[] = [
  { text: '  12 + 3 = 16  ', box: [100, 200, 700, 300], uncertain: false },
  { text: '2 × 3 = 6', box: null, uncertain: false },
  { text: '6 × [?] = 12', box: [100, 400, 800, 550], uncertain: true },
];
const rows: WorkPhotoEvidenceRow[] = [
  { lineIndex: 0, sourceText: '12 + 3 = 16', status: 'FIX', feedback: 'Em nhìn lại phép cộng ở dòng này.', hints: ['Em đếm thêm 3 từ 12 nhé.'] },
  { lineIndex: 1, sourceText: '2 × 3 = 6', status: 'OK', feedback: 'Em đã tính đúng hai nhóm, mỗi nhóm có 3.', hints: [] },
  { lineIndex: 2, sourceText: '6 × [?] = 12', status: 'FIX', feedback: 'Không được kết luận sai từ chữ chưa rõ.', hints: ['Không được gợi ý sửa từ chữ chưa rõ.'] },
];
const choose = jest.fn();
const loads: { uri: string; success: (width: number, height: number) => void; fail: () => void }[] = [];
let view: TestRenderer.ReactTestRenderer;
const props = { imageUri: URI, lines, rows, selectedLine: null as number | null, onSelectLine: choose };
const render = (changes: Partial<React.ComponentProps<typeof WorkPhotoEvidence>> = {}) => {
  act(() => { view = TestRenderer.create(<WorkPhotoEvidence {...props} {...changes} />); });
};
const update = (changes: Partial<React.ComponentProps<typeof WorkPhotoEvidence>>) => {
  act(() => { view.update(<WorkPhotoEvidence {...props} {...changes} />); });
};
const image = () => view.root.findAllByType(Image)[0];
const byId = (id: string) => view.root.findAll(node => node.props.testID === id)[0];
const controls = () => view.root.findAll(node => node.props.accessibilityRole === 'button'
  && typeof node.props.onPress === 'function' && node.props.testID?.startsWith('work-evidence-line-'));
const region = (index: number) => byId(`work-evidence-region-${index}`);
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const load = (width = 1200, height = 2400, uri = URI) => {
  act(() => loads.filter(request => request.uri === uri).at(-1)!.success(width, height));
};

it('focuses correction regions and rows while never inventing a position for an unlocated error', () => {
  render({ issuesOnly: true, rows: rows.map((row, index) => index === 1 ? { ...row, status: 'FIX' } : row),
    lines: lines.map((line, index) => index === 0 ? { ...line, uncertain: false } : line) });
  load();
  expect(region(0)).toBeDefined();
  expect(region(1)).toBeUndefined();
  expect(text()).toContain('Chưa xác định được vị trí một số dòng cần sửa');
  update({ issuesOnly: true }); load();
  expect(byId('work-evidence-line-1')).toBeUndefined();
  expect(byId('work-evidence-line-0')).toBeDefined();
});
beforeEach(() => {
  jest.clearAllMocks(); loads.length = 0;
  jest.spyOn(Image, 'getSize').mockImplementation((uri, success, fail) => {
    loads.push({ uri, success, fail: fail as () => void });
  });
});
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('can show the highlighted photo first and keep line choices in a separate detail section', () => {
  render({ presentation: 'photo' }); load();
  expect(region(0)).toBeDefined(); expect(controls()).toHaveLength(0);
  act(() => view.unmount()); loads.length = 0;
  render({ presentation: 'lines' });
  expect(loads).toHaveLength(0); expect(image()).toBeUndefined(); expect(controls()).toHaveLength(3);
  expect(region(0)).toBeUndefined();
});

it('keeps all source lines in order and waits for this photo before placing highlights', () => {
  render();
  expect(image().props.source).toEqual({ uri: URI });
  expect(Image.getSize).toHaveBeenCalledWith(URI, expect.any(Function), expect.any(Function));
  expect(controls()).toHaveLength(3);
  expect(controls().map(control => control.props.accessibilityLabel)).toEqual([
    'Dòng 1: 12 + 3 = 16. Cùng sửa bước này.',
    'Dòng 2: 2 × 3 = 6. Đã kiểm tra đúng.',
    'Dòng 3: 6 × [?] = 12. Cần đối chiếu.',
  ]);
  expect(view.root.findAllByType(MathText).map(node => node.props.children)).toEqual(lines.map(line => line.text.trim()));
  expect(region(0)).toBeUndefined();
  expect(choose).not.toHaveBeenCalled();
  expect(text()).not.toContain(rows[0].feedback);
});

it.each([[1200, 2400], [200, 5000], [4000, 600]])(
  'keeps the full %s by %s photo and its overlays on the same undistorted canvas', (width, height) => {
    render({ selectedLine: 0 });
    load(width, height);
    const frame = StyleSheet.flatten(byId('work-evidence-photo-frame').props.style);
    expect(frame.aspectRatio).toBe(width / height);
    expect(frame.maxWidth).toBe(Math.min(640, 480 * width / height));
    expect(frame.width).toBe('100%');
    expect(frame.height).toBeUndefined();
    expect(image().props.resizeMode).toBe('contain');
    expect(StyleSheet.flatten(image().props.style)).toMatchObject({ position: 'absolute', top: 0, right: 0, bottom: 0, left: 0 });
    expect(StyleSheet.flatten(region(0).props.style)).toMatchObject({
      left: '10%', top: '20%', width: '60%', height: '10%', borderColor: '#8C5900', borderWidth: 4,
    });
    expect(region(0).findAllByType('Text' as any).some(node => node.props.children === 1)).toBe(true);
    const marker = region(0).findAll(node => node.props.style && StyleSheet.flatten(node.props.style).height === 20)[0];
    expect(StyleSheet.flatten(marker.props.style).top).toBe(-20);
  },
);

it.each([null, [100, 100, 100, 300], [300, 100, 100, 300], [-1, 0, 100, 100],
  [0, 0, 1001, 100], [0, 0, NaN, 100], [0, 0, Infinity, 100], [0, 0, 100], [0, 0, 100.5, 100]].map(box => [box]))(
  'keeps a readable line control when its source box is missing or invalid: %s', box => {
    render({ lines: [{ ...lines[0], box: box as NotebookLine['box'] }], rows: [rows[0]], selectedLine: 0 });
    load();
    expect(region(0)).toBeUndefined();
    expect(controls()).toHaveLength(1);
    expect(controls()[0].props.accessibilityLabel).toContain(lines[0].text.trim());
    expect(controls()[0].props.accessibilityLabel).toContain('Cùng sửa bước này');
    act(() => controls()[0].props.onPress());
    expect(choose).toHaveBeenCalledWith(0);
  },
);

it('never turns an uncertain source line into a red correction or confident praise', () => {
  render({ selectedLine: 2 }); load();
  expect(controls()[2].props.accessibilityLabel).toContain('Cần đối chiếu');
  expect(StyleSheet.flatten(region(2).props.style).borderColor).not.toBe(COLORS.errorText);
  expect(text()).not.toContain(rows[2].feedback);
  expect(text()).not.toContain(rows[2].hints[0]);
  update({ selectedLine: 2, rows: [{ ...rows[2], status: 'OK', feedback: 'Không được khen khi chưa đọc rõ.' }] });
  expect(text()).not.toContain('Không được khen khi chưa đọc rõ.');
  expect(controls()[2].props.accessibilityLabel).toContain('Cần đối chiếu');
});

it('paints a translucent yellow band directly over only the confirmed correction region', () => {
  render({ selectedLine: 0 }); load();
  const correction = StyleSheet.flatten(region(0).props.style);
  expect(correction.backgroundColor).toBe('rgba(255, 221, 0, 0.32)');
  expect(correction.borderColor).toBe('#8C5900');
  expect(correction.opacity).toBeUndefined();
  expect(StyleSheet.flatten(region(2).props.style).backgroundColor).toBe('transparent');
  expect(text()).toContain('Vùng bôi vàng');
  expect(image().props.source).toEqual({ uri: URI });
  expect(choose).not.toHaveBeenCalled();
});

it('accepts only one exact index and trimmed-source match, without guessing across duplicate text', () => {
  const source: NotebookLine[] = [
    { text: '  1/3 + 1/3 = 2/3  ', box: [0, 0, 1000, 100], uncertain: false },
    { text: '1/3 + 1/3 = 2/3', box: [0, 200, 1000, 300], uncertain: false },
    { text: '2 + 2 = 4', box: null, uncertain: false },
  ];
  const review: WorkPhotoEvidenceRow[] = [
    { lineIndex: 0, sourceText: source[0].text.trim(), status: 'OK', feedback: 'Đã đối chiếu dòng thứ nhất.', hints: [] },
    { lineIndex: 1, sourceText: '1/3+1/3=2/3', status: 'FIX', feedback: 'Không được ghép gần giống.', hints: [] },
    { lineIndex: 8, sourceText: source[2].text, status: 'FIX', feedback: 'Không được chuyển nhận xét sang dòng khác.', hints: [] },
  ];
  render({ lines: source, rows: review, selectedLine: 1 }); load();
  expect(controls()[0].props.accessibilityLabel).toContain('Đã kiểm tra đúng');
  expect(controls()[1].props.accessibilityLabel).toContain('Cần đối chiếu');
  expect(controls()[2].props.accessibilityLabel).toContain('Cần đối chiếu');
  expect(view.root.findAllByType(MathText).some(node => node.props.children === source[0].text.trim())).toBe(true);
  update({ lines: source, rows: [review[0], { ...review[0], status: 'FIX' }], selectedLine: 0 });
  expect(controls()[0].props.accessibilityLabel).toContain('Cần đối chiếu');
});

it.each([
  ['\uFEFF2 + 3 = 5\uFEFF', '\uFEFF2 + 3 = 5\uFEFF', '\uFEFF2 + 3 = 5\uFEFF', true],
  ['\uFEFF2 + 3 = 5\uFEFF', '2 + 3 = 5', '\uFEFF2 + 3 = 5\uFEFF', false],
  ['\u001F2 + 3 = 5\u001F', '2 + 3 = 5', '2 + 3 = 5', true],
  ['\u001F2 + 3 = 5\u001F', '\u001F2 + 3 = 5\u001F', '2 + 3 = 5', false],
])('requires the shared Unicode source echo for %j and %j', (source, echo, normalized, matches) => {
  render({
    lines: [{ text: source as string, box: [100, 200, 700, 300], uncertain: false }],
    rows: [{ ...rows[0], sourceText: echo as string, status: 'OK' }], selectedLine: 0,
  });
  load();
  expect(view.root.findAllByType(MathText)[0].props.children).toBe(normalized);
  expect(controls()[0].props.accessibilityLabel).toContain(matches ? 'Đã kiểm tra đúng' : 'Cần đối chiếu');
  expect(StyleSheet.flatten(region(0).props.style)).toMatchObject({
    left: '10%', top: '20%', width: '60%', height: '10%',
    borderColor: matches ? COLORS.success : COLORS.primaryDark,
  });
});

it('keeps selection controlled by the parent and leaves feedback and progressive hints to it', () => {
  render({ selectedLine: 1 });
  expect(controls()[1].props['aria-pressed']).toBe(true);
  expect(text()).not.toContain(rows[1].feedback);
  expect(text()).not.toContain(rows[0].feedback);
  expect(text()).not.toContain(rows[0].hints[0]);
  act(() => controls()[0].props.onPress());
  expect(choose).toHaveBeenCalledWith(0);
  expect(controls()[1].props['aria-pressed']).toBe(true);
  expect(controls()[0].props['aria-pressed']).toBe(false);
  update({ selectedLine: 0 });
  expect(controls()[0].props['aria-pressed']).toBe(true);
  expect(controls()[1].props['aria-pressed']).toBe(false);
  expect(text()).not.toContain(rows[0].feedback);
  expect(text()).not.toContain(rows[0].hints[0]);
  expect(text()).not.toContain(rows[1].feedback);
});

it('ignores old photo load and error callbacks after the source changes', () => {
  render();
  const old = image().props;
  const oldSize = loads[0];
  const next = 'file:///another-work.jpg';
  update({ imageUri: next });
  act(() => oldSize.success(100, 900));
  expect(region(0)).toBeUndefined();
  load(900, 300, next);
  expect(StyleSheet.flatten(byId('work-evidence-photo-frame').props.style).aspectRatio).toBe(3);
  act(() => old.onError({ nativeEvent: { error: 'old photo failed' } }));
  act(() => oldSize.fail());
  expect(image().props.source.uri).toBe(next);
  expect(region(0)).toBeDefined();
  expect(StyleSheet.flatten(byId('work-evidence-photo-frame').props.style).aspectRatio).toBe(3);
});

it('keeps the text on failure and reloads without accepting old dimensions or late success', () => {
  render(); load();
  const old = image().props;
  const oldSize = loads[0];
  act(() => old.onError({ nativeEvent: { error: 'image failed' } }));
  expect(region(0)).toBeUndefined();
  expect(controls()).toHaveLength(3);
  expect(text()).toContain('Em vẫn có thể xem từng dòng bên dưới.');
  act(() => oldSize.success(1200, 2400));
  expect(region(0)).toBeUndefined();
  const retry = view.root.findAll(node => node.props.accessibilityLabel === 'Mở lại ảnh bài làm' && node.props.onPress)[0];
  act(() => retry.props.onPress());
  expect(image().props.source.uri).toBe(URI);
  expect(region(0)).toBeUndefined();
  act(() => oldSize.success(1200, 2400));
  act(() => oldSize.fail());
  expect(region(0)).toBeUndefined();
  load(1800, 900);
  expect(region(0)).toBeDefined();
  expect(StyleSheet.flatten(byId('work-evidence-photo-frame').props.style).aspectRatio).toBe(2);
});

it.each([[0, 900], [900, -1], [NaN, 900], [Infinity, 900], [Number.MAX_VALUE, Number.MIN_VALUE]])(
  'does not place highlights from invalid source dimensions %s by %s', (width, height) => {
    render(); load(width, height);
    expect(region(0)).toBeUndefined();
  },
);

it('hides the image and its regions if natural dimensions fail to load', () => {
  render();
  act(() => loads[0].fail());
  expect(image()).toBeUndefined();
  expect(region(0)).toBeUndefined();
  expect(controls()).toHaveLength(3);
  expect(text()).toContain('Em vẫn có thể xem từng dòng bên dưới.');
});

it('provides named 48px controls, visible keyboard focus, pressed state and decorative image regions', () => {
  jest.replaceProperty(Platform, 'OS', 'web');
  render({ selectedLine: 0 }); load();
  const first = controls()[0];
  expect(first.props.focusable).toBe(true);
  expect(first.props['aria-pressed']).toBe(true);
  expect(controls()[1].props['aria-pressed']).toBe(false);
  expect(StyleSheet.flatten(first.props.style({ pressed: false })).minHeight).toBe(48);
  expect(text()).toContain('Cùng sửa bước này');
  expect(text()).toContain('Đã kiểm tra đúng');
  expect(text()).toContain('Cần đối chiếu');
  const imageErrorHandler = image().props.onError;
  act(() => first.props.onFocus());
  expect(StyleSheet.flatten(controls()[0].props.style({ pressed: false })).borderStyle).toBe('dashed');
  expect(image().props.onError).toBe(imageErrorHandler);
  expect(region(0).props.pointerEvents).toBe('none');
  expect(region(0).props.accessible).toBe(false);
  expect(region(0).props['aria-hidden']).toBe(true);
  expect(region(0).props.focusable).toBe(false);
  expect(region(0).props.importantForAccessibility).toBe('no-hide-descendants');
});

it('handles a missing image while retaining source text and emits no grading or network request', () => {
  const fetch = jest.spyOn(global, 'fetch').mockImplementation(jest.fn());
  render({ imageUri: '', selectedLine: 0 });
  expect(image()).toBeUndefined();
  expect(controls()).toHaveLength(3);
  expect(Image.getSize).not.toHaveBeenCalled();
  act(() => controls()[2].props.onPress());
  expect(choose).toHaveBeenCalledWith(2);
  expect(fetch).not.toHaveBeenCalled();
});
