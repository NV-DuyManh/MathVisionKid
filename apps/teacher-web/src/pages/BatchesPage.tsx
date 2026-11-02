import { useEffect, useState } from 'react';
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
  Chip,
  Card,
} from '@mui/material';
import { AddCircleOutlined, FactCheck, ArrowForward, PendingActions } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Batch } from '../types';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    AppTeacherService.getBatches()
      .then((data) => {
        if (isMounted) {
          setBatches(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

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

      {loading ? (
        <Card sx={{ p: 2.5, borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 1.5, borderRadius: 2 }} />
          ))}
        </Card>
      ) : batches.length === 0 ? (
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          <EmptyState
            title="Chưa có đợt chấm bài nào"
            description="Tải lên từ 10 đến 30 bài làm để hệ thống AI hỗ trợ kiểm tra từng bước tính toán."
            actionText="Tạo đợt chấm đầu tiên"
            onAction={() => navigate('/batches/create')}
            icon={<FactCheck sx={{ fontSize: 42, color: '#94A3B8' }} />}
          />
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
                  <TableCell align="center">Cần xem lại</TableCell>
                  <TableCell>Trạng thái đợt</TableCell>
                  <TableCell>Thời gian tạo</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {batches.map((batch) => {
                  const batchId = batch.id || batch.batchId || '';
                  const total = batch.totalImages || batch.totalCount || 0;
                  const processed = batch.processedCount || 0;
                  const reviewCount = batch.reviewRequiredCount || 0;

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
