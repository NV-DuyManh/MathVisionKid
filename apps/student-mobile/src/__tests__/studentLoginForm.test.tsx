import React from 'react';
import { act, create } from 'react-test-renderer';
import { Text, TextInput } from 'react-native';
import LoginScreen from '../app/login';
import { AuthContext } from '../context/AuthContext';
import { authApi } from '../services/api/authApi';

jest.mock('../context/AuthContext', () => ({ AuthContext: require('react').createContext(undefined) }));
jest.mock('../components/ui/AppIllustration', () => ({ AppIllustration: () => null }));
jest.mock('expo-linear-gradient', () => ({ LinearGradient: require('react-native').View }));
jest.mock('react-native-safe-area-context', () => ({ useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('../components/ui/AppButton', () => ({ AppButton: (props: any) => require('react').createElement('button', props) }));
jest.mock('../services/api/authApi', () => ({ authApi: { requestPasswordReset: jest.fn() } }));

let view: ReturnType<typeof create>;
const login = jest.fn();
const button = (label: string) => view.root.findAll(node => node.props.onPress && node.props.children?.props?.children === label)[0];

beforeEach(async () => {
  await act(async () => {
    view = create(<AuthContext.Provider value={{ user: null, isAuthenticated: false, isLoading: false, login, logout: jest.fn() }}><LoginScreen /></AuthContext.Provider>);
  });
});

afterEach(async () => {
  await act(async () => view.unmount());
  jest.restoreAllMocks();
  jest.clearAllMocks();
});

test('the native keyboard submits login once and reports a rejected password', async () => {
  let rejectLogin: (reason: unknown) => void = () => {};
  login.mockImplementation(() => new Promise((_, reject) => { rejectLogin = reject; }));
  const inputs = view.root.findAllByType(TextInput);
  await act(async () => {
    inputs[0].props.onChangeText('student@example.test');
    inputs[1].props.onChangeText('synthetic-password');
  });
  let pending: Promise<void>;
  await act(async () => {
    pending = inputs[1].props.onSubmitEditing();
    await inputs[1].props.onSubmitEditing();
  });
  expect(login).toHaveBeenCalledTimes(1);
  expect(inputs[0].props.editable).toBe(false);
  act(() => button('Quên mật khẩu?').props.onPress());
  expect(view.root.findAllByType(TextInput)).toHaveLength(2);
  await act(async () => {
    rejectLogin({ response: { status: 401 } });
    await pending;
  });
  expect(view.root.findAllByType(Text).map(node => node.props.children)).toContain('Tài khoản hoặc mật khẩu không đúng. Vui lòng kiểm tra lại.');
  expect(inputs[1].props.value).toBe('');
});

test('mail delivery failure uses student-friendly copy and a duplicate Enter sends one request', async () => {
  act(() => button('Quên mật khẩu?').props.onPress());
  const input = view.root.findByType(TextInput);
  act(() => input.props.onChangeText('student@example.test'));
  let rejectReset: (reason: unknown) => void = () => {};
  jest.mocked(authApi.requestPasswordReset).mockImplementation(() => new Promise((_, reject) => { rejectReset = reject; }));
  let pending: Promise<void>;
  await act(async () => {
    pending = input.props.onSubmitEditing();
    await input.props.onSubmitEditing();
  });
  expect(authApi.requestPasswordReset).toHaveBeenCalledTimes(1);
  await act(async () => {
    rejectReset({ response: { status: 503, data: { error: { code: 'EMAIL_DELIVERY_FAILED' } } } });
    await pending;
  });
  const messages = view.root.findAllByType(Text).map(node => node.props.children).filter(text => typeof text === 'string').join(' ');
  expect(messages).toContain('nhờ thầy cô hỗ trợ');
  expect(messages).not.toMatch(/SMTP|cấu hình|quản trị viên/);
});
