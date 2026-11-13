/**
 * MathVision Kids — Shared Brand & Design System Tokens
 * Kid-First Premium Visual Identity & Multi-Role Design System
 * Unified Architecture across Public Portal, Student Experience, Teacher Portal, and Admin Portal.
 */

export interface RoleConfig {
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  labelVi: string;
  labelEn: string;
  color: string;
  bgLight: string;
  borderColor: string;
  accent: string;
  descriptionVi: string;
}

export const BRAND_NAME = 'MathVision Kids';
export { WEB_DESIGN } from './web-design';
export const BRAND_TAGLINE_EN = 'Kid-First AI-Assisted Handwritten Arithmetic Grading & Tutoring Platform';
export const BRAND_TAGLINE_VI = 'Nền tảng học toán số học ô ly và gia sư thông minh dành cho học sinh Tiểu học';

export const BRAND_COLORS = {
  // Primary: Learning Blue (Clear, energetic, friendly, trustworthy)
  primary: {
    main: '#2563EB', // Blue 600
    light: '#60A5FA', // Blue 400
    dark: '#1D4ED8', // Blue 700
    subtle: '#EFF6FF', // Blue 50
    contrastText: '#FFFFFF',
  },
  // Mascot Star / Sunshine Amber (Delight, curiosity, encouraging rewards)
  joy: {
    main: '#F59E0B', // Amber 500
    light: '#FDE68A', // Amber 200
    dark: '#D97706', // Amber 600
    subtle: '#FFFBEB', // Amber 50
    contrastText: '#0F172A',
  },
  // Growth / Emerald Mint (Accuracy, teacher workspace, progress)
  success: {
    main: '#10B981', // Emerald 500
    light: '#6EE7B7', // Emerald 300
    dark: '#059669', // Emerald 600
    subtle: '#ECFDF5', // Emerald 50
    contrastText: '#FFFFFF',
  },
  // Energy / Warm Coral (Focus, interactive prompts, delight sparks)
  accent: {
    main: '#F43F5E', // Rose 500
    light: '#FDA4AF', // Rose 300
    dark: '#E11D48', // Rose 600
    subtle: '#FFF1F2', // Rose 50
    contrastText: '#FFFFFF',
  },
  // Warning / Attention
  warning: {
    main: '#F59E0B',
    light: '#FBBF24',
    dark: '#D97706',
    subtle: '#FFFBEB',
    contrastText: '#FFFFFF',
  },
  // Error / Needs revision
  error: {
    main: '#EF4444',
    light: '#FCA5A5',
    dark: '#DC2626',
    subtle: '#FEF2F2',
    contrastText: '#FFFFFF',
  },
  // High-contrast, clean slate neutrals
  neutral: {
    background: '#F8FAFC',
    surface: '#FFFFFF',
    border: '#E2E8F0',
    borderSubtle: '#F1F5F9',
    borderDark: '#CBD5E1',
    textPrimary: '#0F172A',
    textSecondary: '#475569',
    textMuted: '#94A3B8',
  },
};

export const ROLE_CONFIGS: Record<'STUDENT' | 'TEACHER' | 'ADMIN', RoleConfig> = {
  STUDENT: {
    role: 'STUDENT',
    labelVi: 'Học sinh',
    labelEn: 'Student',
    color: '#2563EB',
    bgLight: '#EFF6FF',
    borderColor: '#BFDBFE',
    accent: '#F59E0B',
    descriptionVi: 'Chụp trang vở ô ly, cùng ngôi sao MathVision khám phá từng bước tính và tự tin tiến bộ mỗi ngày.',
  },
  TEACHER: {
    role: 'TEACHER',
    labelVi: 'Giáo viên',
    labelEn: 'Teacher',
    color: '#059669',
    bgLight: '#ECFDF5',
    borderColor: '#A7F3D0',
    accent: '#2563EB',
    descriptionVi: 'Quản lý lớp học, kiểm tra bài làm ô ly học sinh và đánh giá tiến độ sư phạm chuẩn mực.',
  },
  ADMIN: {
    role: 'ADMIN',
    labelVi: 'Quản trị viên',
    labelEn: 'Administrator',
    color: '#0F172A',
    bgLight: '#F1F5F9',
    borderColor: '#CBD5E1',
    accent: '#2563EB',
    descriptionVi: 'Vận hành tài khoản, quản lý hệ thống và giám sát nhật ký an toàn bảo mật.',
  },
};

export const DESIGN_TOKENS = {
  radii: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '22px',
    full: '9999px',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  typography: {
    kidsFont: '"Nunito", "Plus Jakarta Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    systemFont: '"Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    codeFont: '"JetBrains Mono", "Fira Code", monospace',
  },
  motion: {
    instant: '100ms cubic-bezier(0.16, 1, 0.3, 1)',
    fast: '160ms cubic-bezier(0.16, 1, 0.3, 1)',
    normal: '240ms cubic-bezier(0.16, 1, 0.3, 1)',
    slow: '360ms cubic-bezier(0.16, 1, 0.3, 1)',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(15, 23, 42, 0.05)',
    card: '0 1px 3px rgba(15, 23, 42, 0.04), 0 6px 16px -4px rgba(15, 23, 42, 0.04)',
    elevated: '0 12px 28px -6px rgba(37, 99, 235, 0.09), 0 4px 10px -2px rgba(15, 23, 42, 0.03)',
    dropdown: '0 10px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.05)',
    modal: '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
    press: '0 1px 2px rgba(15, 23, 42, 0.08)',
  },
};

export const ECOSYSTEM_URLS = {
  portal: 'http://localhost:5172',
  teacher: 'http://localhost:5173',
  admin: 'http://localhost:5174',
  apiBase: 'http://localhost:8080/api/v1',
};
