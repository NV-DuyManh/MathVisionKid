import React from 'react';
import { act, create } from 'react-test-renderer';
import { TextInput } from 'react-native';
import LoginScreen from '../app/login';
import { AuthContext } from '../context/AuthContext';
jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../components/ui/BrandLockup', () => ({ BrandLockup: () => null }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: (props: any) => require('react').createElement('button', props) }));
test('Native login displays the correct web-platform guidance from the role guard', async () => {
  const message = 'Tài khoản quản trị cần sử dụng cổng quản trị trên trình duyệt.';
  const login = jest.fn().mockRejectedValue(Object.assign(new Error(message), { code: 'STUDENT_ACCESS_DENIED' }));
  let view: ReturnType<typeof create>;
  await act(async () => { view = create(<AuthContext.Provider value={{ user: null, isAuthenticated: false, isLoading: false, login, logout: jest.fn() }}><LoginScreen /></AuthContext.Provider>); });
  try {
    const inputs = view!.root.findAllByType(TextInput);
    await act(async () => { inputs[0].props.onChangeText('account@validation.test'); inputs[1].props.onChangeText('fixture-only'); });
    await act(async () => { await view!.root.findByType('button' as any).props.onPress(); });
    expect(JSON.stringify(view!.toJSON())).toContain(message);
    expect(JSON.stringify(view!.toJSON())).not.toContain('Lỗi kết nối máy chủ');
  } finally { await act(async () => view!.unmount()); }
});
