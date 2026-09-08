import { Box, Typography, Grid, Card, CardContent, Button, Chip, CircularProgress } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { SubmissionStatus } from '../types';
import { Warning, ImageNotSupported } from '@mui/icons-material';

export default function ReviewQueuePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: queue, isLoading, isError } = useQuery({
    queryKey: ['reviewQueue', id],
    queryFn: () => AppTeacherService.getReviewQueue(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !queue) {
    return (
      <Box sx={{ textAlign: 'center', mt: 8, p: 4 }}>
        <Typography color="error">Đã xảy ra lỗi khi tải hàng đợi duyệt.</Typography>
      </Box>
    );
  }

  if (queue.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', mt: 8, p: 4, bgcolor: 'success.50', borderRadius: 4, border: '1px solid', borderColor: 'success.100' }}>
        <Typography variant="h5" color="success.main">Tuyệt vời! Không còn bài nào cần xem lại.</Typography>
        <Button variant="outlined" sx={{ mt: 3, borderColor: 'success.main', color: 'success.dark' }} onClick={() => navigate('/dashboard')}>Về trang chủ</Button>
      </Box>
    );
  }

  const getConfidenceSemantic = (score: number) => {
    if (score >= 90) return { label: 'Cao', color: 'success.main' };
    if (score >= 70) return { label: 'Trung bình', color: 'warning.main' };
    return { label: 'Thấp', color: 'error.main' };
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'text.primary' }}>Hàng đợi duyệt</Typography>
      <Typography variant="subtitle1" color="error.main" sx={{ fontWeight: '600', mb: 4 }}>
        Có {queue.length} bài cần giáo viên kiểm tra lại
      </Typography>

      <Grid container spacing={3}>
        {queue.map(sub => (
          <Grid size={{ xs: 12, md: 6, lg: 4 }} key={sub.id || sub.submissionId}>
            <Card sx={{ display: 'flex', flexDirection: 'column', height: '100%', borderColor: sub.status === SubmissionStatus.QUALITY_ISSUE ? 'warning.200' : 'error.200' }}>
              <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" color="text.primary">{sub.studentName}</Typography>
                  {sub.status === SubmissionStatus.QUALITY_ISSUE ? (
                    <Chip icon={<ImageNotSupported />} label="Lỗi Ảnh" color="warning" size="small" variant="outlined" />
                  ) : (
                    <Chip icon={<Warning />} label="Yêu cầu giáo viên xem lại" color="error" size="small" sx={{ bgcolor: 'error.50' }} />
                  )}
                </Box>
                
                <Box sx={{ bgcolor: 'background.default', p: 2, borderRadius: 2, mb: 3, border: '1px solid', borderColor: 'divider', flexGrow: 1 }}>
                  <Typography variant="body2" color="text.secondary">Lý do xem lại (từ AI):</Typography>
                  <Typography variant="body1" sx={{ fontWeight: '600', mt: 0.5, color: 'text.primary' }}>
                    {sub.evidence?.rule || 'Xác nhận kết quả thuật toán'}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>Độ tự tin của hệ thống</Typography>
                      <Typography variant="body2" color={getConfidenceSemantic(sub.recognitionConfidence || 0).color} sx={{ fontWeight: '600' }}>
                        {getConfidenceSemantic(sub.recognitionConfidence || 0).label}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                
                <Button 
                  variant="contained" 
                  fullWidth 
                  color="primary"
                  onClick={() => navigate(`/submissions/${sub.id || sub.submissionId}`)}
                >
                  Xem chi tiết
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
