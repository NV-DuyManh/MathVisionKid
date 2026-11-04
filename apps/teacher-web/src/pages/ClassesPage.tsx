import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Skeleton,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import { School, Groups, AddCircleOutlined, Assignment, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

export default function ClassesPage() {
  const navigate = useNavigate();
  const { data: classes = [], isLoading: loading, isError, refetch } = useQuery({
    queryKey: ['teacher-classes'],
    queryFn: () => AppTeacherService.getClasses(),
  });

  return (
    <Box>
      <PageHeader
        title="Danh sách Lớp học"
        description="Các lớp học được phân công giảng dạy và quản lý danh sách học sinh."
        actions={
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/assignments/create')}
            sx={{ borderRadius: 2.5, fontWeight: 700 }}
          >
            Tạo bài tập cho lớp
          </Button>
        }
      />

      {isError ? (
        <Alert severity="error" action={<Button color="inherit" onClick={() => void refetch()}>Thử lại</Button>}>
          Chưa tải được danh sách. Vui lòng thử lại.
        </Alert>
      ) : loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
              <Skeleton variant="rectangular" height={190} sx={{ borderRadius: 3.5 }} />
            </Grid>
          ))}
        </Grid>
      ) : classes.length === 0 ? (
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          <EmptyState
            title="Chưa có lớp học nào được phân công"
            description="Vui lòng liên hệ quản trị viên nhà trường để được gán quyền phụ trách lớp học trên hệ thống."
            icon={<School sx={{ fontSize: 42, color: '#94A3B8' }} />}
          />
        </Card>
      ) : (
        <Grid container spacing={3}>
          {classes.map((c) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={c.id || c.classId}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  borderRadius: 3.5,
                  border: '1px solid #E2E8F0',
                  transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.08)',
                    borderColor: '#CBD5E1',
                  },
                }}
              >
                <CardContent sx={{ p: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 2.5,
                          bgcolor: '#ECFDF5',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#059669',
                        }}
                      >
                        <School sx={{ fontSize: 24 }} />
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1.05rem' }}>
                          {c.name.startsWith('Lớp ') ? c.name : `Lớp ${c.name}`}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          Lớp được phân công giảng dạy
                        </Typography>
                      </Box>
                    </Box>
                    <Chip
                      label="Được phân công"
                      size="small"
                      sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, fontSize: '0.72rem', border: '1px solid #A7F3D0' }}
                    />
                  </Box>

                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      p: 1.5,
                      bgcolor: '#F8FAFC',
                      borderRadius: 2.5,
                      border: '1px solid #E2E8F0',
                      mb: 1,
                    }}
                  >
                    <Groups sx={{ color: '#64748B', fontSize: 22 }} />
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        {c.studentCount} học sinh
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        Danh sách chính thức trong sổ điểm
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>

                <Box sx={{ px: 2.5, pb: 2.5, pt: 0, display: 'flex', gap: 1.25 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    fullWidth
                    startIcon={<Assignment />}
                    onClick={() => navigate(`/assignments/create?classId=${encodeURIComponent(c.id || c.classId || '')}`)}
                    sx={{ borderRadius: 2, fontWeight: 700 }}
                  >
                    Giao bài tập
                  </Button>
                  <Tooltip title="Tạo đợt chấm bài cho lớp này">
                    <Button
                      variant="contained"
                      size="small"
                      endIcon={<ArrowForward />}
                      sx={{ minWidth: 108, whiteSpace: 'nowrap', borderRadius: 2, fontWeight: 700 }}
                      onClick={() => navigate('/assignments')}
                    >
                      Chấm bài
                    </Button>
                  </Tooltip>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
