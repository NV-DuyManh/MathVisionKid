/**
 * MathVision Kids — Shared Brand & Design Tokens
 */

export interface RoleConfig {
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  labelVi: string;
  labelEn: string;
  color: string;
  bgLight: string;
  borderColor: string;
  descriptionVi: string;
}

export const BRAND_NAME = 'MathVision Kids';
export const BRAND_TAGLINE_EN = 'An AI-Assisted Handwritten Arithmetic Grading and Tutoring Platform';
export const BRAND_TAGLINE_VI = 'Nền tảng chấm điểm số học và nhận diện chữ viết tay ứng dụng AI';

export const BRAND_COLORS = {
  primary: {
    main: '#4F46E5', // Indigo 600
    light: '#818CF8',
    dark: '#3730A3',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#0284C7', // Sky 600
    light: '#38BDF8',
    dark: '#0369A1',
    contrastText: '#FFFFFF',
  },
  success: {
    main: '#10B981', // Emerald 500
    light: '#34D399',
    dark: '#059669',
    contrastText: '#FFFFFF',
  },
  warning: {
    main: '#F59E0B', // Amber 500
    light: '#FBBF24',
    dark: '#D97706',
    contrastText: '#FFFFFF',
  },
  error: {
    main: '#EF4444', // Red 500
    light: '#F87171',
    dark: '#DC2626',
    contrastText: '#FFFFFF',
  },
  neutral: {
    background: '#F8FAFC', // Slate 50
    surface: '#FFFFFF',
    border: '#E2E8F0', // Slate 200
    textPrimary: '#0F172A', // Slate 900
    textSecondary: '#64748B', // Slate 500
  },
};

export const ROLE_CONFIGS: Record<'STUDENT' | 'TEACHER' | 'ADMIN', RoleConfig> = {
  STUDENT: {
    role: 'STUDENT',
    labelVi: 'Học sinh',
    labelEn: 'Student',
    color: '#4F46E5',
    bgLight: '#EEF2FF',
    borderColor: '#C7D2FE',
    descriptionVi: 'Chụp bài viết tay, nhận phản hồi tức thì và rèn luyện kỹ năng số học.',
  },
  TEACHER: {
    role: 'TEACHER',
    labelVi: 'Giáo viên',
    labelEn: 'Teacher',
    color: '#10B981',
    bgLight: '#ECFDF5',
    borderColor: '#A7F3D0',
    descriptionVi: 'Quản lý lớp học, bài tập, tải bài hàng loạt và xem lại kết quả chấm điểm.',
  },
  ADMIN: {
    role: 'ADMIN',
    labelVi: 'Quản trị viên',
    labelEn: 'Administrator',
    color: '#F59E0B',
    bgLight: '#FFFBEB',
    borderColor: '#FDE68A',
    descriptionVi: 'Quản lý tài khoản, lớp học và theo dõi nhật ký hoạt động hệ thống.',
  },
};

export const ECOSYSTEM_URLS = {
  portal: 'http://localhost:5172',
  teacher: 'http://localhost:5173',
  admin: 'http://localhost:5174',
  apiBase: 'http://localhost:8080/api/v1',
};
