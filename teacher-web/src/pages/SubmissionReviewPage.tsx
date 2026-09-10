import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  CircularProgress,
  Divider,
  Alert,
  Chip,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import {
  CheckCircle,
  Edit,
  Warning,
  SmartToy,
  Shield,
  ArrowBack,
  HelpOutlined,
  AutoAwesome,
} from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';

export default function SubmissionReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editScore, setEditScore] = useState<number | string>('');
  const [editReason, setEditReason] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: sub, isLoading, isError } = useQuery({
    queryKey: ['submission', id],
    queryFn: () => AppTeacherService.getSubmissionDetail(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (sub && editScore === '') {
      const initial = sub.suggestedScore !== undefined ? sub.suggestedScore : (sub.gradeProposal?.score ?? 0);
      setEditScore(initial);
    }
  }, [sub, editScore]);

  const approveMutation = useMutation({
    mutationFn: (subId: string) => AppTeacherService.approveSubmission(subId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
      navigate(-1);
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.error?.message || 'Có lỗi khi duyệt điểm. Vui lòng thử lại.');
    },
  });

  const overrideMutation = useMutation({
    mutationFn: ({ subId, score, reason }: { subId: string; score: number; reason: string }) =>
      AppTeacherService.overrideSubmission(subId, score, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
      navigate(-1);
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.error?.message || 'Có lỗi khi điều chỉnh điểm. Vui lòng thử lại.');
    },
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Đang tải chi tiết bài làm học sinh...
        </Typography>
      </Box>
    );
  }

  if (isError || !sub) {
    return (
      <Box sx={{ maxWidth: 640, mx: 'auto', textAlign: 'center', mt: 6, p: 4 }}>
        <Typography color="error" variant="h6" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải chi tiết bài làm.
        </Typography>
        <Button variant="outlined" onClick={() => navigate(-1)}>
          Quay lại danh sách
        </Button>
      </Box>
    );
  }

  const handleApprove = () => {
    if (id) {
      setActionError(null);
      approveMutation.mutate(id);
    }
  };

  const handleOverride = () => {
    if (id && editScore !== '') {
      setActionError(null);
      overrideMutation.mutate({ subId: id, score: Number(editScore), reason: editReason.trim() });
    }
  };

  const suggestedScore = sub.suggestedScore !== undefined ? sub.suggestedScore : sub.gradeProposal?.score;
  const isPending = approveMutation.isPending || overrideMutation.isPending;

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Top Header & Breadcrumb */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Button
            variant="text"
            startIcon={<ArrowBack />}
            onClick={() => navigate(-1)}
            sx={{ mb: 1, px: 0 }}
          >
            Quay lại hàng đợi duyệt
          </Button>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="h5" sx={{ fontWeight: 800 }}>
              Thẩm định bài làm: {sub.studentName || 'Học sinh'}
            </Typography>
            <StatusChip status={sub.status} />
          </Box>
          <Typography variant="body2" color="text.secondary">
            AI đưa ra đánh giá tham vấn. Giáo viên là người có thẩm quyền quyết định điểm số chính thức.
          </Typography>
        </Box>
      </Box>

      {actionError && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {actionError}
        </Alert>
      )}

      <Grid container spacing={3.5}>
        {/* Left Column: Image & Visual Evidence */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card
            sx={{
              height: '100%',
              bgcolor: '#0F172A',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 2.5,
              overflow: 'hidden',
              position: 'relative',
              minHeight: 520,
            }}
          >
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 2,
              }}
            >
              <Box
                component="img"
                src={sub.imageUrl}
                alt={`Bài làm của ${sub.studentName || 'học sinh'}`}
                sx={{
                  maxWidth: '100%',
                  maxHeight: 650,
                  objectFit: 'contain',
                  borderRadius: 1.5,
                }}
              />
            </Box>

            {/* Evidence Overlay / Position Indicator */}
            {sub.evidence?.position && (
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: 'rgba(15, 23, 42, 0.92)',
                  color: 'white',
                  borderTop: '1px solid rgba(255, 255, 255, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <HelpOutlined sx={{ fontSize: 18, color: '#FCD34D' }} />
                <Typography variant="caption" sx={{ color: '#E2E8F0', fontWeight: 600 }}>
                  Vị trí phát hiện nghi vấn: <strong>{sub.evidence.position}</strong>
                </Typography>
              </Box>
            )}
          </Card>
        </Grid>

        {/* Right Column: AI Analysis & Decision Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {/* Card 1: AI Evidence Findings */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#BFDBFE' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <SmartToy sx={{ color: '#2563EB', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#1D4ED8', letterSpacing: '0.04em' }}>
                    GHI NHẬN TỪ HỆ THỐNG AI
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 1.75, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Dấu hiệu cần xem xét
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 700, color: '#B91C1C' }}>
                        {sub.evidence?.rule || 'Quy tắc tính toán hoặc nét chữ'}
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 1.75, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Thuật toán đối soát
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          mt: 0.5,
                          fontWeight: 700,
                          color: sub.decision === 'VALID' ? '#15803D' : '#B91C1C',
                        }}
                      >
                        {sub.decision === 'VALID' ? 'Hợp lệ theo quy tắc' : 'Nghi ngờ có lỗi tính'}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {sub.recognizedText && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                      Ký tự OCR nhận diện:
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        p: 1.5,
                        bgcolor: '#F1F5F9',
                        borderRadius: 1.5,
                        mt: 0.5,
                        color: '#0F172A',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {sub.recognizedText}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Card 2: Advisory Proposed Grade & Confidence Semantics */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', bgcolor: '#F8FAFC' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AutoAwesome sx={{ color: '#2563EB', fontSize: 20 }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#475569', letterSpacing: '0.04em' }}>
                      ĐỀ XUẤT TỪ AI (CHƯA CHÍNH THỨC)
                    </Typography>
                  </Box>
                  <Chip
                    label="Chưa chốt điểm"
                    size="small"
                    sx={{ bgcolor: '#FEF3C7', color: '#B45309', fontWeight: 600, fontSize: '0.75rem' }}
                  />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, my: 1 }}>
                  <Typography variant="h3" sx={{ fontWeight: 800, color: '#2563EB' }}>
                    {suggestedScore !== undefined ? suggestedScore : '--'}
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    / 10 điểm
                  </Typography>
                </Box>

                <Divider sx={{ my: 1.5 }} />

                <Grid container spacing={2}>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      Độ tin cậy nhận diện:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                      {sub.recognitionConfidence !== undefined ? `${Math.round(sub.recognitionConfidence)}%` : 'Chưa có'}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      Độ tin cậy chẩn đoán:
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                      {sub.diagnosisConfidence !== undefined ? `${Math.round(sub.diagnosisConfidence)}%` : 'Chưa có'}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Card 3: Teacher Authority & Final Decision */}
            <Card
              sx={{
                borderRadius: 2.5,
                border: '2px solid #2563EB',
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.12)',
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Shield sx={{ color: '#2563EB', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#2563EB' }}>
                    QUYẾT ĐỊNH CỦA GIÁO VIÊN
                  </Typography>
                </Box>

                {!isEditing ? (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Nếu đồng ý với đánh giá của hệ thống, chọn <strong>Duyệt điểm</strong>. Nếu cần chỉnh sửa theo quy chế nhà trường, chọn <strong>Điều chỉnh điểm</strong>.
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button
                        variant="contained"
                        size="large"
                        startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <CheckCircle />}
                        onClick={handleApprove}
                        disabled={isPending}
                        sx={{ flex: 2, py: 1.25, fontWeight: 700 }}
                      >
                        {isPending ? 'Đang lưu...' : `Duyệt điểm ${suggestedScore !== undefined ? suggestedScore : ''}`}
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        startIcon={<Edit />}
                        onClick={() => setIsEditing(true)}
                        disabled={isPending}
                        sx={{ flex: 1, py: 1.25, fontWeight: 700 }}
                      >
                        Điều chỉnh
                      </Button>
                    </Box>
                  </Box>
                ) : (
                  <Box>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                          fullWidth
                          label="Điểm chính thức"
                          type="number"
                          value={editScore}
                          onChange={(e) => setEditScore(e.target.value)}
                          slotProps={{ htmlInput: { min: 0, max: 10, step: 0.5 } }}
                          disabled={isPending}
                          autoFocus
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 8 }}>
                        <TextField
                          fullWidth
                          label="Lý do điều chỉnh (Bắt buộc)"
                          value={editReason}
                          onChange={(e) => setEditReason(e.target.value)}
                          placeholder="VD: Học sinh cộng nhầm hàng chục nhưng đặt tính đúng"
                          disabled={isPending}
                        />
                      </Grid>
                    </Grid>

                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        mb: 2.5,
                        gap: 1,
                        bgcolor: '#FFFBEB',
                        p: 1.5,
                        borderRadius: 1.5,
                        border: '1px solid #FCD34D',
                      }}
                    >
                      <Warning sx={{ fontSize: 18, color: '#B45309' }} />
                      <Typography variant="caption" sx={{ color: '#92400E', fontWeight: 600 }}>
                        Quyết định này sẽ ghi đè đề xuất của AI và lưu vào sổ điểm chính thức với danh nghĩa giáo viên.
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1.5 }}>
                      <Button
                        variant="contained"
                        onClick={handleOverride}
                        disabled={editScore === '' || !editReason.trim() || isPending}
                        startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : null}
                        sx={{ flex: 1, py: 1, fontWeight: 700 }}
                      >
                        {isPending ? 'Đang lưu...' : 'Xác nhận ghi đè điểm'}
                      </Button>
                      <Button
                        variant="outlined"
                        color="inherit"
                        onClick={() => setIsEditing(false)}
                        disabled={isPending}
                      >
                        Hủy
                      </Button>
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
