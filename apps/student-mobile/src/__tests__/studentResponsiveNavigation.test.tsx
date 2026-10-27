import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { Platform, StyleSheet } from 'react-native';
import { StudentTabBar } from '../app/(tabs)/_layout';

jest.mock('react-native-safe-area-context', () => ({ useSafeAreaInsets: () => ({ top: 0, bottom: 20 }) }));

describe('Student navigation on different screens', () => {
  const state = { index: 0, routes: [
    { key: 'home', name: 'index' }, { key: 'lesson-route-key', name: 'lessons' },
    { key: 'achievements', name: 'achievements' }, { key: 'profile', name: 'profile' },
  ] };
  const renderBar = (width: number, navigate = jest.fn(), emit = jest.fn(() => ({ defaultPrevented: false }))) => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<StudentTabBar {...{ state, emitter: { emit }, navigateToTab: navigate, viewportWidth: width } as any} />); });
    return renderer!;
  };
  const button = (tree: TestRenderer.ReactTestRenderer, label: string) => tree.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];

  it('keeps a bottom bar on phones and shows every destination', () => {
    const tree = renderBar(390);
    expect(button(tree, 'Trang chủ').props.accessibilityState.selected).toBe(true);
    expect(button(tree, 'Bài học')).toBeDefined();
    expect(button(tree, 'Mở rộng menu')).toBeUndefined();
    const bar = tree.root.findAll(node => node.props.accessibilityRole === 'tablist')[0];
    expect(StyleSheet.flatten(bar.props.style).flexDirection).toBe('row');
    act(() => tree.unmount());
  });

  it('lets tablet users expand a compact vertical menu and navigate', () => {
    const navigate = jest.fn();
    const tree = renderBar(820, navigate);
    const expand = button(tree, 'Mở rộng menu');
    expect(expand).toBeDefined();
    act(() => expand.props.onPress());
    expect(button(tree, 'Thu gọn menu').props.accessibilityState.expanded).toBe(true);
    act(() => button(tree, 'Bài học').props.onPress());
    expect(navigate).toHaveBeenCalledWith('lesson-route-key');
    act(() => tree.unmount());
  });

  it('can collapse the desktop menu without changing the selected destination', () => {
    const tree = renderBar(1440);
    expect(button(tree, 'Thu gọn menu')).toBeDefined();
    act(() => button(tree, 'Thu gọn menu').props.onPress());
    expect(button(tree, 'Mở rộng menu')).toBeDefined();
    expect(button(tree, 'Trang chủ').props.accessibilityState.selected).toBe(true);
    act(() => tree.unmount());
  });

  it('respects a prevented tab press and emits long presses through the Router 58 emitter', () => {
    const navigate = jest.fn();
    const emit = jest.fn(() => ({ defaultPrevented: true }));
    const tree = renderBar(820, navigate, emit);
    act(() => button(tree, 'Bài học').props.onPress());
    expect(emit).toHaveBeenCalledWith({ type: 'tabPress', target: 'lesson-route-key', canPreventDefault: true });
    expect(navigate).not.toHaveBeenCalled();
    act(() => button(tree, 'Bài học').props.onLongPress());
    expect(emit).toHaveBeenLastCalledWith({ type: 'tabLongPress', target: 'lesson-route-key' });
    act(() => tree.unmount());
  });

  it('does not navigate again when the selected tab is pressed', () => {
    const navigate = jest.fn();
    const tree = renderBar(390, navigate);
    act(() => button(tree, 'Trang chủ').props.onPress());
    expect(navigate).not.toHaveBeenCalled();
    act(() => tree.unmount());
  });

  it('keeps unselected destinations focusable with an Android tablet keyboard', () => {
    const platform = jest.replaceProperty(Platform, 'OS', 'android');
    try {
      const tree = renderBar(820);
      expect(button(tree, 'Bài học').props.tabIndex).not.toBe(-1);
      act(() => tree.unmount());
    } finally { platform.restore(); }
  });

  it('retains hover feedback and keyboard focus for browser and native event shapes', () => {
    const platform = jest.replaceProperty(Platform, 'OS', 'web');
    try {
      const tree = renderBar(820);
      const home = button(tree, 'Trang chủ');
      const lessons = button(tree, 'Bài học');
      const target = lessons.findAll(node => node.instance && typeof node.instance.focus === 'function')[0].instance;
      const preventDefault = jest.fn();
      act(() => home.props.onKeyDown({ nativeEvent: { key: 'ArrowDown' }, preventDefault }));
      act(() => home.props.onKeyDown({ key: 'ArrowDown', preventDefault }));
      expect(preventDefault).toHaveBeenCalledTimes(2);
      expect(target.focus).toHaveBeenCalledTimes(2);
      act(() => lessons.props.onHoverIn());
      expect(StyleSheet.flatten(button(tree, 'Bài học').props.style({ pressed: false })).backgroundColor).toBe('#6747B6');
      act(() => lessons.props.onHoverOut());
      expect(StyleSheet.flatten(button(tree, 'Bài học').props.style({ pressed: false })).backgroundColor).toBeUndefined();
      act(() => tree.unmount());
    } finally { platform.restore(); }
  });
});
