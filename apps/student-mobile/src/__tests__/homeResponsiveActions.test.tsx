import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { StyleSheet } from 'react-native';
import { HomeDashboard } from '../components/home/HomeDashboard';
import { AuthContext } from '../context/AuthContext';
import { getProblemsByGrade } from '../data/primaryMathCurriculum';
const mockPush = jest.fn();
const mockProfile: { value?: any; failed?: boolean; retry: jest.Mock } = { retry: jest.fn() };
jest.mock('react-native/Libraries/Utilities/useWindowDimensions', () => ({ __esModule: true, default: () => ({ width: 390, height: 844, scale: 1, fontScale: 1 }) }));
jest.mock('expo-router', () => ({ useRouter: () => ({ push: mockPush }), useFocusEffect: jest.fn() }));
jest.mock('../features/calculator/PocketCalculator', () => ({ PocketCalculator: () => null }));
jest.mock('../features/student-profile/useStudentProfile', () => ({ useStudentProfile: () => mockProfile }));
let tree: TestRenderer.ReactTestRenderer;
const button = (label: string) => tree.root.findAll(node => node.props.accessibilityLabel === label && node.props.onPress)[0];
const render = (user?: any, onPractice = jest.fn()) => act(() => { tree = TestRenderer.create(<AuthContext.Provider value={{ user } as any}><HomeDashboard userName="An" userKey={user?.id} onAcquire={() => {}} onArithmetic={() => {}} onPractice={onPractice} onTips={() => {}} onPrivacy={() => {}} /></AuthContext.Provider>); });
beforeEach(() => { jest.clearAllMocks(); mockProfile.value = undefined; mockProfile.failed = false; });
afterEach(() => { act(() => tree?.unmount()); });

it('keeps four equal quick actions in one non-scrolling row on a phone and after resizing', () => {
  render();
  const grid = tree.root.findAll(node => node.props.testID === 'quick-actions-grid')[0];
  expect(StyleSheet.flatten(grid.props.style).flexDirection).toBe('row');
  const cards = grid.findAll(node => typeof node.props.onPress === 'function');
  expect(cards).toHaveLength(4);
  expect(cards.map(card => StyleSheet.flatten(card.props.style({ pressed: false })).flex)).toEqual([1, 1, 1, 1]);
  expect(button('Tiện ích trước')).toBeUndefined();
  expect(button('Tiện ích tiếp theo')).toBeUndefined();
  expect(tree.root.findAll(node => node.props.testID === 'quick-actions-carousel')).toHaveLength(0);
  act(() => button('Luyện tập. Làm bài theo chủ đề').props.onPress());
  expect(mockPush).toHaveBeenLastCalledWith('/(tabs)/lessons');
  act(() => tree.root.findAll(node => node.props.onLayout)[0].props.onLayout({ nativeEvent: { layout: { width: 1100 } } }));
  expect(tree.root.findAll(node => node.props.testID === 'quick-actions-grid')).not.toHaveLength(0);
});

it('uses real identity, recommendations and exactly four journey entry points', () => {
  mockProfile.value = { displayName: 'Bình Minh', gradeLevel: 5, avatar: 'star', stats: { streak: 0, today: 0 }, history: [] };
  render({ id: 'student', gradeLevel: 5 });
  const text = tree.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
  expect(text).toContain('Bình Minh!');
  expect(text).toContain('Bài học gợi ý cho em');
  const journey = tree.root.findAll(node => node.props.testID === 'learning-journey')[0];
  expect(journey.findAll(node => node.props.onPress)).toHaveLength(4);
  act(() => button('Kiểm tra. Thử sức với câu đố').props.onPress());
  expect(mockPush).toHaveBeenLastCalledWith('/quiz');
  const [recommended, second] = getProblemsByGrade(5);
  expect(button(`Học bài ${recommended.title}`)).toBeDefined();
  expect(button(`Học bài ${second.title}`)).toBeUndefined();
  expect(text).not.toContain('Chương trình Toán lớp');
});

it('does not count saved drafts or opens as learning and uses authoritative streak', () => {
  mockProfile.value = { displayName: 'An', gradeLevel: 3, avatar: 'star', stats: { streak: 5, today: 1 }, history: [] };
  render({ id: 'student', gradeLevel: 3 });
  const text = tree.root.findAllByType('Text' as any).map(node => String(node.props.children)).join(' ');
  expect(text).toContain('Em đã học liên tiếp 5 ngày!');
  expect(text).not.toContain('Theo bài đã lưu');
  act(() => button('Thông báo học tập').props.onPress());
  expect(tree.root.findAllByType('Text' as any).some(node => String(node.props.children).includes('Chưa có thông báo mới'))).toBe(true);
});
