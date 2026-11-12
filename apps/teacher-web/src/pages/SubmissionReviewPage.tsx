import { useCallback, useEffect, useRef, useState } from 'react';
import { isAxiosError } from 'axios';
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
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { AuthTokenStore } from '../services/api/AuthTokenStore';
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
import { SubmissionImage, type ImageStatus } from '../components/common/SubmissionImage';
import { SubmissionRetake } from './SubmissionRetake';
import type { EvidenceItem } from '../types';

type GradeDecision = { kind: 'approve' } | { kind: 'override'; score: number; reason: string; imageLegible?: true };

export default function SubmissionReviewPage() {
  const { id } = useParams<{ id: string }>();
  return <SubmissionReview key={id} id={id} />;
}

function SubmissionReview({ id }: { id?: string }) {
  const [params] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [editScore, setEditScore] = useState('');
  const [editReason, setEditReason] = useState('');
  const [isImageLegible, setIsImageLegible] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [needsOutcomeCheck, setNeedsOutcomeCheck] = useState(false);
  const [needsRetryCheck, setNeedsRetryCheck] = useState(false);
  const [findingNext, setFindingNext] = useState(false);
  const [nextError, setNextError] = useState(false);
  const writeInFlight = useRef(false);
  const reviewMounted = useRef(false);
  useEffect(() => {
    reviewMounted.current = true;
    return () => { reviewMounted.current = false; };
  }, []);
  const decisionNoticeRef = useRef<HTMLDivElement>(null);
  const [imageReadiness, setImageReadiness] = useState<{ version?: string; status: ImageStatus } | null>(null);

  const { data: sub, isLoading, isError, fetchStatus, refetch } = useQuery({
    queryKey: ['submission', id],
    queryFn: () => AppTeacherService.getSubmissionDetail(id!),
    enabled: !!id,
    refetchInterval: ({ state }) => state.status === 'success' && state.data?.status === 'PROCESSING' ? 3000 : false,
  });
  const imageVersion = sub?.imageVersion;
  const handleImageStatus = useCallback((status: ImageStatus) => setImageReadiness({ version: imageVersion, status }), [imageVersion]);
  const imageStatus = imageReadiness && imageReadiness.version === imageVersion
    ? imageReadiness.status : { ready: false, reason: 'Đang tải ảnh bài làm...' };
  const isRefreshing = fetchStatus !== 'idle';
  const origin = params.get('from');
  const fromReview = origin === 'review';
  const returnSuffix = fromReview ? '/review' : origin === 'failed' ? '?status=failed' : '';
  const returnPath = sub?.batchId ? '/batches/' + encodeURIComponent(sub.batchId) + returnSuffix : '/batches';
  const returnState = sub?.batchId ? location.state : undefined;
  const queueState = returnState?.reviewQueue;
  const sessionId = AuthTokenStore.getSessionId();
  const nextIds: string[] = fromReview && sessionId && queueState?.sessionId === sessionId
    && queueState?.batchId === sub?.batchId && Array.isArray(returnState?.nextReviewIds)
    ? returnState.nextReviewIds : [];

  const openNextReview = async () => {
    const batchId = sub?.batchId;
    if (!batchId || findingNext) return;
    setFindingNext(true);
    setNextError(false);
    try {
      const queue = await queryClient.fetchQuery({
        queryKey: ['reviewQueue', batchId],
        queryFn: () => AppTeacherService.getReviewQueue(batchId),
        staleTime: 0,
      });
      if (!reviewMounted.current || AuthTokenStore.getSessionId() !== sessionId) return;
      const { statusFilter, searchQuery } = queueState.filters;
      const search = searchQuery.trim().toLocaleLowerCase('vi');
      const nextIndex = nextIds.findIndex(candidate => queue.some(item =>
        (item.id || item.submissionId) === candidate
        && (statusFilter === 'ALL' || item.status === statusFilter)
        && (!search || item.studentName?.toLocaleLowerCase('vi').includes(search))));
      if (nextIndex < 0) {
        navigate(returnPath, { state: returnState, replace: true });
      } else {
        navigate(`/submissions/${encodeURIComponent(nextIds[nextIndex])}?from=review`, {
          state: { ...returnState, nextReviewIds: nextIds.slice(nextIndex + 1) },
          replace: true,
        });
      }
    } catch {
      setNextError(true);
    } finally {
      setFindingNext(false);
    }
  };

  const refreshGradeCounts = () => {
    if (sub?.batchId) {
      void queryClient.invalidateQueries({ queryKey: ['reviewQueue', sub.batchId] });
      void queryClient.invalidateQueries({ queryKey: ['batch', sub.batchId] });
    }
    void queryClient.invalidateQueries({ queryKey: ['teacher-batches'] });
    void queryClient.invalidateQueries({ queryKey: ['teacher-dashboard'] });
  };

  const reloadPermissions = () => {
    setImageReadiness(null);
    queryClient.removeQueries({ queryKey: ['submissionImage', id] });
    return queryClient.resetQueries({ queryKey: ['submission', id], exact: true });
  };

  const decisionMutation = useMutation({
    mutationFn: (decision: GradeDecision) => decision.kind === 'approve'
      ? AppTeacherService.approveSubmission(id!)
      : AppTeacherService.overrideSubmission(id!, decision.score, decision.reason, decision.imageLegible),
    networkMode: 'always',
    retry: false,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['submission', id] });
      refreshGradeCounts();
    },
    onError: (error) => {
      const response = isAxiosError<{ error?: { code?: string } }>(error) ? error.response : undefined;
      const status = response?.status;
      if (!status || status >= 500 || status === 408 || status === 409 || response?.data?.error?.code === 'INVALID_STATE') {
        setNeedsOutcomeCheck(true);
      } else if (status === 401 || status === 403 || status === 404) {
        void reloadPermissions().finally(() => {
          writeInFlight.current = false;
        });
      } else {
        writeInFlight.current = false;
        setActionError('Chưa lưu được điểm. Hãy kiểm tra thông tin và thử lại.');
      }
    },
  });

  const retryProcessing = useMutation({
    mutationFn: () => AppTeacherService.retrySubmissionProcessing(id!),
    networkMode: 'always',
    retry: false,
    onSuccess: async () => {
      refreshGradeCounts();
      await refetch();
    },
    onError: async (error) => {
      const status = isAxiosError(error) ? error.response?.status : undefined;
      if (status === 401 || status === 403 || status === 404) {
        await reloadPermissions();
      } else if (!status || status >= 500 || status === 408 || status === 409) {
        setNeedsRetryCheck(true);
      } else {
        setActionError('Chưa gửi được yêu cầu xử lý lại. Hãy thử lại.');
      }
    },
    onSettled: () => { writeInFlight.current = false; },
  });

  const checkProcessing = async () => {
    if ((await refetch()).isSuccess) {
      setNeedsRetryCheck(false);
      refreshGradeCounts();
    }
  };

  const isFinalized = sub?.status === 'TEACHER_APPROVED' || sub?.status === 'TEACHER_OVERRIDDEN';
  const shouldFocusNotice = decisionMutation.isSuccess || needsOutcomeCheck || (decisionMutation.isError && isFinalized);
  useEffect(() => {
    if (shouldFocusNotice) decisionNoticeRef.current?.focus();
  }, [shouldFocusNotice, isFinalized, isError]);

  const checkSavedDecision = async () => {
    const result = await refetch({ cancelRefetch: false });
    if (!result.isSuccess) return;
    setNeedsOutcomeCheck(false);
    if (result.data?.status === 'TEACHER_APPROVED' || result.data?.status === 'TEACHER_OVERRIDDEN') {
      refreshGradeCounts();
    } else {
      writeInFlight.current = false;
    }
  };

  const nextAction = nextIds.length > 0 && <>
    <Button onClick={() => void openNextReview()} disabled={findingNext}>
      {findingNext ? 'Đang tìm bài tiếp theo…' : 'Duyệt bài tiếp theo'}
    </Button>
    {nextError && <Typography>Chưa tải được hàng đợi. Hãy thử lại hoặc quay lại hàng đợi duyệt.</Typography>}
  </>;
  const decisionNotice = isFinalized && !isError ? (
    <Alert ref={decisionNoticeRef} tabIndex={-1} severity="success" role="status" sx={{ mb: 3 }}>
      <Typography variant="h6">
        {typeof sub?.teacherScore === 'number'
          ? `Điểm chính thức ${sub.teacherScore} / ${sub.maxScore ?? 10}`
          : 'Đã chốt điểm'}
      </Typography>
      {sub?.teacherReason && <Typography sx={{ overflowWrap: 'anywhere' }}>{sub.teacherReason}</Typography>}
      {nextAction}
    </Alert>
  ) : decisionMutation.isSuccess ? (
    <Alert ref={decisionNoticeRef} tabIndex={-1} severity="success" role="status" sx={{ mb: 3 }}>
      Đã lưu quyết định chấm điểm.
      {nextAction}
    </Alert>
  ) : needsOutcomeCheck ? (
    <Alert ref={decisionNoticeRef} tabIndex={-1} severity="warning" sx={{ mb: 3 }}>
      <Typography>Chưa xác nhận được kết quả lưu điểm.</Typography>
      <Typography variant="body2">Kiểm tra kết quả trước khi gửi lại.</Typography>
      <Button disabled={isRefreshing} onClick={() => void checkSavedDecision()}>Kiểm tra kết quả lưu</Button>
    </Alert>
  ) : null;

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
        {decisionNotice}
        <Typography color="error" variant="h6" component="h1" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải chi tiết bài làm.
        </Typography>
        {!needsOutcomeCheck && <Button disabled={isRefreshing} onClick={() => void (needsRetryCheck ? checkProcessing() : refetch())}>
          Thử tải lại chi tiết
        </Button>}
        <Button variant="outlined" component={Link} to={returnPath} state={returnState}>
          {fromReview && sub?.batchId ? 'Quay lại hàng đợi duyệt' : 'Quay lại danh sách đợt chấm'}
        </Button>
      </Box>
    );
  }

  const suggestedScore = sub.suggestedScore;
  const maxScore = sub.maxScore ?? 10;
  const evidenceItems: EvidenceItem[] = sub.evidence?.items ?? (sub.evidence?.rule ? [{ description: sub.evidence.rule }] : []);
  const allowsProposal = sub.status === 'PROPOSED_GRADE' || sub.status === 'REVIEW_REQUIRED' || sub.status === 'FEEDBACK_READY';
  const canApprove = allowsProposal && suggestedScore !== undefined;
  const canAdjust = allowsProposal || sub.status === 'NEEDS_CONFIRMATION';
  const isManualGrade = !canApprove;
  const score = Number(editScore);
  const validScore = editScore.trim() !== '' && Number.isInteger(score) && score >= 0 && score <= maxScore;
  const isPending = decisionMutation.isPending;
  const actionsDisabled = isPending || isRefreshing || retryProcessing.isPending || needsRetryCheck;
  const canSaveOverride = canAdjust && validScore && !!editReason.trim() && (!isManualGrade || isImageLegible);

  const saveDecision = (decision: GradeDecision) => {
    if (!id || !imageStatus.ready || writeInFlight.current || actionsDisabled || needsOutcomeCheck || decisionMutation.isSuccess) return;
    if (decision.kind === 'approve' ? !canApprove : !canSaveOverride) return;
    writeInFlight.current = true;
    setActionError(null);
    decisionMutation.mutate(decision);
  };

  return (
    <Box>
      {/* Top Header & Breadcrumb */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Button
            variant="text"
            startIcon={<ArrowBack />}
            component={Link}
            to={returnPath}
            state={returnState}
            sx={{ mb: 1, px: 0 }}
          >
            {fromReview ? 'Quay lại hàng đợi duyệt' : 'Quay lại đợt chấm'}
          </Button>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.5 }}>
            <Typography variant="h5" component="h1" sx={{ fontWeight: 800 }}>
              Thẩm định bài làm: {sub.studentName || 'Học sinh'}
            </Typography>
            {(isFinalized || !decisionMutation.isSuccess) && <StatusChip status={sub.status} />}
          </Box>
          <Typography variant="body2" color="text.secondary">
            AI đưa ra đánh giá tham vấn. Giáo viên là người có thẩm quyền quyết định điểm số chính thức.
          </Typography>
        </Box>
      </Box>

      {decisionNotice}

      {!isFinalized && !decisionMutation.isSuccess && !needsOutcomeCheck && (needsRetryCheck ? (
        <Alert severity="warning" sx={{ mb: 3 }} action={<Button disabled={isRefreshing} onClick={() => void checkProcessing()}>
          Kiểm tra lại
        </Button>}>
          Chưa xác nhận được yêu cầu xử lý lại. Hãy kiểm tra trạng thái trước khi gửi lại.
        </Alert>
      ) : sub.canRetryProcessing && (
        <Alert severity="warning" sx={{ mb: 3 }} action={<Button disabled={actionsDisabled} onClick={() => {
          if (!id || actionsDisabled || writeInFlight.current) return;
          writeInFlight.current = true;
          setActionError(null);
          retryProcessing.mutate();
        }}>{retryProcessing.isPending ? 'Đang gửi…' : 'Thử xử lý lại'}</Button>}>
          Dịch vụ chấm bài gặp lỗi. Có thể thử xử lý lại trên ảnh đã gửi.
        </Alert>
      ))}

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
              bgcolor: '#211844',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 2.5,
              overflow: 'hidden',
              position: 'relative',
              minHeight: { xs: 240, md: 520 },
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
              <SubmissionImage
                key={imageVersion}
                id={id!}
                version={imageVersion}
                mockUrl={sub.imageUrl}
                studentName={sub.studentName}
                onStatusChange={handleImageStatus}
              />
            </Box>

            {/* Evidence Overlay / Position Indicator */}
            {!sub.evidence?.items?.length && sub.evidence?.position && (
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
                <Typography variant="caption" sx={{ color: '#E9E2F2', fontWeight: 600 }}>
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
            <Card variant="outlined" sx={{ borderRadius: 2.5, borderColor: '#E2E8F0', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <SmartToy sx={{ color: '#2563EB', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#1E40AF', letterSpacing: '0.04em' }}>
                    GHI NHẬN TỪ HỆ THỐNG AI
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  {evidenceItems.length > 0 && <Grid size={{ xs: 12, sm: 6 }}>
                    <Box sx={{ p: 1.75, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Bằng chứng cần xem xét
                      </Typography>
                      <Box component="ul" sx={{ my: 0.5, pl: 2.25, display: 'grid', gap: 1 }}>
                        {evidenceItems.map((item, index) => <li key={index}>
                          {item.description && <Typography variant="body2" sx={{ fontWeight: 700 }}>{item.description}</Typography>}
                          {item.placeValue && <Typography variant="body2">{item.placeValue}</Typography>}
                          {item.observedText && <Typography variant="body2">Ký tự nhận diện {item.observedText}</Typography>}
                        </li>)}
                      </Box>
                    </Box>
                  </Grid>}

                  <Grid size={{ xs: 12, sm: evidenceItems.length > 0 ? 6 : 12 }}>
                    <Box sx={{ p: 1.75, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Thuật toán đối soát
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          mt: 0.5,
                          fontWeight: 700,
                          color: sub.decision === 'VALID' ? '#15803D' : sub.decision === 'INVALID' ? '#B91C1C' : '#475569',
                        }}
                      >
                        {sub.decision === 'VALID' ? 'Hợp lệ theo quy tắc'
                          : sub.decision === 'INVALID' ? 'Phát hiện lỗi tính cần xem lại' : 'Chưa đủ dữ liệu để kết luận'}
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
                      ĐỀ XUẤT TỪ AI (CHƯA CHÍNH THỨC)
                    </Typography>
                  </Box>
                  <Chip
                    label={isFinalized ? 'Điểm tham khảo' : 'Chưa chốt điểm'}
                    size="small"
                    sx={{ bgcolor: '#FEF3C7', color: '#B45309', fontWeight: 600, fontSize: '0.75rem' }}
                  />
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, my: 1 }}>
                  <Typography variant="h3" sx={{ fontWeight: 800, color: '#2563EB' }}>
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

            {/* Card 3: Teacher Authority & Final Decision */}
            {!isFinalized && !decisionMutation.isSuccess && !needsOutcomeCheck && <Card
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

                {sub.status === 'NEEDS_RETAKE' && !sub.canRetryProcessing ? (
                  <SubmissionRetake key={imageVersion} id={id!} refresh={async () => {
                    refreshGradeCounts();
                    return (await refetch()).isSuccess;
                  }} />
                ) : sub.status === 'PROCESSING' ? (
                  <Alert severity="info" role="status">Đang xử lý ảnh bài làm.</Alert>
                ) : !canAdjust ? (
                  <Alert severity="info">Chưa thể chốt điểm cho bài làm ở trạng thái này.</Alert>
                ) : !imageStatus.ready ? (
                  <Box>
                    <Alert severity="warning" sx={{ mb: 2, borderRadius: 2 }} role="status">
                      Chưa thể duyệt hoặc điều chỉnh điểm: {imageStatus.reason || 'Ảnh bài làm chưa được tải hoặc giải mã thành công.'}
                    </Alert>
                    <Typography variant="body2" color="text.secondary">
                      Giáo viên cần nhìn rõ bài làm thực tế của học sinh trước khi quyết định điểm số chính thức.
                    </Typography>
                  </Box>
                ) : !isEditing ? (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {isManualGrade
                        ? 'Nếu đọc rõ bài làm trong ảnh, giáo viên có thể chấm thủ công. Nếu ảnh chưa đủ rõ, hãy chụp lại và để bài ở trạng thái chờ xử lý.'
                        : 'Đối chiếu ảnh bài làm rồi duyệt hoặc điều chỉnh điểm đề xuất.'}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                      {canApprove && <Button
                        variant="contained"
                        size="large"
                        startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : <CheckCircle />}
                        onClick={() => saveDecision({ kind: 'approve' })}
                        disabled={actionsDisabled}
                        sx={{ flex: 2, py: 1.25, fontWeight: 700 }}
                      >
                        {isPending ? 'Đang lưu...' : `Duyệt điểm ${suggestedScore}`}
                      </Button>}
                      <Button
                        variant="outlined"
                        size="large"
                        startIcon={<Edit />}
                        onClick={() => {
                          setEditScore(canApprove ? String(suggestedScore) : '');
                          setEditReason('');
                          setIsImageLegible(false);
                          setActionError(null);
                          setIsEditing(true);
                        }}
                        disabled={actionsDisabled}
                        sx={{ flex: 1, py: 1.25, fontWeight: 700 }}
                      >
                        {isManualGrade ? 'Chấm thủ công' : 'Điều chỉnh'}
                      </Button>
                    </Box>
                  </Box>
                ) : (
                  <Box component="form" onSubmit={(event) => {
                    event.preventDefault();
                    saveDecision({
                      kind: 'override', score, reason: editReason.trim(),
                      imageLegible: sub.status === 'NEEDS_CONFIRMATION' && isImageLegible ? true : undefined,
                    });
                  }}>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid size={{ xs: 12, sm: 4 }}>
                        <TextField
                          fullWidth
                          label="Điểm chính thức"
                          type="number"
                          required
                          value={editScore}
                          onChange={(e) => setEditScore(e.target.value)}
                          error={editScore !== '' && !validScore}
                          helperText={`Nhập điểm nguyên từ 0 đến ${maxScore}.`}
                          slotProps={{ htmlInput: { min: 0, max: maxScore, step: 1 } }}
                          disabled={isPending}
                          autoFocus
                        />
                      </Grid>
                      <Grid size={{ xs: 12, sm: 8 }}>
                        <TextField
                          fullWidth
                          label="Lý do điều chỉnh"
                          required
                          value={editReason}
                          onChange={(e) => setEditReason(e.target.value)}
                          placeholder="VD: Học sinh cộng nhầm hàng chục nhưng đặt tính đúng"
                          disabled={isPending}
                        />
                      </Grid>
                    </Grid>

                    {isManualGrade && <FormControlLabel
                      sx={{ mb: 2 }}
                      label="Tôi đã xem ảnh và đọc rõ bài làm."
                      control={<Checkbox checked={isImageLegible} disabled={isPending} onChange={(event) => setIsImageLegible(event.target.checked)} />}
                    />}

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
                        {isManualGrade
                          ? 'Điểm và lý do chấm thủ công sẽ được lưu làm quyết định chính thức của giáo viên.'
                          : 'Điểm đã điều chỉnh và lý do sẽ được lưu làm quyết định chính thức của giáo viên.'}
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1.5 }}>
                      <Button
                        variant="contained"
                        type="submit"
                        disabled={!canSaveOverride || actionsDisabled}
                        startIcon={isPending ? <CircularProgress size={18} color="inherit" /> : null}
                        sx={{ flex: 1, py: 1, fontWeight: 700 }}
                      >
                        {isPending ? 'Đang lưu...' : isManualGrade ? 'Lưu điểm thủ công' : 'Xác nhận ghi đè điểm'}
                      </Button>
                      <Button
                        variant="outlined"
                        type="button"
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
            </Card>}
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
