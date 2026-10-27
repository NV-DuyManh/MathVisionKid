import apiClient from './apiClient';
import { ENV } from '../../config/env';
import { tokenStorage } from '../auth/tokenStorage';

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user?: any;
}

export const DEMO_STUDENTS: Record<string, { name: string; gradeLevel: number }> = {
  'minh.student@mathvision.local': { name: 'Nguyễn Bình Minh', gradeLevel: 3 },
  'an.student@mathvision.local': { name: 'Trần Văn An', gradeLevel: 3 },
  'binh.student@mathvision.local': { name: 'Lê Thanh Bình', gradeLevel: 3 },
  'cuong.student@mathvision.local': { name: 'Phạm Quốc Cường', gradeLevel: 3 },
  'dung.student@mathvision.local': { name: 'Hoàng Ngọc Dũng', gradeLevel: 3 },
  'giang.student@mathvision.local': { name: 'Vũ Hương Giang', gradeLevel: 3 },
  'ha.student@mathvision.local': { name: 'Đỗ Thu Hà', gradeLevel: 3 },
  'khoa.student@mathvision.local': { name: 'Bùi Anh Khoa', gradeLevel: 3 },
  'linh.student@mathvision.local': { name: 'Ngô Phương Linh', gradeLevel: 3 },
  'mai.student@mathvision.local': { name: 'Đặng Tuyết Mai', gradeLevel: 3 },
  'nam.student@mathvision.local': { name: 'Dương Nhật Nam', gradeLevel: 3 },
};


export const getMockStudentUser = (email: string) => {
  const normEmail = (email || '').toLowerCase().trim();
  const info = DEMO_STUDENTS[normEmail];
  if (!ENV.USE_MOCK || !info) throw Object.assign(new Error('Tài khoản không có quyền sử dụng ứng dụng học sinh. Vui lòng đăng nhập qua cổng MathVision Kids trên trình duyệt.'), { code: 'STUDENT_ACCESS_DENIED' });
  const id = `mock_student_${normEmail.replace(/[^a-z0-9]/g, '_')}`;
  return { userId: id, id, email: normEmail, displayName: info.name, name: info.name,
    role: 'STUDENT', active: true, gradeLevel: info.gradeLevel, grade: info.gradeLevel };
};
export const authApi = {
  async login(credentials: any): Promise<LoginResponse> {
    const email = String(credentials.email || '').trim().toLowerCase();
    if (!ENV.USE_MOCK) {
      const { data } = await apiClient.post('/auth/login', { email, password: credentials.password });
      // Never trust an inline profile; real sessions are verified separately through /me.
      return { accessToken: data.accessToken, refreshToken: data.refreshToken };
    }
    const user = getMockStudentUser(email);
    if (typeof credentials.password !== 'string' || credentials.password.length < 6) {
      throw Object.assign(new Error('Vui lòng nhập mật khẩu có ít nhất 6 ký tự.'), { code: 'VALIDATION_ERROR' });
    }
    return { accessToken: `demo_student_token_${user.userId}`,
      refreshToken: `demo_student_refresh_${user.userId}`, user };
  },
  async logout(accessToken?: string | null): Promise<void> {
    if (ENV.USE_MOCK) return;
    const token = accessToken === undefined ? await tokenStorage.getAccessToken() : accessToken;
    try {
      if (token) await apiClient.post('/auth/logout', {}, { timeout: 5000, headers: { Authorization: `Bearer ${token}` } });
    } catch { /* Local logout remains available offline. */ }
  },
  async getMe(): Promise<any> {
    if (!ENV.USE_MOCK) return (await apiClient.get('/me')).data;
    const [savedUser, token] = await Promise.all([tokenStorage.getUser(), tokenStorage.getAccessToken()]);
    const user = getMockStudentUser(savedUser?.email);
    if (token !== `demo_student_token_${user.userId}` || savedUser?.role !== 'STUDENT') {
      throw new Error('Phiên thử nghiệm không hợp lệ. Vui lòng đăng nhập lại.');
    }
    return user;
  },
};
