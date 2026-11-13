import { useEffect, useMemo, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Paper,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
} from '@mui/material';
import { Link, useLocation, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AuthTokenStore } from '../services/api/AuthTokenStore';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { ArrowBack, ArrowForward, AutoAwesome, Search } from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';

const processingStatuses = ['UPLOADING', 'QUEUED', 'PROCESSING'];
const defaultFilters = { statusFilter: 'ALL', searchQuery: '', sortBy: 'DEFAULT' };

export default function ReviewQueuePage() {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = AuthTokenStore.getSessionId();
  const saved = location.state?.reviewQueue;
  const filters: typeof defaultFilters = sessionId && saved?.sessionId === sessionId && saved?.batchId === id
    ? saved.filters : defaultFilters;
  const { statusFilter, searchQuery, sortBy } = filters;
  const batchListFilter = location.state?.batchListFilter;

  const reviewState = (nextFilters: typeof defaultFilters) => ({
    batchListFilter,
    reviewQueue: { sessionId, batchId: id, filters: nextFilters },
  });
  const updateFilters = (nextFilters: typeof defaultFilters) => {
    navigate({ pathname: location.pathname, search: location.search, hash: location.hash }, {
      replace: true,
      state: reviewState(nextFilters),
    });
  };

  const queueQuery = useQuery({
    queryKey: ['reviewQueue', id],
    queryFn: () => AppTeacherService.getReviewQueue(id),
    enabled: !!id,
  });
  const batchQuery = useQuery({
    queryKey: ['batch', id],
    queryFn: () => AppTeacherService.getBatchStatus(id),
    enabled: !!id,
    refetchInterval: ({ state }) => state.status === 'success'
      && processingStatuses.includes(state.data?.status ?? '') ? 3000 : false,
  });
  const { data: queue, refetch: reloadQueue } = queueQuery;
  const batch = batchQuery.data;
  const observedBatch = useRef<typeof batch>(undefined);
  const pending = batch?.pendingReviewCount ?? batch?.reviewRequiredCount;
  const queueLength = queue?.length;

  useEffect(() => {
    if (!batch || queueQuery.fetchStatus !== 'idle' || observedBatch.current === batch) return;
    // Let any older in-flight queue read finish before reconciling it with newer progress.
    const hasPreviousBatch = !!observedBatch.current;
    observedBatch.current = batch;
    if (hasPreviousBatch || (queueLength !== undefined && queueLength !== pending)) {
      void reloadQueue();
    }
  }, [batch, pending, queueLength, queueQuery.fetchStatus, reloadQueue]);

  const filteredQueue = useMemo(() => {
    if (!queue) return [];
    const query = searchQuery.trim().toLocaleLowerCase('vi');
    const list = queue.filter((sub) =>
      (statusFilter === 'ALL' || sub.status === statusFilter)
      && (!query || sub.studentName?.toLocaleLowerCase('vi').includes(query)),
    );

    if (sortBy === 'CONFIDENCE_ASC') {
      list.sort((a, b) => (a.recognitionConfidence ?? 101) - (b.recognitionConfidence ?? 101));
    } else if (sortBy === 'SCORE_ASC') {
      list.sort((a, b) => (a.suggestedScore ?? Number.MAX_SAFE_INTEGER) - (b.suggestedScore ?? Number.MAX_SAFE_INTEGER));
    } else if (sortBy === 'SCORE_DESC') {
      list.sort((a, b) => (b.suggestedScore ?? -1) - (a.suggestedScore ?? -1));
    }
    return list;
  }, [queue, statusFilter, searchQuery, sortBy]);

  const batchPath = `/batches/${encodeURIComponent(id)}`;
  const isFetching = queueQuery.isFetching || batchQuery.isFetching;
  const isPaused = queueQuery.isPaused || batchQuery.isPaused;
  const isChecking = isFetching || isPaused;
  const heading = <PageHeader
      back={<Button component={Link} to={batchPath} state={{ batchListFilter }} startIcon={<ArrowBack />} sx={{ px: 0 }}>
        Quay lại chi tiết đợt chấm
      </Button>}
      title="Hàng đợi duyệt bài"
      subtitle={queue?.length && !queueQuery.isError && !batchQuery.isError
        ? `Có ${queue.length} bài làm cần giáo viên thẩm định và quyết định điểm số chính thức.`
        : undefined}
      actions={<Button variant="outlined" disabled={isFetching} onClick={() => {
        void batchQuery.refetch();
        void reloadQueue();
      }}>Làm mới</Button>}
    />;

  if (queueQuery.isLoading || batchQuery.isLoading) {
    return (
      <Box>
        {heading}
        <Box role="status" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
          <CircularProgress size={40} />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Đang tải tiến độ và hàng đợi duyệt…
          </Typography>
        </Box>
      </Box>
    );
  }

  if (batchQuery.isError || !batch || queueQuery.isError || !queue) {
    return (
      <Box>
        {heading}
        <Alert severity="error">
          {batchQuery.isError || !batch ? 'Chưa tải được tiến độ đợt chấm.' : 'Chưa tải được hàng đợi duyệt.'}
          {' '}Chọn Làm mới để thử lại.
        </Alert>
      </Box>
    );
  }

  const total = batch.totalCount ?? batch.totalImages ?? 0;
  const failed = batch.failedCount ?? 0;
  const isProcessing = processingStatuses.includes(batch.status);
  const isWaitingForUpload = batch.status === 'CREATED' && total === 0;
  const hasFailures = failed > 0 || batch.status === 'FAILED' || batch.status === 'PARTIAL';
  const queueDisagrees = pending !== queue.length;
  const allFinalized = batch.status === 'COMPLETED' && total > 0 && batch.processedCount === total
    && batch.finalizedCount === total && batch.failedCount === 0 && pending === 0;
  const notices = <>
    {isProcessing && <Alert severity="info" role="status" sx={{ mb: 2 }}>
      {total > 0 ? `Đã xử lý ${batch.processedCount} / ${total} ảnh.` : 'Đợt chấm đang nhận ảnh.'}
    </Alert>}
    {hasFailures && <Alert severity="warning" sx={{ mb: 2 }}>
      {failed > 0 ? `${failed} bài chưa xử lý được.` : 'Đợt chấm có bài chưa xử lý được.'}
      <Button component={Link} to={batchPath + '?status=failed'} state={{ batchListFilter }}
        size="small" sx={{ display: 'flex', width: 'fit-content' }}>
        Xem bài xử lý thất bại
      </Button>
    </Alert>}
    {queueDisagrees && !isChecking && <Alert severity="warning" sx={{ mb: 2 }}>
      Dữ liệu hàng đợi và tiến độ đợt chấm chưa khớp. Chọn Làm mới để kiểm tra lại.
    </Alert>}
  </>;

  if (!queue.length) {
    return <Box>
      {heading}
      {notices}
      {isWaitingForUpload && <Alert severity="info" role="status">
        Đợt chấm đang chờ tải ảnh.
        {batch.assignmentId && <Button component={Link} to={`/batches/create?${new URLSearchParams({ batchId: id })}`}
          size="small" sx={{ display: 'flex', width: 'fit-content' }}>
          Tiếp tục tải ảnh
        </Button>}
      </Alert>}
      {!isProcessing && !isWaitingForUpload && !hasFailures && (isChecking
        ? <Alert severity="info" role="status">
          {isPaused ? 'Đang chờ kết nối để kiểm tra tiến độ đợt chấm…' : 'Đang kiểm tra tiến độ đợt chấm…'}
        </Alert>
        : allFinalized
          ? <Alert severity="success" role="status">Đã chốt điểm cho toàn bộ bài làm.</Alert>
          : !queueDisagrees && <Alert severity="warning">
            Chưa xác nhận được tất cả bài làm đã chốt điểm. Xem chi tiết đợt chấm hoặc chọn Làm mới.
          </Alert>)}
    </Box>;
  }

  return (
    <Box>
      {heading}
      {notices}

      <Box component="section" aria-label="Lọc hàng đợi" className="teacher-review-queue">
      <Paper
        variant="outlined"
        sx={{
          p: { xs: 1.5, sm: 2 },
          mb: 3,
          borderRadius: 2.5,
          bgcolor: '#FFFFFF',
          borderColor: '#E2E8F0',
        }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            label="Tên học sinh"
            placeholder="Tìm theo tên học sinh..."
            value={searchQuery}
            onChange={(e) => updateFilters({ ...filters, searchQuery: e.target.value })}
            slotProps={{
              input: {
                startAdornment: <Search sx={{ fontSize: 18, color: '#94A3B8', mr: 1 }} />,
              },
            }}
            sx={{ minWidth: 0, flex: '1 1 220px' }}
          />

          <FormControl size="small" sx={{ minWidth: 0, flex: { xs: '1 1 100%', sm: '1 1 160px' } }}>
            <InputLabel id="filter-status-label">Trạng thái</InputLabel>
            <Select
              labelId="filter-status-label"
              value={statusFilter}
              label="Trạng thái"
              onChange={(e) => updateFilters({ ...filters, statusFilter: e.target.value })}
            >
              <MenuItem value="ALL">Tất cả trạng thái</MenuItem>
              <MenuItem value="REVIEW_REQUIRED">Cần giáo viên duyệt</MenuItem>
              <MenuItem value="PROPOSED_GRADE">Có điểm đề xuất</MenuItem>
              <MenuItem value="FEEDBACK_READY">Có phản hồi</MenuItem>
              <MenuItem value="NEEDS_CONFIRMATION">Cần xác nhận nét chữ</MenuItem>
              <MenuItem value="NEEDS_RETAKE">Cần chụp lại</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 0, flex: { xs: '1 1 100%', sm: '1 1 190px' } }}>
            <InputLabel id="sort-by-label">Sắp xếp theo</InputLabel>
            <Select
              labelId="sort-by-label"
              value={sortBy}
              label="Sắp xếp theo"
              onChange={(e) => updateFilters({ ...filters, sortBy: e.target.value })}
            >
              <MenuItem value="DEFAULT">Thứ tự mặc định</MenuItem>
              <MenuItem value="CONFIDENCE_ASC">Độ tin cậy: Thấp → Cao</MenuItem>
              <MenuItem value="SCORE_ASC">Điểm đề xuất: Thấp → Cao</MenuItem>
              <MenuItem value="SCORE_DESC">Điểm đề xuất: Cao → Thấp</MenuItem>
            </Select>
          </FormControl>

          {(statusFilter !== 'ALL' || searchQuery.trim() !== '' || sortBy !== 'DEFAULT') && (
            <Button
              variant="text"
              size="small"
              onClick={() => updateFilters(defaultFilters)}
              sx={{ textTransform: 'none', color: '#64748B' }}
            >
              Đặt lại bộ lọc
            </Button>
          )}

        </Box>
        <Typography variant="body2" component="p" role="status" sx={{ mt: 1.25, color: 'text.secondary' }}>
          Hiển thị {filteredQueue.length} / {queue.length} bài
        </Typography>
      </Paper>
      </Box>

      {filteredQueue.length === 0 ? (
        <Alert severity="info" sx={{ borderRadius: 2, my: 4 }}>
          Không tìm thấy bài làm nào phù hợp với bộ lọc hiện tại. Vui lòng thử đổi từ khóa tìm kiếm hoặc trạng thái.
        </Alert>
      ) : (
        <Paper component="ol" aria-label="Bài làm cần duyệt" variant="outlined" className="teacher-queue-register">
          {filteredQueue.map((sub, idx) => {
            const subId = sub.id || sub.submissionId || '';
            const recConf = sub.recognitionConfidence !== undefined ? `${Math.round(sub.recognitionConfidence)}%` : 'Chưa có';
            const diagConf = sub.diagnosisConfidence !== undefined ? `${Math.round(sub.diagnosisConfidence)}%` : 'Chưa có';
            const suggested = sub.suggestedScore;
            const scale = (typeof sub.maxScore === 'number' && Number.isFinite(sub.maxScore) && sub.maxScore > 0)
              ? sub.maxScore
              : 10;

            return (
              <Box component="li" className="teacher-queue-row" key={subId}>
                <Box sx={{ minWidth: 0 }}>
                  <Typography component="h2" variant="subtitle1" id={`review-student-${idx}`} sx={{ overflowWrap: 'anywhere' }}>
                    {sub.studentName || `Học sinh #${idx + 1}`}
                  </Typography>
                  <Typography variant="caption" component="p" sx={{ mb: 0.75 }}>
                    Bài {idx + 1} / {filteredQueue.length}
                  </Typography>
                  <StatusChip status={sub.status} />
                </Box>

                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="caption" component="p">Lý do cần xem lại</Typography>
                  <Typography variant="body2" sx={{ overflowWrap: 'anywhere', mt: 0.25 }}>
                    {sub.evidence?.rule || 'Cần xác nhận nét chữ hoặc bước đặt tính'}
                  </Typography>
                </Box>

                <Box className="teacher-queue-score">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <AutoAwesome fontSize="inherit" color="info" />
                    <Typography variant="caption">AI đề xuất · Chưa chính thức</Typography>
                  </Box>
                  <Typography variant="subtitle1" color="info.dark">
                    {suggested !== undefined ? `${suggested} / ${scale} điểm` : 'Chưa chấm'}
                  </Typography>
                  <Typography variant="caption" component="p">Độ tin cậy nhận diện {recConf}</Typography>
                  <Typography variant="caption" component="p">Độ tin cậy chẩn đoán {diagConf}</Typography>
                </Box>

                <Button
                  variant="outlined"
                  endIcon={<ArrowForward />}
                  aria-describedby={`review-student-${idx}`}
                  onClick={() => navigate(`/submissions/${encodeURIComponent(subId)}?from=review`, {
                    state: {
                      ...reviewState(filters),
                      nextReviewIds: filteredQueue.slice(idx + 1).map(item => item.id || item.submissionId).filter(Boolean),
                    },
                  })}
                  sx={{ justifySelf: { xs: 'stretch', lg: 'end' }, whiteSpace: 'nowrap' }}
                >
                  Duyệt bài này
                </Button>
              </Box>
            );
          })}
        </Paper>
      )}
    </Box>
  );
}
