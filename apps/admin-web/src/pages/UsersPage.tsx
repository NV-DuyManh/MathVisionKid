import React, { useState } from 'react';
import {
  Box,
  Card,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tabs,
  Tab,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { RoleChip } from '../components/common/RoleChip';
import { StatusChip } from '../components/common/StatusChip';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { useNavigate } from 'react-router-dom';
import type { CreateUserRequest } from '../types';

export const UsersPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Filters & Pagination State
  const [roleTab, setRoleTab] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(10);

  // Create User Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [newRole, setNewRole] = useState<'STUDENT' | 'TEACHER'>('STUDENT');
  const [newDisplayName, setNewDisplayName] = useState<string>('');
  const [newEmail, setNewEmail] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [newGradeLevel, setNewGradeLevel] = useState<number>(3);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Query users
  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', roleTab, statusFilter, searchQuery, page, pageSize],
    queryFn: () =>
      adminService.getUsers({
        role: roleTab === 'ALL' ? undefined : roleTab,
        active: statusFilter === 'ALL' ? undefined : statusFilter === 'ACTIVE',
        query: searchQuery ? searchQuery.trim() : undefined,
        page,
        size: pageSize,
      }),
  });

  // Mutation create user
  const createMutation = useMutation({
    mutationFn: (payload: CreateUserRequest) => adminService.createUser(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      setIsCreateOpen(false);
      resetCreateForm();
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setCreateError(e.response?.data?.error?.message || e.message || 'Lỗi khi tạo người dùng.');
    },
  });

  const resetCreateForm = () => {
    setNewRole('STUDENT');
    setNewDisplayName('');
    setNewEmail('');
    setNewPassword('');
    setNewGradeLevel(3);
    setCreateError(null);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDisplayName.trim() || !newEmail.trim() || !newPassword) {
      setCreateError('Vui lòng điền đầy đủ các thông tin bắt buộc.');
      return;
    }
    if (newPassword.length < 6) {
      setCreateError('Mật khẩu phải có ít nhất 6 ký tự.');
      return;
    }

    const payload: CreateUserRequest = {
      displayName: newDisplayName.trim(),
      email: newEmail.trim().toLowerCase(),
      role: newRole,
      initialPassword: newPassword,
    };

    if (newRole === 'STUDENT') {
      payload.gradeLevel = newGradeLevel;
    }

    createMutation.mutate(payload);
  };

  return (
    <Box>
      <AdminTopbar title="Quản lý Người dùng" subtitle="Cấp phát và quản lý danh sách Học sinh và Giáo viên" />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Header Action Row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <Tabs
            value={roleTab}
            onChange={(_, val) => {
              setRoleTab(val);
              setPage(0);
            }}
            sx={{
              '& .MuiTab-root': {
                fontWeight: 600,
                fontSize: '0.9rem',
                textTransform: 'none',
                minWidth: 100,
              },
            }}
          >
            <Tab label="Tất cả" value="ALL" />
            <Tab label="Học sinh" value="STUDENT" />
            <Tab label="Giáo viên" value="TEACHER" />
          </Tabs>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setIsCreateOpen(true)}
            sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
          >
            Cấp tài khoản mới
          </Button>
        </Box>

        {/* Filters Row */}
        <Card sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Tìm kiếm theo tên hoặc email..."
              size="small"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(0);
              }}
              sx={{ flexGrow: 1, minWidth: 260 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" sx={{ color: '#94A3B8' }} />
                    </InputAdornment>
                  ),
                },
              }}
            />

            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Trạng thái</InputLabel>
              <Select
                value={statusFilter}
                label="Trạng thái"
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="ALL">Tất cả trạng thái</MenuItem>
                <MenuItem value="ACTIVE">Đang hoạt động</MenuItem>
                <MenuItem value="DISABLED">Đã vô hiệu hóa</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Card>

        {/* Users Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Họ và tên</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Vai trò</TableCell>
                  <TableCell>Khối lớp</TableCell>
                  <TableCell>Trạng thái</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading ? (
                  <TableSkeleton rows={pageSize} columns={6} />
                ) : data?.content && data.content.length > 0 ? (
                  data.content.map((u) => (
                    <TableRow key={u.userId} hover>
                      <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                        {u.displayName}
                      </TableCell>
                      <TableCell sx={{ color: '#475569' }}>{u.email}</TableCell>
                      <TableCell>
                        <RoleChip role={u.role} />
                      </TableCell>
                      <TableCell sx={{ color: '#64748B' }}>
                        {u.role === 'STUDENT' && u.gradeLevel ? `Lớp ${u.gradeLevel}` : '—'}
                      </TableCell>
                      <TableCell>
                        <StatusChip active={u.active} />
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          endIcon={<OpenInNewIcon fontSize="small" />}
                          onClick={() => navigate(`/users/${u.userId}`)}
                          sx={{ color: '#2563EB', fontWeight: 600 }}
                        >
                          Chi tiết
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6}>
                      <EmptyState
                        title="Không tìm thấy người dùng"
                        description="Không có tài khoản nào phù hợp với bộ lọc hiện tại."
                        actionText="Cấp tài khoản mới"
                        onAction={() => setIsCreateOpen(true)}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={data?.totalElements ?? 0}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[5, 10, 20, 50]}
            labelRowsPerPage="Số hàng mỗi trang:"
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} trên ${count}`}
          />
        </Card>
      </Box>

      {/* Create User Dialog */}
      <Dialog open={isCreateOpen} onClose={() => setIsCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Cấp phát tài khoản người dùng mới
        </DialogTitle>
        <form onSubmit={handleCreateSubmit}>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2.5, fontSize: '0.85rem' }}>
                {createError}
              </Alert>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Vai trò</InputLabel>
                <Select
                  value={newRole}
                  label="Vai trò"
                  onChange={(e) => setNewRole(e.target.value as 'STUDENT' | 'TEACHER')}
                >
                  <MenuItem value="STUDENT">Học sinh (STUDENT)</MenuItem>
                  <MenuItem value="TEACHER">Giáo viên (TEACHER)</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Họ và tên hiển thị"
                size="small"
                fullWidth
                value={newDisplayName}
                onChange={(e) => setNewDisplayName(e.target.value)}
                required
                placeholder="VD: Nguyễn Văn An"
              />

              <TextField
                label="Email đăng nhập"
                type="email"
                size="small"
                fullWidth
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                required
                placeholder="VD: an.student@mathvision.local"
              />

              <TextField
                label="Mật khẩu khởi tạo"
                type={showPassword ? 'text' : 'password'}
                size="small"
                fullWidth
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                placeholder="Tối thiểu 6 ký tự"
                slotProps={{
                  input: {
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                          size="small"
                          aria-label="Ẩn/hiện mật khẩu"
                        >
                          {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  },
                }}
              />

              {newRole === 'STUDENT' && (
                <FormControl fullWidth size="small">
                  <InputLabel>Khối lớp</InputLabel>
                  <Select
                    value={newGradeLevel}
                    label="Khối lớp"
                    onChange={(e) => setNewGradeLevel(Number(e.target.value))}
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
            <Button onClick={() => setIsCreateOpen(false)} sx={{ color: '#64748B' }}>
              Hủy bỏ
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {createMutation.isPending ? 'Đang tạo...' : 'Tạo người dùng'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};
