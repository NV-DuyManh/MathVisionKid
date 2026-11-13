import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Grid,
  Card,
  Button,
  List,
  ListItem,
  ListItemButton,
  Paper,
  Skeleton,
  Chip,
  Alert,
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
import { Link, useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { useAuth } from '../components/layout/AuthContext';
import { StatusChip } from '../components/common/StatusChip';
import { StatCard } from '../components/common/StatCard';
import { EmptyState } from '../components/common/EmptyState';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading, refetch } = useQuery({
    queryKey: ['teacher-dashboard'], queryFn: () => AppTeacherService.getDashboard(),
  });
  const { data: classes = [], isLoading: classesLoading, isError: classesError, refetch: refetchClasses } = useQuery({
    queryKey: ['teacher-classes'], queryFn: () => AppTeacherService.getClasses(),
  });
  const loading = statsLoading || classesLoading;

  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.name || 'Giáo viên');

  if (loading) {
    return (
      <Box role="status" aria-label="Đang tải tổng quan" aria-busy="true">
        <Skeleton variant="text" width={280} height={36} sx={{ mb: 1, maxWidth: '100%' }} />
        <Skeleton variant="text" width={380} height={20} sx={{ mb: 3.5, maxWidth: '100%' }} />
        <Grid container spacing={2} sx={{ mb: 3.5 }}>
          {[1, 2, 3, 4].map((i) => (
            <Grid size={{ xs: 6, lg: 3 }} key={i}>
              <Skeleton variant="rectangular" height={130} sx={{ borderRadius: 3.5 }} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={240} sx={{ borderRadius: 3.5 }} />
      </Box>
    );
  }

  const reviewCount = stats?.reviewRequired || 0;
  const recentReviewBatch = stats?.recentBatches.find(batch => (batch.pendingReviewCount ?? batch.reviewRequiredCount) > 0);
  const reviewBatchId = stats?.nextReviewBatchId || recentReviewBatch?.batchId || recentReviewBatch?.id;
  const totalCount = stats?.totalToday || 0;
  const completedCount = stats?.completed || 0;

  return (
    <Box>
      <Box component="header" className="teacher-dashboard-welcome">
        <Box component="img" src="/ui/mathvision-star.png" alt="" width={72} height={72} className="teacher-dashboard-star" />
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="h2" component="h1" sx={{ fontSize: { xs: '1.5rem', sm: '2rem' }, overflowWrap: 'anywhere' }}>
            Xin chào, {displayName}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.75 }}>
            Theo dõi lớp học, giao bài tập ô ly và duyệt kết quả chấm bài.
          </Typography>
          <Box className="teacher-page-actions" sx={{ mt: 2 }}>
            <Button
              component={Link}
              to="/batches/create"
              variant={reviewCount > 0 ? 'outlined' : 'contained'}
              startIcon={<AddCircleOutlined />}
            >
              Tạo đợt chấm mới
            </Button>
            <Button component={Link} to="/assignments/create" variant="text">
              Tạo bài tập
            </Button>
          </Box>
        </Box>
      </Box>

      {!stats && (
        <Alert severity="warning" sx={{ mb: 3 }}
          action={<Button size="small" onClick={() => void refetch()}>Thử lại</Button>}>
          Chưa tải được thống kê tổng quan. Bạn vẫn có thể mở Lớp học, Bài tập và Đợt chấm từ thanh điều hướng.
        </Alert>
      )}

      {reviewCount > 0 && (
        <Paper component="section" aria-labelledby="dashboard-review-title" variant="outlined" className="teacher-dashboard-review">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
            <Box sx={{ p: 1, borderRadius: '8px', bgcolor: 'warning.light', color: 'warning.dark', display: 'flex' }}>
              <PendingActions fontSize="small" />
            </Box>
            <Box>
              <Typography component="h2" id="dashboard-review-title" variant="subtitle1">
                Có {reviewCount} bài làm chờ giáo viên duyệt
              </Typography>
              <Typography variant="body2">Xem bài làm và chốt điểm khi đã kiểm tra.</Typography>
            </Box>
          </Box>
          <Button
            component={Link}
            to={reviewBatchId ? `/batches/${encodeURIComponent(reviewBatchId)}/review` : '/batches'}
            variant="contained"
            endIcon={<ArrowForward />}
          >
            {reviewBatchId ? 'Xử lý ngay' : 'Xem các đợt chấm'}
          </Button>
        </Paper>
      )}

      {/* Top 4 Operational Metrics using Unified StatCard */}
      <Grid container spacing={2} className="dashboard-metrics" sx={{ mb: 3.5 }}>
        <Grid size={{ xs: 6, lg: 3 }}>
          <StatCard
            title="Lớp học phụ trách"
            value={!classesError ? classes.length : null}
            description={
              !classesError
                ? `Tổng sĩ số: ${classes.reduce((sum, c) => sum + (c.studentCount || 0), 0)} học sinh`
                : 'Chưa tải được dữ liệu'
            }
            icon={<School fontSize="small" />}
            tone="#ECFDF5"
            color="#059669"
            path="/classes"
          />
        </Grid>

        <Grid size={{ xs: 6, lg: 3 }}>
          <StatCard
            title="Tổng bài hôm nay"
            value={stats ? totalCount : null}
            description={stats ? 'Đã nộp trong ngày' : 'Chưa tải được dữ liệu'}
            icon={<AssignmentTurnedIn fontSize="small" />}
            tone="#EFF6FF"
            color="#2563EB"
            path="/batches"
          />
        </Grid>

        <Grid size={{ xs: 6, lg: 3 }}>
          <StatCard
            title="Đã có đề xuất điểm"
            value={stats ? completedCount : null}
            description={stats ? 'AI đã xử lý xong và có đề xuất' : 'Chưa tải được dữ liệu'}
            icon={<FactCheck fontSize="small" />}
            tone="#ECFDF5"
            color="#059669"
            path="/batches"
          />
        </Grid>

        <Grid size={{ xs: 6, lg: 3 }}>
          <StatCard
            title="Cần giáo viên xem"
            value={stats ? reviewCount : null}
            description={
              !stats
                ? 'Chưa tải được dữ liệu'
                : reviewCount > 0
                ? 'Đang chờ giáo viên quyết định'
                : 'Không có bài cần xem lại'
            }
            icon={<PendingActions fontSize="small" />}
            tone={reviewCount > 0 ? '#FEF2F2' : '#F1F5F9'}
            color={reviewCount > 0 ? '#DC2626' : '#64748B'}
            path="/batches"
          />
        </Grid>
      </Grid>

      {/* 2-Column Operational Grid matching Admin Dashboard */}
      <Box className="dashboard-columns">
        {/* Left Column: Recent Batches List */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1, flexWrap: 'wrap' }}>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.01em' }}>
              Đợt chấm bài gần đây
            </Typography>
            <Button
              variant="text"
              size="small"
              endIcon={<ChevronRight />}
              onClick={() => navigate('/batches')}
              sx={{ fontWeight: 700, color: '#059669', '&:hover': { bgcolor: '#ECFDF5' } }}
            >
              Xem tất cả đợt chấm
            </Button>
          </Box>

          <Card sx={{ borderRadius: 3.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
            {!stats?.recentBatches || stats.recentBatches.length === 0 ? (
              <EmptyState
                title={stats ? 'Chưa có đợt chấm bài nào gần đây' : 'Chưa tải được danh sách đợt chấm'}
                description={
                  stats
                    ? 'Bắt đầu bằng việc tạo đợt chấm bài mới hoặc tải ảnh bài làm của học sinh để hệ thống AI hỗ trợ phân tích.'
                    : 'Vui lòng kiểm tra lại kết nối mạng hoặc làm mới trang.'
                }
                actionText={stats ? 'Tạo đợt chấm mới' : undefined}
                onAction={stats ? () => navigate('/batches/create') : undefined}
                icon={<AssignmentTurnedIn sx={{ fontSize: 36, color: '#94A3B8' }} />}
              />
            ) : (
              <List sx={{ p: 0 }}>
                {stats.recentBatches.map((batch, index) => (
                  <ListItem
                    key={batch.id || batch.batchId || index}
                    divider={index !== stats.recentBatches.length - 1}
                    disablePadding
                  >
                    <ListItemButton
                      component={Link}
                      to={`/batches/${encodeURIComponent(batch.id || batch.batchId || '')}`}
                      sx={{ py: 1.75, px: 2.5, gap: 1, flexWrap: 'wrap', minWidth: 0,
                        '&:hover': { bgcolor: '#F8FAFC' },
                        '&.Mui-focusVisible': { outline: '2px solid #047857', outlineOffset: -2 } }}
                    >
                      <Box sx={{ flex: '1 1 180px', minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1.25, mb: 0.25 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '0.9375rem', overflowWrap: 'anywhere' }}>
                            {batch.className ? `Lớp ${batch.className}` : 'Lớp học'} — {batch.assignmentTitle || 'Bài tập Toán'}
                          </Typography>
                          <StatusChip status={batch.status} />
                        </Box>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          {batch.createdAt
                            ? new Date(batch.createdAt).toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
                            : 'Hôm nay'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', minWidth: 0 }}>
                        <Chip
                          label={`${batch.totalImages ?? batch.totalCount ?? 0} bài`}
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#CBD5E1', color: '#475569', fontWeight: 700 }}
                        />
                        <Chip
                          label={`${batch.processedCount ?? 0} đã xử lý`}
                          size="small"
                          sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0' }}
                        />
                        {(batch.pendingReviewCount ?? batch.reviewRequiredCount) > 0 && (
                          <Chip
                            label={`${batch.pendingReviewCount ?? batch.reviewRequiredCount} cần xem`}
                            size="small"
                            sx={{ bgcolor: '#FEF2F2', color: '#DC2626', fontWeight: 800, border: '1px solid #FECACA' }}
                          />
                        )}
                        <ChevronRight sx={{ color: '#94A3B8', ml: 0.5 }} />
                      </Box>
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </Card>
        </Box>

        {/* Right Column: Assigned Classes Overview */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, gap: 1, flexWrap: 'wrap' }}>
            <Typography component="h2" variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.01em' }}>
              Lớp học phụ trách
            </Typography>
            <Button
              variant="text"
              size="small"
              endIcon={<ChevronRight />}
              onClick={() => navigate('/classes')}
              sx={{ fontWeight: 700, color: '#059669', '&:hover': { bgcolor: '#ECFDF5' } }}
            >
              Xem tất cả
            </Button>
          </Box>

          <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0', p: 2 }}>
            {classesError ? (
              <Alert severity="error" action={<Button onClick={() => void refetchClasses()}>Thử lại</Button>}>Chưa tải được lớp học phụ trách.</Alert>
            ) : classes.length === 0 ? (
              <EmptyState
                title="Chưa có lớp học phụ trách"
                description="Bạn chưa được phân công lớp học nào hoặc dữ liệu đang được đồng bộ."
                icon={<School sx={{ fontSize: 36, color: '#94A3B8' }} />}
              />
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {classes.map((cls) => (
                  <Box
                    key={cls.id || cls.classId}
                    sx={{
                      p: 2,
                      borderRadius: 2.5,
                      bgcolor: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap', gap: 1,
                      '&:hover': { bgcolor: '#F1F5F9', borderColor: '#CBD5E1' },
                    }}
                  >
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        {cls.name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        Lớp phụ trách giảng dạy
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={`${cls.studentCount || 0} học sinh`}
                        size="small"
                        sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0' }}
                      />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => navigate(`/assignments/create?classId=${encodeURIComponent(cls.id || cls.classId || '')}`)}
                        sx={{ borderRadius: 2, fontWeight: 700, fontSize: '0.75rem', py: 0.25, px: 1.25 }}
                      >
                        Giao bài
                      </Button>
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </Card>
        </Box>
      </Box>
    </Box>
  );
}
