import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Modal } from 'react-native';
import { PocketCalculator } from '../features/calculator/PocketCalculator';
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: 'SafeAreaView' }));
let view: TestRenderer.ReactTestRenderer;
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const field = () => view.root.findAll(node => node.props.accessibilityLabel === 'Phép tính' && typeof node.props.onChangeText === 'function')[0];
const text = () => view.root.findAllByType('Text' as any).map(node => Array.isArray(node.props.children) ? node.props.children.join('') : String(node.props.children)).join(' ').replace(/\s+/g, ' ');
const press = (label: string) => act(() => button(label).props.onPress());
const enter = (value: string) => act(() => field().props.onChangeText(value));
beforeEach(() => { act(() => { view = TestRenderer.create(<PocketCalculator visible onClose={jest.fn()} />); }); });
afterEach(() => act(() => view.unmount()));

it('uses one compact popup keypad, with extra keys hidden until requested', () => {
  expect(view.root.findByType(Modal).props.transparent).toBe(true);
  expect(button('Số thường')).toBeUndefined(); expect(button('Phân số')).toBeUndefined();
  expect(button('Mở ngoặc')).toBeUndefined();
  press('Nhập 1'); press('Cộng'); press('Nhập 3'); press('Tính kết quả');
  expect(text()).toContain('4'); expect(text()).not.toContain('Bước 1');
  expect(button('Xem cách tính')).toBeUndefined();
  press('Lịch sử phép tính'); press('Sửa phép tính 1+3');
  expect(button('Xem cách tính')).toBeUndefined();
  enter('95+17'); press('Tính kết quả'); expect(text()).toContain('Hàng đơn vị');
  expect(button('Xem cách tính').props.accessibilityState.expanded).toBe(true);
  press('Xem cách tính'); expect(text()).not.toContain('Hàng đơn vị');
  press('Nhập 7'); expect(field().props.value).toBe('7'); expect(button('Xem cách tính')).toBeUndefined();
  press('Thêm chức năng'); expect(button('Mở ngoặc')).toBeDefined();
  press('Đổi dấu số'); expect(field().props.value).toBe('(-7)');
  press('Đổi dấu số'); expect(field().props.value).toBe('7');
});
it('inserts mixed numbers through three labelled fields and shows their equivalent result', () => {
  const fill = (label: string, value: string) => act(() => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onChangeText === 'function')[0].props.onChangeText(value));
  press('Nhập hỗn số');
  fill('Phần nguyên hỗn số', '2'); fill('Tử số hỗn số', '1'); fill('Mẫu số hỗn số', '4');
  press('Thêm hỗn số vào phép tính');
  expect(field().props.value).toBe('2 1/4');
  press('Cộng'); press('Nhập phân số');
  // An incomplete expression is retained rather than silently corrected.
  press('Tính kết quả'); expect(text()).toContain('Phép tính chưa đủ');
  enter('2 1/4+1/4'); press('Tính kết quả');
  expect(text()).toContain('Đổi hỗn số'); expect(text()).toContain('Hỗn số: 2');
  press('Nhập hỗn số'); fill('Phần nguyên hỗn số', '2'); fill('Tử số hỗn số', '4'); fill('Mẫu số hỗn số', '0');
  press('Thêm hỗn số vào phép tính'); expect(text()).toContain('mẫu khác 0');
});

it('converts compound measurements, clears stale results, and preserves each calculator mode', () => {
  const fill = (label: string, value: string) => act(() => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onChangeText === 'function')[0].props.onChangeText(value));
  enter('1/3+2/5'); press('Tính kết quả');
  press('Đổi đơn vị'); fill('Số đo cần đổi', '15');
  press('Thêm số đo'); fill('Số đo thêm', '25');
  press('Đơn vị đích: cm'); press('Chọn m'); press('Đổi đơn vị ngay');
  expect(text()).toContain('15,25 m'); expect(text()).toContain('Cách đổi');
  fill('Số đo thêm', '50'); expect(text()).not.toContain('15,25 m');
  press('Đổi đơn vị ngay'); expect(text()).toContain('15,5 m');
  press('Tính toán'); expect(field().props.value).toBe('1/3+2/5');
  press('Đổi đơn vị'); expect(text()).toContain('15,5 m');
  press('Đổi diện tích'); fill('Số đo cần đổi', '2'); press('Đổi đơn vị ngay');
  expect(text()).toContain('200 dm²');
  press('Đơn vị gốc: m²'); press('Chọn ha');
  expect(text()).not.toContain('200 dm²');
  fill('Số đo cần đổi', ''); press('Đổi đơn vị ngay'); expect(text()).toContain('Em nhập số đo');
});
it('enters fractions on the same keypad and keeps invalid input available to fix', () => {
  press('Nhập 1'); press('Nhập phân số'); press('Nhập 3'); press('Cộng');
  press('Nhập 2'); press('Nhập phân số'); press('Nhập 5'); press('Tính kết quả');
  expect(field().props.value).toBe('1/3+2/5');
  expect(view.root.findAll(node => node.props.testID === 'stacked-fraction').length).toBeGreaterThan(0);
  expect(text()).toContain('11'); expect(text()).toContain('15');
  enter('1/0'); press('Tính kết quả'); expect(text()).toContain('Mẫu số phải khác 0');
  expect(field().props.value).toBe('1/0');
});
it('shows quotient/remainder on demand and preserves the expression after closing', () => {
  enter('17÷5'); press('Tính kết quả'); press('Xem thương và số dư');
  expect(text()).toContain('Thương 3, dư 2'); expect(text()).toContain('Lấy 17 chia 5');
  const close = jest.fn(); act(() => view.update(<PocketCalculator visible onClose={close} />));
  press('Đóng máy tính'); expect(close).toHaveBeenCalledTimes(1);
  act(() => view.update(<PocketCalculator visible={false} onClose={close} />));
  act(() => view.update(<PocketCalculator visible onClose={close} />));
  expect(field().props.value).toBe('17÷5');
  act(() => view.root.findByType(Modal).props.onRequestClose()); expect(close).toHaveBeenCalledTimes(2);
  press('Đóng máy tính bên ngoài'); expect(close).toHaveBeenCalledTimes(3);
});
it('supports exact decimals, chained calculation and history restore', () => {
  press('Nhập 0'); press('Dấu phẩy thập phân'); press('Nhập 1'); press('Cộng');
  press('Nhập 0'); press('Dấu phẩy thập phân'); press('Nhập 2'); press('Tính kết quả');
  expect(text()).toContain('0,3'); press('Nhân'); press('Nhập 1'); press('Nhập 0'); press('Tính kết quả');
  expect(text()).toContain('3'); press('Lịch sử phép tính'); press('Sửa phép tính 0,1+0,2');
  expect(field().props.value).toBe('0,1+0,2'); press('Lịch sử phép tính'); press('Xóa lịch sử máy tính');
  expect(text()).toContain('Chưa có phép tính');
});
it('continues from large and precise results without re-parsing them as limited literals', () => {
  enter('999999+1'); press('Tính kết quả'); press('Cộng'); press('Nhập 1'); press('Tính kết quả');
  expect(text()).toContain('1000001');
  enter('0,0001×0,0001'); press('Tính kết quả'); press('Nhân'); press('Nhập 2'); press('Tính kết quả');
  expect(text()).toContain('0,00000002'); press('Phần trăm'); press('Tính kết quả');
  expect(text()).toContain('0,0000000002');
});
