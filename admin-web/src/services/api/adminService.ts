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
    const { data } = await apiClient.get<AdminDashboardResponse>('/admin/dashboard');
    return data;
  },

  // Users
  async getUsers(params?: {
    role?: string;
    active?: boolean;
    query?: string;
    page?: number;
    size?: number;
  }): Promise<Page<AdminUserResponse>> {
    const { data } = await apiClient.get<Page<AdminUserResponse>>('/admin/users', { params });
    return data;
  },

  async getUser(userId: string): Promise<AdminUserResponse> {
    const { data } = await apiClient.get<AdminUserResponse>(`/admin/users/${userId}`);
    return data;
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
    payload?: ResetPasswordRequest
  ): Promise<ResetPasswordResponse> {
    const { data } = await apiClient.post<ResetPasswordResponse>(
      `/admin/users/${userId}/reset-password`,
      payload || {}
    );
    return data;
  },

  // Classes
  async getClasses(params?: {
    page?: number;
    size?: number;
  }): Promise<Page<AdminClassResponse>> {
    const { data } = await apiClient.get<Page<AdminClassResponse>>('/admin/classes', { params });
    return data;
  },

  async getClass(classId: string): Promise<AdminClassResponse> {
    const { data } = await apiClient.get<AdminClassResponse>(`/admin/classes/${classId}`);
    return data;
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

  async addStudentToClass(classId: string, studentId: string): Promise<AdminClassResponse> {
    const { data } = await apiClient.post<AdminClassResponse>(
      `/admin/classes/${classId}/students/${studentId}`
    );
    return data;
  },

  async removeStudentFromClass(classId: string, studentId: string): Promise<AdminClassResponse> {
    const { data } = await apiClient.delete<AdminClassResponse>(
      `/admin/classes/${classId}/students/${studentId}`
    );
    return data;
  },

  // Audit
  async getAudit(params?: {
    eventType?: string;
    page?: number;
    size?: number;
  }): Promise<Page<AdminAuditEventResponse>> {
    const { data } = await apiClient.get<Page<AdminAuditEventResponse>>('/admin/audit', {
      params,
    });
    return data;
  },
};
