import { Chip } from '@mui/material';
export const EVENT_LABELS: Record<string, string> = {
  ADMIN_USER_CREATED: 'Tạo người dùng', ADMIN_USER_UPDATED: 'Cập nhật hồ sơ',
  ADMIN_USER_DISABLED: 'Khóa tài khoản', ADMIN_USER_ENABLED: 'Mở tài khoản',
  ADMIN_USER_PASSWORD_RESET: 'Đặt lại mật khẩu', ADMIN_CLASS_CREATED: 'Tạo lớp học',
  ADMIN_CLASS_UPDATED: 'Cập nhật lớp', ADMIN_CLASS_TEACHER_ASSIGNED: 'Phân công giáo viên',
  ADMIN_STUDENT_ADDED_TO_CLASS: 'Thêm học sinh vào lớp', ADMIN_STUDENT_REMOVED_FROM_CLASS: 'Xóa học sinh khỏi lớp',
};
export function AuditEventChip({ type }: { type: string }) {
  return <Chip size="small" label={EVENT_LABELS[type] || type} sx={{ bgcolor: 'primary.light', color: 'primary.dark', height: 'auto', minHeight: 28, '& .MuiChip-label': { whiteSpace: 'normal', py: .5 } }} />;
}
