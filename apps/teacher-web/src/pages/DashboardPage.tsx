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
        <Skeleton variant="text" width={280} height={36} sx={{ mb: 1 }} />
        <Skeleton variant="text" width={380} height={20} sx={{ mb: 3.5 }} />
        <Grid container spacing={2} sx={{ mb: 3.5 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={i}>
              <Skeleton variant="rectangular" height={120} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={240} sx={{ borderRadius: 2 }} />
      </Box>
    );
  }

  const reviewCount = stats?.reviewRequired || 0;
  const totalCount = stats?.totalToday || 0;
  const completedCount = stats?.completed || 0;

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header section */}
      <Box
        className="dashboard-welcome"
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="h5" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Xin chào, {displayName}
          </Typography>
          <Typography variant="body2" sx={{ color: '#475569' }}>
            Tổng quan tiến độ chấm bài và các mục cần giáo viên xử lý hôm nay.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
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

      {!stats && (
        <Paper
          role="alert"
          variant="outlined"
          sx={{ mb: 3, p: 2, bgcolor: '#FFFBEB', borderColor: '#FDE68A', color: '#92400E', borderRadius: 2 }}
        >
          Chưa tải được thống kê tổng quan. Bạn vẫn có thể mở Lớp học, Bài tập và Đợt chấm từ thanh điều hướng.
        </Paper>
      )}

      {/* Actionable Urgent Attention Banner */}
      {reviewCount > 0 && (
        <Card
          sx={{
            mb: 3,
            bgcolor: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: 2,
          }}
        >
          <CardContent sx={{ py: 2, px: 2.5, '&:last-child': { pb: 2 } }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 2,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    borderRadius: 1.5,
                    bgcolor: '#FEE2E2',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#DC2626',
                    flexShrink: 0,
                  }}
                >
                  <PendingActions sx={{ fontSize: 24 }} />
                </Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#991B1B' }}>
                    Có {reviewCount} bài làm cần giáo viên xem xét lại
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#B91C1C', fontSize: '0.8125rem' }}>
                    AI nhận diện có điểm chưa chắc chắn hoặc bất thường về quy tắc tính toán.
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="contained"
                endIcon={<ArrowForward />}
                onClick={() => {
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
                  px: 2,
                }}
              >
                Xử lý ngay
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Top 4 Operational Metrics */}
      <Grid container className="dashboard-metrics" spacing={2} sx={{ mb: 3.5 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                  Lớp học phụ trách
                </Typography>
                <Box sx={{ p: 0.75, borderRadius: 1.5, bgcolor: '#ECFDF5', color: '#059669', display: 'flex' }}>
                  <School fontSize="small" />
                </Box>
              </Box>
              <Typography variant="h4" component="p" sx={{ fontWeight: 800, color: '#0F172A', my: 0.5 }}>
                {stats ? classes.length : '—'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                {stats
                  ? `Tổng sĩ số: ${classes.reduce((sum, c) => sum + (c.studentCount || 0), 0)} học sinh`
                  : 'Chưa tải được dữ liệu'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                  Tổng bài hôm nay
                </Typography>
                <Box sx={{ p: 0.75, borderRadius: 1.5, bgcolor: '#F1F5F9', color: '#334155', display: 'flex' }}>
                  <AssignmentTurnedIn fontSize="small" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', my: 0.5 }}>
                {stats ? totalCount : '—'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                {stats ? 'Đã nộp trong ngày' : 'Chưa tải được dữ liệu'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                  Đã có đề xuất điểm
                </Typography>
                <Box sx={{ p: 0.75, borderRadius: 1.5, bgcolor: '#ECFDF5', color: '#059669', display: 'flex' }}>
                  <FactCheck fontSize="small" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, color: '#059669', my: 0.5 }}>
                {stats ? completedCount : '—'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                {stats ? 'AI đã xử lý xong và có đề xuất' : 'Chưa tải được dữ liệu'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                  Cần giáo viên xem
                </Typography>
                <Box
                  sx={{
                    p: 0.75,
                    borderRadius: 1.5,
                    bgcolor: reviewCount > 0 ? '#FEE2E2' : '#F1F5F9',
                    color: reviewCount > 0 ? '#DC2626' : '#64748B',
                    display: 'flex',
                  }}
                >
                  <PendingActions fontSize="small" />
                </Box>
              </Box>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 800,
                  color: reviewCount > 0 ? '#DC2626' : '#0F172A',
                  my: 0.5,
                }}
              >
                {stats ? reviewCount : '—'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                {!stats
                  ? 'Chưa tải được dữ liệu'
                  : reviewCount > 0
                  ? 'Đang chờ giáo viên quyết định'
                  : 'Không có bài cần xem lại'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Batches List */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
          Đợt chấm bài gần đây
        </Typography>
        <Button
          variant="text"
          size="small"
          endIcon={<ChevronRight />}
          onClick={() => navigate('/batches')}
          sx={{ fontWeight: 700, color: '#059669' }}
        >
          Xem tất cả đợt chấm
        </Button>
      </Box>

      <Paper variant="outlined" sx={{ borderRadius: 2.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
          {!stats?.recentBatches || stats.recentBatches.length === 0 ? (
            <Box sx={{ py: 6, px: 3, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: '50%',
                  bgcolor: '#F1F5F9',
                  color: '#64748B',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mb: 2,
                }}
              >
                <AssignmentTurnedIn sx={{ fontSize: 28, color: '#94A3B8' }} />
              </Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#1E293B', mb: 0.5 }}>
                {stats ? 'Chưa có đợt chấm bài nào gần đây' : 'Chưa tải được danh sách đợt chấm'}
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 420, mb: 2.5, lineHeight: 1.55 }}>
                {stats
                  ? 'Bắt đầu bằng việc tạo đợt chấm bài mới hoặc tải ảnh bài làm của học sinh để hệ thống AI hỗ trợ phân tích.'
                  : 'Vui lòng kiểm tra lại kết nối mạng hoặc làm mới trang.'}
              </Typography>
              {stats && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<AddCircleOutlined />}
                  onClick={() => navigate('/batches/create')}
                  sx={{ fontWeight: 700 }}
                >
                  Tạo đợt chấm mới
                </Button>
              )}
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {stats.recentBatches.map((batch, index) => (
                <ListItem
                  key={batch.id || batch.batchId || index}
                  divider={index !== stats.recentBatches.length - 1}
                  sx={{
                    py: 1.5,
                    px: 2.5,
                    '&:hover': { bgcolor: '#F8FAFC' },
                    cursor: 'pointer',
                    transition: 'background-color 140ms',
                  }}
                  onClick={() => navigate(`/batches/${batch.id || batch.batchId}`)}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 0.25 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>
                          {batch.className ? `Lớp ${batch.className}` : 'Lớp học'} — {batch.assignmentTitle || 'Bài tập Toán'}
                        </Typography>
                        <StatusChip status={batch.status} />
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        {batch.createdAt ? new Date(batch.createdAt).toLocaleDateString('vi-VN') : 'Hôm nay'}
                      </Typography>
                    }
                  />
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip
                      label={`${batch.totalImages || batch.totalCount || 0} bài`}
                      size="small"
                      variant="outlined"
                      sx={{ borderColor: '#CBD5E1', color: '#475569' }}
                    />
                    <Chip
                      label={`${batch.processedCount || 0} đã xử lý`}
                      size="small"
                      sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 700 }}
                    />
                    {batch.reviewRequiredCount > 0 && (
                      <Chip
                        label={`${batch.reviewRequiredCount} cần xem`}
                        size="small"
                        sx={{ bgcolor: '#FEF2F2', color: '#DC2626', fontWeight: 700 }}
                      />
                    )}
                    <ChevronRight sx={{ color: '#94A3B8', ml: 0.5 }} />
                  </Box>
                </ListItem>
              ))}
            </List>
          )}
      </Paper>
    </Box>
  );
}
