import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Skeleton,
  Chip,
  Tooltip,
} from '@mui/material';
import { School, Groups, AddCircleOutlined, Assignment, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Class } from '../types';

export default function ClassesPage() {
  const [classes, setClasses] = useState<Class[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    AppTeacherService.getClasses()
      .then((data) => {
        if (isMounted) {
          setClasses(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3.5, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 0.5 }}>
            Danh sách Lớp học
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Các lớp học được phân công giảng dạy và quản lý danh sách học sinh.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddCircleOutlined />}
          onClick={() => navigate('/assignments/create')}
        >
          Tạo bài tập cho lớp
        </Button>
      </Box>

      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
              <Skeleton variant="rectangular" height={180} sx={{ borderRadius: 2.5 }} />
            </Grid>
          ))}
        </Grid>
      ) : classes.length === 0 ? (
        <Card sx={{ p: 6, textAlign: 'center', bgcolor: '#FFFFFF', borderRadius: 2.5 }}>
          <School sx={{ fontSize: 56, color: '#94A3B8', mb: 1.5 }} />
          <Typography variant="h6" sx={{ color: '#0F172A', mb: 1 }}>
            Chưa có lớp học nào được phân công
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mx: 'auto' }}>
            Vui lòng liên hệ quản trị viên nhà trường để được gán quyền phụ trách lớp học trên hệ thống.
          </Typography>
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
                  borderRadius: 2.5,
                  p: 0.5,
                  borderTop: '4px solid #2563EB',
                }}
              >
                <CardContent sx={{ p: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 2,
                          bgcolor: '#EFF6FF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#2563EB',
                        }}
                      >
                        <School sx={{ fontSize: 26 }} />
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 800 }}>
                          Lớp {c.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Tiểu học • Năm học hiện tại
                        </Typography>
                      </Box>
                    </Box>
                    <Chip
                      label="Đang hoạt động"
                      size="small"
                      sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 600, fontSize: '0.75rem' }}
                    />
                  </Box>

                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      p: 1.5,
                      bgcolor: '#F8FAFC',
                      borderRadius: 2,
                      border: '1px solid #E2E8F0',
                      mb: 2,
                    }}
                  >
                    <Groups sx={{ color: '#64748B', fontSize: 22 }} />
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                        {c.studentCount} học sinh
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Danh sách chính thức trong sổ điểm
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>

                <Box sx={{ px: 2.5, pb: 2, pt: 0, display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    fullWidth
                    startIcon={<Assignment />}
                    onClick={() => navigate('/assignments/create')}
                  >
                    Giao bài tập
                  </Button>
                  <Tooltip title="Tạo đợt chấm bài cho lớp này">
                    <Button
                      variant="contained"
                      size="small"
                      endIcon={<ArrowForward />}
                      onClick={() => navigate('/batches/create')}
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
