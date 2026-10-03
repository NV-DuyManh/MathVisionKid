import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useRouter } from 'expo-router';
import HomeScreen from '../app/(tabs)/index';
import CameraScreen from '../app/camera';
import * as ImagePicker from 'expo-image-picker';
import { useCameraPermissions } from 'expo-camera';

jest.mock('expo-router', () => ({ useRouter: jest.fn(), useLocalSearchParams: () => ({}), useFocusEffect: jest.fn() }));
jest.mock('react-native-safe-area-context', () => ({
  useSafeAreaInsets: () => ({ top: 40, bottom: 20, left: 0, right: 0 }), SafeAreaView: 'SafeAreaView',
}));
jest.mock('expo-image-picker', () => ({ launchImageLibraryAsync: jest.fn() }));
jest.mock('expo-camera', () => ({ CameraView: 'CameraView', useCameraPermissions: jest.fn() }));

describe('Native MathVision recognition entry points', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => true });
    (useCameraPermissions as jest.Mock).mockReturnValue([{ granted: true }, jest.fn()]);
  });
  function readScreen(Screen: React.ComponentType) {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<Screen />); });
    const content = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    act(() => renderer!.unmount());
    return content;
  }
  it('offers handwriting, arithmetic and gallery through the home acquisition sheet', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const hero = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Chụp bài toán hoặc bài viết tay' && typeof node.props.onPress === 'function')[0];
    act(() => hero.props.onPress());
    const content = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(content).toContain('MathVision');
    expect(content).toContain('Chụp bài viết tay');
    expect(content).toContain('Chụp phép tính');
    expect(content).toContain('Chọn ảnh có sẵn');
    act(() => renderer!.unmount());
  });
  it('keeps both capture domains available', () => {
    const content = readScreen(CameraScreen);
    expect(content).toContain('Đọc bài giải');
    expect(content).toContain('Đặt tính + / −');
  });
  it('keeps gallery acquisition available while camera permission is pending', () => {
    (useCameraPermissions as jest.Mock).mockReturnValue([null, jest.fn()]);
    expect(readScreen(CameraScreen)).toContain('Chọn ảnh từ thư viện');
  });
  it('routes the new hero and arithmetic lesson to their existing capture domains', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const press = (label: string) => renderer!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0].props.onPress();
    act(() => press('Chụp bài toán hoặc bài viết tay'));
    act(() => press('Chụp bài viết tay'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith({ pathname: '/camera', params: { mode: 'HANDWRITING_TEXT' } });
    act(() => press('Đọc phép tính. Kiểm tra phép cộng và trừ đặt dọc'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith({ pathname: '/camera', params: { mode: 'ARITHMETIC' } });
    act(() => renderer!.unmount());
  });
  it('opens saved history and the real grade-one curriculum', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const press = (label: string) => renderer!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0].props.onPress();
    act(() => press('Bài đã lưu. Xem lại bài làm của em'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith('/(tabs)/profile');
    act(() => press('Luyện phép cộng và trừ trong phạm vi 100, lớp 1'));
    const content = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(content).toContain('Bài toán thêm hoa vào lọ');
    act(() => renderer!.unmount());
  });
  it('keeps the native image picker reachable from the updated home', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const hero = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Chụp bài toán hoặc bài viết tay' && typeof node.props.onPress === 'function')[0];
    act(() => hero.props.onPress());
    const button = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Chọn ảnh bài làm từ thư viện' && typeof node.props.onPress === 'function')[0];
    await act(async () => { await button.props.onPress(); });
    expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith({ mediaTypes: ['images'], allowsEditing: false, quality: 1 });
    act(() => renderer!.unmount());
  });
});
