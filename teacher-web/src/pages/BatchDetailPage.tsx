import { useState, useEffect } from 'react';
import { Box, Typography, Card, CardContent, LinearProgress, Grid, Button } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { MockTeacherService } from '../services/api/MockTeacherService';
import type { Batch } from '../types';
import { BatchStatus } from '../types';

export default function BatchDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [batch, setBatch] = useState<Batch | null>(null);

  useEffect(() => {
    if (!id) return;
    
    // Poll for status
    const interval = setInterval(async () => {
      try {
        const b = await MockTeacherService.getBatchStatus(id);
        setBatch(b);
        if (b.status === BatchStatus.REVIEW_REQUIRED || b.status === BatchStatus.COMPLETED) {
          clearInterval(interval);
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [id]);

  if (!batch) return <Typography>Đang tải...</Typography>;

  const progressPercent = Math.round((batch.processedCount / batch.totalImages) * 100);
  const isDone = batch.status === BatchStatus.REVIEW_REQUIRED || batch.status === BatchStatus.COMPLETED;

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 1 }}>Toán {batch.className}</Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 4 }}>{batch.assignmentTitle} • {batch.totalImages} bài</Typography>

      {!isDone ? (
        <Card sx={{ mb: 4, p: 2 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" color="primary">Đang kiểm tra bằng AI...</Typography>
              <Typography variant="h6">{batch.processedCount} / {batch.totalImages}</Typography>
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
                onClick={() => navigate(`/batches/${batch.id}/review`)}
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
