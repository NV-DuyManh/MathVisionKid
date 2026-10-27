import { useState } from 'react';
import { Alert, Box, Button, Card, CardContent, Dialog, DialogActions, DialogContent, DialogTitle, Skeleton, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, TextField, Typography } from '@mui/material';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import ArrowBack from '@mui/icons-material/ArrowBack';
import Add from '@mui/icons-material/Add';
import { adminService } from '../services/api/adminService';
import { useAdminAction } from '../hooks/useAdminAction';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
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
  const students = (classroom?.students || []).filter(s => (s.displayName + ' ' + s.email).toLocaleLowerCase('vi').includes(search.trim().toLocaleLowerCase('vi')));
  const openPicker = (role: 'TEACHER' | 'STUDENT') => { action.clear(); setSelected(''); setPicker(role); };
  return <Box><AdminTopbar title={classroom?.name || 'Chi tiết lớp học'} subtitle="Thông tin lớp, giáo viên phụ trách và danh sách học sinh" /><PageContent>
    <Button component={Link} to="/classes" startIcon={<ArrowBack />} sx={{ mb: 2 }}>Danh sách lớp học</Button>
    <RequestError error={query.error} retry={() => { void query.refetch(); }} />
    <RequestError error={action.error} />
    {action.notice && <Alert severity="success" sx={{ mb: 2 }}>{action.notice}</Alert>}
    {query.isLoading ? <Skeleton variant="rounded" height={300} role="status" aria-label="Đang tải chi tiết" /> : classroom && !query.error && <>
      <Card sx={{ mb: 3 }}><CardContent sx={{ p: { xs: 2.5, sm: 4 } }}>
        <Box className="page-actions"><Box><Typography variant="h4" component="h2">{classroom.name}</Typography><Typography color="text.secondary">Khối {classroom.gradeLevel} · {classroom.academicYear || 'Chưa xác định năm học'}</Typography></Box><Button variant="outlined" disabled={action.pending} onClick={() => setEditing(true)}>Chỉnh sửa lớp học</Button></Box>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2,minmax(0,1fr))' }, gap: 2 }}>
          <Box sx={{ p: 2.5, bgcolor: '#F7F4FB', borderRadius: 2 }}><Typography variant="caption" color="text.secondary">GIÁO VIÊN PHỤ TRÁCH</Typography><Typography sx={{ fontWeight: 800,  mt: 1 }}>{classroom.teacher?.displayName || 'Chưa phân công'}</Typography><Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{classroom.teacher?.email}</Typography><Button size="small" sx={{ mt: 1, px: 0 }} disabled={action.pending} onClick={() => openPicker('TEACHER')}>Thay đổi giáo viên</Button></Box>
          <Box sx={{ p: 2.5, bgcolor: '#F0F5F2', borderRadius: 2 }}><Typography variant="caption" color="text.secondary">SĨ SỐ HIỆN TẠI</Typography><Typography variant="h4" sx={{ mt: 1 }}>{classroom.studentCount}<Typography component="span" variant="body2" sx={{ ml: 1 }}>học sinh</Typography></Typography><Typography variant="caption" color="text.secondary">Theo danh sách lớp đã được lưu</Typography></Box>
        </Box>
      </CardContent></Card>
      <Card><Box className="page-actions" sx={{ p: 3, mb: 0 }}><Box><Typography variant="h6" component="h2">Danh sách học sinh</Typography><Typography variant="caption" color="text.secondary">Danh sách này được dùng trong không gian giáo viên.</Typography></Box><Button variant="contained" startIcon={<Add />} disabled={action.pending} onClick={() => openPicker('STUDENT')}>Thêm học sinh</Button></Box>
        <Box sx={{ px: 3, pb: 2 }}><TextField size="small" fullWidth label="Tìm trong danh sách lớp theo tên hoặc email" value={search} onChange={e => { setSearch(e.target.value); setPage(0); }} /></Box>
        <TableContainer><Table aria-label="Danh sách học sinh trong lớp" sx={{ minWidth: 600 }}><TableHead><TableRow><TableCell>Học sinh</TableCell><TableCell>Email</TableCell><TableCell>Khối</TableCell><TableCell>Trạng thái</TableCell><TableCell align="right">Thao tác</TableCell></TableRow></TableHead>
          <TableBody>{students.length ? students.slice(page * size, page * size + size).map(s => <TableRow hover key={s.userId}><TableCell><Button component={Link} to={`/users/${s.userId}`} size="small" sx={{ px: 0 }}>{s.displayName}</Button></TableCell><TableCell>{s.email}</TableCell><TableCell>{s.gradeLevel || '—'}</TableCell><TableCell><StatusChip active={s.active} /></TableCell><TableCell align="right"><Button color="error" size="small" disabled={action.pending} aria-label={`Xóa ${s.displayName} khỏi lớp`} onClick={() => { action.clear(); setRemoving(s); }}>Xóa khỏi lớp</Button></TableCell></TableRow>) : <TableRow><TableCell colSpan={5} sx={{ textAlign: 'center', py: 5 }}>Chưa có học sinh phù hợp. Bạn có thể thêm học sinh vào lớp.</TableCell></TableRow>}</TableBody>
        </Table></TableContainer><TablePagination component="div" count={students.length} page={page} rowsPerPage={size} rowsPerPageOptions={[10, 20, 50]} onPageChange={(_, p) => setPage(p)} onRowsPerPageChange={e => { setSize(Number(e.target.value)); setPage(0); }} />
      </Card>
      {editing && <ClassFormDialog classroom={classroom} onClose={() => setEditing(false)} />}
      {picker && <Dialog open onClose={action.pending ? undefined : () => setPicker(null)} fullWidth maxWidth="sm" aria-labelledby="roster-picker-title">
        <DialogTitle id="roster-picker-title">{picker === 'TEACHER' ? 'Phân công giáo viên' : 'Thêm học sinh vào lớp'}</DialogTitle>
        <Box component="form" onSubmit={event => {
          event.preventDefault();
          if (!selected) return;
          void action.run(() => picker === 'TEACHER' ? adminService.assignTeacher(classId, { teacherId: selected }) : adminService.addStudentToClass(classId, selected), () => { setPicker(null); setSelected(''); });
        }}><DialogContent><RequestError error={action.error} /><UserPicker key={picker} role={picker} value={selected} onChange={setSelected} disabled={action.pending} exclude={picker === 'STUDENT' ? classroom.students?.map(s => s.userId) : []} /></DialogContent>
          <DialogActions sx={{ p: 3 }}><Button disabled={action.pending} onClick={() => setPicker(null)}>Hủy</Button><Button variant="contained" type="submit" disabled={action.pending || !selected}>{action.pending ? 'Đang lưu…' : picker === 'TEACHER' ? 'Xác nhận phân công' : 'Thêm vào lớp'}</Button></DialogActions>
        </Box>
      </Dialog>}
      <ConfirmDialog open={!!removing} title="Xóa học sinh khỏi lớp" message={`Xóa ${removing?.displayName || ''} khỏi danh sách lớp ${classroom.name}? Tài khoản học sinh vẫn được giữ lại.`} isDestructive confirmText="Xóa khỏi lớp" loading={action.pending} error={action.error} onCancel={() => setRemoving(null)} onConfirm={() => {
        if (removing) void action.run(() => adminService.removeStudentFromClass(classId, removing.userId), () => { setRemoving(null); setPage(0); });
      }} />
    </>}
  </PageContent></Box>;
}
