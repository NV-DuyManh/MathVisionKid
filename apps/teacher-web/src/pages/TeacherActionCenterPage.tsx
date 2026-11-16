import { Alert, Box, Button, Card, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { PageHeader } from '../components/common/PageHeader';
import apiClient from '../services/api/apiClient';

const filters = {
  PENDING: { label: 'Bài nộp chờ chấm', metric: 'pendingSubmissions', status: 'AWAITING_REVIEW' },
  RETAKE: { label: 'Lượt cần chụp lại', metric: 'retakeRecipients', status: 'RETAKE_REQUESTED' },
  MISSING: { label: 'Bài tập còn học sinh chưa nộp', metric: 'assignmentsWithMissingWork', status: 'AWAITING_IMAGE' },
  RELEASED: { label: 'Bài nộp đã trả kết quả', metric: 'releasedSubmissions', status: 'GRADE_RELEASED' },
} as const;
type WorkFilter = keyof typeof filters;
type Work = {
  assignmentId: string; classId: string; className: string; title: string; publishedAt: string;
  pendingSubmissions: number; retakeRecipients: number; missingRecipients: number; releasedSubmissions: number;
};
type Summary = {
  classCount: number; pendingSubmissions: number; retakeRecipients: number;
  assignmentsWithMissingWork: number; releasedSubmissions: number;
  matchingAssignments: number; page: number; pageSize: number; assignments: Work[];
};

function useTeacherWork(filter: WorkFilter | 'ALL', page: number) {
  return useQuery({
    queryKey: ['teacher-action-center', filter, page],
    queryFn: async ({ signal }) => (await apiClient.get<Summary>('/teacher/assignments/action-center', {
      params: { filter, page }, signal,
    })).data,
    gcTime: 0,
    refetchOnWindowFocus: 'always',
  });
}

export function TeacherWorkOverview() {
  const query = useTeacherWork('ALL', 0);
  return <Card component="section" aria-labelledby="teacher-work-overview" variant="outlined" sx={{ p: 2, mb: 3 }}>
    <Typography component="h2" variant="h6" id="teacher-work-overview">Việc cần xử lý</Typography>
    {query.isPending && <Typography role="status">Đang tải công việc…</Typography>}
    {query.isError && <Alert severity="warning" action={<Button onClick={() => void query.refetch()}>Thử lại</Button>}>
      Chưa tải được công việc của các lớp.
    </Alert>}
    {!query.isError && query.data && <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
      {(Object.keys(filters) as WorkFilter[]).map(key => <Button key={key} component={Link}
        to={`/action-center?filter=${key}`} variant="outlined" sx={{ minHeight: 44 }}>
        {filters[key].label} · {query.data?.[filters[key].metric]}
      </Button>)}
    </Box>}
    <Button component={Link} to="/action-center" sx={{ minHeight: 44, mt: 0.5 }}>Xem tất cả công việc</Button>
  </Card>;
}

export default function TeacherActionCenterPage() {
  const [params] = useSearchParams();
  const requested = params.get('filter') ?? '';
  const filter = Object.hasOwn(filters, requested) ? requested as WorkFilter : 'ALL';
  const pageParam = Number(params.get('page'));
  const page = Number.isInteger(pageParam) && pageParam > 0 && pageParam <= 2147483647 ? pageParam : 0;
  const path = (nextFilter: WorkFilter | 'ALL', nextPage = 0) =>
    `/action-center?filter=${nextFilter}&page=${nextPage}`;
  const query = useTeacherWork(filter, page);
  const summary = query.isError ? undefined : query.data;
  return <Stack spacing={2} sx={{ minWidth: 0 }}>
    <PageHeader focusOnMount title="Việc cần xử lý"
      subtitle={summary && `Bài tập đã giao trong ${summary.classCount} lớp đang phụ trách`}
      back={<Button component={Link} to="/dashboard">Về tổng quan</Button>}
      actions={<Button onClick={() => void query.refetch()} disabled={query.isFetching}>Cập nhật</Button>} />
    {query.isPending && <Typography role="status">Đang tải công việc…</Typography>}
    {query.isError && <Alert severity="error" action={<Button onClick={() => void query.refetch()}>Thử lại</Button>}>
      Chưa tải được công việc của các lớp.
    </Alert>}
    {summary && <>
      <Box component="nav" aria-label="Lọc công việc" sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button component={Link} to={path('ALL')} aria-current={filter === 'ALL' ? 'page' : undefined}
          variant={filter === 'ALL' ? 'contained' : 'outlined'} sx={{ minHeight: 44 }}>Tất cả</Button>
        {(Object.keys(filters) as WorkFilter[]).map(key => <Button component={Link} key={key}
          to={path(key)} aria-current={filter === key ? 'page' : undefined}
          variant={filter === key ? 'contained' : 'outlined'} sx={{ minHeight: 44 }}>
          {filters[key].label} · {summary[filters[key].metric]}
        </Button>)}
      </Box>
      <Typography role="status">{summary.matchingAssignments} bài tập phù hợp</Typography>
      {summary.assignments.length === 0 && <Alert severity="info">
        {summary.matchingAssignments > 0 ? 'Trang này không còn bài tập. Hãy quay về trang đầu.' : 'Không có bài tập phù hợp.'}
      </Alert>}
      {summary.assignments.map(work => {
        const resultParams = new URLSearchParams({ from: 'action-center', work: filter, page: String(page) });
        if (filter !== 'ALL') resultParams.set('status', filters[filter].status);
        if (filter === 'RETAKE' || filter === 'MISSING') resultParams.set('member', 'active');
        return <Card key={work.assignmentId} variant="outlined" sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ justifyContent: 'space-between' }}>
            <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
              <Typography component="h2" variant="h6">{work.title}</Typography>
              <Typography color="text.secondary">{work.className} · {new Date(work.publishedAt).toLocaleDateString('vi-VN')}</Typography>
              <Typography variant="body2">
                {work.pendingSubmissions} chờ chấm · {work.retakeRecipients} cần chụp lại · {work.missingRecipients} chưa nộp · {work.releasedSubmissions} đã trả
              </Typography>
            </Box>
            <Button component={Link} to={`/assignments/${work.assignmentId}/results?${resultParams}`}
              aria-label={`Xem kết quả ${work.title}, lớp ${work.className}`} sx={{ minHeight: 44, alignSelf: 'start', flexShrink: 0 }}>
              Xem kết quả
            </Button>
          </Stack>
        </Card>;
      })}
      <Box component="nav" aria-label="Phân trang bài tập" sx={{ display: 'flex', gap: 1 }}>
        {page > 0 && <Button component={Link} to={path(filter, page - 1)}>Trang trước</Button>}
        {page > 0 && summary.assignments.length === 0 && <Button component={Link} to={path(filter)}>Trang đầu</Button>}
        {(page + 1) * summary.pageSize < summary.matchingAssignments &&
          <Button component={Link} to={path(filter, page + 1)}>Trang sau</Button>}
      </Box>
    </>}
  </Stack>;
}
