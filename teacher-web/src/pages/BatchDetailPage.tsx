import { Typography, Box, Card, CardContent, LinearProgress, Grid, Button } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { BatchStatus } from '../types';

export default function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: batch, isLoading, isError } = useQuery({
    queryKey: ['batch', id],
    queryFn: () => AppTeacherService.getBatchStatus(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const b = query.state.data;
      if (!b) return 3000;
      // Stop polling on terminal states
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

  if (isLoading) return <Typography>Đang tải...</Typography>;
  if (isError || !batch) return <Typography color="error">Lỗi khi tải thông tin đợt chấm.</Typography>;

  const totalImgs = batch.totalImages || batch.totalCount || 0;
  const progressPercent = totalImgs > 0 ? Math.round((batch.processedCount / totalImgs) * 100) : 0;
  
  const isDone = 
    batch.status === BatchStatus.COMPLETED || 
    batch.status === BatchStatus.PARTIAL || 
    batch.status === BatchStatus.FAILED ||
    (batch.status as any) === 'COMPLETED' ||
    (batch.status as any) === 'PARTIAL' ||
    (batch.status as any) === 'FAILED';

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 1 }}>Toán {batch.className}</Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>{batch.assignmentTitle} • {totalImgs} bài</Typography>

      {!isDone ? (
        <Card sx={{ mb: 4, p: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" color="primary">Đang kiểm tra bằng AI...</Typography>
              <Typography variant="h6">{batch.processedCount} / {totalImgs}</Typography>
            </Box>
            <LinearProgress variant="determinate" value={progressPercent} sx={{ height: 12, borderRadius: 6 }} />
          </CardContent>
        </Card>
      ) : (
        <Box>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: 'success.50', borderColor: 'success.200' }}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h3" color="success.main" sx={{ fontWeight: '800', mb: 1 }}>
                    {batch.processedCount - batch.reviewRequiredCount}
                  </Typography>
                  <Typography variant="subtitle1" color="success.dark" sx={{ fontWeight: '600' }}>AI đủ chắc chắn</Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: 'error.50', borderColor: 'error.200' }}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h3" color="error.main" sx={{ fontWeight: '800', mb: 1 }}>
                    {batch.reviewRequiredCount}
                  </Typography>
                  <Typography variant="subtitle1" color="error.dark" sx={{ fontWeight: '600' }}>Cần xem lại</Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Card sx={{ bgcolor: 'warning.50', borderColor: 'warning.200' }}>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h3" color="warning.main" sx={{ fontWeight: '800', mb: 1 }}>0</Typography>
                  <Typography variant="subtitle1" color="warning.dark" sx={{ fontWeight: '600' }}>Chưa rõ ảnh</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {batch.reviewRequiredCount > 0 && (
            <Box sx={{ textAlign: 'center' }}>
              <Button 
                variant="contained" 
                size="large" 
                color="error" 
                sx={{ px: 6, py: 1.5, fontSize: 18 }}
                onClick={() => navigate(`/batches/${batch.id || batch.batchId}/review`)}
              >
                Xem bài cần chú ý
              </Button>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
