import { useState } from 'react';
import { Dialog, DialogTitle, DialogContent } from '@mui/material';
import { CreateClassForm } from './ClassroomFoundation';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  Button,
  Skeleton,
  Alert,
} from '@mui/material';
import { School, AddCircleOutlined, ArrowForward } from '@mui/icons-material';
import { Link, useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

export default function ClassesPage() {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);
  const { data: classes = [], isLoading: loading, isError, refetch } = useQuery({
    queryKey: ['teacher-classes'],
    queryFn: () => AppTeacherService.getClasses(),
  });

  return (
    <Box>
      <PageHeader
        title="Danh sách Lớp học"
        description="Xem học sinh và bài tập của các lớp được phân công."
        actions={
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => setCreating(true)}
            sx={{ borderRadius: 2.5, fontWeight: 700 }}
          >
            Tạo lớp
          </Button>
        }
      />

      <Dialog open={creating} onClose={() => setCreating(false)} fullWidth maxWidth="xs" aria-labelledby="create-class-title">
        <DialogTitle id="create-class-title">Tạo lớp</DialogTitle>
        <DialogContent>
          <CreateClassForm onCreated={id => { void refetch(); navigate('/classes/' + id); }} />
        </DialogContent>
      </Dialog>
      {isError ? (
        <Alert severity="error" action={<Button color="inherit" onClick={() => void refetch()}>Thử lại</Button>}>
          Chưa tải được danh sách. Vui lòng thử lại.
        </Alert>
      ) : loading ? (
        <Card variant="outlined" aria-busy="true" sx={{ p: 2 }}>
          {[1, 2, 3].map((row) => <Skeleton key={row} height={64} />)}
        </Card>
      ) : classes.length === 0 ? (
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          <EmptyState
            title="Chưa có lớp học nào được phân công"
            description="Tạo lớp đầu tiên rồi mời học sinh tham gia."
            icon={<School sx={{ fontSize: 42, color: '#94A3B8' }} />}
          />
        </Card>
      ) : (
        <Card variant="outlined">
          <Box component="ul" aria-label="Lớp được phân công" sx={{ listStyle: 'none', m: 0, p: 0 }}>
            {classes.map((classroom) => {
              const id = encodeURIComponent(classroom.id || classroom.classId || '');
              const name = classroom.name.startsWith('Lớp ') ? classroom.name : `Lớp ${classroom.name}`;
              return (
                <Box component="li" key={id} sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: 'minmax(0, 1fr) auto' },
                  gap: 1.5, alignItems: 'center', p: { xs: 2, md: 2.5 },
                  '& + &': { borderTop: '1px solid', borderColor: 'divider' },
                }}>
                  <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', minWidth: 0 }}>
                    <Box sx={{ display: 'grid', placeItems: 'center', width: 44, height: 44, flexShrink: 0,
                      borderRadius: '12px', bgcolor: 'primary.light', color: 'primary.main' }}>
                      <School aria-hidden="true" />
                    </Box>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography component="h2" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{name}</Typography>
                      <Typography color="text.secondary" variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                        {classroom.studentCount} học sinh
                      </Typography>
                    </Box>
                  </Box>
                  <Box role="group" aria-label={name} sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                    <Button component={Link} to={`/classes/${id}`} variant="outlined" size="small" endIcon={<ArrowForward />}>
                      Xem học sinh
                    </Button>
                    <Button component={Link} to={`/assignments/create?classId=${id}`} size="small">Giao bài tập</Button>
                    <Button component={Link} to={`/assignments?classId=${id}`} size="small">Bài tập của lớp</Button>
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Card>
      )}
    </Box>
  );
}
