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
} from '@mui/material';
import { AddCircleOutlined, Assignment, ArrowForward, Search } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';
import { StatusChip } from '../components/common/StatusChip';

export default function AssignmentsPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const { data: assignments = [], isLoading: loading, isFetching, isError, refetch } = useQuery({
    queryKey: ['teacher-assignments'],
    queryFn: () => AppTeacherService.getAssignments(),
  });

  const filteredAssignments = useMemo(() => {
    return assignments.filter((a) => {
      return (
        !searchTerm.trim() ||
        (a.title && a.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
        ((a as any).className && (a as any).className.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    });
  }, [assignments, searchTerm]);

  const getMathTypeLabel = (type?: string) => {
    switch (type) {
      case 'VERTICAL_ADDITION':
        return { label: 'Phép cộng đặt tính', color: '#2563EB', bg: '#EFF6FF', border: '#BFDBFE' };
      case 'VERTICAL_SUBTRACTION':
        return { label: 'Phép trừ đặt tính', color: '#059669', bg: '#ECFDF5', border: '#A7F3D0' };
      default:
        return { label: type || 'Toán đặt tính', color: '#475569', bg: '#F1F5F9', border: '#CBD5E1' };
    }
  };

  return (
    <Box>
      <PageHeader
        title="Danh sách Bài tập"
        description="Quản lý các đề bài toán đặt tính và khởi tạo các đợt thu thập bài làm."
        actions={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => void refetch()}
              disabled={isFetching}
              sx={{ borderRadius: 2.5, fontWeight: 600, textTransform: 'none' }}
            >
              {isFetching ? 'Đang tải...' : 'Làm mới'}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddCircleOutlined />}
              onClick={() => navigate('/assignments/create')}
              sx={{ borderRadius: 2.5, fontWeight: 700 }}
            >
              Tạo bài tập mới
            </Button>
          </Box>
        }
      />

      {/* Search Bar */}
      <Box sx={{ mb: 3 }}>
        <TextField
          size="small"
          placeholder="Tìm bài tập theo tên hoặc lớp..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ maxWidth: 420, width: '100%', bgcolor: '#FFFFFF' }}
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
      ) : assignments.length === 0 ? (
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0' }}>
          <EmptyState
            title="Chưa có bài tập nào"
            description="Hãy tạo bài tập toán đặt tính đầu tiên để bắt đầu thu thập ảnh và chấm bài bằng AI."
            actionText="Tạo bài tập đầu tiên"
            onAction={() => navigate('/assignments/create')}
            icon={<Assignment sx={{ fontSize: 42, color: '#94A3B8' }} />}
          />
        </Card>
      ) : filteredAssignments.length === 0 ? (
        <Card sx={{ p: 4, borderRadius: 3.5, border: '1px solid #E2E8F0', textAlign: 'center' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#475569', mb: 1 }}>
            Không tìm thấy bài tập phù hợp
          </Typography>
          <Button size="small" onClick={() => setSearchTerm('')}>
            Xóa từ khóa tìm kiếm
          </Button>
        </Card>
      ) : (
        <Card sx={{ borderRadius: 3.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
          <TableContainer>
            <Table sx={{ minWidth: 700 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Tên bài tập</TableCell>
                  <TableCell>Dạng phép tính</TableCell>
                  <TableCell>Ngày tạo</TableCell>
                  <TableCell>Trạng thái</TableCell>
                  <TableCell align="right">Hành động</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAssignments.map((a) => {
                  const mathTypeInfo = getMathTypeLabel(a.mathType);
                  return (
                    <TableRow key={a.id || a.assignmentId} hover>
                      <TableCell>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                          {a.title}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          Mã bài: {a.assignmentId || a.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={mathTypeInfo.label}
                          size="small"
                          sx={{
                            fontWeight: 800,
                            fontSize: '0.72rem',
                            backgroundColor: mathTypeInfo.bg,
                            color: mathTypeInfo.color,
                            border: `1px solid ${mathTypeInfo.border}`,
                            borderRadius: 1.5,
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ color: '#475569' }}>
                          {a.createdAt ? new Date(a.createdAt).toLocaleDateString('vi-VN') : 'Mới tạo'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <StatusChip status={a.status || 'ACTIVE'} />
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          variant="outlined"
                          size="small"
                          endIcon={<ArrowForward />}
                          onClick={() =>
                            navigate(`/batches/create?assignmentId=${encodeURIComponent(a.assignmentId || a.id || '')}`)
                          }
                          sx={{
                            borderRadius: 2,
                            fontWeight: 700,
                            borderColor: '#CBD5E1',
                            color: '#0F172A',
                            '&:hover': {
                              borderColor: '#059669',
                              color: '#059669',
                              bgcolor: '#ECFDF5',
                            },
                          }}
                        >
                          Tạo đợt chấm
                        </Button>
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
