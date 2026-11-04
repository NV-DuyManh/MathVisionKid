import { useState } from 'react';
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import Add from '@mui/icons-material/Add';
import Search from '@mui/icons-material/Search';
import InputAdornment from '@mui/material/InputAdornment';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';
import { RequestError } from '../components/common/RequestError';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { RoleChip } from '../components/common/RoleChip';
import { StatusChip } from '../components/common/StatusChip';
import { UserFormDialog } from '../components/users/UserFormDialog';

export function UsersPage() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const role = params.get('role') || '';
  const active = params.get('active') || '';
  const rawPage = Number(params.get('page') || 0);
  const page = Number.isSafeInteger(rawPage) && rawPage >= 0 ? rawPage : 0;
  const setPage = (value: number) => setParams(prev => {
    const next = new URLSearchParams(prev);
    if (value) next.set('page', String(value)); else next.delete('page');
    return next;
  });
  const setFilter = (key: string, value: string) => setParams(prev => {
    const next = new URLSearchParams(prev);
    if (value) next.set(key, value); else next.delete(key);
    next.delete('page');
    return next;
  });
  const [size, setSize] = useState(10);
  const creating = params.get('create') === 'true';
  const setCreating = (value: boolean) => setParams(prev => {
    const next = new URLSearchParams(prev);
    if (value) next.set('create', 'true'); else next.delete('create');
    return next;
  }, { replace: !value });
  const [notice, setNotice] = useState('');
  const users = useQuery({
    queryKey: ['admin-users', role, active, search, page, size],
    queryFn: () =>
      adminService.getUsers({
        role: role || undefined,
        active: active ? active === 'true' : undefined,
        query: search || undefined,
        page,
        size,
      }),
  });

  return (
    <Box>
      <AdminTopbar title="Quản lý người dùng" subtitle="Tài khoản học sinh, giáo viên và trạng thái truy cập" />
      <PageContent>
        <PageHeader
          title="Danh bạ người dùng"
          description={
            users.data
              ? `${users.data.totalElements.toLocaleString('vi-VN')} tài khoản phù hợp trong hệ thống`
              : 'Tra cứu và quản lý tài khoản người dùng'
          }
          actions={
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => {
                setNotice('');
                setCreating(true);
              }}
              sx={{ borderRadius: 2.5, fontWeight: 700 }}
            >
              Tạo người dùng
            </Button>
          }
        />

        {notice && (
          <Alert severity="success" sx={{ mb: 2, borderRadius: 2.5 }} onClose={() => setNotice('')}>
            {notice}
          </Alert>
        )}

        <RequestError
          error={users.error}
          retry={() => {
            void users.refetch();
          }}
        />

        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0', overflow: 'hidden' }}>
          <Box
            component="form"
            className="filter-bar"
            onSubmit={(e) => {
              e.preventDefault();
              setSearch(query.trim());
              setPage(0);
            }}
            sx={{
              p: 2.5,
              display: 'flex',
              gap: 1.5,
              flexWrap: 'wrap',
              bgcolor: '#F8FAFC',
              borderBottom: '1px solid #E2E8F0',
            }}
          >
            <TextField
              size="small"
              label="Tìm theo tên hoặc email"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              sx={{ flex: 1, minWidth: 220 }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search fontSize="small" sx={{ color: '#64748B' }} />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <TextField
              size="small"
              select
              label="Vai trò"
              value={role}
              sx={{ minWidth: 160 }}
              onChange={(e) => {
                setFilter('role', e.target.value);
              }}
            >
              <MenuItem value="">Tất cả vai trò</MenuItem>
              <MenuItem value="STUDENT">Học sinh</MenuItem>
              <MenuItem value="TEACHER">Giáo viên</MenuItem>
              <MenuItem value="ADMIN">Quản trị viên</MenuItem>
            </TextField>
            <TextField
              size="small"
              select
              label="Trạng thái"
              value={active}
              sx={{ minWidth: 170 }}
              onChange={(e) => {
                setFilter('active', e.target.value);
              }}
            >
              <MenuItem value="">Tất cả trạng thái</MenuItem>
              <MenuItem value="true">Đang hoạt động</MenuItem>
              <MenuItem value="false">Đã bị khóa</MenuItem>
            </TextField>
            <Button
              type="submit"
              variant="outlined"
              disabled={users.isFetching}
              sx={{ borderRadius: 2, fontWeight: 700, px: 2.5 }}
            >
              Tìm kiếm
            </Button>
          </Box>

          {!users.error && (
            <>
              <TableContainer>
                <Table aria-label="Danh sách người dùng" sx={{ minWidth: 760 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Người dùng</TableCell>
                      <TableCell>Vai trò</TableCell>
                      <TableCell>Khối</TableCell>
                      <TableCell>Trạng thái</TableCell>
                      <TableCell>Ngày tạo</TableCell>
                      <TableCell align="right">Thao tác</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {users.isLoading ? (
                      <TableSkeleton rows={5} columns={6} />
                    ) : users.data?.content.length ? (
                      users.data.content.map((user) => (
                        <TableRow hover key={user.userId}>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                              <Avatar
                                sx={{
                                  width: 36,
                                  height: 36,
                                  bgcolor: '#EFF6FF',
                                  color: '#2563EB',
                                  fontSize: 14,
                                  fontWeight: 800,
                                }}
                              >
                                {user.displayName?.slice(0, 1)}
                              </Avatar>
                              <Box>
                                <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                                  {user.displayName}
                                </Typography>
                                <Typography variant="caption" sx={{ color: '#64748B' }}>
                                  {user.email}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <RoleChip role={user.role} />
                          </TableCell>
                          <TableCell sx={{ color: '#334155' }}>
                            {user.gradeLevel ? `Khối ${user.gradeLevel}` : '—'}
                          </TableCell>
                          <TableCell>
                            <StatusChip active={user.active} />
                          </TableCell>
                          <TableCell sx={{ color: '#334155' }}>
                            {new Date(user.createdAt).toLocaleDateString('vi-VN')}
                          </TableCell>
                          <TableCell align="right">
                            <Button
                              component={Link}
                              to={`/users/${user.userId}`}
                              variant="outlined"
                              size="small"
                              aria-label={`Xem chi tiết ${user.displayName}`}
                              sx={{
                                borderRadius: 2,
                                fontWeight: 700,
                                borderColor: '#CBD5E1',
                                color: '#0F172A',
                                '&:hover': { borderColor: '#94A3B8', bgcolor: '#F8FAFC' },
                              }}
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
                            description="Thử tên, email hoặc bộ lọc khác."
                          />
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                component="div"
                count={users.data?.totalElements || 0}
                page={page}
                onPageChange={(_, p) => setPage(p)}
                rowsPerPage={size}
                rowsPerPageOptions={[10, 20, 50]}
                onRowsPerPageChange={(e) => {
                  setSize(Number(e.target.value));
                  setPage(0);
                }}
              />
            </>
          )}
        </Card>

        {creating && (
          <UserFormDialog
            onSaved={() => setNotice('Đã tạo tài khoản thành công.')}
            onClose={() => {
              setCreating(false);

            }}
          />
        )}
      </PageContent>
    </Box>
  );
}
