import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  Paper,
  Skeleton,
  Chip,
} from '@mui/material';
import {
  AssignmentTurnedIn,
  PendingActions,
  FactCheck,
  ChevronRight,
  AddCircleOutlined,
  School,
  ArrowForward,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { DashboardStats, Class } from '../types';
import { useAuth } from '../components/layout/AuthContext';
import { StatusChip } from '../components/common/StatusChip';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [classes, setClasses] = useState<Class[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      AppTeacherService.getDashboard(),
      AppTeacherService.getClasses().catch(() => []),
    ])
      .then(([dashStats, classList]) => {
        if (isMounted) {
          setStats(dashStats);
          setClasses(classList);
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

  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.name || 'Giáo viên');

  if (loading) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
        <Skeleton variant="text" width={280} height={42} sx={{ mb: 1 }} />
        <Skeleton variant="text" width={380} height={24} sx={{ mb: 4 }} />
        <Grid container spacing={2.5} sx={{ mb: 4 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
              <Skeleton variant="rectangular" height={130} sx={{ borderRadius: 2.5 }} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={260} sx={{ borderRadius: 2.5 }} />
      </Box>
    );
  }

  const reviewCount = stats?.reviewRequired || 0;
  const totalCount = stats?.totalToday || 0;
  const completedCount = stats?.completed || 0;

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header section */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3.5, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 0.5 }}>
            Xin chào, {displayName}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Tổng quan tiến độ chấm bài và các mục cần giáo viên xử lý hôm nay.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button
            variant="outlined"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/assignments/create')}
          >
            Tạo bài tập
          </Button>
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/batches/create')}
          >
            Tạo đợt chấm mới
          </Button>
        </Box>
      </Box>

      {/* Actionable Urgent Attention Banner */}
      {reviewCount > 0 && (
        <Card
          sx={{
            mb: 3.5,
            bgcolor: '#FEF2F2',
            border: '1.5px solid #FCA5A5',
            borderRadius: 2.5,
            p: 1,
          }}
        >
          <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2,
                    bgcolor: '#FEE2E2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#B91C1C',
                  }}
                >
                  <PendingActions sx={{ fontSize: 26 }} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#991B1B' }}>
                    Có {reviewCount} bài làm cần giáo viên xem xét lại
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#7F1D1D' }}>
                    AI nhận diện có điểm chưa chắc chắn hoặc bất thường về quy tắc tính toán.
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="contained"
                color="error"
                endIcon={<ArrowForward />}
                onClick={() => {
                  // Navigate to the first batch with review items or to batches list
                  const targetBatch = stats?.recentBatches?.find((b) => b.reviewRequiredCount > 0);
                  if (targetBatch) {
                    navigate(`/batches/${targetBatch.id || targetBatch.batchId}/review`);
                  } else {
                    navigate('/batches');
                  }
                }}
                sx={{
                  bgcolor: '#DC2626',
                  '&:hover': { bgcolor: '#B91C1C' },
                  px: 2.5,
                }}
              >
                Xử lý ngay
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Top 4 Operational Metrics */}
      <Grid container spacing={2.5} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #2563EB' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
                  Lớp học phụ trách
                </Typography>
                <School sx={{ color: '#2563EB', fontSize: 22 }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A' }}>
                {classes.length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Tổng sĩ số: {classes.reduce((sum, c) => sum + (c.studentCount || 0), 0)} học sinh
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #0D9488' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
                  Tổng bài hôm nay
                </Typography>
                <AssignmentTurnedIn sx={{ color: '#0D9488', fontSize: 22 }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A' }}>
                {totalCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Đã nộp trong ngày
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #16A34A' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
                  Đã có đề xuất điểm
                </Typography>
                <FactCheck sx={{ color: '#16A34A', fontSize: 22 }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#15803D' }}>
                {completedCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                AI đã xử lý xong và có đề xuất
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%', borderLeft: '4px solid #DC2626' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography color="text.secondary" variant="body2" sx={{ fontWeight: 600 }}>
                  Cần giáo viên xem
                </Typography>
                <PendingActions sx={{ color: '#DC2626', fontSize: 22 }} />
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: reviewCount > 0 ? '#B91C1C' : '#0F172A' }}>
                {reviewCount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {reviewCount > 0 ? 'Đang chờ giáo viên quyết định' : 'Hàng đợi sạch sẽ'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Batches List */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Đợt chấm bài gần đây</Typography>
        <Button variant="text" size="small" endIcon={<ChevronRight />} onClick={() => navigate('/batches')}>
          Xem tất cả đợt chấm
        </Button>
      </Box>

      <Paper variant="outlined" sx={{ borderRadius: 2.5, overflow: 'hidden' }}>
        <List sx={{ p: 0 }}>
          {!stats?.recentBatches || stats.recentBatches.length === 0 ? (
            <ListItem sx={{ py: 4, textAlign: 'center', justifyContent: 'center' }}>
              <Typography color="text.secondary">Chưa có đợt chấm bài nào được tạo gần đây.</Typography>
            </ListItem>
          ) : (
            stats.recentBatches.map((batch, index) => (
              <ListItem
                key={batch.id || batch.batchId || index}
                divider={index !== stats.recentBatches.length - 1}
                sx={{
                  py: 1.75,
                  px: 3,
                  '&:hover': { bgcolor: '#F8FAFC' },
                  cursor: 'pointer',
                  transition: 'background-color 150ms',
                }}
                onClick={() => navigate(`/batches/${batch.id || batch.batchId}`)}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                        {batch.className ? `Lớp ${batch.className}` : 'Lớp học'} — {batch.assignmentTitle || 'Bài tập Toán'}
                      </Typography>
                      <StatusChip status={batch.status} />
                    </Box>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {batch.createdAt ? new Date(batch.createdAt).toLocaleDateString('vi-VN') : 'Hôm nay'}
                    </Typography>
                  }
                />
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Chip label={`${batch.totalImages || batch.totalCount || 0} bài`} size="small" variant="outlined" />
                  <Chip
                    label={`${batch.processedCount || 0} đã xử lý`}
                    size="small"
                    sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 600 }}
                  />
                  {batch.reviewRequiredCount > 0 && (
                    <Chip
                      label={`${batch.reviewRequiredCount} cần xem`}
                      size="small"
                      sx={{ bgcolor: '#FEF2F2', color: '#B91C1C', fontWeight: 700 }}
                    />
                  )}
                  <ChevronRight sx={{ color: '#94A3B8', ml: 1 }} />
                </Box>
              </ListItem>
            ))
          )}
        </List>
      </Paper>
    </Box>
  );
}
