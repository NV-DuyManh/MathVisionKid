import { useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, CircularProgress, Paper, Divider } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { CheckCircle, ArrowBack, ArrowForward, AutoAwesome, Check } from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';

export default function ReviewQueuePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [quickApproveId, setQuickApproveId] = useState<string | null>(null);

  const { data: queue, isLoading, isError, refetch } = useQuery({
    queryKey: ['reviewQueue', id],
    queryFn: () => AppTeacherService.getReviewQueue(id!),
    enabled: !!id,
    refetchInterval: 5000, // Tự động làm mới khi các bài được duyệt xong
  });

  const quickApproveMutation = useMutation({
    mutationFn: (subId: string) => AppTeacherService.approveSubmission(subId),
    onSuccess: (_, subId) => {
      setQuickApproveId(null);
      queryClient.invalidateQueries({ queryKey: ['reviewQueue', id] });
      queryClient.invalidateQueries({ queryKey: ['submission', subId] });
      queryClient.invalidateQueries({ queryKey: ['batch', id] });
      queryClient.invalidateQueries({ queryKey: ['teacher-dashboard'] });
    },
    onError: () => {
      setQuickApproveId(null);
    },
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
        <Typography color="error" variant="h6" component="h1" sx={{ mb: 2 }}>
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
          <Typography variant="h5" component="h1" sx={{ fontWeight: 800, color: '#15803D', mb: 1 }}>
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
    <Box>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate(`/batches/${id}`)}
        sx={{ mb: 2 }}
      >
        Quay lại chi tiết đợt chấm
      </Button>

      <PageHeader
        title="Hàng đợi Thẩm định & Duyệt bài"
        subtitle={`Có ${queue.length} bài làm cần giáo viên thẩm định và quyết định điểm số chính thức.`}
        actions={
          <Button
            variant="outlined"
            size="small"
            onClick={() => void refetch()}
            sx={{ borderRadius: 2.5, fontWeight: 600, textTransform: 'none' }}
          >
            Làm mới danh sách
          </Button>
        }
      />

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
                  boxShadow: '0 1px 3px rgba(15,23,42,0.05)',
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

                  {/* Actions */}
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {suggested !== undefined && (
                      <Button
                        variant="outlined"
                        size="medium"
                        color="success"
                        startIcon={quickApproveId === subId ? <CircularProgress size={16} color="inherit" /> : <Check />}
                        disabled={quickApproveMutation.isPending}
                        onClick={() => {
                          setQuickApproveId(subId);
                          quickApproveMutation.mutate(subId);
                        }}
                        sx={{
                          py: 1.1,
                          fontWeight: 700,
                          flexShrink: 0,
                          borderColor: '#10B981',
                          color: '#059669',
                          '&:hover': { bgcolor: '#ECFDF5', borderColor: '#059669' },
                        }}
                      >
                        Duyệt nhanh
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      fullWidth
                      size="medium"
                      endIcon={<ArrowForward />}
                      onClick={() => navigate(`/submissions/${subId}`)}
                      sx={{
                        py: 1.1,
                        fontWeight: 700,
                      }}
                    >
                      Chi tiết & Chấm
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
