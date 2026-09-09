import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LockResetIcon from '@mui/icons-material/LockReset';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SchoolIcon from '@mui/icons-material/School';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { RoleChip } from '../components/common/RoleChip';
import { StatusChip } from '../components/common/StatusChip';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import type { UpdateUserRequest, ResetPasswordResponse } from '../types';

export const UserDetailPage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Dialog states
  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [editDisplayName, setEditDisplayName] = useState<string>('');
  const [editGradeLevel, setEditGradeLevel] = useState<number>(3);
  const [editError, setEditError] = useState<string | null>(null);

  const [isDisableConfirmOpen, setIsDisableConfirmOpen] = useState<boolean>(false);
  const [isEnableConfirmOpen, setIsEnableConfirmOpen] = useState<boolean>(false);

  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState<boolean>(false);
  const [resetSuccessData, setResetSuccessData] = useState<ResetPasswordResponse | null>(null);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  // Fetch user details
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['admin-user', userId],
    queryFn: () => adminService.getUser(userId!),
    enabled: !!userId,
  });

  // Edit mutation
  const editMutation = useMutation({
    mutationFn: (payload: UpdateUserRequest) => adminService.updateUser(userId!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-user', userId], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setIsEditOpen(false);
      setEditError(null);
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setEditError(e.response?.data?.error?.message || e.message || 'Cập nhật thất bại.');
    },
  });

  // Disable mutation
  const disableMutation = useMutation({
    mutationFn: () => adminService.disableUser(userId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-user', userId] });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      setIsDisableConfirmOpen(false);
    },
  });

  // Enable mutation
  const enableMutation = useMutation({
    mutationFn: () => adminService.enableUser(userId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-user', userId] });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      setIsEnableConfirmOpen(false);
    },
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: () => adminService.resetPassword(userId!),
    onSuccess: (data) => {
      setResetSuccessData(data);
      setIsResetConfirmOpen(false);
    },
  });

  const handleOpenEdit = () => {
    if (!user) return;
    setEditDisplayName(user.displayName);
    if (user.role === 'STUDENT' && user.gradeLevel) {
      setEditGradeLevel(user.gradeLevel);
    }
    setEditError(null);
    setIsEditOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const payload: UpdateUserRequest = {
      displayName: editDisplayName.trim(),
    };
    if (user?.role === 'STUDENT') {
      payload.gradeLevel = editGradeLevel;
    }
    editMutation.mutate(payload);
  };

  const handleCopyPassword = () => {
    if (resetSuccessData?.temporaryPassword) {
      navigator.clipboard.writeText(resetSuccessData.temporaryPassword);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={36} sx={{ color: '#0F172A' }} />
      </Box>
    );
  }

  if (error || !user) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Không thể tải thông tin người dùng hoặc người dùng không tồn tại.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/users')}>
          Quay lại danh sách
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <AdminTopbar title="Chi tiết Người dùng" subtitle={`ID: ${user.userId}`} />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Back Link */}
        <Box sx={{ mb: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/users')}
            sx={{ color: '#64748B', fontWeight: 600 }}
          >
            Danh sách người dùng
          </Button>
        </Box>

        {/* Profile Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 3 }}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  {user.displayName}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
                  {user.email}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mt: 1.5, alignItems: 'center' }}>
                  <RoleChip role={user.role} />
                  <StatusChip active={user.active} />
                  {user.role === 'STUDENT' && user.gradeLevel && (
                    <Typography variant="caption" sx={{ bgcolor: '#F1F5F9', px: 1, py: 0.5, borderRadius: 1, fontWeight: 600 }}>
                      Khối {user.gradeLevel}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={handleOpenEdit}
                  sx={{ borderColor: '#CBD5E1', color: '#0F172A' }}
                >
                  Chỉnh sửa
                </Button>

                <Button
                  variant="outlined"
                  size="small"
                  color="warning"
                  startIcon={<LockResetIcon />}
                  onClick={() => setIsResetConfirmOpen(true)}
                >
                  Đặt lại mật khẩu
                </Button>

                {user.active ? (
                  <Button
                    variant="outlined"
                    size="small"
                    color="error"
                    startIcon={<BlockIcon />}
                    onClick={() => setIsDisableConfirmOpen(true)}
                  >
                    Vô hiệu hóa
                  </Button>
                ) : (
                  <Button
                    variant="outlined"
                    size="small"
                    color="success"
                    startIcon={<CheckCircleIcon />}
                    onClick={() => setIsEnableConfirmOpen(true)}
                  >
                    Kích hoạt lại
                  </Button>
                )}
              </Box>
            </Box>

            <Divider sx={{ my: 2.5 }} />

            {/* Metadata Grid */}
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Mã người dùng
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A', wordBreak: 'break-all', mt: 0.5 }}>
                  {user.userId}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Ngày tạo tài khoản
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A', mt: 0.5 }}>
                  {new Date(user.createdAt).toLocaleString('vi-VN')}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Cập nhật lần cuối
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A', mt: 0.5 }}>
                  {new Date(user.updatedAt).toLocaleString('vi-VN')}
                </Typography>
              </Grid>

              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Bảo mật vai trò
                </Typography>
                <Typography variant="body2" sx={{ color: '#059669', mt: 0.5, fontWeight: 500 }}>
                  Vai trò cố định bất biến
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Classes Enrollment/Teaching Section */}
        <Card>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SchoolIcon sx={{ color: '#2563EB' }} />
              <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                {user.role === 'TEACHER' ? 'Các lớp đang phụ trách giảng dạy' : 'Các lớp đang tham gia'}
              </Typography>
            </Box>

            {user.classes && user.classes.length > 0 ? (
              <Grid container spacing={2}>
                {user.classes.map((cls) => (
                  <Grid size={{ xs: 12, sm: 6, md: 4 }} key={cls.classId}>
                    <Card
                      variant="outlined"
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        '&:hover': { borderColor: '#2563EB', bgcolor: '#F8FAFC' },
                      }}
                      onClick={() => navigate(`/classes/${cls.classId}`)}
                    >
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#0F172A' }}>
                        {cls.name}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#64748B' }}>
                        Khối {cls.gradeLevel} {cls.academicYear ? `• Năm học ${cls.academicYear}` : ''}
                      </Typography>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography variant="body2" sx={{ py: 2, color: '#94A3B8' }}>
                {user.role === 'TEACHER'
                  ? 'Giáo viên này chưa được phân công phụ trách lớp học nào.'
                  : 'Học sinh này chưa được thêm vào danh sách lớp học nào.'}
              </Typography>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Edit Profile Dialog */}
      <Dialog open={isEditOpen} onClose={() => setIsEditOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Chỉnh sửa thông tin hồ sơ
        </DialogTitle>
        <form onSubmit={handleEditSubmit}>
          <DialogContent>
            {editError && (
              <Alert severity="error" sx={{ mb: 2, fontSize: '0.85rem' }}>
                {editError}
              </Alert>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label="Họ và tên hiển thị"
                size="small"
                fullWidth
                value={editDisplayName}
                onChange={(e) => setEditDisplayName(e.target.value)}
                required
              />

              {user.role === 'STUDENT' && (
                <FormControl fullWidth size="small">
                  <InputLabel>Khối lớp</InputLabel>
                  <Select
                    value={editGradeLevel}
                    label="Khối lớp"
                    onChange={(e) => setEditGradeLevel(Number(e.target.value))}
                  >
                    <MenuItem value={1}>Lớp 1</MenuItem>
                    <MenuItem value={2}>Lớp 2</MenuItem>
                    <MenuItem value={3}>Lớp 3</MenuItem>
                    <MenuItem value={4}>Lớp 4</MenuItem>
                    <MenuItem value={5}>Lớp 5</MenuItem>
                  </Select>
                </FormControl>
              )}
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setIsEditOpen(false)} sx={{ color: '#64748B' }}>
              Hủy
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={editMutation.isPending}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {editMutation.isPending ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Disable Confirm Dialog */}
      <ConfirmDialog
        open={isDisableConfirmOpen}
        title="Xác nhận vô hiệu hóa tài khoản"
        message={`Bạn có chắc chắn muốn vô hiệu hóa tài khoản ${user.email}? Người dùng sẽ bị chấm dứt phiên làm việc và không thể đăng nhập lại cho đến khi được kích hoạt.`}
        confirmText="Vô hiệu hóa"
        isDestructive={true}
        loading={disableMutation.isPending}
        onConfirm={() => disableMutation.mutate()}
        onCancel={() => setIsDisableConfirmOpen(false)}
      />

      {/* Enable Confirm Dialog */}
      <ConfirmDialog
        open={isEnableConfirmOpen}
        title="Kích hoạt lại tài khoản"
        message={`Bạn có chắc chắn muốn kích hoạt lại tài khoản ${user.email}? Người dùng sẽ có thể đăng nhập bình thường.`}
        confirmText="Kích hoạt"
        loading={enableMutation.isPending}
        onConfirm={() => enableMutation.mutate()}
        onCancel={() => setIsEnableConfirmOpen(false)}
      />

      {/* Reset Password Confirm Dialog */}
      <ConfirmDialog
        open={isResetConfirmOpen}
        title="Xác nhận đặt lại mật khẩu"
        message={`Hệ thống sẽ tạo một mật khẩu tạm thời ngẫu nhiên và hủy toàn bộ phiên đăng nhập hiện có của ${user.email}. Bạn có muốn tiếp tục?`}
        confirmText="Tạo mật khẩu tạm thời"
        loading={resetPasswordMutation.isPending}
        onConfirm={() => resetPasswordMutation.mutate()}
        onCancel={() => setIsResetConfirmOpen(false)}
      />

      {/* Reset Password Result Dialog */}
      <Dialog
        open={!!resetSuccessData}
        onClose={() => setResetSuccessData(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Mật khẩu tạm thời đã được tạo
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2.5, fontSize: '0.85rem' }}>
            Mật khẩu tạm thời này chỉ hiển thị duy nhất một lần tại đây và không được lưu dưới dạng văn bản thô. Hãy sao chép và bàn giao an toàn cho người dùng.
          </Alert>

          <Box
            sx={{
              p: 2,
              bgcolor: '#F1F5F9',
              borderRadius: 2,
              border: '1px solid #CBD5E1',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box>
              <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, display: 'block' }}>
                MẬT KHẨU TẠM THỜI
              </Typography>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: '#0F172A',
                  fontFamily: 'monospace',
                  letterSpacing: '0.1em',
                }}
              >
                {resetSuccessData?.temporaryPassword}
              </Typography>
            </Box>
            <Tooltip title={copySuccess ? 'Đã sao chép!' : 'Sao chép mật khẩu'}>
              <IconButton onClick={handleCopyPassword} color={copySuccess ? 'success' : 'primary'}>
                <ContentCopyIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Typography variant="caption" sx={{ color: '#94A3B8', mt: 2, display: 'block' }}>
            * Lưu ý: Cơ chế bắt buộc đổi mật khẩu ở lần đăng nhập đầu tiên chưa được áp dụng tại phiên bản A1.2.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            variant="contained"
            onClick={() => setResetSuccessData(null)}
            sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
          >
            Đã lưu & Đóng
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
