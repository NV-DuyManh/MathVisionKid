import React from 'react';
import TestRenderer, { act } from 'react-test-renderer';
import { useRouter } from 'expo-router';
import PortalScreen from '../features/portal/PortalScreen';

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('expo-router', () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
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

const getAllText = () =>
  view.root
    .findAllByType('Text' as any)
    .map((node) => String(node.props.children))
    .join(' ');

beforeEach(() => {
  jest.clearAllMocks();
});

afterEach(() => {
  if (view) {
    act(() => view.unmount());
  }
});

describe('PortalScreen (Unified Mobile Portal)', () => {
  it('renders the complete Unified Portal Web UI on mobile and navigates to login when pressed', async () => {
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

    // Check CTA section
    expect(fullText).toContain('Sẵn sàng đồng hành cùng bé chinh phục môn Toán?');

    // Check Login navigation buttons
    const headerLoginBtn = findByLabel('Đăng nhập');
    expect(headerLoginBtn).toBeDefined();
    act(() => headerLoginBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/login');

    const heroLoginBtn = findByLabel('Đăng nhập để bắt đầu');
    expect(heroLoginBtn).toBeDefined();
    act(() => heroLoginBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/login');

    const googleBtn = findByLabel('Tiếp tục với Google');
    expect(googleBtn).toBeDefined();
    act(() => googleBtn.props.onPress());
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('interactively switches grade calculation when grade selector buttons are tapped', async () => {
    await act(async () => {
      view = TestRenderer.create(<PortalScreen />);
    });

    // Default is Grade 3: Lớp 3A, Nguyễn B***
    expect(getAllText()).toContain('Nguyễn B***');
    expect(getAllText()).toContain('Lớp 3A');

    // Select Grade 1
    const grade1Btn = findByLabel('Lớp 1');
    expect(grade1Btn).toBeDefined();
    act(() => grade1Btn.props.onPress());
    expect(getAllText()).toContain('Trần M***');
    expect(getAllText()).toContain('Lớp 1B');

    // Select Grade 5
    const grade5Btn = findByLabel('Lớp 5');
    expect(grade5Btn).toBeDefined();
    act(() => grade5Btn.props.onPress());
    expect(getAllText()).toContain('Hoàng K***');
    expect(getAllText()).toContain('Lớp 5B');
  });

  it('toggles child answer and displays teacher response', async () => {
    await act(async () => {
      view = TestRenderer.create(<PortalScreen />);
    });

    const replyBtn = findByLabel('Con trả lời: 5 + 8 = 13');
    expect(replyBtn).toBeDefined();

    // Tap to answer
    act(() => replyBtn.props.onPress());
    expect(getAllText()).toContain('Đúng rồi! 5 + 8 = 13');
    expect(getAllText()).toContain('✓ Đã kiểm tra lại');

    // Tap again to toggle back
    const checkedBtn = findByLabel('Đã kiểm tra lại');
    expect(checkedBtn).toBeDefined();
    act(() => checkedBtn.props.onPress());
    expect(getAllText()).toContain('Con trả lời: 5 + 8 = 13');
  });
});
