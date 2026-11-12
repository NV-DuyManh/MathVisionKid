import { Alert, Box, Button, Card, LinearProgress, List, ListItem, ListItemText, Skeleton, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import { StatusChip } from '../components/common/StatusChip';
import { AppTeacherService } from '../services/api/ServiceLocator';

export default function BatchDetailPage() {
  const { id = '' } = useParams();
  const { state } = useLocation();
  const [params] = useSearchParams();
  const failedOnly = params.get('status') === 'failed';
  const { data: batch, isPending, isError, isFetching, refetch } = useQuery({
    queryKey: ['batch', id],
    queryFn: () => AppTeacherService.getBatchStatus(id),
    refetchInterval: ({ state }) => state.status !== 'error'
      && ['UPLOADING', 'QUEUED', 'PROCESSING'].includes(state.data?.status ?? '') ? 3000 : false,
  });

  const total = batch?.totalCount ?? batch?.totalImages ?? 0;
  const processed = batch?.processedCount ?? 0;
  const pending = batch?.pendingReviewCount ?? batch?.reviewRequiredCount ?? 0;
  const failed = batch?.failedCount ?? 0;
  const finalized = batch?.finalizedCount ?? 0;
  const percent = total ? Math.min(100, Math.round(processed * 100 / total)) : 0;
  const batchPath = '/batches/' + encodeURIComponent(id);
  const submissions = batch?.submissions ?? [];
  const visibleSubmissions = failedOnly ? submissions.filter(submission => submission.status === 'FAILED') : submissions;
  const uploadPath = '/batches/create?' + new URLSearchParams({ batchId: id });
  const counts = [
    { label: 'Ảnh đã xử lý', value: processed + ' / ' + total },
    { label: 'Chờ giáo viên xem', value: pending },
    { label: 'Đã chốt điểm', value: finalized },
    { label: 'Xử lý thất bại', value: failed },
  ];

  return <Box>
    <Button component={Link} to={state?.batchListFilter === 'pending' || state?.batchListFilter === 'failed'
      ? '/batches?filter=' + state.batchListFilter : '/batches'} sx={{ mb: 2 }}>Quay lại danh sách đợt chấm</Button>
    <PageHeader title={batch?.assignmentTitle || 'Chi tiết đợt chấm'} subtitle={batch?.className}
      actions={<Button variant="outlined" disabled={isFetching} onClick={() => void refetch()}>Làm mới</Button>} />
    {isPending && <Skeleton variant="rounded" height={160} aria-label="Đang tải đợt chấm" />}
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>
      Chưa tải được đợt chấm. Vui lòng thử lại.
    </Alert>}
    {batch && <>
      <Stack spacing={2.5}>
        <Card variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ justifyContent: 'space-between', alignItems: { sm: 'center' } }}>
            <Box>
              <Typography component="h2" variant="h6">Tiến độ đợt chấm</Typography>
              <StatusChip status={batch.status} />
            </Box>
            {pending > 0 && <Button component={Link} to={batchPath + '/review'} state={state} variant="contained">
              Vào hàng đợi duyệt ({pending} bài)
            </Button>}
          </Stack>
          {batch.status === 'CREATED' && <Alert severity="info" sx={{ mt: 2 }}
            action={batch.assignmentId && <Button component={Link} to={uploadPath}>Tiếp tục tải ảnh</Button>}>
            Đợt chấm chưa nhận ảnh. Hãy chọn và che thông tin trên ảnh trước khi gửi.
          </Alert>}
          {batch.status !== 'CREATED' && <>
            <LinearProgress aria-label="Tỷ lệ ảnh đã xử lý" variant="determinate" value={percent} sx={{ my: 2 }} />
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, minmax(0, 1fr))', md: 'repeat(4, minmax(0, 1fr))' }, gap: 1 }}>
              {counts.map(({ label, value }) => <Box key={label} sx={{ p: 1.5, bgcolor: 'action.hover', borderRadius: 2 }}>
                <Typography variant="body2" color="text.secondary">{label}</Typography>
                <Typography variant="h6" sx={{ fontVariantNumeric: 'tabular-nums' }}>{value}</Typography>
              </Box>)}
            </Box>
          </>}
          {failed > 0 && <Alert severity="warning" sx={{ mt: 2 }}>
            {failed} bài chưa xử lý được. Mở bài lỗi để xem cách xử lý tiếp.
            {!failedOnly && <Button component={Link} to={batchPath + '?status=failed'} state={state} size="small"
              sx={{ display: 'flex', width: 'fit-content' }}>Xem bài xử lý thất bại</Button>}
          </Alert>}
        </Card>
        <Card variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
          <Typography component="h2" variant="h6">Bài làm trong đợt</Typography>
          {failedOnly && <Button component={Link} to={batchPath} state={state} size="small">Xem tất cả bài</Button>}
          {visibleSubmissions.length ? <List aria-label="Bài làm trong đợt">
            {visibleSubmissions.map(submission => <ListItem key={submission.submissionId} disableGutters divider
              sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
              <ListItemText primary={submission.studentName || 'Chưa có tên học sinh'} sx={{ flex: '1 1 160px', minWidth: 0, overflowWrap: 'anywhere' }} />
              <StatusChip status={submission.status} />
              <Button component={Link} state={state} to={'/submissions/' + encodeURIComponent(submission.submissionId)
                + (failedOnly ? '?from=failed' : '')}>Xem bài</Button>
            </ListItem>)}
          </List> : <Typography role="status" color="text.secondary" sx={{ mt: 1 }}>
            {failedOnly ? 'Không có bài ở trạng thái xử lý thất bại.' : 'Chưa có bài làm trong đợt này.'}
          </Typography>}
        </Card>
      </Stack>
    </>}
  </Box>;
}
