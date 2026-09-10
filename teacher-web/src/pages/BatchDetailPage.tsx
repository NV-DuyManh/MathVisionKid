import { Typography, Box, Card, CardContent, LinearProgress, Grid, Button, Skeleton } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { BatchStatus } from '../types';
import { StatusChip } from '../components/common/StatusChip';
import { CheckCircle, Warning, ArrowBack, PendingActions, Refresh } from '@mui/icons-material';

export default function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: batch, isLoading, isError, refetch } = useQuery({
    queryKey: ['batch', id],
    queryFn: () => AppTeacherService.getBatchStatus(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const b = query.state.data;
      if (!b) return 3000;
      if (
        b.status === BatchStatus.COMPLETED ||
        b.status === BatchStatus.PARTIAL ||
        b.status === BatchStatus.FAILED ||
        (b.status as any) === 'COMPLETED' ||
        (b.status as any) === 'PARTIAL' ||
        (b.status as any) === 'FAILED'
      ) {
        return false;
      }
      return 3000;
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ maxWidth: 960, mx: 'auto', mt: 2 }}>
        <Skeleton variant="text" width={240} height={36} sx={{ mb: 1 }} />
        <Skeleton variant="rectangular" height={160} sx={{ borderRadius: 2.5, mb: 3 }} />
        <Grid container spacing={2.5}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 12, md: 4 }} key={i}>
              <Skeleton variant="rectangular" height={140} sx={{ borderRadius: 2.5 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (isError || !batch) {
    return (
      <Box sx={{ maxWidth: 960, mx: 'auto', mt: 4, textAlign: 'center' }}>
        <Typography color="error" variant="h6" sx={{ mb: 2 }}>
          Không thể tải thông tin đợt chấm bài.
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/batches')}>
          Quay lại danh sách đợt chấm
        </Button>
      </Box>
    );
  }

  const totalImgs = batch.totalImages || batch.totalCount || 0;
  const processed = batch.processedCount || 0;
  const reviewCount = batch.reviewRequiredCount || 0;
  const confidentCount = Math.max(0, processed - reviewCount);
  const progressPercent = totalImgs > 0 ? Math.round((processed / totalImgs) * 100) : 0;

  const isDone =
    batch.status === BatchStatus.COMPLETED ||
    batch.status === BatchStatus.PARTIAL ||
    batch.status === BatchStatus.FAILED ||
    (batch.status as any) === 'COMPLETED' ||
    (batch.status as any) === 'PARTIAL' ||
    (batch.status as any) === 'FAILED';

  return (
    <Box sx={{ maxWidth: 960, mx: 'auto', mt: 2 }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/batches')}
        sx={{ mb: 2 }}
      >
        Quay lại danh sách đợt chấm
      </Button>

      {/* Header Info */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3.5, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 800 }}>
              {batch.className ? `Lớp ${batch.className}` : 'Lớp học'}
            </Typography>
            <StatusChip status={batch.status} />
          </Box>
          <Typography variant="subtitle1" color="text.secondary">
            {batch.assignmentTitle || 'Bài tập Toán đặt tính'} • Tổng số: <strong>{totalImgs} bài làm</strong>
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => refetch()}
          size="small"
        >
          Làm mới
        </Button>
      </Box>

      {/* In-Progress State */}
      {!isDone ? (
        <Card sx={{ mb: 4, borderRadius: 2.5, border: '1px solid #BFDBFE', bgcolor: '#EFF6FF' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6" color="primary" sx={{ fontWeight: 700 }}>
                  Đang phân tích và nhận diện bài làm bằng AI...
                </Typography>
              </Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#1D4ED8' }}>
                {processed} / {totalImgs} bài ({progressPercent}%)
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progressPercent}
              sx={{ height: 10, borderRadius: 5, bgcolor: '#DBEAFE', '& .MuiLinearProgress-bar': { bgcolor: '#2563EB' } }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
              Hệ thống đang đối soát từng cột số và bước đặt tính. Trang sẽ tự động cập nhật khi hoàn tất.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Box>
          {/* Summary KPIs */}
          <Grid container spacing={2.5} sx={{ mb: 4 }}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: '#F0FDF4', borderColor: '#86EFAC', borderRadius: 2.5 }}>
                <CardContent sx={{ textAlign: 'center', py: 3.5 }}>
                  <CheckCircle sx={{ fontSize: 36, color: '#16A34A', mb: 0.5 }} />
                  <Typography variant="h3" sx={{ fontWeight: 800, color: '#15803D', mb: 0.5 }}>
                    {confidentCount}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#166534' }}>
                    Đã có đề xuất điểm
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    AI đã hoàn tất đề xuất (chờ GV duyệt/chốt)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: '#FEF2F2', borderColor: '#FCA5A5', borderRadius: 2.5 }}>
                <CardContent sx={{ textAlign: 'center', py: 3.5 }}>
                  <Warning sx={{ fontSize: 36, color: '#DC2626', mb: 0.5 }} />
                  <Typography variant="h3" sx={{ fontWeight: 800, color: '#B91C1C', mb: 0.5 }}>
                    {reviewCount}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#991B1B' }}>
                    Cần giáo viên xem lại
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Chữ viết mờ hoặc nghi ngờ lỗi tính
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: '#F8FAFC', borderColor: '#CBD5E1', borderRadius: 2.5 }}>
                <CardContent sx={{ textAlign: 'center', py: 3.5 }}>
                  <PendingActions sx={{ fontSize: 36, color: '#475569', mb: 0.5 }} />
                  <Typography variant="h3" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                    {totalImgs}
                  </Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#334155' }}>
                    Tổng số bài nộp
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Tất cả ảnh đã được xử lý xong
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Action to enter Review Queue */}
          {reviewCount > 0 ? (
            <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#FEF2F2', borderColor: '#FCA5A5', borderRadius: 2.5 }}>
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#991B1B', mb: 1 }}>
                Còn {reviewCount} bài làm cần bạn xem xét và đưa ra quyết định điểm số
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
                Giáo viên là người có thẩm quyền quyết định cuối cùng đối với điểm số học sinh.
              </Typography>
              <Button
                variant="contained"
                size="large"
                color="error"
                startIcon={<PendingActions />}
                onClick={() => navigate(`/batches/${batch.id || batch.batchId}/review`)}
                sx={{
                  px: 5,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 700,
                  bgcolor: '#DC2626',
                  '&:hover': { bgcolor: '#B91C1C' },
                }}
              >
                Vào hàng đợi xem bài ({reviewCount} bài)
              </Button>
            </Card>
          ) : (
            <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#F0FDF4', borderColor: '#86EFAC', borderRadius: 2.5 }}>
              <CheckCircle sx={{ fontSize: 44, color: '#16A34A', mb: 1 }} />
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#15803D', mb: 0.5 }}>
                Đợt chấm đã hoàn tất xuất sắc!
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Không còn bài làm nào cần giáo viên xử lý thủ công.
              </Typography>
            </Card>
          )}
        </Box>
      )}
    </Box>
  );
}
