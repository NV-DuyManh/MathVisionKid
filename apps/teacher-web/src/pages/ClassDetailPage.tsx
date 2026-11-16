import { ClassroomSettings } from './ClassroomFoundation';
import apiClient from '../services/api/apiClient';
import { useState } from 'react';
import { Alert, Box, Button, Card, List, ListItem, ListItemText, Skeleton, Tab, Tabs, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { ClassAssignmentsPanel } from './ClassAssignmentsPanel';

export default function ClassDetailPage() {
  const { id = '' } = useParams();
  return <ClassDetail key={id} id={id} />;
}

function ClassDetail({ id }: { id: string }) {
  const [search, setSearch] = useState('');
  const [removing, setRemoving] = useState(false);
  const [removeError, setRemoveError] = useState(false);
  const [tab, setTab] = useState(0);
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
      actions={classroom && <Button component={Link} to={`/assignments/create?${classFilter}`} variant="outlined">Chấm ảnh theo đợt</Button>} />
    {isPending && <Skeleton variant="rounded" height={160} aria-label="Đang tải học sinh" />}
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>
      Chưa tải được lớp học. Vui lòng kiểm tra lớp được phân công và thử lại.
    </Alert>}
    {classroom && <Tabs value={tab} onChange={(_, value) => setTab(value)} aria-label="Thông tin lớp học" sx={{ mb: 2 }}>
      <Tab label="Học sinh" />
      <Tab label="Bài tập" />
    </Tabs>}
    {classroom && tab === 0 && <>
    <ClassroomSettings key={id} id={id} refresh={refetch} />
    {removeError && <Alert severity="error">Chưa gỡ được học sinh. Hãy tải lại lớp và thử lại.</Alert>}
    <Card variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
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
            <Button disabled={removing} onClick={async () => {
              if (!window.confirm('Gỡ học sinh khỏi lớp? Học sinh sẽ cần được duyệt khi muốn vào lại.')) return;
              setRemoving(true); setRemoveError(false);
              try {
                await apiClient.delete('/teacher/classes/' + encodeURIComponent(id) + '/students/' + encodeURIComponent(student.id));
                await refetch();
              } catch { setRemoveError(true); }
              finally { setRemoving(false); }
            }}>Gỡ khỏi lớp</Button>
          </ListItem>)}
        </List>
      </> : <Typography color="text.secondary">Lớp chưa có học sinh. Chia sẻ lời mời để học sinh vào lớp.</Typography>}
    </Card>
    </>}
    {classroom && tab === 1 && <ClassAssignmentsPanel classId={id} studentCount={classroom.studentCount} />}
  </Box>;
}
