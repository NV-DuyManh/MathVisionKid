import { apiClient } from './apiClient';
import type {
  AdminDashboardResponse,
  AdminUserResponse,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest,
  ResetPasswordResponse,
  AdminClassResponse,
  CreateClassRequest,
  UpdateClassRequest,
  AssignTeacherRequest,
  AdminAuditEventResponse,
  Page,
} from '../../types';

export const adminService = {
  // Dashboard
  async getDashboard(): Promise<AdminDashboardResponse> {
    try {
      const { data } = await apiClient.get<AdminDashboardResponse>('/admin/dashboard');
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        return {
          totalStudents: 150,
          activeStudents: 148,
          disabledStudents: 2,
          totalTeachers: 12,
          activeTeachers: 12,
          disabledTeachers: 0,
          totalClasses: 8,
        };
      }
      throw err;
    }
  },

  // Users
  async getUsers(params?: {
    role?: string;
    active?: boolean;
    query?: string;
    page?: number;
    size?: number;
  }): Promise<Page<AdminUserResponse>> {
    try {
      const { data } = await apiClient.get<Page<AdminUserResponse>>('/admin/users', { params });
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        const mockUsers: AdminUserResponse[] = [
          { userId: 'u_1', email: 'admin.demo@mathvision.local', displayName: 'Demo Administrator', role: 'ADMIN', active: true, createdAt: '2026-09-01T00:00:00Z', updatedAt: '2026-09-01T00:00:00Z' },
          { userId: 'u_2', email: 'lan.teacher@mathvision.local', displayName: 'Ms. Lan', role: 'TEACHER', active: true, createdAt: '2026-09-01T00:00:00Z', updatedAt: '2026-09-01T00:00:00Z', classes: [{ classId: 'c_3a', name: 'Lớp 3A', gradeLevel: 3 }] },
          { userId: 'u_3', email: 'minh.student@mathvision.local', displayName: 'Nguyễn Bình Minh', role: 'STUDENT', gradeLevel: 3, active: true, createdAt: '2026-09-01T00:00:00Z', updatedAt: '2026-09-01T00:00:00Z' },
          { userId: 'u_4', email: 'an.student@mathvision.local', displayName: 'Trần Văn An', role: 'STUDENT', gradeLevel: 3, active: true, createdAt: '2026-09-01T00:00:00Z', updatedAt: '2026-09-01T00:00:00Z' },
          { userId: 'u_5', email: 'binh.student@mathvision.local', displayName: 'Lê Thanh Bình', role: 'STUDENT', gradeLevel: 3, active: true, createdAt: '2026-09-01T00:00:00Z', updatedAt: '2026-09-01T00:00:00Z' },
        ];
        return {
          content: mockUsers,
          totalPages: 1,
          totalElements: mockUsers.length,
          number: 0,
          size: 10,
          first: true,
          last: true,
          empty: false,
        };
      }
      throw err;
    }
  },

  async getUser(userId: string): Promise<AdminUserResponse> {
    try {
      const { data } = await apiClient.get<AdminUserResponse>(`/admin/users/${userId}`);
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        return {
          userId,
          email: 'admin.demo@mathvision.local',
          displayName: 'Demo Administrator',
          role: 'ADMIN',
          active: true,
          createdAt: '2026-09-01T00:00:00Z',
          updatedAt: '2026-09-01T00:00:00Z',
        };
      }
      throw err;
    }
  },

  async createUser(payload: CreateUserRequest): Promise<AdminUserResponse> {
    const { data } = await apiClient.post<AdminUserResponse>('/admin/users', payload);
    return data;
  },

  async updateUser(userId: string, payload: UpdateUserRequest): Promise<AdminUserResponse> {
    const { data } = await apiClient.patch<AdminUserResponse>(`/admin/users/${userId}`, payload);
    return data;
  },

  async disableUser(userId: string): Promise<void> {
    await apiClient.post(`/admin/users/${userId}/disable`);
  },

  async enableUser(userId: string): Promise<void> {
    await apiClient.post(`/admin/users/${userId}/enable`);
  },

  async resetPassword(
    userId: string,
    payload: ResetPasswordRequest
  ): Promise<ResetPasswordResponse> {
    const { data } = await apiClient.post<ResetPasswordResponse>(
      `/admin/users/${userId}/reset-password`,
      payload
    );
    return data;
  },

  // Classes
  async getClasses(params?: {
    gradeLevel?: number;
    academicYear?: string;
    page?: number;
    size?: number;
  }): Promise<Page<AdminClassResponse>> {
    try {
      const { data } = await apiClient.get<Page<AdminClassResponse>>('/admin/classes', { params });
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        const mockClasses: AdminClassResponse[] = [
          {
            classId: 'c_3a',
            name: 'Lớp 3A',
            gradeLevel: 3,
            academicYear: '2025-2026',
            teacher: { userId: 'u_2', email: 'lan.teacher@mathvision.local', displayName: 'Ms. Lan', role: 'TEACHER', active: true },
            studentCount: 30,
            createdAt: '2026-09-01T00:00:00Z',
          },
          {
            classId: 'c_4a',
            name: 'Lớp 4A',
            gradeLevel: 4,
            academicYear: '2025-2026',
            teacher: { userId: 'u_2', email: 'lan.teacher@mathvision.local', displayName: 'Ms. Lan', role: 'TEACHER', active: true },
            studentCount: 28,
            createdAt: '2026-09-01T00:00:00Z',
          },
        ];
        return {
          content: mockClasses,
          totalPages: 1,
          totalElements: mockClasses.length,
          number: 0,
          size: 10,
          first: true,
          last: true,
          empty: false,
        };
      }
      throw err;
    }
  },

  async getClass(classId: string): Promise<AdminClassResponse> {
    try {
      const { data } = await apiClient.get<AdminClassResponse>(`/admin/classes/${classId}`);
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        return {
          classId,
          name: 'Lớp 3A',
          gradeLevel: 3,
          academicYear: '2025-2026',
          teacher: { userId: 'u_2', email: 'lan.teacher@mathvision.local', displayName: 'Ms. Lan', role: 'TEACHER', active: true },
          studentCount: 30,
          createdAt: '2026-09-01T00:00:00Z',
        };
      }
      throw err;
    }
  },

  async createClass(payload: CreateClassRequest): Promise<AdminClassResponse> {
    const { data } = await apiClient.post<AdminClassResponse>('/admin/classes', payload);
    return data;
  },

  async updateClass(classId: string, payload: UpdateClassRequest): Promise<AdminClassResponse> {
    const { data } = await apiClient.patch<AdminClassResponse>(`/admin/classes/${classId}`, payload);
    return data;
  },

  async assignTeacher(classId: string, payload: AssignTeacherRequest): Promise<AdminClassResponse> {
    const { data } = await apiClient.put<AdminClassResponse>(
      `/admin/classes/${classId}/teacher`,
      payload
    );
    return data;
  },

  // Audit
  async getAudit(params?: {
    eventType?: string;
    actorUserId?: string;
    page?: number;
    size?: number;
  }): Promise<Page<AdminAuditEventResponse>> {
    try {
      const { data } = await apiClient.get<Page<AdminAuditEventResponse>>('/admin/audit', { params });
      return data;
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response || err.message?.includes('Network Error')) {
        return {
          content: [
            {
              auditEventId: 'evt_1',
              eventType: 'USER_LOGIN_SUCCESS',
              actorUserId: 'u_admin_001',
              actorEmail: 'admin.demo@mathvision.local',
              metadata: { role: 'ADMIN' },
              createdAt: new Date().toISOString(),
            },
            {
              auditEventId: 'evt_2',
              eventType: 'CLASS_CREATED',
              actorUserId: 'u_admin_001',
              actorEmail: 'admin.demo@mathvision.local',
              metadata: { className: 'Lớp 3A', gradeLevel: 3 },
              createdAt: new Date(Date.now() - 3600000).toISOString(),
            },
          ],
          totalPages: 1,
          totalElements: 2,
          number: 0,
          size: 10,
          first: true,
          last: true,
          empty: false,
        };
      }
      throw err;
    }
  },
};
