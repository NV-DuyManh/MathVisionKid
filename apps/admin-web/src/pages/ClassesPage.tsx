import React, { useState } from 'react';
import {
  Box,
  Card,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import SchoolIcon from '@mui/icons-material/School';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { useNavigate } from 'react-router-dom';
import type { CreateClassRequest } from '../types';

export const ClassesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [page, setPage] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(10);

  // Create Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [className, setClassName] = useState<string>('');
  const [gradeLevel, setGradeLevel] = useState<number>(3);
  const [academicYear, setAcademicYear] = useState<string>('2025-2026');
  const [teacherId, setTeacherId] = useState<string>('');
  const [createError, setCreateError] = useState<string | null>(null);

  // Fetch classes
  const { data, isLoading } = useQuery({
    queryKey: ['admin-classes', page, pageSize],
    queryFn: () => adminService.getClasses({ page, size: pageSize }),
  });

  // Fetch active teachers for selection dropdown
  const { data: teachersData } = useQuery({
    queryKey: ['admin-active-teachers'],
    queryFn: () => adminService.getUsers({ role: 'TEACHER', active: true, size: 50 }),
    enabled: isCreateOpen,
  });

  // Create class mutation
  const createMutation = useMutation({
    mutationFn: (payload: CreateClassRequest) => adminService.createClass(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-classes'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      setIsCreateOpen(false);
      resetCreateForm();
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setCreateError(e.response?.data?.error?.message || e.message || 'Lỗi khi tạo lớp học.');
    },
  });

  const resetCreateForm = () => {
    setClassName('');
    setGradeLevel(3);
    setAcademicYear('2025-2026');
    setTeacherId('');
    setCreateError(null);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!className.trim() || !teacherId) {
      setCreateError('Vui lòng nhập tên lớp và chọn giáo viên phụ trách.');
      return;
    }

    const payload: CreateClassRequest = {
      name: className.trim(),
      gradeLevel,
      academicYear: academicYear.trim(),
      teacherId,
    };

    createMutation.mutate(payload);
  };

  return (
    <Box>
      <AdminTopbar title="Quản lý Lớp học" subtitle="Danh sách lớp học, giáo viên phụ trách và sĩ số học sinh" />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Header Action Row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SchoolIcon sx={{ color: '#0F172A' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
              Danh sách lớp học
            </Typography>
          </Box>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setIsCreateOpen(true)}
            sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
          >
            Tạo lớp học mới
          </Button>
        </Box>

        {/* Classes Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Tên lớp học</TableCell>
                  <TableCell>Khối</TableCell>
                  <TableCell>Năm học</TableCell>
                  <TableCell>Giáo viên phụ trách</TableCell>
                  <TableCell>Sĩ số học sinh</TableCell>
                  <TableCell>Ngày tạo</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading ? (
                  <TableSkeleton rows={pageSize} columns={7} />
                ) : data?.content && data.content.length > 0 ? (
                  data.content.map((cls) => (
                    <TableRow key={cls.classId} hover>
                      <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                        {cls.name}
                      </TableCell>
                      <TableCell sx={{ color: '#475569' }}>Lớp {cls.gradeLevel}</TableCell>
                      <TableCell sx={{ color: '#64748B' }}>{cls.academicYear || '—'}</TableCell>
                      <TableCell sx={{ color: '#0F172A', fontWeight: 500 }}>
                        {cls.teacher ? `${cls.teacher.displayName} (${cls.teacher.email})` : 'Chưa phân công'}
                      </TableCell>
                      <TableCell sx={{ fontWeight: 600, color: '#2563EB' }}>
                        {cls.studentCount} học sinh
                      </TableCell>
                      <TableCell sx={{ color: '#64748B' }}>
                        {new Date(cls.createdAt).toLocaleDateString('vi-VN')}
                      </TableCell>
                      <TableCell align="right">
                        <Button
                          size="small"
                          endIcon={<OpenInNewIcon fontSize="small" />}
                          onClick={() => navigate(`/classes/${cls.classId}`)}
                          sx={{ color: '#2563EB', fontWeight: 600 }}
                        >
                          Chi tiết & Roster
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7}>
                      <EmptyState
                        title="Chưa có lớp học nào"
                        description="Bắt đầu tạo lớp học đầu tiên và phân công giáo viên phụ trách."
                        actionText="Tạo lớp học mới"
                        onAction={() => setIsCreateOpen(true)}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={data?.totalElements ?? 0}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[5, 10, 20]}
            labelRowsPerPage="Số hàng mỗi trang:"
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} trên ${count}`}
          />
        </Card>
      </Box>

      {/* Create Class Dialog */}
      <Dialog open={isCreateOpen} onClose={() => setIsCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Tạo lớp học mới
        </DialogTitle>
        <form onSubmit={handleCreateSubmit}>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2.5, fontSize: '0.85rem' }}>
                {createError}
              </Alert>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <TextField
                label="Tên lớp học"
                size="small"
                fullWidth
                value={className}
                onChange={(e) => setClassName(e.target.value)}
                required
                placeholder="VD: Lớp 3A"
              />

              <FormControl fullWidth size="small">
                <InputLabel>Khối lớp</InputLabel>
                <Select
                  value={gradeLevel}
                  label="Khối lớp"
                  onChange={(e) => setGradeLevel(Number(e.target.value))}
                >
                  <MenuItem value={1}>Khối 1</MenuItem>
                  <MenuItem value={2}>Khối 2</MenuItem>
                  <MenuItem value={3}>Khối 3</MenuItem>
                  <MenuItem value={4}>Khối 4</MenuItem>
                  <MenuItem value={5}>Khối 5</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Năm học"
                size="small"
                fullWidth
                value={academicYear}
                onChange={(e) => setAcademicYear(e.target.value)}
                placeholder="VD: 2025-2026"
              />

              <FormControl fullWidth size="small" required>
                <InputLabel>Giáo viên phụ trách</InputLabel>
                <Select
                  value={teacherId}
                  label="Giáo viên phụ trách"
                  onChange={(e) => setTeacherId(e.target.value)}
                >
                  {teachersData?.content && teachersData.content.length > 0 ? (
                    teachersData.content.map((t) => (
                      <MenuItem key={t.userId} value={t.userId}>
                        {t.displayName} ({t.email})
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled value="">
                      Không có giáo viên khả dụng
                    </MenuItem>
                  )}
                </Select>
              </FormControl>
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setIsCreateOpen(false)} sx={{ color: '#64748B' }}>
              Hủy
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isPending}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {createMutation.isPending ? 'Đang tạo...' : 'Tạo lớp học'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
};
