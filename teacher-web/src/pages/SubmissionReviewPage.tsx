import { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, TextField, CircularProgress } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { CheckCircle, Edit, Warning, SmartToy, Policy, Shield } from '@mui/icons-material';

export default function SubmissionReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [isEditing, setIsEditing] = useState(false);
  const [editScore, setEditScore] = useState<number | string>('');
  const [editReason, setEditReason] = useState('');

  const { data: sub, isLoading, isError } = useQuery({
    queryKey: ['submission', id],
    queryFn: () => AppTeacherService.getSubmissionDetail(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (sub && editScore === '') {
      setEditScore(sub.suggestedScore || sub.gradeProposal?.score || 0);
    }
  }, [sub, editScore]);

  const approveMutation = useMutation({
    mutationFn: (subId: string) => AppTeacherService.approveSubmission(subId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
      navigate(-1);
    }
  });

  const overrideMutation = useMutation({
    mutationFn: ({ subId, score }: { subId: string, score: number }) => AppTeacherService.overrideSubmission(subId, score),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
      navigate(-1);
    }
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !sub) {
    return (
      <Box sx={{ textAlign: 'center', mt: 8, p: 4 }}>
        <Typography color="error">Đã xảy ra lỗi khi tải chi tiết bài làm.</Typography>
      </Box>
    );
  }

  const handleApprove = () => {
    if (id) approveMutation.mutate(id);
  };

  const handleOverride = () => {
    if (id && editScore !== '') {
      overrideMutation.mutate({ subId: id, score: Number(editScore) });
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: '700' }}>Chi tiết duyệt bài: {sub.studentName}</Typography>
          <Typography variant="body2" color="text.secondary">Hệ thống AI đã đánh giá bài làm. Quyết định cuối cùng thuộc về bạn.</Typography>
        </Box>
        <Button variant="text" onClick={() => navigate(-1)}>Quay lại hàng đợi</Button>
      </Box>

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ height: '100%', bgcolor: 'grey.100', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 500, border: '1px solid', borderColor: 'divider', position: 'relative' }}>
            <Box
              component="img"
              src={sub.imageUrl}
              alt="Bài làm"
              sx={{ maxWidth: '100%', maxHeight: 800, objectFit: 'contain' }}
            />
            {sub.evidence?.position && (
              <Box sx={{ position: 'absolute', bottom: 16, left: 16, bgcolor: 'rgba(255,255,255,0.9)', p: 1, borderRadius: 1, boxShadow: 1 }}>
                <Typography variant="caption" color="text.secondary">Vị trí phát hiện lỗi: {sub.evidence.position}</Typography>
              </Box>
            )}
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, height: '100%' }}>
            
            <Card variant="outlined" sx={{ borderColor: 'primary.100' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <SmartToy color="primary" fontSize="small" />
                  <Typography variant="subtitle2" color="primary.main" sx={{ fontWeight: '700', letterSpacing: '0.05em' }}>GHI NHẬN TỪ AI</Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                      <Typography variant="body2" color="text.secondary">Quy tắc vi phạm</Typography>
                      <Typography variant="body1" color="error.main" sx={{ mt: 0.5, fontWeight: '600' }}>{sub.evidence?.rule || 'Không'}</Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                      <Typography variant="body2" color="text.secondary">Thuật toán đánh giá</Typography>
                      <Typography variant="body1" color={sub.decision === 'VALID' ? 'success.main' : 'error.main'} sx={{ mt: 0.5, fontWeight: '600' }}>
                        {sub.decision === 'VALID' ? 'Đúng' : 'Sai'}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
                
                {sub.recognizedText && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">Bản dịch OCR:</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', p: 1, bgcolor: 'grey.100', borderRadius: 1, mt: 0.5 }}>{sub.recognizedText}</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ borderColor: 'divider', bgcolor: 'grey.50' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Policy color="action" fontSize="small" />
                  <Typography variant="subtitle2" color="text.secondary" sx={{ fontWeight: '700', letterSpacing: '0.05em' }}>ĐỀ XUẤT ĐIỂM (CHƯA PHẢI ĐIỂM CHÍNH THỨC)</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                  <Typography variant="h3" color="text.primary" sx={{ fontWeight: '800' }}>{sub.suggestedScore}</Typography>
                  <Typography variant="h6" color="text.secondary">/ 10</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Dựa trên cấu trúc bài làm. Độ tự tin: <strong>{sub.diagnosisConfidence}%</strong>
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ mt: 'auto', border: '2px solid', borderColor: 'primary.main', boxShadow: '0 4px 12px rgba(79, 70, 229, 0.15)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <Shield color="primary" fontSize="small" />
                  <Typography variant="subtitle1" color="primary.main" sx={{ fontWeight: '700' }}>QUYẾT ĐỊNH CỦA GIÁO VIÊN</Typography>
                </Box>

                {!isEditing ? (
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button 
                      variant="contained" 
                      color="primary" 
                      size="large" 
                      startIcon={<CheckCircle />}
                      onClick={handleApprove}
                      disabled={approveMutation.isPending || overrideMutation.isPending}
                      sx={{ flex: 2, py: 1.5 }}
                    >
                      Duyệt điểm {sub.suggestedScore}
                    </Button>
                    <Button 
                      variant="outlined" 
                      color="primary" 
                      size="large" 
                      startIcon={<Edit />}
                      onClick={() => setIsEditing(true)}
                      disabled={approveMutation.isPending || overrideMutation.isPending}
                      sx={{ flex: 1, py: 1.5 }}
                    >
                      Điều chỉnh
                    </Button>
                  </Box>
                ) : (
                  <Box>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField 
                          fullWidth
                          label="Điểm chính thức" 
                          type="number"
                          value={editScore}
                          onChange={e => setEditScore(e.target.value)}
                          slotProps={{ htmlInput: { min: 0, max: 10 } }}
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 8 }}>
                        <TextField 
                          fullWidth
                          label="Lý do điều chỉnh (Bắt buộc)" 
                          value={editReason}
                          onChange={e => setEditReason(e.target.value)}
                        />
                      </Grid>
                    </Grid>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3, gap: 1, color: 'warning.dark', bgcolor: 'warning.50', p: 1.5, borderRadius: 1 }}>
                      <Warning fontSize="small" />
                      <Typography variant="body2">Kết quả này sẽ thay thế đề xuất của AI và được lưu làm điểm chính thức.</Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleOverride}
                        disabled={editScore === '' || editReason.trim() === '' || approveMutation.isPending || overrideMutation.isPending}
                        sx={{ flex: 1 }}
                      >
                        Xác nhận ghi đè
                      </Button>
                      <Button variant="text" onClick={() => setIsEditing(false)}>Hủy</Button>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
