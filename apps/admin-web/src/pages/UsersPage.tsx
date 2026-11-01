import { useState } from 'react';
import { Alert, Avatar, Box, Button, Card, MenuItem, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, TextField, Typography } from '@mui/material';
import Add from '@mui/icons-material/Add';
import Search from '@mui/icons-material/Search';
import InputAdornment from '@mui/material/InputAdornment';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
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
  const [role, setRole] = useState(params.get('role') || '');
  const [active, setActive] = useState(params.get('active') || '');
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const [creating, setCreating] = useState(params.get('create') === 'true');
  const [notice, setNotice] = useState('');
  const users = useQuery({
    queryKey: ['admin-users', role, active, search, page, size],
    queryFn: () => adminService.getUsers({ role: role || undefined, active: active ? active === 'true' : undefined, query: search || undefined, page, size }),
  });
  return <Box><AdminTopbar title="Quản lý người dùng" subtitle="Tài khoản học sinh, giáo viên và trạng thái truy cập" /><PageContent>
    <Box className="page-actions"><Box><Typography component="h2" variant="h5">Danh bạ người dùng</Typography><Typography color="text.secondary" variant="body2">{users.data ? `${users.data.totalElements.toLocaleString('vi-VN')} tài khoản phù hợp` : 'Tra cứu và quản lý tài khoản'}</Typography></Box><Button variant="contained" startIcon={<Add />} onClick={() => { setNotice(''); setCreating(true); }}>Tạo người dùng</Button></Box>
    {notice && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setNotice('')}>{notice}</Alert>}
    <RequestError error={users.error} retry={() => { void users.refetch(); }} />
    <Card>
      <Box component="form" className="filter-bar" onSubmit={e => { e.preventDefault(); setSearch(query.trim()); setPage(0); }}>
        <TextField size="small" label="Tìm theo tên hoặc email" value={query} onChange={e => setQuery(e.target.value)} sx={{ flex: 1, minWidth: 220 }} slotProps={{ input: { startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> } }} />
        <TextField size="small" select label="Vai trò" value={role} sx={{ minWidth: 160 }} onChange={e => { setRole(e.target.value); setPage(0); }}><MenuItem value="">Tất cả vai trò</MenuItem><MenuItem value="STUDENT">Học sinh</MenuItem><MenuItem value="TEACHER">Giáo viên</MenuItem><MenuItem value="ADMIN">Quản trị viên</MenuItem></TextField>
        <TextField size="small" select label="Trạng thái" value={active} sx={{ minWidth: 170 }} onChange={e => { setActive(e.target.value); setPage(0); }}><MenuItem value="">Tất cả trạng thái</MenuItem><MenuItem value="true">Đang hoạt động</MenuItem><MenuItem value="false">Đã bị khóa</MenuItem></TextField>
        <Button type="submit" variant="outlined" disabled={users.isFetching}>Tìm kiếm</Button>
      </Box>
      {!users.error && <><TableContainer><Table aria-label="Danh sách người dùng" sx={{ minWidth: 760 }}><TableHead><TableRow><TableCell>Người dùng</TableCell><TableCell>Vai trò</TableCell><TableCell>Khối</TableCell><TableCell>Trạng thái</TableCell><TableCell>Ngày tạo</TableCell><TableCell align="right">Thao tác</TableCell></TableRow></TableHead>
        <TableBody>{users.isLoading ? <TableSkeleton rows={5} columns={6} /> : users.data?.content.length ? users.data.content.map(user => <TableRow hover key={user.userId}>
          <TableCell><Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}><Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.light', color: 'primary.dark', fontSize: 14 }}>{user.displayName?.slice(0, 1)}</Avatar><Box><Typography variant="body2" sx={{ fontWeight: 800,  }}>{user.displayName}</Typography><Typography variant="caption" color="text.secondary">{user.email}</Typography></Box></Box></TableCell>
          <TableCell><RoleChip role={user.role} /></TableCell><TableCell>{user.gradeLevel ? `Khối ${user.gradeLevel}` : '—'}</TableCell><TableCell><StatusChip active={user.active} /></TableCell><TableCell>{new Date(user.createdAt).toLocaleDateString('vi-VN')}</TableCell>
          <TableCell align="right"><Button component={Link} to={`/users/${user.userId}`} size="small" aria-label={`Xem chi tiết ${user.displayName}`}>Chi tiết</Button></TableCell>
        </TableRow>) : <TableRow><TableCell colSpan={6}><EmptyState title="Không tìm thấy người dùng" description="Thử tên, email hoặc bộ lọc khác." /></TableCell></TableRow>}</TableBody>
      </Table></TableContainer>
      <TablePagination component="div" count={users.data?.totalElements || 0} page={page} onPageChange={(_, p) => setPage(p)} rowsPerPage={size} rowsPerPageOptions={[10, 20, 50]} onRowsPerPageChange={e => { setSize(Number(e.target.value)); setPage(0); }} /></>}
    </Card>
    {creating && <UserFormDialog onSaved={() => setNotice('Đã tạo tài khoản thành công.')} onClose={() => { setCreating(false); if (params.has('create')) { params.delete('create'); setParams(params, { replace: true }); } }} />}
  </PageContent></Box>;
}
