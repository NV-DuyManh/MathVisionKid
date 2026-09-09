import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Divider,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { DeleteOutlined as DeleteOutlineIcon } from '@mui/icons-material';
import EditIcon from '@mui/icons-material/Edit';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SchoolIcon from '@mui/icons-material/School';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { StatusChip } from '../components/common/StatusChip';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { EmptyState } from '../components/common/EmptyState';
import type { UpdateClassRequest, AssignTeacherRequest } from '../types';

export const ClassDetailPage: React.FC = () => {
  const { classId } = useParams<{ classId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Dialog States
  const [isAssignTeacherOpen, setIsAssignTeacherOpen] = useState<boolean>(false);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>('');

  const [isAddStudentOpen, setIsAddStudentOpen] = useState<boolean>(false);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');

  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>('');
  const [editGrade, setEditGrade] = useState<number>(3);
  const [editYear, setEditYear] = useState<string>('');

  const [studentToRemove, setStudentToRemove] = useState<{ id: string; name: string } | null>(null);

  // Fetch Class Detail
  const { data: classroom, isLoading, error } = useQuery({
    queryKey: ['admin-class', classId],
    queryFn: () => adminService.getClass(classId!),
    enabled: !!classId,
  });

  // Fetch active teachers
  const { data: teachersData } = useQuery({
    queryKey: ['admin-active-teachers'],
    queryFn: () => adminService.getUsers({ role: 'TEACHER', active: true, size: 50 }),
    enabled: isAssignTeacherOpen,
  });

  // Fetch active students
  const { data: studentsData } = useQuery({
    queryKey: ['admin-active-students'],
    queryFn: () => adminService.getUsers({ role: 'STUDENT', active: true, size: 100 }),
    enabled: isAddStudentOpen,
  });

  // Reassign teacher mutation
  const assignTeacherMutation = useMutation({
    mutationFn: (payload: AssignTeacherRequest) => adminService.assignTeacher(classId!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-class', classId], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-classes'] });
      setIsAssignTeacherOpen(false);
    },
  });

  // Edit class mutation
  const editClassMutation = useMutation({
    mutationFn: (payload: UpdateClassRequest) => adminService.updateClass(classId!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-class', classId], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-classes'] });
      setIsEditOpen(false);
    },
  });

  // Add student mutation
  const addStudentMutation = useMutation({
    mutationFn: (studentId: string) => adminService.addStudentToClass(classId!, studentId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-class', classId], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-classes'] });
      setIsAddStudentOpen(false);
      setSelectedStudentId('');
    },
  });

  // Remove student mutation
  const removeStudentMutation = useMutation({
    mutationFn: (studentId: string) => adminService.removeStudentFromClass(classId!, studentId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-class', classId], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-classes'] });
      setStudentToRemove(null);
    },
  });

  const handleOpenEdit = () => {
    if (!classroom) return;
    setEditName(classroom.name);
    setEditGrade(classroom.gradeLevel);
    setEditYear(classroom.academicYear || '');
    setIsEditOpen(true);
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    editClassMutation.mutate({
      name: editName.trim(),
      gradeLevel: editGrade,
      academicYear: editYear.trim() || undefined,
    });
  };

  const handleAssignTeacherSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedTeacherId) {
      assignTeacherMutation.mutate({ teacherId: selectedTeacherId });
    }
  };

  const handleAddStudentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedStudentId) {
      addStudentMutation.mutate(selectedStudentId);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={36} sx={{ color: '#0F172A' }} />
      </Box>
    );
  }

  if (error || !classroom) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Không thể tải thông tin lớp học hoặc lớp học không tồn tại.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/classes')}>
          Quay lại danh sách lớp học
        </Button>
      </Box>
    );
  }

  // Filter students available to add (not currently in roster)
  const currentStudentIds = new Set(classroom.students?.map((s) => s.userId) || []);
  const availableStudents = studentsData?.content?.filter((s) => !currentStudentIds.has(s.userId)) || [];

  return (
    <Box>
      <AdminTopbar title={classroom.name} subtitle={`Khối ${classroom.gradeLevel} • ${classroom.academicYear || 'Chưa định năm học'}`} />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        <Box sx={{ mb: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/classes')}
            sx={{ color: '#64748B', fontWeight: 600 }}
          >
            Danh sách lớp học
          </Button>
        </Box>

        {/* Class Overview Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: { xs: 2.5, md: 3.5 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 2, mb: 3 }}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  {classroom.name}
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
                  Khối {classroom.gradeLevel} {classroom.academicYear ? `• Năm học ${classroom.academicYear}` : ''}
                </Typography>
              </Box>

              <Button
                variant="outlined"
                size="small"
                startIcon={<EditIcon />}
                onClick={handleOpenEdit}
                sx={{ borderColor: '#CBD5E1', color: '#0F172A' }}
              >
                Chỉnh sửa lớp
              </Button>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={3}>
              {/* Teacher Assignment */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 2, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SchoolIcon sx={{ color: '#2563EB', fontSize: 20 }} />
                      <Typography variant="subtitle2" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                        Giáo viên phụ trách
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      startIcon={<SwapHorizIcon />}
                      onClick={() => {
                        setSelectedTeacherId(classroom.teacher?.userId || '');
                        setIsAssignTeacherOpen(true);
                      }}
                      sx={{ color: '#2563EB', fontWeight: 600, fontSize: '0.8rem' }}
                    >
                      Đổi giáo viên
                    </Button>
                  </Box>

                  {classroom.teacher ? (
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 700, color: '#0F172A' }}>
                        {classroom.teacher.displayName}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#475569' }}>
                        {classroom.teacher.email}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" sx={{ color: '#EF4444', fontWeight: 500 }}>
                      Chưa có giáo viên phụ trách
                    </Typography>
                  )}
                </Box>
              </Grid>

              {/* Roster Summary */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 2, bgcolor: '#F8FAFC', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <PeopleAltIcon sx={{ color: '#10B981', fontSize: 20 }} />
                    <Typography variant="subtitle2" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                      Sĩ số lớp học
                    </Typography>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    {classroom.studentCount} học sinh
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B' }}>
                    Đã đăng ký trong danh sách lớp chính thức
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Canonical Roster Invariant Notice Banner */}
        <Alert
          severity="info"
          icon={<InfoOutlinedIcon />}
          sx={{
            mb: 3,
            bgcolor: '#EFF6FF',
            color: '#1E40AF',
            border: '1px solid #BFDBFE',
            '& .MuiAlert-icon': { color: '#2563EB' },
          }}
        >
          <strong>Quy tắc đồng bộ danh sách lớp:</strong> Danh sách học sinh dưới đây là nguồn dữ liệu chuẩn duy nhất (Single Source of Truth). Giáo viên phụ trách sẽ sử dụng danh sách này khi chấm bài theo đợt (Batch Submission) để ghép nối ảnh bài làm của học sinh tương ứng.
        </Alert>

        {/* Student Roster Table */}
        <Card>
          <Box sx={{ p: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                Danh sách học sinh trong lớp ({classroom.studentCount})
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748B' }}>
                Học sinh thuộc danh sách lớp học này
              </Typography>
            </Box>

            <Button
              variant="contained"
              startIcon={<PersonAddIcon />}
              onClick={() => {
                setSelectedStudentId('');
                setIsAddStudentOpen(true);
              }}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              Thêm học sinh vào lớp
            </Button>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Họ và tên học sinh</TableCell>
                  <TableCell>Email tài khoản</TableCell>
                  <TableCell>Khối</TableCell>
                  <TableCell>Trạng thái tài khoản</TableCell>
                  <TableCell align="right">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {classroom.students && classroom.students.length > 0 ? (
                  classroom.students.map((student) => (
                    <TableRow key={student.userId} hover>
                      <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                        {student.displayName}
                      </TableCell>
                      <TableCell sx={{ color: '#475569' }}>{student.email}</TableCell>
                      <TableCell sx={{ color: '#64748B' }}>
                        {student.gradeLevel ? `Lớp ${student.gradeLevel}` : '—'}
                      </TableCell>
                      <TableCell>
                        <StatusChip active={student.active} />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Xóa khỏi danh sách lớp">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() =>
                              setStudentToRemove({
                                id: student.userId,
                                name: student.displayName,
                              })
                            }
                          >
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <EmptyState
                        title="Chưa có học sinh trong lớp"
                        description="Lớp học này hiện tại chưa có học sinh nào. Thêm học sinh để giáo viên có thể giao bài tập và chấm bài theo đợt."
                        actionText="Thêm học sinh ngay"
                        onAction={() => setIsAddStudentOpen(true)}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </Box>

      {/* Assign Teacher Dialog */}
      <Dialog open={isAssignTeacherOpen} onClose={() => setIsAssignTeacherOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Phân công giáo viên phụ trách
        </DialogTitle>
        <form onSubmit={handleAssignTeacherSubmit}>
          <DialogContent>
            <FormControl fullWidth size="small" required sx={{ mt: 1 }}>
              <InputLabel>Chọn giáo viên</InputLabel>
              <Select
                value={selectedTeacherId}
                label="Chọn giáo viên"
                onChange={(e) => setSelectedTeacherId(e.target.value)}
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
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setIsAssignTeacherOpen(false)} sx={{ color: '#64748B' }}>
              Hủy
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={assignTeacherMutation.isPending || !selectedTeacherId}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {assignTeacherMutation.isPending ? 'Đang phân công...' : 'Lưu phân công'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Add Student to Class Dialog */}
      <Dialog open={isAddStudentOpen} onClose={() => setIsAddStudentOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Thêm học sinh vào lớp học
        </DialogTitle>
        <form onSubmit={handleAddStudentSubmit}>
          <DialogContent>
            <FormControl fullWidth size="small" required sx={{ mt: 1 }}>
              <InputLabel>Chọn học sinh</InputLabel>
              <Select
                value={selectedStudentId}
                label="Chọn học sinh"
                onChange={(e) => setSelectedStudentId(e.target.value)}
              >
                {availableStudents.length > 0 ? (
                  availableStudents.map((s) => (
                    <MenuItem key={s.userId} value={s.userId}>
                      {s.displayName} ({s.email}) — Lớp {s.gradeLevel}
                    </MenuItem>
                  ))
                ) : (
                  <MenuItem disabled value="">
                    Không có học sinh khả dụng chưa vào lớp
                  </MenuItem>
                )}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setIsAddStudentOpen(false)} sx={{ color: '#64748B' }}>
              Hủy
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={addStudentMutation.isPending || !selectedStudentId}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {addStudentMutation.isPending ? 'Đang thêm...' : 'Thêm vào lớp'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Edit Class Dialog */}
      <Dialog open={isEditOpen} onClose={() => setIsEditOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Chỉnh sửa thông tin lớp học
        </DialogTitle>
        <form onSubmit={handleEditSubmit}>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Tên lớp học"
                size="small"
                fullWidth
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                required
              />

              <FormControl fullWidth size="small">
                <InputLabel>Khối lớp</InputLabel>
                <Select
                  value={editGrade}
                  label="Khối lớp"
                  onChange={(e) => setEditGrade(Number(e.target.value))}
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
                value={editYear}
                onChange={(e) => setEditYear(e.target.value)}
              />
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setIsEditOpen(false)} sx={{ color: '#64748B' }}>
              Hủy
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={editClassMutation.isPending}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              {editClassMutation.isPending ? 'Đang lưu...' : 'Lưu thay đổi'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Remove Student Confirmation Dialog */}
      <ConfirmDialog
        open={!!studentToRemove}
        title="Xác nhận xóa học sinh khỏi lớp"
        message={`Bạn có chắc chắn muốn xóa học sinh "${studentToRemove?.name}" khỏi danh sách lớp học này? Học sinh sẽ không còn hiển thị trong danh sách chấm bài của giáo viên phụ trách.`}
        confirmText="Xóa khỏi lớp"
        isDestructive={true}
        loading={removeStudentMutation.isPending}
        onConfirm={() => {
          if (studentToRemove) {
            removeStudentMutation.mutate(studentToRemove.id);
          }
        }}
        onCancel={() => setStudentToRemove(null)}
      />
    </Box>
  );
};
