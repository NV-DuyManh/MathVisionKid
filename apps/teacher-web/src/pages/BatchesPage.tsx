import { useState, useMemo } from 'react';
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
  TextField,
  InputAdornment,
  MenuItem,
} from '@mui/material';
import { AddCircleOutlined, FactCheck, ArrowForward, PendingActions, Search, FilterList } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

export default function BatchesPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const { data: batches = [], isLoading: loading, isFetching, isError, refetch } = useQuery({
    queryKey: ['teacher-batches'],
    queryFn: () => AppTeacherService.getBatches(),
    refetchInterval: 5000, // Tự động cập nhật tiến độ các đợt chấm mỗi 5s
  });

  const filteredBatches = useMemo(() => {
    return batches.filter((b) => {
      const matchSearch =
        !searchTerm.trim() ||
        (b.className && b.className.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (b.assignmentTitle && b.assignmentTitle.toLowerCase().includes(searchTerm.toLowerCase()));

      let matchStatus = true;
      if (statusFilter === 'REVIEW_REQUIRED') {
        matchStatus = (b.reviewRequiredCount || 0) > 0;
      } else if (statusFilter === 'COMPLETED') {
        matchStatus = b.status === 'COMPLETED';
      } else if (statusFilter === 'PROCESSING') {
        matchStatus = b.status === 'PROCESSING' || b.status === 'CREATED';
      }

      return matchSearch && matchStatus;
    });
  }, [batches, searchTerm, statusFilter]);

  return (
    <Box>
      <PageHeader
        title="Quản lý Đợt chấm bài"
        description="Theo dõi tiến độ chấm hàng loạt và các bài làm cần giáo viên thẩm định lại."
        actions={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => void refetch()}
              disabled={isFetching}
              sx={{ borderRadius: 2.5, fontWeight: 600, textTransform: 'none' }}
            >
              {isFetching ? 'Đang cập nhật...' : 'Làm mới'}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddCircleOutlined />}
              onClick={() => navigate('/batches/create')}
              sx={{ borderRadius: 2.5, fontWeight: 700 }}
            >
              Tạo đợt chấm mới
            </Button>
          </Box>
        }
      />

      {/* Filter and Search Bar */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Tìm theo tên lớp hoặc bài tập..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ flexGrow: 1, minWidth: 260, bgcolor: '#FFFFFF' }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <Search sx={{ color: '#94A3B8', fontSize: 20 }} />
                </InputAdornment>
              ),
            },
          }}
        />
        <TextField
          select
          size="small"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          sx={{ minWidth: 200, bgcolor: '#FFFFFF' }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <FilterList sx={{ color: '#94A3B8', fontSize: 18 }} />
                </InputAdornment>
              ),
            },
          }}
        >
          <MenuItem value="ALL">Tất cả trạng thái</MenuItem>
          <MenuItem value="REVIEW_REQUIRED">🔴 Có bài cần xem lại</MenuItem>
          <MenuItem value="PROCESSING">⏳ Đang xử lý</MenuItem>
          <MenuItem value="COMPLETED">✅ Đã hoàn thành</MenuItem>
        </TextField>
      </Box>

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
      ) : filteredBatches.length === 0 ? (
        <Card sx={{ p: 4, borderRadius: 3.5, border: '1px solid #E2E8F0', textAlign: 'center' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#475569', mb: 1 }}>
            Không tìm thấy đợt chấm phù hợp với bộ lọc
          </Typography>
          <Button size="small" onClick={() => { setSearchTerm(''); setStatusFilter('ALL'); }}>
            Xóa bộ lọc tìm kiếm
          </Button>
        </Card>
      ) : (
        <Card sx={{ borderRadius: 3.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
          <TableContainer>
            <Table sx={{ minWidth: 800 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Lớp & Bài tập</TableCell>
                  <TableCell align="center">Tổng số bài</TableCell>
                  <TableCell align="center">Đã xử lý</TableCell>
                  <TableCell align="center">Chờ giáo viên</TableCell>
                  <TableCell>Trạng thái đợt</TableCell>
                  <TableCell>Thời gian tạo</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredBatches.map((batch) => {
                  const batchId = batch.id || batch.batchId || '';
                  const total = batch.totalImages || batch.totalCount || 0;
                  const processed = batch.processedCount || 0;
                  const reviewCount = batch.pendingReviewCount ?? batch.reviewRequiredCount ?? 0;

                  return (
                    <TableRow key={batchId} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                          {batch.className ? `Lớp ${batch.className}` : 'Lớp học'}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          {batch.assignmentTitle || 'Bài tập Toán'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={`${total} ảnh`}
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#CBD5E1', color: '#475569', fontWeight: 700, borderRadius: 1.5 }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={`${processed} / ${total}`}
                          size="small"
                          sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0', borderRadius: 1.5 }}
                        />
                      </TableCell>
                      <TableCell align="center">
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
                      <TableCell>
                        <StatusChip status={batch.status} />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ color: '#475569' }}>
                          {batch.createdAt ? new Date(batch.createdAt).toLocaleDateString('vi-VN') : 'Hôm nay'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          {reviewCount > 0 ? (
                            <Button
                              variant="contained"
                              color="error"
                              size="small"
                              onClick={() => navigate(`/batches/${batchId}/review`)}
                              sx={{ bgcolor: '#DC2626', '&:hover': { bgcolor: '#B91C1C' }, borderRadius: 2, fontWeight: 700 }}
                            >
                              Duyệt ({reviewCount})
                            </Button>
                          ) : null}
                          <Button
                            variant="outlined"
                            size="small"
                            endIcon={<ArrowForward />}
                            onClick={() => navigate(`/batches/${batchId}`)}
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
        </Card>
      )}
    </Box>
  );
}
