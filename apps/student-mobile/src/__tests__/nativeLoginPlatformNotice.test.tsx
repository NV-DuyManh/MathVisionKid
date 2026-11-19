import React from 'react';
import { act, create } from 'react-test-renderer';
import { Text, TextInput } from 'react-native';
import LoginScreen from '../app/login';
import { AuthContext } from '../context/AuthContext';
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../components/ui/BrandLockup', () => ({ BrandLockup: () => null }));
jest.mock('../components/ui/AppIllustration', () => ({ AppIllustration: () => null }));
jest.mock('expo-linear-gradient', () => ({ LinearGradient: require('react-native').View }));
jest.mock('react-native-safe-area-context', () => ({ useSafeAreaInsets: () => ({ top: 24, bottom: 20, left: 0, right: 0 }) }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: (props: any) => require('react').createElement('button', props) }));
test('Native login displays the correct web-platform guidance from the role guard', async () => {
  const message = 'Tài khoản quản trị cần sử dụng cổng quản trị trên trình duyệt.';
  const login = jest.fn().mockRejectedValue(Object.assign(new Error(message), { code: 'STUDENT_ACCESS_DENIED' }));
  let view: ReturnType<typeof create>;
  await act(async () => { view = create(<AuthContext.Provider value={{ user: null, isAuthenticated: false, isLoading: false, login, logout: jest.fn() }}><LoginScreen /></AuthContext.Provider>); });
  try {
    expect(view!.root.findAllByProps({ testID: 'student-auth-hero' }).length).toBeGreaterThan(0);
    const inputs = view!.root.findAllByType(TextInput);
    await act(async () => { inputs[0].props.onChangeText('account@validation.test'); inputs[1].props.onChangeText('fixture-only'); });
    await act(async () => { await view!.root.findByType('button' as any).props.onPress(); });
    const notices = view!.root.findAllByType(Text).map(node => node.props.children);
    expect(notices).toContain(message);
    expect(notices).not.toContain('Lỗi kết nối máy chủ. Vui lòng kiểm tra và thử lại.');
  } finally { await act(async () => view!.unmount()); }
});
