import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import { RecoveryNotice } from '../components/ui/RecoveryNotice';

it('announces the explanation separately from compact, labelled recovery actions', () => {
  const retry=jest.fn(), fallback=jest.fn(); let view!: TestRenderer.ReactTestRenderer;
  act(() => { view=TestRenderer.create(<RecoveryNotice title="Chưa nghe được" message="Em thử lại nhé." messageId="audio-error" actions={[
    {label:'Thử lại',accessibilityLabel:'Tải lại lời giảng',onPress:retry},
    {label:'Dùng giọng thiết bị',onPress:fallback},
  ]} />); });
  const alert=view.root.findAll(node=>node.props.accessibilityRole==='alert'&&node.type==='View')[0];
  expect(alert.props.nativeID).toBe('audio-error');
  const buttons=view.root.findAll(node=>node.props.accessibilityRole==='button'&&typeof node.props.onPress==='function'&&typeof node.props.style==='function');
  expect(buttons).toHaveLength(2);
  expect(StyleSheet.flatten(buttons[0].props.style({pressed:false})).minHeight).toBe(44);
  act(()=>buttons[0].props.onPress());act(()=>buttons[1].props.onPress());
  expect(retry).toHaveBeenCalledTimes(1);expect(fallback).toHaveBeenCalledTimes(1);
  expect(alert.findAll(node=>node.props.accessibilityRole==='button')).toHaveLength(0);
  act(()=>view.unmount());
});
