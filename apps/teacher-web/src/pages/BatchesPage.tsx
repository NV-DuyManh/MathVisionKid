import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Skeleton,
  Alert,
  Chip,
  Card,
  Stack,
} from '@mui/material';
import { AddCircleOutlined, FactCheck, ArrowForward, PendingActions } from '@mui/icons-material';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

const filters = [
  { id: 'all', label: 'Tất cả' },
  { id: 'pending', label: 'Chờ duyệt' },
  { id: 'failed', label: 'Có bài lỗi' },
];
const wideColumn = { display: { xs: 'none', md: 'table-cell' } };
const pendingCount = (batch: { pendingReviewCount?: number; reviewRequiredCount?: number }) =>
  batch.pendingReviewCount ?? batch.reviewRequiredCount ?? 0;

export default function BatchesPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const filter = params.get('filter');
  const { data: batches = [], isLoading: loading, isError, refetch } = useQuery({
    queryKey: ['teacher-batches'],
    queryFn: () => AppTeacherService.getBatches(),
  });
  const activeFilter = filter === 'pending' || filter === 'failed' ? filter : 'all';
  const visibleBatches = batches.filter(batch => {
    if (activeFilter === 'pending') return pendingCount(batch) > 0;
    if (activeFilter === 'failed') return (batch.failedCount ?? 0) > 0 || ['FAILED', 'PARTIAL'].includes(batch.status);
    return true;
  });

  return (
    <Box>
      <PageHeader
        title="Quản lý Đợt chấm bài"
        description="Theo dõi tiến độ chấm hàng loạt và các bài làm cần giáo viên thẩm định lại."
        actions={
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/batches/create')}
            sx={{ borderRadius: 2.5, fontWeight: 700 }}
          >
            Tạo đợt chấm mới
          </Button>
        }
      />

      {isError ? (
        <Alert severity="error" action={<Button color="inherit" onClick={() => void refetch()}>Thử lại</Button>}>
          Chưa tải được danh sách. Vui lòng thử lại.
        </Alert>
      ) : loading ? (
        <Card sx={{ p: 2.5, borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 1.5, borderRadius: 2 }} />
          ))}
        </Card>
      ) : batches.length === 0 ? (
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          <EmptyState
            title="Chưa có đợt chấm bài nào"
            description="Tải lên từ 1 đến 30 bài làm để hệ thống AI hỗ trợ kiểm tra từng bước tính toán."
            actionText="Tạo đợt chấm đầu tiên"
            onAction={() => navigate('/batches/create')}
            icon={<FactCheck sx={{ fontSize: 42, color: '#94A3B8' }} />}
          />
        </Card>
      ) : (
        <Card sx={{ borderRadius: 3.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ p: 2, alignItems: { sm: 'center' } }}>
            <Box role="group" aria-label="Lọc đợt chấm" sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {filters.map(({ id, label }) => <Button key={id} size="small"
                variant={activeFilter === id ? 'contained' : 'outlined'} aria-pressed={activeFilter === id}
                onClick={() => setParams(id === 'all' ? {} : { filter: id }, { replace: true })}>
                {label}
              </Button>)}
            </Box>
            <Typography role="status" variant="body2" color="text.secondary">
              Hiển thị {visibleBatches.length} / {batches.length} đợt
            </Typography>
          </Stack>
          {visibleBatches.length === 0 ? (
            <Typography sx={{ px: 2, pb: 2 }}>Không có đợt chấm phù hợp với bộ lọc.</Typography>
          ) : (
          <TableContainer role="region" aria-label="Bảng đợt chấm" tabIndex={0} sx={{ '&:focus-visible': { outlineOffset: '-3px' } }}>
            <Table aria-label="Danh sách đợt chấm">
              <TableHead>
                <TableRow>
                  <TableCell>Lớp & Bài tập</TableCell>
                  <TableCell align="center" sx={wideColumn}>Tổng số bài</TableCell>
                  <TableCell align="center" sx={wideColumn}>Đã xử lý</TableCell>
                  <TableCell align="center" sx={wideColumn}>Chờ giáo viên</TableCell>
                  <TableCell sx={wideColumn}>Trạng thái đợt</TableCell>
                  <TableCell sx={wideColumn}>Thời gian tạo</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {visibleBatches.map((batch) => {
                  const batchId = batch.id || batch.batchId || '';
                  const total = batch.totalImages || batch.totalCount || 0;
                  const processed = batch.processedCount || 0;
                  const reviewCount = pendingCount(batch);
                  const batchPath = `/batches/${encodeURIComponent(batchId)}`;
                  const created = batch.createdAt
                    ? new Date(batch.createdAt).toLocaleDateString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
                    : '—';

                  return (
                    <TableRow key={batchId} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                          {batch.className ? `Lớp ${batch.className}` : 'Lớp học'}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#64748B', overflowWrap: 'anywhere' }}>
                          {batch.assignmentTitle || 'Bài tập Toán'}
                        </Typography>
                        <Box sx={{ display: { xs: 'grid', md: 'none' }, gap: 0.5, mt: 0.5, justifyItems: 'start' }}>
                          <StatusChip status={batch.status} />
                          <Typography variant="caption" color="text.secondary">
                            {processed}/{total} ảnh đã xử lý · {reviewCount} bài chờ duyệt
                          </Typography>
                          <Typography variant="caption" color="text.secondary">{created}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center" sx={wideColumn}>
                        <Chip
                          label={`${total} ảnh`}
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#CBD5E1', color: '#475569', fontWeight: 700, borderRadius: 1.5 }}
                        />
                      </TableCell>
                      <TableCell align="center" sx={wideColumn}>
                        <Chip
                          label={`${processed} / ${total}`}
                          size="small"
                          sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0', borderRadius: 1.5 }}
                        />
                      </TableCell>
                      <TableCell align="center" sx={wideColumn}>
                        {reviewCount > 0 ? (
                          <Chip
                            icon={<PendingActions sx={{ fontSize: '14px !important', color: '#DC2626 !important' }} />}
                            label={`${reviewCount} bài`}
                            size="small"
                            sx={{ bgcolor: '#FEF2F2', color: '#DC2626', fontWeight: 800, border: '1px solid #FECACA', borderRadius: 1.5 }}
                          />
                        ) : (
                          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                            0 bài
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell sx={wideColumn}>
                        <StatusChip status={batch.status} />
                      </TableCell>
                      <TableCell sx={wideColumn}>
                        <Typography variant="body2" sx={{ color: '#475569' }}>
                          {created}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1, justifyContent: 'flex-end' }}>
                          {reviewCount > 0 ? (
                            <Button
                              variant="contained"
                              color="error"
                              size="small"
                              component={Link}
                              to={batchPath + '/review'}
                              state={{ batchListFilter: activeFilter }}
                              sx={{ bgcolor: '#DC2626', '&:hover': { bgcolor: '#B91C1C' }, borderRadius: 2, fontWeight: 700 }}
                            >
                              Duyệt ({reviewCount})
                            </Button>
                          ) : null}
                          <Button
                            variant="outlined"
                            size="small"
                            endIcon={<ArrowForward />}
                            component={Link}
                            to={batchPath}
                            state={{ batchListFilter: activeFilter }}
                            sx={{ borderRadius: 2, fontWeight: 700 }}
                          >
                            Chi tiết
                          </Button>
                        </Box>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          )}
        </Card>
      )}
    </Box>
  );
}
