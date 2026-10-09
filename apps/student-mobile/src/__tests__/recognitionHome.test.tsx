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
  it('opens the calculator from quick tools and closes back to the unchanged home', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const press = (label: string) => renderer!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];
    act(() => press('Mở máy tính bỏ túi').props.onPress());
    expect(press('Đóng máy tính')).toBeDefined();
    act(() => press('Đóng máy tính').props.onPress());
    expect(press('Chụp bài toán')).toBeDefined();
    expect((useRouter as jest.Mock)().push).not.toHaveBeenCalled();
    act(() => renderer!.unmount());
  });
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
  it('offers one student learning flow through camera or gallery', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const hero = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Chụp bài toán' && typeof node.props.onPress === 'function')[0];
    act(() => hero.props.onPress());
    const content = renderer!.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
    expect(content).toContain('MathVision');
    expect(content).not.toContain('Chụp đề, học cách giải');
    expect(content).not.toContain('Chọn ảnh có sẵn');
    expect(content).not.toContain('Chụp bài viết tay');
    expect(content).not.toContain('Chụp phép tính');
    act(() => renderer!.unmount());
  });
  it('starts the student camera in the unified learning flow', () => {
    const content = readScreen(CameraScreen);
    expect(content).toContain('Chụp bài toán để cùng học');
    expect(content).not.toContain('Đặt tính + / −');
  });
  it('opens the camera directly from the home capture action', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const press = (label: string) => renderer!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0].props.onPress();
    act(() => press('Chụp bài toán'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } });
    act(() => renderer!.unmount());
  });
  it('keeps gallery acquisition available while camera permission is pending', () => {
    (useCameraPermissions as jest.Mock).mockReturnValue([null, jest.fn()]);
    expect(readScreen(CameraScreen)).toContain('Chọn ảnh từ thư viện');
  });
  it('routes both home capture actions to the unified learning flow', () => {
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<HomeScreen />); });
    const press = (label: string) => renderer!.root.findAll(node => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0].props.onPress();
    act(() => press('Chụp bài toán'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } });
    act(() => press('Đọc phép tính. Kiểm tra phép cộng và trừ đặt dọc'));
    expect((useRouter as jest.Mock).mock.results.at(-1)?.value.push).toHaveBeenLastCalledWith({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } });
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
  it('keeps the native image picker reachable inside the camera', async () => {
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({ canceled: true });
    let renderer: TestRenderer.ReactTestRenderer;
    act(() => { renderer = TestRenderer.create(<CameraScreen />); });
    const button = renderer!.root.findAll(node => node.props.accessibilityLabel === 'Chọn ảnh từ thư viện' && typeof node.props.onPress === 'function')[0];
    await act(async () => { await button.props.onPress(); });
    expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalledWith({ mediaTypes: ['images'], allowsEditing: false, quality: 1 });
    act(() => renderer!.unmount());
  });
});
