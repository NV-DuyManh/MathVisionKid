import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { ParentModePreview, ParentProfilePinDialog } from '../features/student-profile/ParentModePreview';
import { confirmParentPinCode, requestParentPinCode, openParentMode, readParentControlStatus, readParentSettings, saveParentDailyLimit, saveParentGameLimit } from '../features/student-profile/parentControlApi';
import { readStudentUsageWeek } from '../features/student-profile/studentUsage';
import {
  clearParentModeSession,
  consumeParentModeHandoff,
  readParentModeSession,
  storeParentModeHandoff,
  updateParentModeSession,
} from '../features/student-profile/parentModeHandoff';

// Exercise the workspace state without importing or timing native presentation primitives.
jest.mock('react-native', () => ({
  ActivityIndicator: 'ActivityIndicator',
  AppState: { currentState: 'active', addEventListener: () => ({ remove: jest.fn() }) },
  Modal: 'Modal',
  KeyboardAvoidingView: 'View',
  Pressable: 'Pressable',
  ScrollView: 'ScrollView',
  Text: 'Text',
  TextInput: 'TextInput',
  View: 'View',
  Platform: { OS: 'ios' },
  StyleSheet: { create: (style: unknown) => style },
  useWindowDimensions: jest.fn(() => ({ width: 390 })),
}));
jest.mock('expo-linear-gradient', () => ({
  LinearGradient: ({ children, ...props }: { children?: React.ReactNode }) =>
    require('react').createElement('View', props, children),
}));
jest.mock('../components/ui/AppButton', () => ({
  AppButton: ({ title, onPress }: { title: string; onPress: () => void }) =>
    require('react').createElement('Button', { accessibilityLabel: title, onPress }),
}));
jest.mock('../components/ui/AppIllustration', () => ({
  AppIllustration: () => null,
}));
jest.mock('react-native-safe-area-context', () => ({ SafeAreaView: require('react-native').View }));
jest.mock('@expo/vector-icons', () => ({ Ionicons: () => null }));
jest.mock('../features/student-profile/ProfileCards', () => ({ StudentAvatar: () => null }));
jest.mock('../features/student-profile/useStudentProfile', () => ({
  useStudentProfile: () => ({
    value: {
      displayName: 'Kiểm thử',
      gradeLevel: 5,
      classrooms: [],
      stars: 3,
      rank: { name: 'Đồng III', masterStars: 0, progress: 3, goal: 5 },
      titles: [],
      history: [],
      stats: { today: 0, week: 0, month: 0, streak: 0, days: 0, lessons: 0, quizzes: 0, games: 0 },
    },
  }),
}));
jest.mock('../features/student-profile/parentControlApi', () => ({
  openParentMode: jest.fn(),
  requestParentPinCode: jest.fn(),
  confirmParentPinCode: jest.fn(),
  readParentControlStatus: jest.fn(),
  readParentSettings: jest.fn(),
  isParentGrantRejected: (cause: unknown) => cause === 'expired',
  saveParentDailyLimit: jest.fn(),
  saveParentGameLimit: jest.fn(),
  parentControlError: (cause: any) =>
    cause?.response?.data?.error?.code === 'PARENT_PIN_INVALID'
      ? 'Mã PIN chưa đúng. Vui lòng thử lại.'
      : 'Chưa kết nối được với tài khoản. Vui lòng thử lại.',
}));
jest.mock('../features/student-profile/studentUsage', () => ({ readStudentUsageWeek: jest.fn() }));

let view: TestRenderer.ReactTestRenderer;
const text = () =>
  view.root
    .findAllByType('Text' as any)
    .map(node => (Array.isArray(node.props.children) ? node.props.children.join('') : String(node.props.children)))
    .join(' ');
const press = async (name: string) =>
  act(async () => {
    view.root.findAll(node => node.props.accessibilityLabel === name && node.props.onPress)[0].props.onPress();
  });
const type = (name: string, value: string) =>
  act(() => {
    view.root.findAll(node => node.props.accessibilityLabel === name && node.props.onChangeText)[0].props.onChangeText(value);
  });

beforeEach(() => {
  require('react-native').Platform.OS = 'ios';
  require('react-native').useWindowDimensions.mockReturnValue({ width: 390 });
  clearParentModeSession();
  jest.clearAllMocks();
  jest.mocked(readParentControlStatus).mockResolvedValue({
    pinConfigured: true,
    dailyLimitReached: false,
    activityVerified: true,
  });
  jest.mocked(openParentMode).mockResolvedValue({ dailyMinutes: 45 });
  jest.mocked(readStudentUsageWeek).mockResolvedValue({
    today: '2026-11-20',
    totalMillis: 900000,
    days: [
      { date: '2026-11-20', elapsedMillis: 900000 },
      { date: '2026-11-21', elapsedMillis: 0 },
    ],
  });
});
afterEach(() => {
  if (view) act(() => view.unmount());
  clearParentModeSession();
  require('react-native').Platform.OS = 'ios';
});

it('labels previously loaded limits when settings are unavailable and refreshes without another PIN', async () => {
  storeParentModeHandoff('student-a', { dailyMinutes: 45, grant: 'parent-grant' });
  jest.mocked(readParentSettings).mockRejectedValueOnce(new Error('network unavailable'))
    .mockResolvedValueOnce({ dailyMinutes: 60 });
  await act(async () => {
    view = TestRenderer.create(<ParentModePreview owner="student-a" onExit={jest.fn()} />);
  });
  expect(text()).toContain('Số liệu giới hạn hiển thị là lần tải gần nhất');
  await press('Tải lại cài đặt');
  expect(text()).not.toContain('Số liệu giới hạn hiển thị là lần tải gần nhất');
  expect(readParentModeSession('student-a')?.dailyMinutes).toBe(60);
  expect(openParentMode).not.toHaveBeenCalled();
});

it('consumes the profile PIN handoff once, retains the active session until cleared, and expires handoff quickly', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2026-11-20T04:00:00Z'));
  storeParentModeHandoff('student-a', { dailyMinutes: 45 });
  expect(consumeParentModeHandoff('student-b')).toBeUndefined();
  expect(consumeParentModeHandoff('student-a')).toBeUndefined();

  storeParentModeHandoff('student-a', { dailyMinutes: 45 });
  expect(consumeParentModeHandoff('student-a')).toEqual({ dailyMinutes: 45 });
  expect(consumeParentModeHandoff('student-a')).toBeUndefined();
  expect(readParentModeSession('student-a')).toEqual({ dailyMinutes: 45 });

  updateParentModeSession('student-a', { dailyMinutes: 60 });
  expect(readParentModeSession('student-a')).toEqual({ dailyMinutes: 60 });
  clearParentModeSession();
  expect(readParentModeSession('student-a')).toBeUndefined();

  storeParentModeHandoff('student-a', { dailyMinutes: 30 });
  jest.advanceTimersByTime(15_001);
  expect(consumeParentModeHandoff('student-a')).toBeUndefined();
  jest.useRealTimers();
});

it('uses a six-slot web PIN dialog on Profile and never prompts for PIN inside web Parent Mode', async () => {
  const { Platform } = require('react-native');
  Platform.OS = 'web';
  jest.mocked(openParentMode)
    .mockRejectedValueOnce({ response: { data: { error: { code: 'PARENT_PIN_INVALID' } } } })
    .mockResolvedValueOnce({ dailyMinutes: 45 });
  const onOpen = jest.fn(settings => storeParentModeHandoff('student-a', settings));
  await act(async () => {
    view = TestRenderer.create(<ParentProfilePinDialog owner="student-a" onExit={jest.fn()} onOpen={onOpen} />);
  });
  expect(view.root.findAllByProps({ testID: 'pin-cell' })).toHaveLength(6);
  expect(view.root.findByProps({ accessibilityRole: 'dialog' })).toBeDefined();
  type('Mã PIN', '000000');
  expect(openParentMode).toHaveBeenCalledWith('000000', false, expect.anything());
  await act(async () => {});
  expect(text()).toContain('Mã PIN chưa đúng');
  expect(onOpen).not.toHaveBeenCalled();

  type('Mã PIN', '864209');
  await act(async () => {});
  expect(onOpen).toHaveBeenCalledWith({ dailyMinutes: 45 });

  const onExit = jest.fn();
  await act(async () => {
    view.update(<ParentModePreview owner="student-a" onExit={onExit} />);
  });
  expect(view.root.findAllByProps({ testID: 'pin-cell' })).toHaveLength(0);
  expect(text()).toContain('Tiến độ học tập');
  expect(text()).toContain('Sử dụng an toàn');

  await press('Khóa Góc phụ huynh');
  expect(onExit).toHaveBeenCalledTimes(1);
  expect(readParentModeSession('student-a')).toBeUndefined();
});

it('exits web Parent Mode immediately when opened without an unlocked profile session', async () => {
  const { Platform, useWindowDimensions } = require('react-native');
  Platform.OS = 'web';
  useWindowDimensions.mockReturnValue({ width: 1440 });
  const onExit = jest.fn();
  await act(async () => {
    view = TestRenderer.create(<ParentModePreview owner="student-a" onExit={onExit} />);
  });
  expect(onExit).toHaveBeenCalledTimes(1);
  expect(view.root.findAllByProps({ testID: 'pin-cell' })).toHaveLength(0);
  expect(text()).not.toContain('Nhập mã PIN');
});

it('shows the no-PIN notice on Android with a live region and native-safe roles', async () => {
  require('react-native').Platform.OS = 'android';
  jest.mocked(readParentControlStatus).mockResolvedValueOnce({
    pinConfigured: false, dailyLimitReached: false, activityVerified: true,
  });
  await act(async () => {
    view = TestRenderer.create(<ParentProfilePinDialog owner="student-a" onExit={jest.fn()} onOpen={jest.fn()} />);
  });
  const dialog = view.root.findByProps({ accessibilityViewIsModal: true });
  expect(dialog.props.accessibilityRole).toBeUndefined();
  const notice = dialog.findByProps({ accessibilityLiveRegion: 'polite' });
  expect(notice.props.children).toContain('Tài khoản chưa có mã PIN');
  expect(notice.props.accessibilityRole).toBeUndefined();
});

it('shows verified use beside learning on native mobile, then confirms a limit change only after a successful PIN save', async () => {
  require('react-native').Platform.OS = 'android';
  jest.mocked(saveParentDailyLimit).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ dailyMinutes: null });
  const open = jest.fn(settings => storeParentModeHandoff('student-a', settings));
  await act(async () => {
    view = TestRenderer.create(<ParentProfilePinDialog owner="student-a" onExit={jest.fn()} onOpen={open} />);
  });
  expect(view.root.findAllByType('Modal' as any)).toHaveLength(1);
  expect(readStudentUsageWeek).not.toHaveBeenCalled();
  type('Mã PIN', '864209');
  await press('Mở Góc phụ huynh');
  expect(open).toHaveBeenCalledWith({ dailyMinutes: 45 });
  await act(async () => view.update(<ParentModePreview owner="student-a" onExit={jest.fn()} />));
  expect(text()).toContain('Tiến độ học tập');
  expect(text()).toContain('Sử dụng an toàn');
  expect(text()).toContain('Chưa có hoạt động học tập');
  expect(text()).toContain('15 phút');
  await press('Đổi giới hạn');
  await press('Không giới hạn');
  await press('Xác nhận thay đổi');
  expect(view.root.findByProps({ accessibilityViewIsModal: true }).props.accessibilityLabel).toBe('Xác nhận bằng mã PIN');
  expect(view.root.findAllByType('Modal' as any)).toHaveLength(1);
  await press('Hủy xác nhận');
  expect(saveParentDailyLimit).not.toHaveBeenCalled();
  await press('Xác nhận thay đổi');
  type('Mã PIN để lưu', '864209');
  await press('Lưu giới hạn');
  expect(text()).toContain('45 phút/ngày');
  expect(text()).toContain('Giới hạn xác nhận gần nhất');
  expect(text()).not.toContain('Đã lưu giới hạn');
  type('Mã PIN để lưu', '864209');
  await press('Lưu giới hạn');
  expect(saveParentDailyLimit).toHaveBeenCalledWith('864209', null, expect.anything());
  expect(text()).toContain('Đã lưu giới hạn');
  expect(view.root.findByProps({ accessibilityLiveRegion: 'polite' }).props.accessibilityRole).toBeUndefined();
  expect(text()).not.toContain('45 phút/ngày');
});

it('aborts an unlock when the account changes and ignores its response', async () => {
  let finish!: (value: { dailyMinutes: number }) => void;
  const open = jest.fn();
  jest.mocked(openParentMode).mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
  await act(async () => {
    view = TestRenderer.create(<ParentProfilePinDialog key="student-a" owner="student-a" onExit={jest.fn()} onOpen={open} />);
  });
  type('Mã PIN', '864209');
  await press('Mở Góc phụ huynh');
  const request = jest.mocked(openParentMode).mock.calls[0][2];
  await act(async () => view.update(<ParentProfilePinDialog key="student-b" owner="student-b" onExit={jest.fn()} onOpen={open} />));
  await act(async () => finish({ dailyMinutes: 60 }));
  expect(request?.aborted).toBe(true);
  expect(open).not.toHaveBeenCalled();
  expect(text()).toContain('Nhập mã PIN');
});

it('saves the game budget through its own PIN-protected API and retains the shared budget', async () => {
  storeParentModeHandoff('student-a', { dailyMinutes: 60, gameMinutes: 30 });
  jest.mocked(saveParentGameLimit).mockResolvedValue({ dailyMinutes: 60, gameMinutes: 15 });
  await act(async () => {
    view = TestRenderer.create(<ParentModePreview owner="student-a" onExit={jest.fn()} />);
  });
  await press('Đổi giới hạn');
  await press('Chơi trò chơi');
  expect(text()).toContain('30 phút/ngày');
  expect(text()).toContain('Chưa tải được thời gian hôm nay.');
  jest.mocked(readStudentUsageWeek).mockResolvedValue({
    today: '2026-11-20',
    totalMillis: 900000,
    days: [{ date: '2026-11-20', elapsedMillis: 900000, gameElapsedMillis: 480000 }],
  });
  await press('Tải lại');
  expect(text()).toContain('8 phút');
  await press('Chọn 15 phút mỗi ngày');
  await press('Xác nhận thay đổi');
  expect(saveParentGameLimit).not.toHaveBeenCalled();
  type('Mã PIN để lưu', '864209');
  await press('Lưu giới hạn');
  expect(saveParentGameLimit).toHaveBeenCalledWith('864209', 15, expect.anything());
  expect(saveParentDailyLimit).not.toHaveBeenCalled();
  expect(text()).toContain('Mức mới: 15 phút/ngày');
  await press('Tổng thời gian');
  expect(text()).toContain('60 phút/ngày');
});


it('polls the protected settings without overwriting a limit draft and prompts again after expiry', async () => {
  jest.useFakeTimers();
  try {
    storeParentModeHandoff('student-a', { dailyMinutes: 45, gameMinutes: 30, grant: 'synthetic-grant' });
    jest.mocked(readParentSettings)
      .mockResolvedValueOnce({ dailyMinutes: 45, gameMinutes: 30 })
      .mockResolvedValueOnce({ dailyMinutes: 90, gameMinutes: 15 })
      .mockRejectedValueOnce('expired');
    await act(async () => {
      view = TestRenderer.create(<ParentModePreview owner="student-a" onExit={jest.fn()} />);
    });
    await press('Đổi giới hạn');
    await press('Chọn 30 phút mỗi ngày');
    await act(async () => { jest.advanceTimersByTime(5000); });
    expect(text()).toContain('90 phút/ngày');
    expect(text()).toContain('Lựa chọn đang chỉnh sửa vẫn được giữ.');
    await press('Xác nhận thay đổi');
    expect(text()).toContain('Tổng thời gian sử dụng · 30 phút/ngày');
    await act(async () => { jest.advanceTimersByTime(5000); });
    expect(text()).toContain('Phiên phụ huynh đã hết hạn');
    expect(text()).not.toContain('90 phút/ngày');
    expect(readParentModeSession('student-a')).toBeUndefined();
  } finally {
    jest.useRealTimers();
  }
});

it.each([
  [false, 'Thiết lập mã PIN', 'SETUP'],
  [true, 'Quên mã PIN?', 'RESET'],
] as const)('recovers the Android PIN using masked account email (configured = %s)', async (configured, title, purpose) => {
  require('react-native').Platform.OS = 'android';
  jest.mocked(readParentControlStatus).mockResolvedValueOnce({
    pinConfigured: configured, dailyLimitReached: true, activityVerified: true,
  });
  jest.mocked(requestParentPinCode).mockResolvedValueOnce({ maskedEmail: 'st***@example.test' });
  jest.mocked(confirmParentPinCode).mockResolvedValueOnce(undefined);
  const onOpen = jest.fn();
  await act(async () => {
    view = TestRenderer.create(<ParentProfilePinDialog owner="student-a" onExit={jest.fn()} onOpen={onOpen} />);
  });
  await press(title);
  await press('Gửi mã xác nhận');
  expect(requestParentPinCode).toHaveBeenCalledWith(purpose, expect.anything());
  expect(text()).toContain('st***@example.test');
  type('Mã xác nhận từ email', '716025');
  type('Mã PIN mới', '398451');
  type('Nhập lại mã PIN mới', '398451');
  await press('Lưu mã PIN mới');
  expect(confirmParentPinCode).toHaveBeenCalledWith(purpose, '716025', '398451', expect.anything());
  expect(onOpen).not.toHaveBeenCalled();
  expect(text()).toContain('Đã lưu mã PIN mới');
  type('Mã PIN', '398451');
  await press('Mở Góc phụ huynh');
  expect(onOpen).toHaveBeenCalled();
});
