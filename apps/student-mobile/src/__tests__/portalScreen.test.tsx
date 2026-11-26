import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import PortalScreen from '../features/portal/PortalScreen';
import { hasCompletedOnboarding } from '../features/onboarding/onboardingStorage';

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
}));

jest.mock('../features/onboarding/onboardingStorage', () => ({
  hasCompletedOnboarding: jest.fn(async () => true),
}));

jest.mock('react-native-safe-area-context', () => ({
  SafeAreaView: 'SafeAreaView',
}));

jest.mock('expo-linear-gradient', () => ({
  LinearGradient: 'LinearGradient',
}));

jest.mock('@expo/vector-icons', () => ({
  Ionicons: 'Ionicons',
}));

let view: TestRenderer.ReactTestRenderer;

const findByLabel = (label: string) =>
  view.root.findAll((node) => node.props.accessibilityLabel === label && typeof node.props.onPress === 'function')[0];

const findByLabelPrefix = (prefix: string) =>
  view.root.findAll(
    (node) => typeof node.props.accessibilityLabel === 'string' && node.props.accessibilityLabel.startsWith(prefix) && typeof node.props.onPress === 'function'
  )[0];

const getAllText = () =>
  view.root
    .findAllByType('Text' as any)
    .map((node) => {
      const children = node.props.children;
      return Array.isArray(children) ? children.join('') : String(children ?? '');
    })
    .join(' ');

beforeEach(() => {
  jest.clearAllMocks();
  jest.mocked(hasCompletedOnboarding).mockResolvedValue(true);
});

afterEach(() => {
  if (view) {
    act(() => view.unmount());
  }
});

describe('PortalScreen (Unified Mobile Portal)', () => {
  it('renders the complete Unified Portal Web UI on mobile and routes based on onboarding state', async () => {
    await act(async () => {
      view = TestRenderer.create(<PortalScreen />);
    });

    const fullText = getAllText();

    // Check Header & Hero headline
    expect(fullText).toContain('MathVisionKids');
    expect(fullText).toContain('Mở vở ô ly, học toán');
    expect(fullText).toContain('từng bước');
    expect(fullText).toContain('Gia sư gợi mở cho học sinh lớp 1 đến lớp 5');

    // Check Socratic, Comparison, and Ethics sections
    expect(fullText).toContain('Phương pháp Socratic');
    expect(fullText).toContain('Bé hiểu bài thật sâu, thay vì chép bài thụ động');
    expect(fullText).toContain('Tại sao gợi mở tư duy tốt hơn đưa sẵn đáp số?');
    expect(fullText).toContain('Cam kết sư phạm và an toàn cho trẻ');
    expect(fullText).toContain('Không giải hộ bài tập');
    expect(fullText).toContain('Thầy cô là người định đoạt');
    expect(fullText).toContain('Bảo vệ dữ liệu học sinh');

    // Check CTA section does not promise unsupported Facebook/unconfigured social login
    expect(fullText).toContain('Sẵn sàng đồng hành cùng bé chinh phục môn Toán?');
    expect(fullText).not.toContain('Tiếp tục với Facebook');
    expect(fullText).not.toContain('Tiếp tục với Google');

    // Check Login navigation buttons when onboarding is completed
    const headerLoginBtn = findByLabel('Đăng nhập');
    expect(headerLoginBtn).toBeDefined();
    await act(async () => headerLoginBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/login');

    const heroLoginBtn = findByLabel('Đăng nhập để bắt đầu');
    expect(heroLoginBtn).toBeDefined();
    await act(async () => heroLoginBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/login');

    // Check first-time onboarding route when not completed
    jest.mocked(hasCompletedOnboarding).mockResolvedValueOnce(false);
    const ctaLoginBtn = findByLabel('Đăng nhập tài khoản');
    expect(ctaLoginBtn).toBeDefined();
    await act(async () => ctaLoginBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/welcome');
  });

  it('interactively switches grade calculation, updates accessibilityState, and resets checked state', async () => {
    await act(async () => {
      view = TestRenderer.create(<PortalScreen />);
    });

    // Default is Grade 3: Lớp 3A, Nguyễn B***, selected accessibilityState
    expect(getAllText()).toContain('Nguyễn B***');
    expect(getAllText()).toContain('Lớp 3A');
    expect(findByLabelPrefix('Lớp 3').props.accessibilityState).toEqual({ selected: true });
    expect(findByLabelPrefix('Lớp 1').props.accessibilityState).toEqual({ selected: false });

    // Toggle answer in Grade 3 first
    const grade3ReplyBtn = findByLabel('Con trả lời: 5 + 8 = 13');
    act(() => grade3ReplyBtn.props.onPress());
    expect(getAllText()).toContain('↺ Xem lại bài làm ban đầu');

    // Select Grade 1 -> resets answered state and updates selected state
    act(() => findByLabelPrefix('Lớp 1').props.onPress());
    expect(getAllText()).toContain('Trần M***');
    expect(getAllText()).toContain('Lớp 1B');
    expect(getAllText()).not.toContain('↺ Xem lại bài làm ban đầu');
    expect(findByLabelPrefix('Lớp 1').props.accessibilityState).toEqual({ selected: true });
    expect(findByLabelPrefix('Lớp 3').props.accessibilityState).toEqual({ selected: false });

    // Select Grade 5
    act(() => findByLabelPrefix('Lớp 5').props.onPress());
    expect(getAllText()).toContain('Hoàng K***');
    expect(getAllText()).toContain('Lớp 5B');
  });

  it('shows corrected digits and historical label across all 5 grades when checked', async () => {
    await act(async () => {
      view = TestRenderer.create(<PortalScreen />);
    });

    const expectedByGrade: Record<number, { wrong: string; corrected: string; answerLabel: string }> = {
      1: { wrong: '11', corrected: '12', answerLabel: 'Con trả lời: 7 + 5 = 12' },
      2: { wrong: '74', corrected: '84', answerLabel: 'Con trả lời: 4 + 3 + 1 = 8' },
      3: { wrong: '413', corrected: '423', answerLabel: 'Con trả lời: 5 + 8 = 13' },
      4: { wrong: '4252', corrected: '4262', answerLabel: 'Con trả lời: 2 + 3 + 1 = 6' },
      5: { wrong: '53,3', corrected: '54,3', answerLabel: 'Con trả lời: 4 + 9 + 1 = 14' },
    };

    for (const grade of [1, 2, 3, 4, 5]) {
      act(() => findByLabelPrefix(`Lớp ${grade}`).props.onPress());
      const info = expectedByGrade[grade];
      expect(getAllText()).toContain('Bài làm ban đầu của học sinh:');

      const replyBtn = findByLabel(info.answerLabel);
      expect(replyBtn).toBeDefined();
      act(() => replyBtn.props.onPress());

      const afterText = getAllText();
      expect(afterText).toContain('✓ Đã sửa theo gợi ý:');
      expect(afterText).toContain(`(Gốc chưa sửa: ${info.wrong} → Kết quả đúng: ${info.corrected})`);
      expect(afterText).toContain('↺ Xem lại bài làm ban đầu');

      // Toggle back to initial state
      const resetBtn = findByLabel('Xem lại bài làm ban đầu');
      expect(resetBtn).toBeDefined();
      act(() => resetBtn.props.onPress());
      expect(getAllText()).toContain(info.answerLabel);
    }
  });
});
