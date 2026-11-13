import { useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Dialog, DialogActions, DialogContent, DialogTitle, Skeleton, Table, TableBody, TableCell, TableHead, TablePagination, TableRow, TextField, Typography } from '@mui/material';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ArrowBack from '@mui/icons-material/ArrowBack';
import Add from '@mui/icons-material/Add';
import { adminService } from '../services/api/adminService';
import { useAdminAction } from '../hooks/useAdminAction';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';
import { LedgerTable } from '../components/common/LedgerTable';
import { EmptyState } from '../components/common/EmptyState';
import { RequestError } from '../components/common/RequestError';
import { StatusChip } from '../components/common/StatusChip';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { UserPicker } from '../components/classes/UserPicker';
import { ClassFormDialog } from '../components/classes/ClassFormDialog';
import type { AdminUserSummary } from '../types';

export function ClassDetailPage() {
  const { classId = '' } = useParams();
  return <ClassDetail key={classId} classId={classId} />;
}

function ClassDetail({ classId }: { classId: string }) {
  const query = useQuery({ queryKey: ['admin-class', classId], queryFn: () => adminService.getClass(classId) });
  const classroom = query.data;
  const action = useAdminAction();
  const [editing, setEditing] = useState(false);
  const [picker, setPicker] = useState<'TEACHER' | 'STUDENT' | null>(null);
  const [selected, setSelected] = useState('');
  const [removing, setRemoving] = useState<AdminUserSummary | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const searchTerm = search.trim().toLocaleLowerCase('vi');
  const students = (classroom?.students || []).filter(student =>
    (student.displayName + ' ' + student.email).toLocaleLowerCase('vi').includes(searchTerm));
  const openPicker = (role: 'TEACHER' | 'STUDENT') => {
    action.clear();
    setSelected('');
    setPicker(role);
  };

  return (
    <Box>
      <AdminTopbar title="Chi tiết lớp học" />
      <PageContent>
        <Button component={Link} to="/classes" startIcon={<ArrowBack />} sx={{ mb: 2 }}>Danh sách lớp học</Button>
        <RequestError error={query.error} retry={() => { void query.refetch(); }} />
        {!picker && !removing && <RequestError error={action.error} />}
        {action.notice && <Alert severity="success" sx={{ mb: 2 }}>{action.notice}</Alert>}
        {query.isLoading ? (
          <Skeleton variant="rounded" height={300} role="status" aria-label="Đang tải chi tiết" />
        ) : classroom && !query.error && (
          <>
            <PageHeader
              title={classroom.name}
              description={`Khối ${classroom.gradeLevel} · ${classroom.academicYear || 'Chưa xác định năm học'}`}
              actions={<Button variant="outlined" disabled={action.pending} onClick={() => setEditing(true)}>Chỉnh sửa lớp học</Button>}
            />
            <Card component="section" aria-labelledby="class-teacher" sx={{ mb: 2, bgcolor: 'var(--admin-paper)', borderColor: 'var(--admin-paper-line)' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 }, display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'flex-end', justifyContent: 'space-between' }}>
                <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
                  <Typography id="class-teacher" component="h2" variant="h4">Giáo viên phụ trách</Typography>
                  <Typography sx={{ fontWeight: 800, mt: 0.75, color: 'text.primary' }}>{classroom.teacher?.displayName || 'Chưa phân công'}</Typography>
                  {classroom.teacher?.email && <Typography variant="body2" color="text.secondary">{classroom.teacher.email}</Typography>}
                </Box>
                <Button variant="outlined" disabled={action.pending} onClick={() => openPicker('TEACHER')}>Thay đổi giáo viên</Button>
              </CardContent>
            </Card>
            <Card component="section" aria-labelledby="class-students" aria-busy={query.isFetching}>
              <Box className="page-actions" sx={{ p: { xs: 2, sm: 3 }, mb: 0 }}>
                <Box>
                  <Typography id="class-students" variant="h4" component="h2">Danh sách học sinh</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                    {classroom.studentCount.toLocaleString('vi-VN')} học sinh trong lớp
                  </Typography>
                </Box>
                <Button variant="contained" startIcon={<Add />} disabled={action.pending} onClick={() => openPicker('STUDENT')}>Thêm học sinh</Button>
              </Box>
              <Box className="filter-bar">
                <TextField
                  size="small" fullWidth label="Tìm theo tên hoặc email" value={search}
                  onChange={event => { setSearch(event.target.value); setPage(0); }}
                  sx={{ maxWidth: 420 }}
                />
              </Box>
              <LedgerTable label="Vùng cuộn danh sách học sinh">
                <Table aria-label="Danh sách học sinh trong lớp" sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Học sinh</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Khối</TableCell>
                      <TableCell>Trạng thái</TableCell>
                      <TableCell align="right">Thao tác</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {students.length ? students.slice(page * size, page * size + size).map(student => (
                      <TableRow hover key={student.userId}>
                        <TableCell><Button component={Link} to={`/users/${student.userId}`} size="small" sx={{ px: 0, textAlign: 'left' }}>{student.displayName}</Button></TableCell>
                        <TableCell sx={{ maxWidth: 220, overflowWrap: 'anywhere' }}>{student.email}</TableCell>
                        <TableCell>{student.gradeLevel || '—'}</TableCell>
                        <TableCell><StatusChip active={student.active} /></TableCell>
                        <TableCell align="right">
                          <Button color="error" size="small" disabled={action.pending} aria-label={`Xóa ${student.displayName} khỏi lớp`}
                            onClick={() => { action.clear(); setRemoving(student); }}>Xóa khỏi lớp</Button>
                        </TableCell>
                      </TableRow>
                    )) : (
                      <TableRow>
                        <TableCell colSpan={5}>
                          <EmptyState
                            title={searchTerm ? 'Không tìm thấy học sinh' : 'Lớp chưa có học sinh'}
                            description={searchTerm ? 'Thử tìm theo tên hoặc email khác.' : 'Chọn Thêm học sinh để cập nhật danh sách lớp.'}
                          />
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </LedgerTable>
              <TablePagination
                component="div" count={students.length} page={page} rowsPerPage={size} rowsPerPageOptions={[10, 20, 50]}
                onPageChange={(_, value) => setPage(value)}
                onRowsPerPageChange={event => { setSize(Number(event.target.value)); setPage(0); }}
              />
            </Card>
            {editing && <ClassFormDialog classroom={classroom} onClose={() => setEditing(false)} />}
            {picker && (
              <Dialog open onClose={action.pending ? undefined : () => setPicker(null)} fullWidth maxWidth="sm" aria-labelledby="roster-picker-title">
                <DialogTitle id="roster-picker-title">{picker === 'TEACHER' ? 'Phân công giáo viên' : 'Thêm học sinh vào lớp'}</DialogTitle>
                <Box component="form" aria-busy={action.pending} onSubmit={event => {
                  event.preventDefault();
                  if (!selected) return;
                  void action.run(
                    () => picker === 'TEACHER' ? adminService.assignTeacher(classId, { teacherId: selected }) : adminService.addStudentToClass(classId, selected),
                    () => { setPicker(null); setSelected(''); },
                  );
                }}>
                  <DialogContent>
                    <RequestError error={action.error} />
                    <UserPicker key={picker} role={picker} value={selected} onChange={setSelected} disabled={action.pending} exclude={picker === 'STUDENT' ? classroom.students?.map(student => student.userId) : []} />
                  </DialogContent>
                  <DialogActions sx={{ p: { xs: 2, sm: 3 }, flexWrap: 'wrap', gap: 1 }}>
                    <Button disabled={action.pending} onClick={() => setPicker(null)}>Hủy</Button>
                    <Button variant="contained" type="submit" disabled={action.pending || !selected}>
                      {action.pending ? 'Đang lưu…' : picker === 'TEACHER' ? 'Xác nhận phân công' : 'Thêm vào lớp'}
                    </Button>
                  </DialogActions>
                </Box>
              </Dialog>
            )}
            <ConfirmDialog
              open={!!removing}
              title="Xóa học sinh khỏi lớp"
              message={`Xóa ${removing?.displayName || ''} khỏi danh sách lớp ${classroom.name}? Tài khoản học sinh vẫn được giữ lại.`}
              isDestructive
              confirmText="Xóa khỏi lớp"
              loading={action.pending}
              error={action.error}
              onCancel={() => setRemoving(null)}
              onConfirm={() => {
                if (removing) void action.run(() => adminService.removeStudentFromClass(classId, removing.userId), () => { setRemoving(null); setPage(0); });
              }}
            />
          </>
        )}
      </PageContent>
    </Box>
  );
}
