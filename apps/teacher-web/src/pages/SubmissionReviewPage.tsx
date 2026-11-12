import {
  ArrowBack,
  CheckCircle,
  CheckCircleOutlined,
  Edit,
  NavigateBefore,
  NavigateNext,
  School,
  Shield,
} from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { StatusChip } from '../components/common/StatusChip';
import { SubmissionImage, type ImageStatus } from '../components/common/SubmissionImage';
import { AppTeacherService } from '../services/api/ServiceLocator';

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

  const currentSubId = (sub ? sub.id || (sub as any).submissionId || id : null) ?? null;
  const [prevSubId, setPrevSubId] = useState<string | null>(null);
  if (sub && currentSubId !== prevSubId) {
    setPrevSubId(currentSubId);
    if (typeof sub.teacherScore === 'number') {
      setEditScore(sub.teacherScore);
    } else if (typeof sub.suggestedScore === 'number') {
      setEditScore(sub.suggestedScore);
    } else {
      setEditScore(10);
    }
    if (sub.teacherReason) {
      setEditReason(sub.teacherReason);
    }
  }

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
      setActionError(err.response?.data?.error?.message || 'Có lỗi khi lưu điểm. Vui lòng thử lại.');
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
        <Typography color="error" variant="h6" component="h1" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải chi tiết bài làm.
        </Typography>
        <Button onClick={() => void refetch()}>Thử lại</Button>
        <Button variant="outlined" component={Link} to="/batches">
          Quay lại danh sách
        </Button>
      </Box>
    );
  }

  const isFinalized = sub.status === 'TEACHER_APPROVED' || sub.status === 'TEACHER_OVERRIDDEN';
  const isPending = overrideMutation.isPending;

  const handleSaveGrade = (advanceNext = false) => {
    if (!imageStatus.ready) {
      setActionError(`Chưa thể lưu điểm: ${imageStatus.reason || 'Ảnh bài làm chưa tải và giải mã thành công.'}`);
      return;
    }
    if (id && editScore !== '') {
      const score = Number(editScore);
      const maxScore = sub.maxScore ?? 10;
      if (!Number.isInteger(score) || score < 0 || score > maxScore) {
        setActionError(`Vui lòng nhập điểm số nguyên từ 0 đến ${maxScore}.`);
        return;
      }
      const reason = editReason.trim() || 'Giáo viên đã trực tiếp chấm bài và ghi nhận kết quả.';
      setActionError(null);
      overrideMutation.mutate(
        { subId: id, score, reason },
        {
          onSuccess: () => {
            setIsEditing(false);
            if (advanceNext && nextSub) {
              navigate(`/submissions/${encodeURIComponent(nextSub.submissionId)}${fromReview ? '?from=review' : ''}`);
            } else if (!advanceNext && !returnPath) {
              // stay on current page
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
            component={Link}
            to={returnPath}
            sx={{ mb: 1, px: 0 }}
          >
            {fromReview ? 'Quay lại hàng đợi duyệt' : 'Quay lại đợt chấm'}
          </Button>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="h5" component="h1" sx={{ fontWeight: 800 }}>
              Chấm bài học sinh: {sub.studentName || 'Học sinh'}
            </Typography>
            <StatusChip status={sub.status} />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Giáo viên trực tiếp quan sát ảnh bài làm, dùng bút đỏ nhận xét và cho điểm chính thức.
          </Typography>
        </Box>

        {/* Sibling Navigation Bar */}
        {totalSubmissions > 0 && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={`Bài ${currentIndex + 1} / ${totalSubmissions}`}
              variant="outlined"
              size="small"
              sx={{ fontWeight: 700, borderColor: '#CBD5E1', color: '#475569' }}
            />
            <Button
              variant="outlined"
              size="small"
              startIcon={<NavigateBefore />}
              disabled={!prevSub}
              component={Link}
              to={`/submissions/${encodeURIComponent(prevSub?.submissionId || '')}${fromReview ? '?from=review' : ''}`}
              sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
            >
              Bài trước
            </Button>
            <Button
              variant="outlined"
              size="small"
              endIcon={<NavigateNext />}
              disabled={!nextSub}
              component={Link}
              to={`/submissions/${encodeURIComponent(nextSub?.submissionId || '')}${fromReview ? '?from=review' : ''}`}
              sx={{ borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
            >
              Kế tiếp
            </Button>
          </Box>
        )}
      </Box>

      {isFinalized && !isEditing && (
        <Alert
          severity="success"
          sx={{ mb: 3, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          action={
            <Button
              color="inherit"
              size="small"
              startIcon={<Edit />}
              onClick={() => setIsEditing(true)}
              sx={{ fontWeight: 700, textTransform: 'none' }}
            >
              Chấm lại
            </Button>
          }
        >
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
              {typeof sub.teacherScore === 'number'
                ? `Điểm chính thức: ${sub.teacherScore} / ${sub.maxScore ?? 10} điểm`
                : 'Đã hoàn tất chấm điểm'}
            </Typography>
            {sub.teacherReason && <Typography variant="body2">{sub.teacherReason}</Typography>}
          </Box>
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
              />
            </Box>
          </Card>
        </Grid>

        {/* Right Column: Teacher Direct Grading & Feedback Section */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {/* Card 1: Student Submission Information */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', bgcolor: '#FFFFFF' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 1.5 }}>
                  <School sx={{ color: '#059669', fontSize: 24 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#065F46' }}>
                    THÔNG TIN BÀI NỘP CỦA HỌC SINH
                  </Typography>
                </Box>
                <Grid container spacing={1.5}>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary">Học sinh:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                      {sub.studentName || 'Học sinh'}
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary">Thang điểm bài:</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                      {sub.maxScore ?? 10} điểm
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary">Mã bài nộp:</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#475569' }}>
                      {id?.slice(0, 8)}...
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 6 }}>
                    <Typography variant="caption" color="text.secondary">Trạng thái:</Typography>
                    <Box sx={{ mt: 0.25 }}>
                      <StatusChip status={sub.status} />
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Card 2: Rubric Criteria Guide */}
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', bgcolor: '#F8FAFC' }}>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                  <CheckCircleOutlined sx={{ color: '#059669', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#065F46' }}>
                    TIÊU CHÍ CHẤM ĐIỂM SƯ PHẠM (RUBRIC THAM KHẢO)
                  </Typography>
                </Box>
                <Grid container spacing={1.5}>
                  <Grid size={{ xs: 4 }}>
                    <Box sx={{ p: 1.25, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0', textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Phương pháp giải
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, color: '#059669' }}>
                        6.0 / 10 đ
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Box sx={{ p: 1.25, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0', textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Kết quả số học
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, color: '#059669' }}>
                        3.0 / 10 đ
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Box sx={{ p: 1.25, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0', textAlign: 'center' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Trình bày & ô ly
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 800, color: '#059669' }}>
                        1.0 / 10 đ
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Card 3: Teacher Direct Grading & Feedback Card */}
            {(!isFinalized || isEditing) && (
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
                      BẢNG CHẤM ĐIỂM & NHẬN XÉT CỦA GIÁO VIÊN
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
                  ) : (
                    <Box>
                      <Grid container spacing={2} sx={{ mb: 2.5 }}>
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
                            label="Lời nhận xét / Lời phê cho học sinh"
                            value={editReason}
                            onChange={(e) => setEditReason(e.target.value)}
                            placeholder="Nhập lời phê, nhận xét bài làm của học sinh..."
                            disabled={isPending}
                            multiline
                            rows={1.5}
                          />
                        </Grid>
                      </Grid>

                      {/* Quick Sticker Tag Chips */}
                      <Box sx={{ mb: 2.5 }}>
                        <Typography variant="caption" sx={{ color: '#475569', fontWeight: 700, display: 'block', mb: 1 }}>
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

                      <Stack spacing={1.5}>
                        {nextSub && (
                          <Button
                            variant="contained"
                            color="success"
                            size="large"
                            endIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <NavigateNext />}
                            onClick={() => handleSaveGrade(true)}
                            disabled={!imageStatus.ready || isPending || editScore === ''}
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
                            onClick={() => handleSaveGrade(false)}
                            disabled={!imageStatus.ready || isPending || editScore === ''}
                            sx={{ flex: 2, py: 1.25, fontWeight: 700 }}
                          >
                            {isPending ? 'Đang lưu...' : `Lưu kết quả chấm bài (${editScore}đ)`}
                          </Button>

                          {isEditing && (
                            <Button
                              variant="outlined"
                              color="inherit"
                              onClick={() => setIsEditing(false)}
                              disabled={isPending}
                              sx={{ flex: 1, py: 1.25 }}
                            >
                              Hủy
                            </Button>
                          )}
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
