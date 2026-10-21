import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Platform, StyleSheet } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { FractionExplorer, fractionsInProblem } from '../features/tutoring/FractionExplorer';
import { FractionShape, FractionShapeKind } from '../features/tutoring/FractionShape';
import { COLORS } from '../constants/theme';
import apiClient from '../services/api/apiClient';

jest.mock('../services/api/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() } }));

let view: TestRenderer.ReactTestRenderer;
const render = (numerator: number, denominator: number) => {
  act(() => { view = TestRenderer.create(<FractionExplorer numerator={numerator} denominator={denominator} />); });
};
const pieces = () => view.root.findAll(node => node.props.accessibilityRole === 'checkbox' && typeof node.props.onPress === 'function');
const button = (label: string) => view.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
const text = () => view.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
const selected = () => pieces().filter(node => node.props.accessibilityState.checked);
const regions = () => view.root.findAll(node => [Circle, Path, Rect].includes(node.type as any)
  && typeof node.props.onPress === 'function');
afterEach(() => { if (view) act(() => view.unmount()); jest.restoreAllMocks(); });

it('starts empty, toggles equal parts, checks only their quantity and resets', () => {
  render(2, 5);
  expect(pieces()).toHaveLength(5);
  expect(selected()).toHaveLength(0);
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('chưa khớp với phân số đã cho');
  act(() => pieces()[3].props.onPress());
  expect(text()).not.toContain('chưa khớp với phân số đã cho');
  act(() => pieces()[0].props.onPress());
  expect(selected()).toHaveLength(2);
  expect(pieces()[0].props['aria-checked']).toBe(true);
  expect(view.root.findAll(node => node.props.accessibilityLabel === 'Em đã chọn: 2 phần 5.').length).toBeGreaterThan(0);
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('số phần em chọn biểu diễn phân số đã cho');
  expect(text()).toContain('Em đã chọn 2 phần, đúng với tử số 2.');
  act(() => pieces()[0].props.onPress());
  expect(selected()).toHaveLength(1);
  expect(text()).not.toContain('số phần em chọn biểu diễn phân số đã cho');
  act(() => button('Chọn lại từ đầu').props.onPress());
  expect(selected()).toHaveLength(0);
});

it('represents an improper fraction with equally divided wholes', () => {
  render(7, 3);
  expect(pieces()).toHaveLength(9);
  expect(pieces()[8].props.accessibilityLabel).toBe('Phần 3 trong 3 phần bằng nhau của hình nguyên 3');
  act(() => { pieces().slice(0, 7).forEach(piece => piece.props.onPress()); });
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('số phần em chọn biểu diễn phân số đã cho');
  expect(text()).toContain('Em đã chọn 7 phần, đúng với tử số 7.');
  expect(text()).toContain('Mẫu số vẫn là 3 vì mỗi hình nguyên vẫn chia thành 3 phần bằng nhau.');
});

it.each([
  [1, 'Em đã chọn 1 phần và cần 2 phần theo tử số. Em chọn thêm 1 phần nhé.'],
  [4, 'Em đã chọn 4 phần và cần 2 phần theo tử số. Em bỏ chọn 2 phần nhé.'],
])('explains the next action for %s selected parts without changing the selection', (count, action) => {
  render(2, 5);
  act(() => { pieces().slice(0, count).forEach(piece => piece.props.onPress()); });
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain(action);
  expect(text()).toContain('Mẫu số vẫn là 5 vì mỗi hình nguyên vẫn chia thành 5 phần bằng nhau.');
  expect(selected()).toHaveLength(count);
  const feedback = view.root.findAll(node => node.props.accessibilityLiveRegion === 'polite'
    && typeof node.props.children === 'string' && node.props.children.includes(action));
  expect(feedback.length).toBeGreaterThan(0);
  act(() => regions()[0].props.onPress());
  expect(text()).not.toContain(action);
});

it('offers a short equal-parts explanation without requiring it before selection', () => {
  jest.replaceProperty(Platform, 'OS', 'web');
  render(5, 3);
  const explanation = () => button('Vì sao mỗi phần bằng nhau?');
  expect(explanation().props['aria-expanded']).toBe(false);
  expect(text()).not.toContain('Chọn hay bỏ chọn chỉ đổi số phần được chọn');
  act(() => pieces()[4].props.onPress());
  act(() => explanation().props.onPress());
  expect(explanation().props['aria-expanded']).toBe(true);
  expect(explanation().props.accessibilityState.expanded).toBe(true);
  const content = view.root.findAll(node => node.props.nativeID === explanation().props['aria-controls']);
  expect(content.length).toBeGreaterThan(0);
  expect(text()).toContain('Chia đều một hình nguyên thành 3 phần');
  expect(text()).toContain('Các hình nguyên bằng nhau');
  expect(text()).toContain('Chọn hay bỏ chọn chỉ đổi số phần được chọn');
  expect(selected()).toHaveLength(1);
  act(() => explanation().props.onPress());
  expect(text()).not.toContain('Chọn hay bỏ chọn chỉ đổi số phần được chọn');
  expect(selected()).toHaveLength(1);
});

it('explains zero and whole pieces honestly and keeps empty-selection checks available', () => {
  render(0, 1);
  expect(button('Kiểm tra phần em chọn').props.disabled).not.toBe(true);
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('Em chưa chọn phần nào, đúng với tử số 0.');
  expect(text()).toContain('Mẫu số vẫn là 1 vì mỗi phần là trọn một hình nguyên.');
  act(() => pieces()[0].props.onPress());
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('Em đã chọn 1 phần và cần 0 phần theo tử số. Em bỏ chọn 1 phần nhé.');
  act(() => button('Vì sao mỗi phần bằng nhau?').props.onPress());
  expect(text()).toContain('Mẫu số 1 nghĩa là mỗi hình nguyên là 1 phần.');
  act(() => button('Chọn lại từ đầu').props.onPress());
  expect(selected()).toHaveLength(0);
  expect(text()).not.toContain('Em bỏ chọn 1 phần nhé.');
});

it('keeps fraction exploration local without making tutoring or network requests', () => {
  const fetch = jest.spyOn(global, 'fetch').mockImplementation(jest.fn());
  render(2, 3);
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  act(() => regions()[0].props.onPress());
  act(() => pieces()[2].props.onPress());
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  act(() => button('Vì sao mỗi phần bằng nhau?').props.onPress());
  act(() => button('Hình vuông').props.onPress());
  act(() => button('Chọn lại từ đầu').props.onPress());
  expect(fetch).not.toHaveBeenCalled();
  expect(apiClient.get).not.toHaveBeenCalled();
  expect(apiClient.post).not.toHaveBeenCalled();
});

it('changes geometric representations while keeping the selected parts and fraction', () => {
  render(3, 4);
  expect(button('Hình tròn').props['aria-pressed']).toBe(true);
  act(() => pieces()[2].props.onPress());
  act(() => button('Hình vuông').props.onPress());
  expect(button('Hình vuông').props['aria-pressed']).toBe(true);
  expect(button('Hình tròn').props['aria-pressed']).toBe(false);
  expect(selected()).toHaveLength(1);
  expect(pieces()[2].props.accessibilityState.checked).toBe(true);
  act(() => button('Thanh phân số').props.onPress());
  expect(selected()).toHaveLength(1);
  expect(view.root.findAll(node => node.props.accessibilityLabel === 'Em đã chọn: 1 phần 4.').length).toBeGreaterThan(0);
});

it.each(['Hình tròn', 'Hình vuông', 'Thanh phân số'])(
  'synchronizes a tap on %s with its numbered checkbox, including a later whole', shape => {
    render(7, 3);
    act(() => button(shape).props.onPress());
    act(() => regions()[5].props.onPress());
    expect(selected()).toHaveLength(1);
    expect(pieces()[5].props.accessibilityState.checked).toBe(true);
    expect(regions()[5].props.fill).toBe(COLORS.primaryDark);
    act(() => pieces()[5].props.onPress());
    expect(selected()).toHaveLength(0);
    expect(regions()[5].props.fill).toBe(COLORS.surface);
  },
);

it('hides duplicate SVG targets from assistive technology while retaining named controls', () => {
  render(1, 20);
  const svg = view.root.findByType(Svg);
  expect(svg.props['aria-hidden']).toBe(true);
  expect(svg.props.accessible).toBe(false);
  expect(svg.props.focusable).toBe(false);
  expect(svg.props.accessibilityElementsHidden).toBe(true);
  expect(svg.props.importantForAccessibility).toBe('no-hide-descendants');
  expect(regions()).toHaveLength(20);
  expect(regions().every(region => region.props.accessible === false && region.props.focusable === false)).toBe(true);
  expect(pieces()).toHaveLength(20);
  expect(pieces().every(piece => piece.props.accessibilityLabel && piece.props.focusable)).toBe(true);
  ['Hình tròn', 'Hình vuông', 'Thanh phân số'].forEach(label => {
    const control = button(label);
    expect(control.props.accessibilityRole).toBe('button');
    expect(StyleSheet.flatten(control.props.style({ pressed: false })).minHeight).toBe(48);
  });
});

describe.each(['circle', 'square', 'bar'] as FractionShapeKind[])('%s geometry', shape => {
  it.each(Array.from({ length: 20 }, (_, i) => i + 1))('partitions a whole into %s equal areas without gaps or overlap', denominator => {
    act(() => { view = TestRenderer.create(<FractionShape shape={shape} denominator={denominator} whole={0} selected={[]} onToggle={jest.fn()} />); });
    const parts = regions();
    expect(parts).toHaveLength(denominator);
    if (shape === 'circle') {
      if (denominator === 1) {
        expect(parts[0].type).toBe(Circle);
        expect(parts[0].props.r).toBe(108);
        expect(view.root.findAllByType(Path)).toHaveLength(0);
        return;
      }
      const endpoints = parts.map(part => {
        const numbers = part.props.d.match(/[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi).map(Number);
        expect(numbers).toHaveLength(11);
        expect(numbers.every(Number.isFinite)).toBe(true);
        const [cx, cy, sx, sy, rx, ry, rotation, largeArc, clockwise, ex, ey] = numbers;
        expect([cx, cy, rx, ry, rotation, largeArc, clockwise]).toEqual([120, 120, 108, 108, 0, 0, 1]);
        expect(Math.hypot(sx - cx, sy - cy)).toBeCloseTo(108, 8);
        expect(Math.hypot(ex - cx, ey - cy)).toBeCloseTo(108, 8);
        const start = Math.atan2(sy - cy, sx - cx);
        const end = Math.atan2(ey - cy, ex - cx);
        const angle = (end - start + 2 * Math.PI) % (2 * Math.PI);
        expect(108 * 108 * angle / 2).toBeCloseTo(Math.PI * 108 * 108 / denominator, 7);
        return { sx, sy, ex, ey };
      });
      endpoints.forEach((point, i) => {
        const next = endpoints[(i + 1) % denominator];
        expect(point.ex).toBeCloseTo(next.sx, 8);
        expect(point.ey).toBeCloseTo(next.sy, 8);
      });
    } else {
      const height = shape === 'bar' ? 72 : 216;
      const bounds = parts.map(part => part.props);
      let totalArea = 0;
      bounds.forEach(({ x, y, width, height: partHeight }, i) => {
        expect(width * partHeight).toBeCloseTo(216 * height / denominator, 8);
        expect(x).toBeGreaterThanOrEqual(12);
        expect(y).toBeGreaterThanOrEqual(12);
        expect(x + width).toBeLessThanOrEqual(228 + 1e-8);
        expect(y + partHeight).toBeLessThanOrEqual(12 + height + 1e-8);
        totalArea += width * partHeight;
        bounds.slice(i + 1).forEach(other => {
          const overlapX = Math.max(0, Math.min(x + width, other.x + other.width) - Math.max(x, other.x));
          const overlapY = Math.max(0, Math.min(y + partHeight, other.y + other.height) - Math.max(y, other.y));
          expect(overlapX * overlapY).toBeLessThan(1e-8);
        });
      });
      expect(totalArea).toBeCloseTo(216 * height, 8);
    }
  });
});

it.each([[1, 0], [1, -2], [-1, 3], [1, 21], [10, 3], [1.2, 3], [1, 3.5], [Infinity, 3], [1, NaN]])(
  'uses a safe text fallback without misleading pieces for %s/%s', (numerator, denominator) => {
    render(numerator, denominator);
    expect(pieces()).toHaveLength(0);
    expect(button('Kiểm tra phần em chọn')).toBeUndefined();
    expect(text()).toContain('chưa có hình tương tác phù hợp');
  },
);

it('supports zero and resets exploration when the given fraction changes', () => {
  render(0, 4);
  act(() => button('Kiểm tra phần em chọn').props.onPress());
  expect(text()).toContain('số phần em chọn biểu diễn phân số đã cho');
  act(() => pieces()[0].props.onPress());
  act(() => view.update(<FractionExplorer numerator={3} denominator={4} />));
  expect(selected()).toHaveLength(0);
  expect(text()).not.toContain('số phần em chọn biểu diễn phân số đã cho');
});

it('exposes named checkboxes that grow with text, focus feedback and Space activation on web', () => {
  jest.replaceProperty(Platform, 'OS', 'web');
  render(1, 3);
  const first = pieces()[0];
  expect(first.props.focusable).toBe(true);
  expect(first.props.accessibilityLabel).toBe('Phần 1 trong 3 phần bằng nhau của hình nguyên 1');
  const before = StyleSheet.flatten(first.props.style({ pressed: false }));
  expect(before.minWidth).toBe(48);
  expect(before.minHeight).toBe(48);
  expect(before.width).toBeUndefined();
  expect(before.height).toBeUndefined();
  expect(first.findAllByType('Text' as any).every(node => node.props.allowFontScaling !== false)).toBe(true);
  act(() => first.props.onFocus());
  expect(StyleSheet.flatten(pieces()[0].props.style({ pressed: false })).borderStyle).toBe('dashed');
  const preventDefault = jest.fn();
  act(() => pieces()[0].props.onKeyDown({ key: ' ', preventDefault, repeat: false }));
  expect(preventDefault).toHaveBeenCalled();
  expect(selected()).toHaveLength(1);
  act(() => pieces()[0].props.onKeyDown({ key: ' ', preventDefault, repeat: true }));
  expect(selected()).toHaveLength(1);
  act(() => pieces()[0].props.onKeyDown({ key: ' ', preventDefault, repeat: false }));
  expect(selected()).toHaveLength(0);
});

it('takes at most two literal distinct fractions without reducing or calculating them', () => {
  expect(fractionsInProblem('Táo 2 / 6, xoài 3/5. Còn lại bao nhiêu? 2/6 rồi 1/4.')).toEqual([
    { numerator: 2, denominator: 6 }, { numerator: 3, denominator: 5 },
  ]);
});

it.each(['Ngày 2/5/2026', 'Ngày 2 / 5 / 2026', '2026/05/02', 'Ngày 2/5', 'date: 2/5',
  '1/0', '3/[?]', '1.5/2', '1/2,5', '-1/3', '−1/3', 'abc1/3', '1/3abc', 'https://example.org/1/3', '1/9007199254740992'])(
  'does not use a date, unresolved or unsupported literal as a source fraction: %s', source => {
    expect(fractionsInProblem(source)).toEqual([]);
  },
);

it('continues past a date and preserves a zero numerator from the source', () => {
  expect(fractionsInProblem('Ngày 2 / 5 / 2026, em có 0/3 và 5/4.')).toEqual([
    { numerator: 0, denominator: 3 }, { numerator: 5, denominator: 4 },
  ]);
});

it.each(['- 1/3', '− 1/3', '+ 1/3', '-\t1/3', '−\n1/3', '+1/3'])(
  'does not discard the sign of a source fraction: %s', source => {
    expect(fractionsInProblem(source)).toEqual([]);
  },
);

it('continues past a spaced signed fraction to ordinary fractions in prose', () => {
  expect(fractionsInProblem('Phân số − 1/3, còn táo 2/5 và xoài 3/7.')).toEqual([
    { numerator: 2, denominator: 5 }, { numerator: 3, denominator: 7 },
  ]);
});
