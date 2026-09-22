import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
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
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3.5, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 0.5 }}>
            Quản lý Đợt chấm bài
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Theo dõi tiến độ chấm hàng loạt và các bài làm cần giáo viên thẩm định lại.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddCircleOutlined />}
          onClick={() => navigate('/batches/create')}
        >
          Tạo đợt chấm mới
        </Button>
      </Box>

      {loading ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </Paper>
      ) : batches.length === 0 ? (
        <Card sx={{ p: 6, textAlign: 'center', bgcolor: '#FFFFFF', borderRadius: 2.5 }}>
          <FactCheck sx={{ fontSize: 56, color: '#94A3B8', mb: 1.5 }} />
          <Typography variant="h6" sx={{ color: '#0F172A', mb: 1 }}>
            Chưa có đợt chấm bài nào
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mx: 'auto', mb: 3 }}>
            Tải lên từ 10 đến 30 bài làm để hệ thống AI hỗ trợ kiểm tra từng bước tính toán.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/batches/create')}
          >
            Tạo đợt chấm đầu tiên
          </Button>
        </Card>
      ) : (
        <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2.5, overflow: 'hidden' }}>
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
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                        {batch.className ? `Lớp ${batch.className}` : 'Lớp học'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {batch.assignmentTitle || 'Bài tập Toán'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip label={`${total} ảnh`} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${processed} / ${total}`}
                        size="small"
                        sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 600 }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {reviewCount > 0 ? (
                        <Chip
                          icon={<PendingActions sx={{ fontSize: '14px !important', color: '#B91C1C !important' }} />}
                          label={`${reviewCount} bài`}
                          size="small"
                          sx={{ bgcolor: '#FEF2F2', color: '#B91C1C', fontWeight: 700, border: '1px solid #FCA5A5' }}
                        />
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          0 bài
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusChip status={batch.status} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
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
                            sx={{ bgcolor: '#DC2626', '&:hover': { bgcolor: '#B91C1C' } }}
                          >
                            Duyệt ({reviewCount})
                          </Button>
                        ) : null}
                        <Button
                          variant="outlined"
                          size="small"
                          endIcon={<ArrowForward />}
                          onClick={() => navigate(`/batches/${batchId}`)}
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
    </Box>
  );
}
