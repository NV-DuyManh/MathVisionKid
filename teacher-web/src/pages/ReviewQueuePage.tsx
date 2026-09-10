import { Box, Typography, Grid, Card, CardContent, Button, CircularProgress, Paper, Divider } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { CheckCircle, ArrowBack, ArrowForward, AutoAwesome } from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';

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
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Đang tải danh sách bài làm cần xem lại...
        </Typography>
      </Box>
    );
  }

  if (isError || !queue) {
    return (
      <Box sx={{ textAlign: 'center', mt: 6, p: 4 }}>
        <Typography color="error" variant="h6" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải hàng đợi duyệt.
        </Typography>
        <Button variant="outlined" onClick={() => navigate(`/batches/${id}`)}>
          Quay lại đợt chấm
        </Button>
      </Box>
    );
  }

  // Meaningful completion state per Section 34
  if (queue.length === 0) {
    return (
      <Box sx={{ maxWidth: 680, mx: 'auto', textAlign: 'center', mt: 8 }}>
        <Paper
          variant="outlined"
          sx={{
            p: 5,
            bgcolor: '#F0FDF4',
            borderColor: '#86EFAC',
            borderRadius: 3,
          }}
        >
          <CheckCircle sx={{ fontSize: 56, color: '#16A34A', mb: 1.5 }} />
          <Typography variant="h5" sx={{ fontWeight: 800, color: '#15803D', mb: 1 }}>
            Đã xử lý hết các bài cần giáo viên xem lại.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 440, mx: 'auto', mb: 3 }}>
            Tất cả các bài làm trong đợt này đã được giáo viên xem xét hoặc đã có đầy đủ đề xuất từ hệ thống.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button variant="outlined" onClick={() => navigate(`/batches/${id}`)}>
              Xem chi tiết đợt chấm
            </Button>
            <Button variant="contained" onClick={() => navigate('/dashboard')}>
              Về trang tổng quan
            </Button>
          </Box>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate(`/batches/${id}`)}
        sx={{ mb: 2 }}
      >
        Quay lại chi tiết đợt chấm
      </Button>

      <Box sx={{ mb: 3.5 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          Hàng đợi Thẩm định & Duyệt bài
        </Typography>
        <Typography variant="body1" sx={{ color: '#B91C1C', fontWeight: 600 }}>
          Có {queue.length} bài làm cần giáo viên thẩm định và quyết định điểm số chính thức.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {queue.map((sub, idx) => {
          const subId = sub.id || sub.submissionId || '';
          const recConf = sub.recognitionConfidence !== undefined ? `${Math.round(sub.recognitionConfidence)}%` : 'Chưa có';
          const diagConf = sub.diagnosisConfidence !== undefined ? `${Math.round(sub.diagnosisConfidence)}%` : 'Chưa có';
          const suggested = sub.suggestedScore !== undefined ? sub.suggestedScore : sub.gradeProposal?.score;

          return (
            <Grid size={{ xs: 12, md: 6, lg: 4 }} key={subId}>
              <Card
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  height: '100%',
                  borderRadius: 2.5,
                  border: '1.5px solid #FCA5A5',
                  transition: 'box-shadow 150ms ease, transform 150ms ease',
                  '&:hover': {
                    boxShadow: '0 6px 16px rgba(220, 38, 38, 0.1)',
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2.5 }}>
                  {/* Top Bar: Student Name + StatusChip */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        {sub.studentName || `Học sinh #${idx + 1}`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Thứ tự trong hàng đợi: #{idx + 1}/{queue.length}
                      </Typography>
                    </Box>
                    <StatusChip status={sub.status} />
                  </Box>

                  {/* Review reason callout */}
                  <Box
                    sx={{
                      bgcolor: '#FEF2F2',
                      p: 1.75,
                      borderRadius: 2,
                      mb: 2,
                      border: '1px solid #FECACA',
                    }}
                  >
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#991B1B', display: 'block' }}>
                      Lý do cần giáo viên xem xét:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: '#7F1D1D', mt: 0.25 }}>
                      {sub.evidence?.rule || 'Cần xác nhận nét chữ hoặc bước đặt tính'}
                    </Typography>
                  </Box>

                  {/* Advisory Score and Confidence Metrics */}
                  <Box sx={{ bgcolor: '#F8FAFC', p: 1.75, borderRadius: 2, border: '1px solid #E2E8F0', mb: 2.5, flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <AutoAwesome sx={{ fontSize: 16, color: '#2563EB' }} />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                          AI đề xuất (chưa chính thức):
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#2563EB' }}>
                        {suggested !== undefined ? `${suggested} / 10 điểm` : 'Chưa chấm'}
                      </Typography>
                    </Box>

                    <Divider sx={{ my: 1 }} />

                    <Grid container spacing={1}>
                      <Grid size={{ xs: 6 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          Độ tin cậy nhận diện:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                          {recConf}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 6 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          Độ tin cậy chẩn đoán:
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                          {diagConf}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Primary Action */}
                  <Button
                    variant="contained"
                    fullWidth
                    size="medium"
                    endIcon={<ArrowForward />}
                    onClick={() => navigate(`/submissions/${subId}`)}
                    sx={{
                      py: 1,
                      fontWeight: 700,
                      bgcolor: '#2563EB',
                      '&:hover': { bgcolor: '#1D4ED8' },
                    }}
                  >
                    Duyệt bài này
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
