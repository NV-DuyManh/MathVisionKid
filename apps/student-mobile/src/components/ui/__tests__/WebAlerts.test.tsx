import React from 'react';
import { Alert, Modal } from 'react-native';
import TestRenderer, { act } from 'react-test-renderer';
import { WebAlerts } from '../WebAlerts.web';

test('web confirmations require a chosen action, dismiss safely, and restore Alert on unmount', () => {
  const original = Alert.alert;
  const logout = jest.fn();
  const dismissed = jest.fn();
  let renderer: TestRenderer.ReactTestRenderer;
  act(() => { renderer = TestRenderer.create(<WebAlerts />); });
  const show = () => Alert.alert('Đăng xuất', 'Em muốn đăng xuất?', [
    { text: 'Ở lại', style: 'cancel' }, { text: 'Đăng xuất', onPress: logout },
  ], { onDismiss: dismissed });
  try {
    act(show);
    expect(logout).not.toHaveBeenCalled();
    act(() => renderer.root.findByType(Modal).props.onRequestClose());
    expect(dismissed).toHaveBeenCalledTimes(1);
    expect(logout).not.toHaveBeenCalled();
    expect(renderer.toJSON()).toBeNull();
    act(show);
    act(() => renderer.root.findByProps({ accessibilityLabel: 'Ở lại' }).props.onPress());
    expect(logout).not.toHaveBeenCalled();
    act(show);
    act(() => renderer.root.findAllByProps({ accessibilityLabel: 'Đăng xuất' }).find(button => button.props.onPress)!.props.onPress());
    expect(logout).toHaveBeenCalledTimes(1);
    expect(renderer.toJSON()).toBeNull();
  } finally {
    act(() => renderer.unmount());
  }
  expect(Alert.alert).toBe(original);
});
