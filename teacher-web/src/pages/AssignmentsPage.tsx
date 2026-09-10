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
import { AddCircleOutlined, Assignment, ArrowForward } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Assignment as AssignmentType } from '../types';

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentType[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    AppTeacherService.getAssignments()
      .then((data) => {
        if (isMounted) {
          setAssignments(data);
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

  const getMathTypeLabel = (type?: string) => {
    switch (type) {
      case 'VERTICAL_ADDITION':
        return { label: 'Phép cộng đặt tính', color: '#2563EB', bg: '#EFF6FF' };
      case 'VERTICAL_SUBTRACTION':
        return { label: 'Phép trừ đặt tính', color: '#0D9488', bg: '#CCFBF1' };
      default:
        return { label: type || 'Toán đặt tính', color: '#475569', bg: '#F1F5F9' };
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3.5, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 0.5 }}>
            Danh sách Bài tập
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Quản lý các đề bài toán đặt tính và khởi tạo các đợt thu thập bài làm.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddCircleOutlined />}
          onClick={() => navigate('/assignments/create')}
        >
          Tạo bài tập mới
        </Button>
      </Box>

      {loading ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} variant="rectangular" height={50} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </Paper>
      ) : assignments.length === 0 ? (
        <Card sx={{ p: 6, textAlign: 'center', bgcolor: '#FFFFFF', borderRadius: 2.5 }}>
          <Assignment sx={{ fontSize: 56, color: '#94A3B8', mb: 1.5 }} />
          <Typography variant="h6" sx={{ color: '#0F172A', mb: 1 }}>
            Chưa có bài tập nào
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mx: 'auto', mb: 3 }}>
            Hãy tạo bài tập toán đặt tính đầu tiên để bắt đầu thu thập ảnh và chấm bài bằng AI.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddCircleOutlined />}
            onClick={() => navigate('/assignments/create')}
          >
            Tạo bài tập đầu tiên
          </Button>
        </Card>
      ) : (
        <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2.5, overflow: 'hidden' }}>
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
              {assignments.map((a) => {
                const mathTypeInfo = getMathTypeLabel(a.mathType);
                return (
                  <TableRow key={a.id || a.assignmentId} hover>
                    <TableCell>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                        {a.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Mã bài: {a.assignmentId || a.id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={mathTypeInfo.label}
                        size="small"
                        sx={{
                          fontWeight: 600,
                          fontSize: '0.75rem',
                          backgroundColor: mathTypeInfo.bg,
                          color: mathTypeInfo.color,
                          border: `1px solid ${mathTypeInfo.color}33`,
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {a.createdAt ? new Date(a.createdAt).toLocaleDateString('vi-VN') : 'Mới tạo'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={a.status === 'ACTIVE' ? 'Đang hoạt động' : (a.status ? a.status : 'Không rõ')}
                        size="small"
                        sx={
                          a.status === 'ACTIVE'
                            ? { bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 600 }
                            : { bgcolor: '#F1F5F9', color: '#475569', fontWeight: 600 }
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Button
                        variant="contained"
                        size="small"
                        endIcon={<ArrowForward />}
                        onClick={() =>
                          navigate('/batches/create', {
                            state: { assignmentId: a.assignmentId || a.id },
                          })
                        }
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
      )}
    </Box>
  );
}
