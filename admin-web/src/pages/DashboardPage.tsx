import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  Skeleton,
} from '@mui/material';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import SchoolIcon from '@mui/icons-material/School';
import ClassIcon from '@mui/icons-material/Class';
import AddIcon from '@mui/icons-material/Add';
import HistoryIcon from '@mui/icons-material/History';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { useNavigate } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const { data: dashboard, isLoading: dashLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: adminService.getDashboard,
  });

  const { data: recentAudit, isLoading: auditLoading } = useQuery({
    queryKey: ['admin-recent-audit'],
    queryFn: () => adminService.getAudit({ page: 0, size: 6 }),
  });

  return (
    <Box>
      <AdminTopbar title="Tổng quan hệ thống" subtitle="Báo cáo số liệu vận hành tài khoản và lớp học" />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Quick Actions Row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
            Chỉ số vận hành
          </Typography>
          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => navigate('/users')}
              sx={{ borderColor: '#CBD5E1', color: '#0F172A' }}
            >
              Thêm người dùng
            </Button>
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => navigate('/classes')}
              sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
            >
              Tạo lớp học
            </Button>
          </Box>
        </Box>

        {/* Metric Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Students Card */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                      Học sinh
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#0F172A', mt: 0.5 }}>
                      {dashLoading ? <Skeleton width={60} /> : dashboard?.totalStudents ?? 0}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 1.2,
                      borderRadius: 2,
                      bgcolor: '#F0FDF4',
                      color: '#16A34A',
                    }}
                  >
                    <PeopleAltIcon />
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, pt: 1, borderTop: '1px solid #F1F5F9' }}>
                  <Typography variant="body2" sx={{ color: '#166534' }}>
                    <strong>{dashboard?.activeStudents ?? 0}</strong> hoạt động
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#991B1B' }}>
                    <strong>{dashboard?.disabledStudents ?? 0}</strong> vô hiệu hóa
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Teachers Card */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                      Giáo viên
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#0F172A', mt: 0.5 }}>
                      {dashLoading ? <Skeleton width={60} /> : dashboard?.totalTeachers ?? 0}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 1.2,
                      borderRadius: 2,
                      bgcolor: '#EFF6FF',
                      color: '#2563EB',
                    }}
                  >
                    <SchoolIcon />
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', gap: 2, pt: 1, borderTop: '1px solid #F1F5F9' }}>
                  <Typography variant="body2" sx={{ color: '#1E40AF' }}>
                    <strong>{dashboard?.activeTeachers ?? 0}</strong> hoạt động
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#991B1B' }}>
                    <strong>{dashboard?.disabledTeachers ?? 0}</strong> vô hiệu hóa
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Classes Card */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: '#64748B', textTransform: 'uppercase' }}>
                      Lớp học
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#0F172A', mt: 0.5 }}>
                      {dashLoading ? <Skeleton width={60} /> : dashboard?.totalClasses ?? 0}
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 1.2,
                      borderRadius: 2,
                      bgcolor: '#FAF5FF',
                      color: '#9333EA',
                    }}
                  >
                    <ClassIcon />
                  </Box>
                </Box>
                <Box sx={{ pt: 1, borderTop: '1px solid #F1F5F9' }}>
                  <Typography variant="body2" sx={{ color: '#6B21A8' }}>
                    Đã gán giáo viên & danh sách học sinh
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Audit Events */}
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon sx={{ color: '#475569' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
              Nhật ký thao tác gần đây
            </Typography>
          </Box>
          <Button
            size="small"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/audit')}
            sx={{ color: '#2563EB', fontWeight: 600 }}
          >
            Xem tất cả nhật ký
          </Button>
        </Box>

        <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 2 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Thời gian</TableCell>
                <TableCell>Người thực hiện</TableCell>
                <TableCell>Loại sự kiện</TableCell>
                <TableCell>Mục tiêu / Chi tiết</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {auditLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton width={140} /></TableCell>
                    <TableCell><Skeleton width={160} /></TableCell>
                    <TableCell><Skeleton width={120} /></TableCell>
                    <TableCell><Skeleton width={180} /></TableCell>
                  </TableRow>
                ))
              ) : recentAudit?.content && recentAudit.content.length > 0 ? (
                recentAudit.content.map((event) => (
                  <TableRow key={event.auditEventId} hover>
                    <TableCell sx={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                      {new Date(event.createdAt).toLocaleString('vi-VN')}
                    </TableCell>
                    <TableCell sx={{ fontWeight: 500, color: '#0F172A' }}>
                      {event.actorEmail || 'Hệ thống'}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={event.eventType}
                        size="small"
                        sx={{
                          fontWeight: 600,
                          fontSize: '0.7rem',
                          bgcolor: '#F1F5F9',
                          color: '#334155',
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ color: '#475569', fontSize: '0.85rem' }}>
                      {event.metadata ? (
                        JSON.stringify(event.metadata)
                      ) : (
                        '—'
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 4, color: '#94A3B8' }}>
                    Chưa có nhật ký hoạt động nào được ghi nhận.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};
