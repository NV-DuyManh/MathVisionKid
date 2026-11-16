import { useRef, useState } from 'react';
import { Alert, Box, Button, Card, MenuItem, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import apiClient from '../services/api/apiClient';
import AssignedReviewDialog from './AssignedReviewDialog';

const labels = {
  AWAITING_IMAGE: 'Chưa nộp',
  UPLOADING: 'Đang gửi',
  AWAITING_REVIEW: 'Chờ chấm',
  RETAKE_REQUESTED: 'Cần chụp lại',
  GRADE_RELEASED: 'Đã trả',
};
type Status = keyof typeof labels;
type Recipient = {
  studentId: string; studentName: string; member: boolean; activeMember: boolean; status: Status;
  submissionId: string | null; score: number | null;
};
type Publication = {
  assignmentId: string; classId: string; className: string; teacherName: string; title: string;
  publishedAt: string; maxScore: number; recipientCount: number;
  counts: Record<Status, number>; recipients: Recipient[];
};

export default function AssignmentResultsPage() {
  const { id = '' } = useParams();
  return <AssignmentResults key={id} id={id} />;
}

function AssignmentResults({ id }: { id: string }) {
  const client = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [reviewId, setReviewId] = useState<string>();
  const [nextBusy, setNextBusy] = useState(false);
  const [nextNotice, setNextNotice] = useState('');
  const [search, setSearch] = useState('');
  const resultsStatus = useRef<HTMLParagraphElement>(null);
  const reviewTrigger = useRef<HTMLButtonElement | null>(null);
  const query = useQuery({
    queryKey: ['assignment-results', id],
    queryFn: async ({ signal }) => (await apiClient.get<Publication>(
      `/teacher/assignments/${encodeURIComponent(id)}/results`, { signal },
    )).data,
    gcTime: 0,
    refetchOnWindowFocus: 'always',
  });
  const errorStatus = isAxiosError(query.error) ? query.error.response?.status : undefined;
  const accessLost = errorStatus === 401 || errorStatus === 403 || errorStatus === 404;
  if (accessLost && reviewId) setReviewId(undefined);
  const publication = query.isError ? undefined : query.data;
  const requestedStatus = params.get('status') ?? '';
  const status = Object.hasOwn(labels, requestedStatus) ? requestedStatus as Status : '';
  const activeOnly = params.get('member') === 'active';
  const fromActions = params.get('from') === 'action-center';
  const actionsParams = new URLSearchParams({ filter: params.get('work') ?? 'ALL', page: params.get('page') ?? '0' });
  const matchesSearch = (row: Recipient) => row.studentName.toLocaleLowerCase('vi')
    .includes(search.trim().toLocaleLowerCase('vi'));
  const rows = publication?.recipients.filter(row =>
    (!status || row.status === status) && (!activeOnly || row.activeMember) && matchesSearch(row)) ?? [];
  const setStatus = (value: string) => setParams(previous => {
    const next = new URLSearchParams(previous);
    if (value) next.set('status', value);
    else next.delete('status');
    next.delete('member');
    return next;
  }, { replace: true });
  const refresh = () => {
    void client.invalidateQueries({ queryKey: ['teacher-action-center'] });
    return query.refetch();
  };
  const nextReview = async () => {
    if (nextBusy) return;
    const previousId = reviewId;
    setNextBusy(true);
    setNextNotice('');
    try {
      const fresh = await query.refetch();
      if (fresh.isError) return;
      const candidate = fresh.data?.recipients.find(row =>
        row.status === 'AWAITING_REVIEW' && row.submissionId !== previousId && matchesSearch(row));
      if (!candidate?.submissionId) setNextNotice('Không còn bài chờ chấm phù hợp.');
      setReviewId(current => current === previousId ? candidate?.submissionId ?? undefined : current);
    } finally { setNextBusy(false); }
  };

  return <Box sx={{ display: 'grid', gap: 2, minWidth: 0 }}>
    <PageHeader focusOnMount title={publication?.title ?? 'Kết quả bài tập'}
      subtitle={publication && `${publication.className} · Giáo viên phụ trách: ${publication.teacherName}`}
      back={<Button component={Link} to={fromActions ? `/action-center?${actionsParams}` :
        publication ? `/classes/${publication.classId}?tab=assignments` : '/classes'}>
        {fromActions ? 'Quay lại việc cần xử lý' : 'Quay lại lớp học'}
      </Button>}
      actions={<Button disabled={query.isFetching} onClick={() => void refresh()}>Cập nhật kết quả</Button>} />
    {query.isPending && <Typography role="status">Đang tải kết quả…</Typography>}
    {query.isError && <Alert severity="error" action={<Button onClick={() => void refresh()}>Thử lại</Button>}>
      Chưa mở được kết quả bài tập. Hãy kiểm tra quyền phụ trách lớp hoặc thử lại.
    </Alert>}
    {publication && <>
      <Typography component="h2" variant="h6">{publication.recipientCount} học sinh được giao bài</Typography>
      <Box component="ul" sx={{ display: 'flex', flexWrap: 'wrap', listStyle: 'none', p: 0, m: 0, gap: 1 }}>
        {Object.entries(labels).map(([key, label]) => <Box component="li" key={key}>
          <Button aria-pressed={status === key} variant={status === key ? 'contained' : 'outlined'}
            sx={{ minHeight: 44 }} onClick={() => setStatus(status === key ? '' : key)}>
            {label}: {publication.counts[key as Status]}
          </Button>
        </Box>)}
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'minmax(160px, 1fr) 2fr' }, gap: 1.5 }}>
        <TextField select label="Trạng thái" value={status} onChange={event => setStatus(event.target.value)}
          slotProps={{ inputLabel: { shrink: true }, select: { displayEmpty: true } }}>
          <MenuItem value="">Tất cả</MenuItem>
          {Object.entries(labels).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}
        </TextField>
        <TextField label="Tìm theo tên học sinh" value={search} onChange={event => setSearch(event.target.value)} />
      </Box>
      <Typography component="p" ref={resultsStatus} role="status" tabIndex={-1} color="text.secondary">
        {nextNotice || `Hiển thị ${rows.length} / ${publication.recipientCount} học sinh${activeOnly ? ' · Chỉ học sinh còn hoạt động trong lớp' : ''}`}
      </Typography>
      {rows.length === 0 ? <Alert severity="info">
        {publication.recipientCount === 0 ? 'Bài tập này chưa được giao cho học sinh nào.' : 'Không có học sinh phù hợp với bộ lọc.'}
      </Alert> : <Card variant="outlined" sx={{ minWidth: 0 }}>
        <TableContainer role="region" aria-label="Bảng kết quả học sinh" tabIndex={0} sx={{ maxHeight: '65vh' }}>
          <Table stickyHeader size="small" aria-label="Kết quả học sinh" sx={{ minWidth: 430 }}>
            <TableHead><TableRow>
              <TableCell scope="col">Học sinh</TableCell><TableCell scope="col">Trạng thái</TableCell>
              <TableCell scope="col">Điểm</TableCell><TableCell scope="col">Tác vụ</TableCell>
            </TableRow></TableHead>
            <TableBody>{rows.map(row => <TableRow key={row.studentId}>
              <TableCell component="th" scope="row" sx={{ overflowWrap: 'anywhere' }}>
                {row.studentName}{!row.member && <Typography variant="caption" sx={{ display: 'block' }}>Đã rời lớp</Typography>}
              </TableCell>
              <TableCell>{labels[row.status]}</TableCell>
              <TableCell>{row.score == null ? '—' : `${row.score}/${publication.maxScore}`}</TableCell>
              <TableCell>{row.submissionId && row.status !== 'UPLOADING' && row.status !== 'AWAITING_IMAGE' &&
                <Button sx={{ minHeight: 44 }} aria-label={`Mở bài của ${row.studentName}`} onClick={event => {
                  reviewTrigger.current = event.currentTarget;
                  setNextNotice(''); setReviewId(row.submissionId ?? undefined);
                }}>{row.status === 'AWAITING_REVIEW' ? 'Chấm bài' : 'Xem bài'}</Button>}
              </TableCell>
            </TableRow>)}</TableBody>
          </Table>
        </TableContainer>
      </Card>}
    </>}
    {!accessLost && reviewId && <AssignedReviewDialog id={reviewId} onClose={() => {
      setReviewId(undefined);
      requestAnimationFrame(() => {
        if (reviewTrigger.current?.isConnected) reviewTrigger.current.focus();
        else resultsStatus.current?.focus();
      });
    }}
      onSaved={() => void refresh()} onNext={() => void nextReview()} nextBusy={nextBusy} />}
  </Box>;
}
