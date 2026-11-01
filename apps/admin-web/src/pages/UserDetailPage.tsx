import { useState } from 'react';
import { Alert, Avatar, Box, Button, Card, CardContent, Divider, Skeleton, Typography } from '@mui/material';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import EditOutlined from '@mui/icons-material/EditOutlined';
import LockResetOutlined from '@mui/icons-material/LockResetOutlined';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { adminService } from '../services/api/adminService';
import { useAdminAction } from '../hooks/useAdminAction';
import { useAuth } from '../context/AuthContext';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { RequestError } from '../components/common/RequestError';
import { RoleChip } from '../components/common/RoleChip';
import { StatusChip } from '../components/common/StatusChip';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { UserFormDialog } from '../components/users/UserFormDialog';
import { PasswordResetDialog } from '../components/users/PasswordResetDialog';
export function UserDetailPage() {
  const { userId = '' } = useParams();
  return <UserDetail key={userId} userId={userId} />;
}
function UserDetail({ userId }: { userId: string }) {
  const { user: actor } = useAuth();
  const [editing, setEditing] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [resetting, setResetting] = useState(false);
  const action = useAdminAction();
  const query = useQuery({ queryKey: ['admin-user', userId], queryFn: () => adminService.getUser(userId) });
  const user = query.data;
  return <Box><AdminTopbar title="Chi tiết người dùng" subtitle="Hồ sơ, trạng thái và các lớp học liên quan" /><PageContent>
    <Button component={Link} to="/users" startIcon={<ArrowBack />} sx={{ mb: 2 }}>Danh sách người dùng</Button>
    <RequestError error={query.error} retry={() => { void query.refetch(); }} />
    <RequestError error={action.error} />
    {action.notice && <Alert severity="success" sx={{ mb: 2 }}>{action.notice}</Alert>}
    {query.isLoading ? <Skeleton variant="rounded" height={300} role="status" aria-label="Đang tải chi tiết" /> : user && !query.error && <>
      <Card sx={{ mb: 3 }}><CardContent sx={{ p: { xs: 2.5, sm: 4 } }}>
        <Box className="page-actions">
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', minWidth: 0 }}><Avatar sx={{ bgcolor: 'primary.light', color: 'primary.dark', width: 56, height: 56, fontWeight: 800 }}>{user.displayName?.slice(0, 1)}</Avatar>
            <Box sx={{ minWidth: 0 }}><Typography component="h2" variant="h5" sx={{ overflowWrap: 'anywhere' }}>{user.displayName}</Typography><Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{user.email}</Typography></Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}><RoleChip role={user.role} /><StatusChip active={user.active} /></Box>
        </Box>
        <Divider sx={{ mb: 3 }} />
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2,minmax(0,1fr))', lg: 'repeat(3,minmax(0,1fr))' }, gap: 3 }}>
          {[['Mã người dùng', user.userId], ['Ngày tạo', new Date(user.createdAt).toLocaleString('vi-VN')], ['Cập nhật gần nhất', new Date(user.updatedAt).toLocaleString('vi-VN')], ...(user.gradeLevel ? [['Khối lớp', `Khối ${user.gradeLevel}`]] : [])].map(([label, value]) =>
            <Box key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2" sx={{ mt: .5, overflowWrap: 'anywhere' }}>{value}</Typography></Box>)}
        </Box>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, mt: 4 }}>
          <Button startIcon={<EditOutlined />} variant="outlined" onClick={() => setEditing(true)} disabled={action.pending}>Chỉnh sửa hồ sơ</Button>
          <Button startIcon={<LockResetOutlined />} variant="outlined" color="warning" onClick={() => setResetting(true)} disabled={action.pending}>Đặt lại mật khẩu</Button>
          <Button variant="outlined" color={user.active ? 'error' : 'success'} disabled={action.pending || actor?.userId === user.userId} onClick={() => { action.clear(); setConfirm(true); }}>{user.active ? 'Khóa tài khoản' : 'Mở tài khoản'}</Button>
        </Box>
        {actor?.userId === user.userId && <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>Bạn không thể tự khóa tài khoản đang sử dụng.</Typography>}
      </CardContent></Card>
      <Card><CardContent sx={{ p: 3 }}>
        <Typography variant="h6" component="h2" sx={{ mb: 2 }}>{user.role === 'TEACHER' ? 'Lớp đang phụ trách' : user.role === 'STUDENT' ? 'Lớp đang tham gia' : 'Phạm vi quản trị'}</Typography>
        {user.role === 'ADMIN' ? <Typography color="text.secondary">Quản lý vận hành hệ thống theo quyền quản trị được cấp.</Typography> :
          user.classes?.length ? <Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: { xs: '1fr', sm: 'repeat(2,minmax(0,1fr))' } }}>{user.classes.map(c => <Button key={c.classId} component={Link} to={`/classes/${c.classId}`} variant="outlined" sx={{ display: 'block', textAlign: 'left', p: 2 }}>
            <Typography sx={{ fontWeight: 800,  }}>{c.name}</Typography><Typography variant="caption" color="text.secondary">Khối {c.gradeLevel} · {c.academicYear || 'Chưa có năm học'}</Typography>
          </Button>)}</Box> : <Typography color="text.secondary">Chưa có lớp học liên quan.</Typography>}
      </CardContent></Card>
      {editing && <UserFormDialog user={user} onClose={() => setEditing(false)} />}
      {resetting && <PasswordResetDialog user={user} onClose={() => setResetting(false)} />}
      <ConfirmDialog open={confirm} title={user.active ? 'Khóa tài khoản' : 'Mở lại tài khoản'} message={`Xác nhận ${user.active ? 'khóa' : 'mở lại'} tài khoản ${user.email}?`} confirmText="Xác nhận" isDestructive={user.active} loading={action.pending} error={action.error}
        onCancel={() => setConfirm(false)} onConfirm={() => { void action.run(() => user.active ? adminService.disableUser(userId) : adminService.enableUser(userId), () => setConfirm(false)); }} />
    </>}
  </PageContent></Box>;
}
