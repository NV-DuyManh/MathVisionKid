import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { HintSheetContent } from '../features/tutoring/HintSheetContent';
import { FractionExplorer } from '../features/tutoring/FractionExplorer';
import { buildHintVisual, type HintVisual } from '../features/tutoring/hintVisualModel';

const orchard = 'Vườn có 1/3 số cây táo, 2/5 số cây xoài. Còn lại là cam. Hỏi số cây cam chiếm bao nhiêu phần?';

describe('verified hint illustrations', () => {
  it.each([[1, 3], [2, 5], [3, 4]])('uses source fraction %s/%s dynamically', (numerator, denominator) => {
    const value = `${numerator}/${denominator}`;
    expect(buildHintVisual(`Biểu diễn phân số ${value}.`, value)).toEqual({
      kind: 'fractions', values: [{ numerator, denominator }],
    });
  });

  it.each([
    [orchard, '1 − (1/3 + 2/5)', 15],
    ['Tính 3/4 − 1/2 ?', '3/4 − 1/2', 4],
    ['Tính 1/6 + 1/8 = ?', '1/6 + 1/8', 24],
  ])('uses a shared grid for source operands in %s', (source, expression, denominator) => {
    expect(buildHintVisual(source, expression)).toMatchObject({ kind: 'fractions', commonDenominator: denominator });
  });

  it.each([
    ['Tính 3 × 4', '3 × 4', { kind: 'array', rows: 3, columns: 4 }],
    ['Có 3 hộp, mỗi hộp có 4 bút.', '4 × 3', { kind: 'array', rows: 3, columns: 4 }],
    ['Có 12 viên bi, chia đều cho 3 bạn.', '12 ÷ 3', { kind: 'sharing', amount: 12, groups: 3 }],
    ['Tính 12 ÷ 3', '12/3', { kind: 'sharing', amount: 12, groups: 3 }],
    ['Chia đều 18 quả cam vào 6 hộp.', '18/6', { kind: 'sharing', amount: 18, groups: 6 }],
    ['Chia đều 14 viên bi cho 3 bạn. Còn dư bao nhiêu?', '14/3', { kind: 'sharing', amount: 14, groups: 3, allowsRemainder: true }],
    ['Lan có 8 viên bi. Bạn ấy mua thêm 3 viên bi.', '8 + 3', { kind: 'relation', mode: 'add', initial: 8, change: 3 }],
    ['Lan có 12 quả táo. Bạn ấy cho đi 4 quả táo.', '12 − 4', { kind: 'relation', mode: 'remove', initial: 12, change: 4 }],
  ])('models the quantities and relation found in %s', (source, expression, model) => {
    expect(buildHintVisual(source, expression)).toEqual(model);
  });

  it.each([
    [orchard, ''],
    ['Có 1/3 cây táo, [?] cây xoài.', '1/3 + 2/5'],
    [orchard, '1/3 + 3/4'],
    ['Tô 1/0 hình.', '1/0'],
    ['Tô 2/25 hình.', '2/25'],
    ['Ngày 2/5 có 3 hộp.', '2/5'],
    ['Có − 1/3.', '1/3'],
    ['Có 3,5 hộp, mỗi hộp có 4 bút.', '5 × 4'],
    ['Tính diện tích hình chữ nhật dài 3 m và rộng 4 m.', '3 × 4'],
    ['Có 12 viên bi, mỗi túi 3 viên. Cần bao nhiêu túi?', '12 ÷ 3'],
    ['Có 12 viên bi, mỗi túi 3 viên. Cần bao nhiêu túi?', '12/3'],
    ['Tính 14 ÷ 3', '14/3'],
    ['Lan có 8 viên bi. Bạn ấy mua thêm 3 hộp bi.', '8 + 3'],
    ['Có 3 hộp, mỗi hộp có 4 bút.', '3 × 4 = 12'],
  ])('falls back for unclear or unsupported source %s', (source, expression) => {
    expect(buildHintVisual(source, expression)).toBeNull();
  });
});

let view: TestRenderer.ReactTestRenderer;
function render(visual: HintVisual | null, key = 'lesson-a') {
  const next = <HintSheetContent key={key} hint="Em tìm các phần bằng nhau." visual={visual} children={null} />;
  act(() => { if (view) view.update(next); else view = TestRenderer.create(next); });
}
const control = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const press = (label: string) => act(() => control(label).props.onPress());
afterEach(() => { if (view) act(() => view.unmount()); view = undefined as unknown as TestRenderer.ReactTestRenderer; });

it('visualizes the original fractions one at a time and aligns operands without solving the step', () => {
  render(buildHintVisual(orchard, '1 − (1/3 + 2/5)'));
  expect(view.root.findAllByType(FractionExplorer)[0].props).toMatchObject({ numerator: 1, denominator: 3 });
  press('Phần 1 trong 3 phần bằng nhau của hình nguyên 1');
  press('Kiểm tra phần em chọn');
  expect(text()).toContain('đúng với tử số 1');
  press('Xem phân số 2 phần 5');
  expect(view.root.findAllByType(FractionExplorer)[0].props).toMatchObject({ numerator: 2, denominator: 5 });
  expect(control('Phần 1 trong 5 phần bằng nhau của hình nguyên 1').props.accessibilityState.checked).toBe(false);
  press('Xem hai phân số cùng mẫu');
  expect(view.root.findAllByProps({ accessibilityLabel: '2 phần 5 bằng 6 phần 15' }).length).toBeGreaterThan(0);
  expect(JSON.stringify(view.toJSON())).not.toContain('4/15');
});

it('offers concrete feedback about arrays without displaying the product', () => {
  render({ kind: 'array', rows: 2, columns: 3 });
  press('Kiểm tra cách xếp');
  expect(text()).toContain('Em cần xếp thêm 2 hàng');
  press('Thêm một hàng');
  press('Thêm một hàng');
  expect(control('Thêm một hàng').props.disabled).toBe(true);
  press('Kiểm tra cách xếp');
  expect(text()).toContain('Em đếm hoặc tính số chấm của tất cả');
  expect(text()).not.toMatch(/\b6\b/);
});

it('keeps a valid total during taps and checks equally shared groups', () => {
  render({ kind: 'sharing', amount: 4, groups: 2 });
  press('Kiểm tra cách chia');
  expect(text()).toContain('Vẫn còn chấm chưa chia');
  const first = control('Nhóm 1, có 0 chấm').props.onPress;
  act(() => { for (let i = 0; i < 6; i++) first(); });
  expect(control('Nhóm 1, có 4 chấm').props.disabled).toBe(true);
  press('Kiểm tra cách chia');
  expect(text()).toContain('chưa bằng nhau');
  press('Chia lại');
  for (let index = 0; index < 2; index++) {
    press(`Nhóm 1, có ${index} chấm`);
    press(`Nhóm 2, có ${index} chấm`);
  }
  press('Kiểm tra cách chia');
  expect(text()).toContain('Các nhóm có cùng số chấm');
});

it('checks a remainder after equal sharing and allows undo', () => {
  render({ kind: 'sharing', amount: 7, groups: 3, allowsRemainder: true });
  for (let count = 0; count < 2; count++) {
    for (let group = 1; group <= 3; group++) press(`Nhóm ${group}, có ${count} chấm`);
  }
  press('Kiểm tra cách chia');
  expect(text()).toContain('Các nhóm bằng nhau. Không đủ chấm để chia thêm một lượt.');
  press('Bỏ lượt cuối');
  expect(text()).toContain('Còn 2 chấm chưa chia');
  press('Kiểm tra cách chia');
  expect(text()).toContain('chưa bằng nhau');
});

it('shows a relationship with an unknown and clears yesterday’s interaction when the lesson key changes', () => {
  render({ kind: 'relation', initial: 8, change: 3, mode: 'add' });
  expect(text()).toContain('Tất cả ?');
  expect(text()).not.toMatch(/\b11\b/);
  render({ kind: 'fractions', values: [{ numerator: 1, denominator: 3 }] }, 'lesson-other');
  press('Phần 1 trong 3 phần bằng nhau của hình nguyên 1');
  render({ kind: 'fractions', values: [{ numerator: 1, denominator: 3 }] }, 'account-other');
  expect(control('Phần 1 trong 3 phần bằng nhau của hình nguyên 1').props.accessibilityState.checked).toBe(false);
});

it('renders the existing hint when it cannot justify a diagram', () => {
  render(null);
  expect(text()).toContain('Em tìm các phần bằng nhau.');
  expect(view.root.findAllByType(FractionExplorer)).toHaveLength(0);
});
