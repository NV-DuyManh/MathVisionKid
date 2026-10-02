import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useRouter } from 'expo-router';
import HomeScreen from '../app/(tabs)/index';
import CameraScreen from '../app/camera';

jest.mock('expo-router', () => ({ useRouter: jest.fn(), useLocalSearchParams: () => ({}) }));
jest.mock('react-native-safe-area-context', () => ({
  useSafeAreaInsets: () => ({ top: 40, bottom: 20, left: 0, right: 0 }), SafeAreaView: 'SafeAreaView',
}));
jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
jest.mock('expo-camera', () => ({ CameraView: 'CameraView', useCameraPermissions: () => [{ granted: true }, jest.fn()] }));

describe('Native MathVision recognition entry points', () => {
  beforeEach(() => (useRouter as jest.Mock).mockReturnValue({ push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => true }));
  function readScreen(Screen: React.ComponentType) {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<Screen />); });
    const content = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    act(() => renderer!.unmount());
    return content;
  }
  it('offers handwriting and arithmetic on the curriculum home', () => {
    const content = readScreen(HomeScreen);
    expect(content).toContain('MATHVISION KIDS');
    expect(content).toContain('Đọc chữ viết tay');
    expect(content).toContain('Đọc phép tính');
    expect(content).toContain('Cộng, trừ, nhân, chia đặt tính rồi tính');
  });
  it('keeps both capture domains available', () => {
    const content = readScreen(CameraScreen);
    expect(content).toContain('Chữ viết tay');
    expect(content).toContain('Phép tính');
  });
});
