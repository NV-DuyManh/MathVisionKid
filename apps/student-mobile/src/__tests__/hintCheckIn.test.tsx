import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { HintCheckIn, hintConcept } from '../features/tutoring/HintCheckIn';

let view: TestRenderer.ReactTestRenderer;
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
const reduction = { expression: '675000/900', hint: 'Khi chia, có thể rút gọn: cả hai số đều chia hết cho trăm. Chia tử và mẫu cho trăm rồi tính tiếp sẽ dễ hơn.' };
const conversion = { expression: '45/4 × 6 × 10000', hint: 'Tính diện tích rồi nhân thêm mười nghìn để đổi ra xăng-ti-mét-vuông.', stepTitle: 'Diện tích căn phòng', unit: 'cm²' };

afterEach(() => { if (view) act(() => view.unmount()); });

it.each([['(−7) + 3', '+'], ['-7 × 3', '×'], ['12 − 5', '−'], ['12-5', '-']])(
  'teaches the binary operation in %s when no hint text was supplied', (expression, symbol) => {
    act(() => { view = TestRenderer.create(<HintCheckIn expression={expression} onReady={jest.fn()} />); });
    expect(text()).toContain(`Dấu ${symbol} có nghĩa gì?`);
  },
);

it('does not invent a subtraction check for a unary sign', () => {
  expect(hintConcept({ expression: '−7' })).toBeNull();
});

it('grounds addition and subtraction checks in grouping and taking-away hints', () => {
  const adding = hintConcept({ expression: '12 + 5', hint: 'Em gộp hai nhóm lại để biết tất cả có bao nhiêu.' })!;
  expect(adding.question).toBe('Dấu + có nghĩa gì?');
  expect(adding.correct).toBe('Gộp các nhóm lại');
  expect(adding.other).toBe('Bớt một nhóm đi');
  const subtracting = hintConcept({ expression: '12 − 5', hint: 'Bớt số đã cho để tìm phần còn lại.' })!;
  expect(subtracting.correct).toBe('Bớt một phần để tìm phần còn lại');
  expect(subtracting.question).not.toBe(adding.question);
  expect(hintConcept({ expression: '12 ÷ 5', hint: 'Em gộp hai nhóm lại.' })).toBeNull();
});

it('asks about unit conversion rather than the numerator merely because a fraction occurs in the expression', () => {
  const check = hintConcept(conversion)!;
  expect(check.question).toContain('hai diện tích');
  expect(check.correct).toBe('Đưa hai diện tích về cùng đơn vị');
  expect(check.question).not.toMatch(/Tử số|Mẫu số/);
  expect(hintConcept({ ...conversion, hint: 'Đổi diện tích căn phòng về xăng-ti-mét vuông.' })?.correct).toBe(check.correct);
});

it('asks about preserving the quotient when the current hint simplifies a division', () => {
  const check = hintConcept(reduction)!;
  expect(check.question).toContain('675000/900');
  expect(check.correct).toBe('Cả số bị chia và số chia');
  expect(check.why).toContain('thương không thay đổi');
  expect(check.question).not.toMatch(/Tử số|Mẫu số/);
  expect(hintConcept({ expression: '1/3 + 1/4', hint: 'Rút gọn bằng cách chia tử và mẫu.' })).toBeNull();
});

it('distinguishes the tile count hint from the unit conversion and reduction hints in the same lesson', () => {
  const check = hintConcept({ expression: '675000/900', hint: 'Cả nền phòng được lát kín bằng các viên gạch như nhau. Lấy tổng diện tích phòng chia cho diện tích một viên gạch sẽ ra số viên cần dùng.', unit: 'viên' })!;
  expect(check.correct).toBe('Diện tích nền nhà chia diện tích một viên gạch');
  expect(new Set([check.question, hintConcept(conversion)?.question, hintConcept(reduction)?.question]).size).toBe(3);
});

it('asks about the specific fraction concept named in the hint, independent of hint depth', () => {
  expect(hintConcept({ expression: '1/3', hint: 'Mẫu số cho biết hình nguyên chia thành những phần bằng nhau.' })?.question).toBe('Mẫu số cho biết điều gì?');
  expect(hintConcept({ expression: '1/3', hint: 'Tử số đếm số phần được lấy.' })?.question).toBe('Tử số cho biết điều gì?');
  expect(hintConcept({ expression: '1/3+1/4', hint: 'Quy đồng hai phân số khác mẫu.' })?.correct).toBe('Quy đồng để có cùng mẫu số');
});

it('keeps every answer visible, clearly marks the chosen wrong answer, and allows a retry before explicit continuation', () => {
  const ready = jest.fn();
  act(() => { view = TestRenderer.create(<HintCheckIn {...reduction} onReady={ready} />); });
  act(() => button('Chỉ số bị chia').props.onPress());
  expect(button('Chỉ số bị chia').props['aria-pressed']).toBe(true);
  expect(button('Chỉ số bị chia').props.accessibilityHint).toContain('chưa đúng');
  expect(button('Cả số bị chia và số chia').props.disabled).toBe(false);
  expect(text()).toContain('Đã chọn · Chưa đúng');
  expect(button('Em đã hiểu, để em thử')).toBeUndefined();
  act(() => button('Cả số bị chia và số chia').props.onPress());
  expect(button('Chỉ số bị chia')).toBeDefined();
  expect(button('Cả số bị chia và số chia').props['aria-pressed']).toBe(true);
  expect(text()).toContain('Đã chọn · Đúng');
  expect(ready).not.toHaveBeenCalled();
  expect(button('Chỉ số bị chia').props.disabled).toBe(true);
  act(() => button('Em đã hiểu, để em thử').props.onPress());
  expect(ready).toHaveBeenCalledTimes(1);
});

it('does not carry a selected answer into a new hint when the parent updates without a key', () => {
  const ready = jest.fn();
  act(() => { view = TestRenderer.create(<HintCheckIn {...reduction} onReady={ready} />); });
  act(() => button('Cả số bị chia và số chia').props.onPress());
  act(() => view.update(<HintCheckIn {...conversion} onReady={ready} />));
  expect(button('Em đã hiểu, để em thử')).toBeUndefined();
  expect(text()).not.toContain('Đã chọn');
  expect(button('Đưa hai diện tích về cùng đơn vị').props['aria-pressed']).toBe(false);
});

it('uses the current reading hint and does not ask the pupil to calculate', () => {
  const check = hintConcept({ expression: '', reading: true, hint: 'Đọc lại câu hỏi để tìm điều đề yêu cầu.' })!;
  expect(check.correct).toBe('Điều đề bài yêu cầu tìm');
  expect(hintConcept({ expression: '', reading: true, hint: 'Đối chiếu các dữ kiện đề cho biết.' })?.correct).toBe('Những thông tin đề bài đã cho');
});

it('omits a fabricated concept question when the hint is unrecognised and allows returning to the actual task', () => {
  const ready = jest.fn();
  act(() => { view = TestRenderer.create(<HintCheckIn expression="1/3" hint="Em thử vẽ sơ đồ như phần gợi ý." onReady={ready} />); });
  expect(text()).not.toMatch(/Tử số|Mẫu số|Kiểm tra cách hiểu/);
  act(() => button('Em đã hiểu, để em thử').props.onPress());
  expect(ready).toHaveBeenCalledTimes(1);
});

it('disables selecting an answer when the lesson is busy or expired', () => {
  act(() => { view = TestRenderer.create(<HintCheckIn {...reduction} disabled onReady={jest.fn()} />); });
  expect(button('Cả số bị chia và số chia').props.disabled).toBe(true);
  act(() => button('Cả số bị chia và số chia').props.onPress());
  expect(text()).not.toContain('Đã chọn');
});
