import { useState } from 'react';
import { Alert, Avatar, Box, Button, Card, CardContent, Skeleton, Typography } from '@mui/material';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import EditOutlined from '@mui/icons-material/EditOutlined';
import LockResetOutlined from '@mui/icons-material/LockResetOutlined';
import ArrowBack from '@mui/icons-material/ArrowBack';
import ArrowForward from '@mui/icons-material/ArrowForward';
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
  const isOwnAccount = Boolean(user && actor?.userId === user.userId);
  const fields = user ? [
    ['Mã người dùng', user.userId],
    ['Ngày tạo', new Date(user.createdAt).toLocaleString('vi-VN')],
    ['Cập nhật gần nhất', new Date(user.updatedAt).toLocaleString('vi-VN')],
    ...(user.gradeLevel ? [['Khối lớp', `Khối ${user.gradeLevel}`]] : []),
  ] : [];
  const classTitle = user?.role === 'TEACHER' ? 'Lớp đang phụ trách'
    : user?.role === 'STUDENT' ? 'Lớp đang tham gia' : 'Phạm vi quản trị';

  return (
    <Box>
      <AdminTopbar title="Chi tiết người dùng" />
      <PageContent>
        <Button component={Link} to="/users" startIcon={<ArrowBack />} sx={{ mb: 2 }}>Danh sách người dùng</Button>
        <RequestError error={query.error} retry={() => { void query.refetch(); }} />
        {!confirm && <RequestError error={action.error} />}
        {action.notice && <Alert severity="success" sx={{ mb: 2 }}>{action.notice}</Alert>}
        {query.isLoading ? (
          <Skeleton variant="rounded" height={300} role="status" aria-label="Đang tải chi tiết" />
        ) : user && !query.error && (
          <>
            <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: 'minmax(0, 1fr) minmax(265px, 0.48fr)' } }}>
              <Card component="section" aria-labelledby="user-name" sx={{ overflow: 'visible' }}>
                <Box sx={{ p: { xs: 2, sm: 3 }, bgcolor: 'var(--admin-paper)', borderRadius: 'var(--admin-panel-radius) var(--admin-panel-radius) 0 0', borderBottom: 1, borderColor: 'var(--admin-paper-line)' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar aria-hidden sx={{ bgcolor: 'var(--admin-tint)', color: 'primary.main', width: 48, height: 48, fontWeight: 800 }}>
                      {user.displayName?.slice(0, 1)}
                    </Avatar>
                    <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
                      <Typography id="user-name" component="h1" variant="h2">{user.displayName}</Typography>
                      <Typography variant="body2" color="text.secondary">{user.email}</Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                    <RoleChip role={user.role} />
                    <StatusChip active={user.active} />
                  </Box>
                </Box>
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Typography component="h2" variant="h4">Thông tin tài khoản</Typography>
                  <Box component="dl" sx={{ m: 0, mt: 2, display: 'grid', gridTemplateColumns: { xs: 'minmax(0,1fr)', sm: 'repeat(2,minmax(0,1fr))' }, columnGap: 2 }}>
                    {fields.map(([label, value]) => (
                      <Box key={label} sx={{ py: 1.25, borderTop: 1, borderColor: 'divider', minWidth: 0 }}>
                        <Typography component="dt" variant="body2" color="text.secondary">{label}</Typography>
                        <Typography component="dd" variant="body2" sx={{ m: 0, mt: 0.25, color: 'text.primary', fontWeight: 700, overflowWrap: 'anywhere', fontVariantNumeric: 'tabular-nums' }}>{value}</Typography>
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>

              <Card component="section" aria-labelledby="user-actions" sx={{ alignSelf: 'start', overflow: 'visible' }}>
                <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                  <Typography id="user-actions" component="h2" variant="h4">Thao tác tài khoản</Typography>
                  <Box sx={{ display: 'grid', gap: 1, mt: 2, '& .MuiButton-root': { justifyContent: 'flex-start' } }}>
                    <Button startIcon={<EditOutlined />} variant="outlined" onClick={() => setEditing(true)} disabled={action.pending}>Chỉnh sửa hồ sơ</Button>
                    <Button startIcon={<LockResetOutlined />} variant="outlined" onClick={() => setResetting(true)} disabled={action.pending}>Đặt lại mật khẩu</Button>
                    <Button variant="outlined" color={user.active ? 'error' : 'success'} disabled={action.pending || isOwnAccount}
                      onClick={() => { action.clear(); setConfirm(true); }}>
                      {user.active ? 'Khóa tài khoản' : 'Mở tài khoản'}
                    </Button>
                  </Box>
                  {isOwnAccount && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Bạn không thể tự khóa tài khoản đang sử dụng.</Typography>
                  )}
                </CardContent>
              </Card>
            </Box>

            <Card component="section" aria-labelledby="user-classes" sx={{ mt: 2, overflow: 'visible' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography id="user-classes" component="h2" variant="h4">{classTitle}</Typography>
                {user.role === 'ADMIN' ? (
                  <Typography color="text.secondary" sx={{ mt: 1.5 }}>Quản lý vận hành hệ thống theo quyền quản trị được cấp.</Typography>
                ) : user.classes?.length ? (
                  <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, mt: 1.5 }}>
                    {user.classes.map((classroom) => (
                      <Box component="li" key={classroom.classId} sx={{ borderTop: 1, borderColor: 'divider' }}>
                        <Button component={Link} to={`/classes/${classroom.classId}`} fullWidth endIcon={<ArrowForward />} sx={{ justifyContent: 'space-between', textAlign: 'left', px: 1 }}>
                          <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
                            <Typography variant="body2" sx={{ fontWeight: 800, color: 'text.primary' }}>{classroom.name}</Typography>
                            <Typography variant="caption" color="text.secondary">Khối {classroom.gradeLevel} · {classroom.academicYear || 'Chưa có năm học'}</Typography>
                          </Box>
                        </Button>
                      </Box>
                    ))}
                  </Box>
                ) : <Typography color="text.secondary" sx={{ mt: 1.5 }}>Chưa có lớp học liên quan.</Typography>}
              </CardContent>
            </Card>
            {editing && <UserFormDialog user={user} onClose={() => setEditing(false)} />}
            {resetting && <PasswordResetDialog user={user} onClose={() => setResetting(false)} />}
            <ConfirmDialog
              open={confirm}
              title={user.active ? 'Khóa tài khoản' : 'Mở lại tài khoản'}
              message={`Xác nhận ${user.active ? 'khóa' : 'mở lại'} tài khoản ${user.email}?`}
              confirmText="Xác nhận"
              isDestructive={user.active}
              loading={action.pending}
              error={action.error}
              onCancel={() => setConfirm(false)}
              onConfirm={() => { void action.run(() => user.active ? adminService.disableUser(userId) : adminService.enableUser(userId), () => setConfirm(false)); }}
            />
          </>
        )}
      </PageContent>
    </Box>
  );
}
