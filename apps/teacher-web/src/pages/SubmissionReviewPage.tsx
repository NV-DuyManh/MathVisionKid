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
  Stack,
} from '@mui/material';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
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
  NavigateBefore,
  NavigateNext,
  InfoOutlined,
} from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';
import { SubmissionImage, type ImageStatus } from '../components/common/SubmissionImage';

export default function SubmissionReviewPage() {
  const { id } = useParams<{ id: string }>();
  return <SubmissionReview key={id} id={id} />;
}

function SubmissionReview({ id }: { id?: string }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editScore, setEditScore] = useState<number | string>('');
  const [editReason, setEditReason] = useState('');
  const [hasAnnotations, setHasAnnotations] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [imageStatus, setImageStatus] = useState<ImageStatus>({
    ready: false,
    reason: 'Đang tải ảnh bài làm...',
  });

  const { data: sub, isLoading, isError, refetch } = useQuery({
    queryKey: ['submission', id],
    queryFn: () => AppTeacherService.getSubmissionDetail(id!),
    enabled: !!id,
  });
  const fromReview = params.get('from') === 'review';
  const returnPath = sub?.batchId ? '/batches/' + encodeURIComponent(sub.batchId) + (fromReview ? '/review' : '') : '/batches';

  const batchId = sub?.batchId;
  const { data: batchData } = useQuery({
    queryKey: ['batch', batchId],
    queryFn: () => AppTeacherService.getBatchStatus(batchId!),
    enabled: !!batchId,
  });

  const submissionsList = batchData?.submissions || [];
  const currentIndex = submissionsList.findIndex((s) => (s.submissionId || (s as any).id) === id);
  const totalSubmissions = submissionsList.length;
  const prevSub = currentIndex > 0 ? submissionsList[currentIndex - 1] : null;
  const nextSub = currentIndex >= 0 && currentIndex < totalSubmissions - 1 ? submissionsList[currentIndex + 1] : null;

  const suggestedScore = typeof sub?.suggestedScore === 'number'
    ? sub.suggestedScore
    : typeof sub?.gradeProposal?.score === 'number'
    ? sub.gradeProposal.score
    : undefined;

  const isFinalized = sub?.status === 'TEACHER_APPROVED' || sub?.status === 'TEACHER_OVERRIDDEN';
  const isProcessing = sub?.status === 'PROCESSING';
  const canDecide = !isFinalized && !isProcessing;

  const currentSubId = (sub ? sub.id || (sub as any).submissionId || id : null) ?? null;
  const [prevSubId, setPrevSubId] = useState<string | null>(null);
  if (sub && currentSubId !== prevSubId) {
    setPrevSubId(currentSubId);
    setIsEditing(false);
    if (typeof sub.teacherScore === 'number') {
      setEditScore(sub.teacherScore);
    } else {
      setEditScore(suggestedScore ?? '');
    }
    setEditReason(sub.teacherReason || '');
  }

  // Dirty state tracking to prevent loss of unsaved grades or annotations
  const isFormDirty = isEditing && (editScore !== (suggestedScore ?? '') || editReason.trim() !== '');
  const isDirty = isFormDirty || hasAnnotations;

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  const handleNavigateWithGuard = (targetPath: string) => {
    if (isDirty) {
      const ok = typeof window !== 'undefined' && typeof window.confirm === 'function'
        ? window.confirm('Thầy cô có điểm số hoặc lời phê chưa được lưu. Rời khỏi trang sẽ hủy các thay đổi này. Thầy cô có chắc chắn muốn chuyển bài?')
        : true;
      if (!ok) return;
    }
    navigate(targetPath);
  };

  const approveMutation = useMutation({
    mutationFn: (subId: string) => AppTeacherService.approveSubmission(subId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submission', id] });
      queryClient.invalidateQueries({ queryKey: ['reviewQueue'] });
      queryClient.invalidateQueries({ queryKey: ['batch'] });
      queryClient.invalidateQueries({ queryKey: ['teacher-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['teacher-batches'] });
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
      queryClient.invalidateQueries({ queryKey: ['teacher-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['teacher-batches'] });
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.error?.message || 'Có lỗi khi lưu điểm điều chỉnh. Vui lòng thử lại.');
    },
  });

  const isPending = approveMutation.isPending || overrideMutation.isPending;

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
        <Typography color="error" variant="h6" component="h1" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải chi tiết bài làm.
        </Typography>
        <Button onClick={() => void refetch()}>Thử lại</Button>
        <Button variant="outlined" onClick={() => navigate('/batches')}>
          Quay lại danh sách
        </Button>
      </Box>
    );
  }

  const handleApprove = (advanceNext = false) => {
    if (!imageStatus.ready) {
      setActionError(`Chưa thể duyệt điểm: ${imageStatus.reason || 'Ảnh bài làm chưa tải và giải mã thành công.'}`);
      return;
    }
    if (suggestedScore === undefined) {
      setActionError('Hệ thống không có điểm đề xuất để duyệt. Vui lòng nhập điểm và ghi lý do để chấm thủ công.');
      return;
    }
    if (id) {
      setActionError(null);
      approveMutation.mutate(id, {
        onSuccess: () => {
          if (advanceNext && nextSub) {
            navigate(`/submissions/${encodeURIComponent(nextSub.submissionId)}${fromReview ? '?from=review' : ''}`);
          } else if (advanceNext && !nextSub && returnPath) {
            navigate(returnPath);
          }
        },
      });
    }
  };

  const handleOverride = (advanceNext = false) => {
    if (!imageStatus.ready) {
      setActionError(`Chưa thể lưu điểm: ${imageStatus.reason || 'Ảnh bài làm chưa tải và giải mã thành công.'}`);
      return;
    }
    if (editScore === '') {
      setActionError('Vui lòng nhập điểm số chính thức của bài làm.');
      return;
    }
    const score = Number(editScore);
    const maxScore = sub.maxScore ?? 10;
    if (!Number.isInteger(score) || score < 0 || score > maxScore) {
      setActionError(`Vui lòng nhập điểm số nguyên từ 0 đến ${maxScore}.`);
      return;
    }
    if (!editReason.trim()) {
      setActionError('Vui lòng nhập lý do chấm/điều chỉnh điểm để lưu vào hồ sơ sư phạm.');
      return;
    }
    if (id) {
      setActionError(null);
      overrideMutation.mutate(
        { subId: id, score, reason: editReason.trim() },
        {
          onSuccess: () => {
            setIsEditing(false);
            if (advanceNext && nextSub) {
              navigate(`/submissions/${encodeURIComponent(nextSub.submissionId)}${fromReview ? '?from=review' : ''}`);
            } else if (advanceNext && !nextSub && returnPath) {
              navigate(returnPath);
            }
          },
        }
      );
    }
  };

  return (
    <Box>
      {/* Top Header & Breadcrumb with Sibling Navigation */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Button
            variant="text"
            startIcon={<ArrowBack />}
            onClick={() => handleNavigateWithGuard(returnPath)}
            sx={{ mb: 1, px: 0 }}
          >
            {fromReview ? 'Quay lại hàng đợi duyệt' : 'Quay lại đợt chấm'}
          </Button>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="h5" component="h1" sx={{ fontWeight: 800 }}>
              Thẩm định bài làm: {sub.studentName || 'Học sinh'}
            </Typography>
            <StatusChip status={sub.status} />
          </Box>
          <Typography variant="body2" color="text.secondary">
            AI đưa ra đánh giá tham vấn. Giáo viên là người có thẩm quyền quyết định điểm số chính thức.
          </Typography>
        </Box>

        {/* Sibling Queue Navigation */}
        {totalSubmissions > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={`Bài ${currentIndex >= 0 ? currentIndex + 1 : 1} / ${totalSubmissions}`}
              variant="outlined"
              size="small"
              sx={{ fontWeight: 700, borderColor: '#CBD5E1', color: '#475569' }}
            />
            <Button
              variant="outlined"
              size="small"
              startIcon={<NavigateBefore />}
              disabled={!prevSub}
              onClick={() => {
                if (prevSub) {
                  handleNavigateWithGuard(`/submissions/${encodeURIComponent(prevSub.submissionId)}${fromReview ? '?from=review' : ''}`);
                }
              }}
              sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
            >
              Bài trước
            </Button>
            <Button
              variant="outlined"
              size="small"
              endIcon={<NavigateNext />}
              disabled={!nextSub}
              onClick={() => {
                if (nextSub) {
                  handleNavigateWithGuard(`/submissions/${encodeURIComponent(nextSub.submissionId)}${fromReview ? '?from=review' : ''}`);
                }
              }}
              sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
            >
              Kế tiếp
            </Button>
          </Box>
        )}
      </Box>

      {/* Finalized Banner */}
      {isFinalized && (
        <Alert
          severity="success"
          sx={{ mb: 3, borderRadius: 2 }}
          icon={<CheckCircle sx={{ fontSize: 24 }} />}
        >
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
              {typeof sub.teacherScore === 'number'
                ? `Điểm chính thức: ${sub.teacherScore} / ${sub.maxScore ?? 10} điểm`
                : 'Đã hoàn tất chấm điểm'}
            </Typography>
            {sub.teacherReason && <Typography variant="body2" sx={{ mt: 0.25 }}>{sub.teacherReason}</Typography>}
            <Typography variant="caption" sx={{ color: '#047857', display: 'block', mt: 0.5 }}>
              ✓ Bài làm đã được giáo viên phê duyệt chính thức vào sổ điểm.
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Processing State Banner */}
      {isProcessing && (
        <Alert
          severity="info"
          sx={{ mb: 3, borderRadius: 2 }}
          icon={<InfoOutlined sx={{ fontSize: 24 }} />}
        >
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            Bài làm đang trong quá trình nhận diện và chẩn đoán tự động.
          </Typography>
          <Typography variant="body2">
            Vui lòng đợi hệ thống xử lý hoàn tất trước khi thực hiện phê duyệt hoặc điều chỉnh điểm.
          </Typography>
        </Alert>
      )}

      {/* Review Required Alert */}
      {sub.status === 'REVIEW_REQUIRED' && !isFinalized && (
        <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
            Hệ thống yêu cầu giáo viên xem lại bài làm này.
          </Typography>
          <Typography variant="body2">
            Độ tin cậy nhận diện thấp hoặc phát hiện bước giải cần xác nhận của giáo viên. Thầy cô vui lòng đối chiếu kỹ ảnh bài làm với kết quả OCR bên dưới.
          </Typography>
        </Alert>
      )}

      {actionError && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {actionError}
        </Alert>
      )}

      <Grid container spacing={3.5}>
        {/* Left Column: Image & Interactive Drawing Canvas */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card
            sx={{
              height: '100%',
              bgcolor: '#1E293B',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 2.5,
              overflow: 'hidden',
              position: 'relative',
              minHeight: { xs: 320, md: 540 },
              boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
            }}
          >
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                p: 1.5,
              }}
            >
              <SubmissionImage
                id={id!}
                mockUrl={sub.imageUrl}
                studentName={sub.studentName}
                onStatusChange={setImageStatus}
                onAnnotationsChange={setHasAnnotations}
              />
            </Box>

            {/* Evidence Overlay / Position Indicator */}
            {sub.evidence?.position && (
              <Box
                sx={{
                  p: 1.5,
                  bgcolor: 'rgba(15, 23, 42, 0.94)',
                  color: 'white',
                  borderTop: '1px solid rgba(255, 255, 255, 0.12)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <HelpOutlined sx={{ fontSize: 18, color: '#FCD34D' }} />
                <Typography variant="caption" sx={{ color: '#E9E2F2', fontWeight: 600 }}>
                  Vị trí phát hiện nghi vấn trên bài: <strong>{sub.evidence.position}</strong>
                </Typography>
              </Box>
            )}

            <Box sx={{ p: 1.5, bgcolor: '#0F172A', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <Typography variant="caption" sx={{ display: 'block', color: '#94A3B8', textAlign: 'center', fontSize: '0.73rem' }}>
                💡 Bút vẽ và tem chấm là công cụ đối soát trực quan trong phiên làm việc. Điểm số chính thức và lời phê là dữ liệu lưu trữ vĩnh viễn vào sổ điểm.
              </Typography>
            </Box>
          </Card>
        </Grid>

        {/* Right Column: AI Analysis Findings & Decision Authority */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>

            {/* Card 1: AI Evidence & OCR Findings */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', bgcolor: '#FFFFFF', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <SmartToy sx={{ color: '#2563EB', fontSize: 22 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#1E40AF', letterSpacing: '0.04em' }}>
                    GHI NHẬN TỪ HỆ THỐNG AI
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Dấu hiệu cần xem xét
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 700, color: '#B91C1C' }}>
                        {sub.evidence?.rule || 'Quy tắc tính toán hoặc nét chữ'}
                      </Typography>
                    </Box>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 1.5, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Thuật toán đối soát
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          mt: 0.5,
                          fontWeight: 700,
                          color: sub.decision === 'VALID' ? '#15803D' : sub.decision === 'INVALID' ? '#B91C1C' : '#D97706',
                        }}
                      >
                        {sub.decision === 'VALID'
                          ? 'Hợp lệ theo quy tắc'
                          : sub.decision === 'INVALID'
                          ? 'Phát hiện lỗi tính cần xem lại'
                          : 'Chưa đủ dữ liệu để kết luận'}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>

                {sub.recognizedText ? (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                      Ký tự OCR nhận diện từ ảnh bài làm:
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        p: 1.5,
                        bgcolor: '#F8FAFC',
                        borderRadius: 1.5,
                        mt: 0.5,
                        color: '#0F172A',
                        border: '1px solid #E2E8F0',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {sub.recognizedText}
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ mt: 2, p: 1.25, bgcolor: '#F1F5F9', borderRadius: 1.5, border: '1px dashed #CBD5E1' }}>
                    <Typography variant="caption" color="text.secondary">
                      Chưa có văn bản OCR được trích xuất hoặc ảnh đang được xử lý.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Card 2: Advisory Proposed Grade & Confidence Semantics */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', bgcolor: '#F8FAFC', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AutoAwesome sx={{ color: '#2563EB', fontSize: 20 }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#475569', letterSpacing: '0.04em' }}>
                      ĐỀ XUẤT TỪ AI (THAM VẤN)
                    </Typography>
                  </Box>
                  <Chip
                    label={isFinalized ? 'Điểm tham khảo' : suggestedScore !== undefined ? 'Chưa chốt điểm' : 'Không có điểm đề xuất'}
                    size="small"
                    sx={{
                      bgcolor: suggestedScore !== undefined ? '#FEF3C7' : '#F1F5F9',
                      color: suggestedScore !== undefined ? '#B45309' : '#64748B',
                      fontWeight: 600,
                      fontSize: '0.75rem',
                    }}
                  />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, my: 1 }}>
                  <Typography variant="h3" sx={{ fontWeight: 800, color: suggestedScore !== undefined ? '#2563EB' : '#94A3B8' }}>
                    {suggestedScore !== undefined ? suggestedScore : '--'}
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    / {sub.maxScore ?? 10} điểm
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

            {/* Card 3: Teacher Authority & Final Decision Card */}
            {canDecide && (
              <Card
                sx={{
                  borderRadius: 2.5,
                  border: '2px solid #059669',
                  boxShadow: '0 4px 14px rgba(5, 150, 105, 0.12)',
                }}
              >
                <CardContent sx={{ p: 2.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Shield sx={{ color: '#059669', fontSize: 22 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#059669' }}>
                      QUYẾT ĐỊNH CỦA GIÁO VIÊN
                    </Typography>
                  </Box>

                  {!imageStatus.ready ? (
                    <Box>
                      <Alert severity="warning" sx={{ mb: 2, borderRadius: 2 }} role="status">
                        Chưa thể duyệt hoặc điều chỉnh điểm: {imageStatus.reason || 'Ảnh bài làm chưa được tải hoặc giải mã thành công.'}
                      </Alert>
                      <Typography variant="body2" color="text.secondary">
                        Thầy cô vui lòng kiểm tra bài làm của học sinh bên trái trước khi cho điểm chính thức.
                      </Typography>
                    </Box>
                  ) : !isEditing ? (
                    <Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {suggestedScore !== undefined
                          ? 'Nếu đồng ý với đánh giá của hệ thống, chọn Duyệt điểm. Nếu cần chỉnh sửa theo quy chế nhà trường, chọn Điều chỉnh.'
                          : 'Hệ thống không có điểm đề xuất cho bài làm này. Thầy cô vui lòng chọn Chấm bài để nhập điểm và lý do trực tiếp.'}
                      </Typography>

                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
                        {suggestedScore !== undefined ? (
                          <>
                            {nextSub && (
                              <Button
                                variant="contained"
                                color="success"
                                size="large"
                                endIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <NavigateNext />}
                                onClick={() => handleApprove(true)}
                                disabled={!imageStatus.ready || isPending}
                                sx={{
                                  flex: { xs: '1 1 100%', sm: 2 },
                                  py: 1.25,
                                  fontWeight: 700,
                                  bgcolor: '#059669',
                                  '&:hover': { bgcolor: '#047857' },
                                }}
                              >
                                {isPending ? 'Đang lưu...' : `Duyệt ${suggestedScore}đ & Sang bài kế tiếp ➔`}
                              </Button>
                            )}

                            <Button
                              variant={nextSub ? 'outlined' : 'contained'}
                              color="success"
                              size="large"
                              startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <CheckCircle />}
                              onClick={() => handleApprove(false)}
                              disabled={!imageStatus.ready || isPending}
                              sx={{ flex: { xs: '1 1 100%', sm: 1 }, py: 1.25, fontWeight: 700 }}
                            >
                              {isPending ? 'Đang lưu...' : `Duyệt điểm ${suggestedScore}`}
                            </Button>

                            <Button
                              variant="outlined"
                              size="large"
                              startIcon={<Edit />}
                              onClick={() => {
                                setEditScore(suggestedScore);
                                setEditReason('');
                                setIsEditing(true);
                              }}
                              disabled={!imageStatus.ready || isPending}
                              sx={{ flex: { xs: '1 1 100%', sm: 1 }, py: 1.25, fontWeight: 700 }}
                            >
                              Điều chỉnh
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="contained"
                            color="success"
                            size="large"
                            startIcon={<Edit />}
                            onClick={() => {
                              setEditScore('');
                              setEditReason('');
                              setIsEditing(true);
                            }}
                            disabled={!imageStatus.ready || isPending}
                            sx={{ flex: 1, py: 1.25, fontWeight: 700, bgcolor: '#059669', '&:hover': { bgcolor: '#047857' } }}
                          >
                            Chấm bài & Cho điểm thủ công
                          </Button>
                        )}
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
                            slotProps={{ htmlInput: { min: 0, max: sub.maxScore ?? 10, step: 1 } }}
                            disabled={isPending}
                            autoFocus
                            placeholder={`0 – ${sub.maxScore ?? 10}`}
                            sx={{
                              '& .MuiInputBase-input': {
                                fontSize: '1.25rem',
                                fontWeight: 800,
                                color: '#059669',
                              },
                            }}
                          />
                        </Grid>
                        <Grid size={{ xs: 12, sm: 8 }}>
                          <TextField
                            fullWidth
                            label="Lý do điều chỉnh / Lời phê (Bắt buộc)"
                            value={editReason}
                            onChange={(e) => setEditReason(e.target.value)}
                            placeholder="Nhập lý do cho điểm hoặc nhận xét bài làm..."
                            disabled={isPending}
                            multiline
                            rows={1.5}
                          />
                        </Grid>
                      </Grid>

                      {/* Quick Sticker Tag Chips */}
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" sx={{ color: '#475569', fontWeight: 700, display: 'block', mb: 0.75 }}>
                          Gắn Sticker nhận xét nhanh:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
                          {[
                            '⭐ Trình bày sạch đẹp, đặt tính thẳng hàng',
                            '⭐ Tính toán nhanh và chính xác',
                            '💡 Chú ý bước quy đồng mẫu số',
                            '💡 Cần rút gọn phân số tối giản',
                            '⚠️ Chú ý nhớ 1 khi cộng/trừ qua hàng chục',
                            '👏 Bài làm rất tốt, đáng khen!',
                          ].map((sticker) => (
                            <Chip
                              key={sticker}
                              label={sticker}
                              size="small"
                              variant="outlined"
                              onClick={() => {
                                setEditReason((prev) => (prev ? `${prev}; ${sticker}` : sticker));
                              }}
                              sx={{
                                cursor: 'pointer',
                                fontSize: '0.73rem',
                                borderRadius: 2,
                                borderColor: '#CBD5E1',
                                '&:hover': { bgcolor: '#F0FDF4', borderColor: '#86EFAC' },
                              }}
                            />
                          ))}
                        </Box>
                      </Box>

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

                      <Stack spacing={1.5}>
                        {nextSub && (
                          <Button
                            variant="contained"
                            color="success"
                            size="large"
                            endIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <NavigateNext />}
                            onClick={() => handleOverride(true)}
                            disabled={!imageStatus.ready || isPending || editScore === '' || !editReason.trim()}
                            sx={{
                              py: 1.25,
                              fontWeight: 700,
                              bgcolor: '#059669',
                              '&:hover': { bgcolor: '#047857' },
                            }}
                          >
                            {isPending ? 'Đang lưu...' : `Lưu ${editScore !== '' ? editScore : ''}đ & Sang bài kế tiếp ➔`}
                          </Button>
                        )}

                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
                          <Button
                            variant={nextSub ? 'outlined' : 'contained'}
                            color="success"
                            size="large"
                            startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <CheckCircle />}
                            onClick={() => handleOverride(false)}
                            disabled={!imageStatus.ready || isPending || editScore === '' || !editReason.trim()}
                            sx={{ flex: 2, py: 1.25, fontWeight: 700 }}
                          >
                            {isPending ? 'Đang lưu...' : 'Xác nhận ghi đè điểm'}
                          </Button>

                          <Button
                            variant="outlined"
                            color="inherit"
                            onClick={() => setIsEditing(false)}
                            disabled={isPending}
                            sx={{ flex: 1, py: 1.25 }}
                          >
                            Hủy
                          </Button>
                        </Box>
                      </Stack>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}

          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
