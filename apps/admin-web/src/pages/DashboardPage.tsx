import { Box, Button, Card, CardContent, LinearProgress, Skeleton, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import PeopleOutline from '@mui/icons-material/PeopleAltOutlined';
import SchoolOutlined from '@mui/icons-material/SchoolOutlined';
import MeetingRoomOutlined from '@mui/icons-material/MeetingRoomOutlined';
import LockOutlined from '@mui/icons-material/LockOutlined';
import Refresh from '@mui/icons-material/Refresh';
import ArrowForward from '@mui/icons-material/ArrowForward';
import Add from '@mui/icons-material/Add';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';
import { StatCard } from '../components/common/StatCard';
import { RequestError } from '../components/common/RequestError';
import { AuditEventChip } from '../components/common/AuditEventChip';

export function DashboardPage() {
  const { user } = useAuth();
  const dashboard = useQuery({ queryKey: ['admin-dashboard'], queryFn: adminService.getDashboard });
  const audit = useQuery({ queryKey: ['admin-recent-audit'], queryFn: () => adminService.getAudit({ page: 0, size: 5 }) });
  const data = dashboard.data;

  const metrics = [
    {
      label: 'Học sinh',
      value: data?.totalStudents,
      description: 'Tài khoản học sinh toàn hệ thống',
      icon: PeopleOutline,
      path: '/users?role=STUDENT',
      tone: '#EFF6FF',
      color: '#2563EB',
    },
    {
      label: 'Giáo viên',
      value: data?.totalTeachers,
      description: 'Đội ngũ cán bộ giảng dạy',
      icon: SchoolOutlined,
      path: '/users?role=TEACHER',
      tone: '#ECFDF5',
      color: '#059669',
    },
    {
      label: 'Lớp học',
      value: data?.totalClasses,
      description: 'Lớp học đang vận hành',
      icon: MeetingRoomOutlined,
      path: '/classes',
      tone: '#F1F5F9',
      color: '#334155',
    },
    {
      label: 'Tài khoản bị khóa',
      value: data && data.disabledStudents + data.disabledTeachers,
      description: 'Cần kiểm tra hoặc kích hoạt lại',
      icon: LockOutlined,
      path: '/users?active=false',
      tone: '#FEF2F2',
      color: '#DC2626',
    },
  ];

  return (
    <Box>
      <AdminTopbar title="Tổng quan vận hành" />
      <PageContent>
        <Box className="dashboard-hero">
        <PageHeader
          title={`Xin chào, ${user?.displayName || 'Quản trị viên'}`}
          description="Xem tình trạng tài khoản, lớp học và nhật ký hoạt động."
          actions={
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              disabled={dashboard.isFetching || audit.isFetching}
              onClick={() => {
                void dashboard.refetch();
                void audit.refetch();
              }}
              sx={{ borderRadius: 2.5, fontWeight: 700 }}
            >
              Làm mới dữ liệu
            </Button>
          }
        />
          <Box component="img" src="/ui/mathvision-star.png" alt="" width={86} height={86} className="hero-illustration" />
        </Box>

        <RequestError
          error={dashboard.error}
          retry={() => {
            void dashboard.refetch();
          }}
        />

        <Typography component="h2" variant="h4" sx={{ mb: 1.5 }}>Tài khoản và lớp học</Typography>
        <Box className="metric-grid" sx={{ mb: 3 }} aria-busy={dashboard.isFetching}>
          {metrics.map(({ label, value, description, icon: Icon, path, tone, color }) => (
            <StatCard
              key={label}
              title={label}
              value={dashboard.isLoading ? null : value}
              loading={dashboard.isLoading}
              description={description}
              icon={<Icon fontSize="small" />}
              tone={tone}
              color={color}
              path={path}
            />
          ))}
        </Box>

        {/* Two-Column Structured Section */}
        <Box className="dashboard-columns">
          <Card component="section" aria-label="Nhật ký hoạt động gần đây" aria-busy={audit.isFetching}>
            <Box
              sx={{
                p: 2.5,
                display: 'flex',
                justifyContent: 'space-between',
                gap: 2,
                alignItems: 'center',
                flexWrap: 'wrap',
                borderBottom: '1px solid #F1F5F9',
              }}
            >
              <Box>
                <Typography variant="h6" component="h2" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1rem' }}>
                  Nhật ký hoạt động gần đây
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B' }}>
                  Các sự kiện bảo mật và đăng nhập mới nhất
                </Typography>
              </Box>
              <Button component={Link} to="/audit" size="small" endIcon={<ArrowForward />} sx={{ fontWeight: 700, color: '#0F172A', '&:hover': { color: '#2563EB' } }}>
                Toàn bộ nhật ký
              </Button>
            </Box>
            <Box sx={{ px: 2.5, pb: 1 }}>
              <RequestError
                error={audit.error}
                retry={() => {
                  void audit.refetch();
                }}
              />
            </Box>
            {audit.isLoading ? (
              <Box sx={{ px: 2.5, pb: 2.5 }}>
                {[0, 1, 2].map((i) => (
                  <Skeleton height={56} key={i} />
                ))}
              </Box>
            ) : audit.data?.content.length ? (
              audit.data.content.map((event) => (
                <Box
                  key={event.auditEventId}
                  sx={{
                    px: 2.5,
                    py: 1.75,
                    borderBottom: '1px solid #F8FAFC',
                    display: 'flex',
                    gap: 1.75,
                    alignItems: 'flex-start',
                    '&:hover': { bgcolor: '#F8FAFC' },
                    transition: 'background-color 140ms',
                  }}
                >
                  <Box
                    aria-hidden
                    sx={{
                      mt: 1,
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      flexShrink: 0,
                      bgcolor: '#2563EB',
                    }}
                  />
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <AuditEventChip type={event.eventType} />
                    <Typography variant="body2" sx={{ mt: 0.5, fontWeight: 600, color: '#334155', overflowWrap: 'anywhere' }}>
                      {event.actorEmail || 'Hệ thống'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(event.createdAt).toLocaleString('vi-VN')}
                    </Typography>
                  </Box>
                </Box>
              ))
            ) : (
              !audit.error && (
                <Typography color="text.secondary" sx={{ px: 2.5, py: 3, textAlign: 'center' }}>
                  Chưa có hoạt động được ghi nhận.
                </Typography>
              )
            )}
          </Card>

          {/* Account Health & Quick Actions */}
          <Box sx={{ display: 'grid', gap: 2.5, alignContent: 'start' }}>
            <Card>
              <CardContent sx={{ p: 2.5 }}>
                <Typography variant="h6" component="h2" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1rem', mb: 2 }}>
                  Trạng thái tài khoản
                </Typography>
                {dashboard.isLoading ? (
                  <Skeleton height={100} />
                ) : data ? (
                  [
                    {
                      label: 'Học sinh đang hoạt động',
                      active: data.activeStudents,
                      total: data.totalStudents,
                      disabled: data.disabledStudents,
                    },
                    {
                      label: 'Giáo viên đang hoạt động',
                      active: data.activeTeachers,
                      total: data.totalTeachers,
                      disabled: data.disabledTeachers,
                    },
                  ].map((item) => (
                    <Box key={item.label} sx={{ mt: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1, mb: 0.75 }}>
                        <Typography variant="body2" sx={{ fontWeight: 600, color: '#334155' }}>
                          {item.label}
                        </Typography>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                          {item.active}/{item.total}
                        </Typography>
                      </Box>
                      <LinearProgress
                        color={item.label.startsWith('Giáo viên') ? 'success' : 'primary'}
                        variant="determinate"
                        value={item.total ? (item.active / item.total) * 100 : 0}
                        aria-label={item.label}
                        sx={{ height: 6, borderRadius: 3, bgcolor: '#F1F5F9' }}
                      />
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.5 }}>
                        {item.disabled} tài khoản tạm khóa
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography color="text.secondary">Chưa tải được trạng thái.</Typography>
                )}
              </CardContent>
            </Card>

            <Card component="section" aria-label="Tác vụ nhanh" sx={{ bgcolor: 'var(--admin-paper)', borderColor: 'var(--admin-paper-line)' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Typography component="h2" variant="h6" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1rem', mb: 0.5 }}>
                  Tác vụ nhanh
                </Typography>
                <Box sx={{ display: 'grid', gap: 1, mt: 2 }}>
                  <Button component={Link} to="/users?create=true" variant="contained" startIcon={<Add />}>
                    Tạo tài khoản người dùng
                  </Button>
                  <Button component={Link} to="/classes?create=true" variant="outlined" startIcon={<Add />}>
                    Tạo lớp học mới
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {dashboard.dataUpdatedAt > 0 && (
          <Typography variant="caption" sx={{ display: 'block', mt: 3, color: 'text.secondary' }}>
            Dữ liệu được làm mới lúc {new Date(dashboard.dataUpdatedAt).toLocaleTimeString('vi-VN')}
          </Typography>
        )}
      </PageContent>
    </Box>
  );
}
export default DashboardPage;
