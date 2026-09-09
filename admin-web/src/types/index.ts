export type Role = 'STUDENT' | 'TEACHER' | 'ADMIN';

export interface AdminUserSummary {
  userId: string;
  email: string;
  displayName: string;
  role: Role;
  gradeLevel?: number | null;
  active: boolean;
}

export interface AdminClassSummary {
  classId: string;
  name: string;
  gradeLevel: number;
  academicYear?: string | null;
}

export interface AdminUserResponse {
  userId: string;
  email: string;
  displayName: string;
  role: Role;
  gradeLevel?: number | null;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  classes?: AdminClassSummary[];
}

export interface CreateUserRequest {
  email: string;
  displayName: string;
  role: 'STUDENT' | 'TEACHER';
  initialPassword: string;
  gradeLevel?: number;
}

export interface UpdateUserRequest {
  displayName?: string;
  gradeLevel?: number;
}

export interface ResetPasswordRequest {
  temporaryPassword?: string;
}

export interface ResetPasswordResponse {
  userId: string;
  email: string;
  temporaryPassword: string;
  message: string;
}

export interface AdminClassResponse {
  classId: string;
  name: string;
  gradeLevel: number;
  academicYear?: string | null;
  teacher?: AdminUserSummary | null;
  studentCount: number;
  students?: AdminUserSummary[];
  createdAt: string;
}

export interface CreateClassRequest {
  name: string;
  gradeLevel: number;
  academicYear?: string;
  teacherId: string;
}

export interface UpdateClassRequest {
  name?: string;
  gradeLevel?: number;
  academicYear?: string;
}

export interface AssignTeacherRequest {
  teacherId: string;
}

export interface AdminDashboardResponse {
  totalStudents: number;
  activeStudents: number;
  disabledStudents: number;
  totalTeachers: number;
  activeTeachers: number;
  disabledTeachers: number;
  totalClasses: number;
}

export interface AdminAuditEventResponse {
  auditEventId: string;
  eventType: string;
  actorUserId?: string | null;
  actorEmail?: string | null;
  metadata?: Record<string, unknown> | null;
  createdAt: string;
}

export interface Page<T> {
  content: T[];
  totalPages: number;
  totalElements: number;
  number: number;
  size: number;
  first: boolean;
  last: boolean;
  empty: boolean;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    requestId?: string | null;
    details?: Record<string, string> | null;
  };
}
