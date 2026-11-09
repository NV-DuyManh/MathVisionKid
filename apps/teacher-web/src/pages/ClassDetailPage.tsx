import { useState } from 'react';
import { Alert, Box, Button, Card, List, ListItem, ListItemText, Skeleton, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { AppTeacherService } from '../services/api/ServiceLocator';

export default function ClassDetailPage() {
  const { id = '' } = useParams();
  const [search, setSearch] = useState('');
  const { data: classroom, isPending, isError, refetch } = useQuery({
    queryKey: ['teacher-class', id],
    queryFn: () => AppTeacherService.getClassDetail(id),
  });

  const classFilter = `classId=${encodeURIComponent(id)}`;
  const normalized = search.trim().toLocaleLowerCase('vi');
  const students = classroom?.students.filter(student =>
    !normalized || student.name?.toLocaleLowerCase('vi').includes(normalized)) ?? [];
  const title = classroom?.name || 'Danh sách học sinh';

  return <Box sx={{ maxWidth: 960 }}>
    <Button component={Link} to="/classes" sx={{ mb: 2 }}>Quay lại lớp học</Button>
    <PageHeader title={title} subtitle={classroom ? `${classroom.studentCount} học sinh` : undefined}
      actions={classroom && <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button component={Link} to={`/assignments?${classFilter}`} variant="outlined">Bài tập của lớp</Button>
        <Button component={Link} to={`/assignments/create?${classFilter}`} variant="contained">Giao bài tập</Button>
      </Box>} />
    {isPending && <Skeleton variant="rounded" height={160} aria-label="Đang tải học sinh" />}
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>
      Chưa tải được lớp học. Vui lòng kiểm tra lớp được phân công và thử lại.
    </Alert>}
    {classroom && <Card variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
      <Typography component="h2" variant="h6" sx={{ mb: 2 }}>Danh sách học sinh</Typography>
      {classroom.students.length ? <>
        <TextField size="small" fullWidth label="Tìm theo tên học sinh" value={search}
          onChange={event => setSearch(event.target.value)} />
        <Typography role="status" color="text.secondary" sx={{ mt: 2 }}>
          Hiển thị {students.length} / {classroom.students.length} học sinh
        </Typography>
        <List aria-label="Học sinh trong lớp">
          {students.map(student => <ListItem key={student.id} disableGutters divider>
            <ListItemText primary={student.name || 'Chưa có tên hiển thị'} />
          </ListItem>)}
        </List>
      </> : <Typography color="text.secondary">Lớp chưa có học sinh. Hãy liên hệ quản trị viên để cập nhật danh sách lớp.</Typography>}
    </Card>}
  </Box>;
}
