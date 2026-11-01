import { Box, Button, Card, CardContent, Chip, LinearProgress, Skeleton, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import PeopleOutline from '@mui/icons-material/PeopleAltOutlined';
import SchoolOutlined from '@mui/icons-material/SchoolOutlined';
import MeetingRoomOutlined from '@mui/icons-material/MeetingRoomOutlined';
import LockOutlined from '@mui/icons-material/LockOutlined';
import Refresh from '@mui/icons-material/Refresh';
import ArrowForward from '@mui/icons-material/ArrowForward';
import Add from '@mui/icons-material/Add';
import HistoryOutlined from '@mui/icons-material/HistoryOutlined';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
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
      <AdminTopbar title="Tổng quan vận hành" subtitle="Tài khoản, lớp học và hoạt động quản trị" />
      <PageContent>
        {/* Header Action Bar */}
        <Box className="page-actions">
          <Box>
            <Typography variant="h5" component="h2" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
              Xin chào, {user?.displayName || 'Quản trị viên'}
            </Typography>
            <Typography variant="body2" sx={{ color: '#475569' }}>
              Kiểm soát trạng thái tài khoản, phân bổ lớp học và bảo mật hệ thống.
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            disabled={dashboard.isFetching || audit.isFetching}
            onClick={() => {
              void dashboard.refetch();
              void audit.refetch();
            }}
          >
            Làm mới dữ liệu
          </Button>
        </Box>

        {/* Operational Overview Hero */}
        <Box component="section" aria-label="Tổng quan điều hành" className="dashboard-hero">
          <Box sx={{ maxWidth: 640 }}>
            <Chip
              label="TRUNG TÂM QUẢN TRỊ HỆ THỐNG"
              size="small"
              sx={{
                mb: 1.5,
                bgcolor: '#F1F5F9',
                color: '#0F172A',
                fontWeight: 800,
                fontSize: '0.68rem',
                borderRadius: 1,
                border: '1px solid #CBD5E1',
              }}
            />
            <Typography component="h3" variant="h5" sx={{ fontWeight: 800, color: '#0F172A', mb: 1 }}>
              Điều phối tài khoản & Giám sát dữ liệu tập trung
            </Typography>
            <Typography variant="body2" sx={{ color: '#475569', mb: 2.5, lineHeight: 1.6 }}>
              Quản trị viên có toàn quyền cấu hình danh sách học sinh, phân quyền giáo viên theo khối lớp và theo dõi nhật ký kiểm toán hệ thống theo thời gian thực.
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
              <Button component={Link} to="/users" variant="contained" startIcon={<PeopleOutline />}>
                Quản lý người dùng
              </Button>
              <Button component={Link} to="/classes" variant="outlined">
                Danh sách lớp học
              </Button>
              <Button component={Link} to="/audit" variant="outlined" startIcon={<HistoryOutlined />}>
                Nhật ký hệ thống
              </Button>
            </Box>
          </Box>
        </Box>

        <RequestError
          error={dashboard.error}
          retry={() => {
            void dashboard.refetch();
          }}
        />

        {/* Top 4 Operational Metrics */}
        <Box className="metric-grid" sx={{ mb: 3 }}>
          {metrics.map(({ label, value, description, icon: Icon, path, tone, color }) => (
            <Card key={label}>
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569' }}>
                    {label}
                  </Typography>
                  <Box sx={{ p: 0.75, borderRadius: 1.5, bgcolor: tone, color, display: 'flex' }}>
                    <Icon fontSize="small" />
                  </Box>
                </Box>
                <Typography
                  variant="h4"
                  component="p"
                  sx={{
                    fontSize: '2rem',
                    fontWeight: 800,
                    color: '#0F172A',
                    fontVariantNumeric: 'tabular-nums',
                    mb: 0.5,
                  }}
                >
                  {dashboard.isLoading ? <Skeleton width={70} /> : value?.toLocaleString('vi-VN') ?? '—'}
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1.5 }}>
                  {description}
                </Typography>
                <Box sx={{ borderTop: '1px solid #F1F5F9', pt: 1 }}>
                  <Button
                    component={Link}
                    to={path}
                    size="small"
                    endIcon={<ArrowForward fontSize="small" />}
                    sx={{ px: 0, fontWeight: 700, color: '#0F172A', '&:hover': { color: '#2563EB' } }}
                  >
                    Xem chi tiết
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>

        {/* Two-Column Structured Section */}
        <Box className="dashboard-columns">
          {/* Recent Audit Events */}
          <Card>
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
                  Các sự kiện bảo mật và đăng nhập mới nhất ghi nhận bởi hệ thống
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
                    <Typography variant="caption" sx={{ color: '#94A3B8' }}>
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
                <Chip
                  label="Dữ liệu đồng bộ trực tiếp từ cơ sở dữ liệu"
                  size="small"
                  variant="outlined"
                  sx={{ mt: 2.5, borderColor: '#E2E8F0', color: '#64748B', fontSize: '0.72rem' }}
                />
              </CardContent>
            </Card>

            <Card sx={{ bgcolor: '#F8FAFC', border: '1px solid #E2E8F0' }}>
              <CardContent sx={{ p: 2.5 }}>
                <Typography component="h2" variant="h6" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1rem', mb: 0.5 }}>
                  Tác vụ khởi tạo nhanh
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 2 }}>
                  Tạo tài khoản học sinh, cấp tài khoản giáo viên hoặc thiết lập lớp học mới.
                </Typography>
                <Box sx={{ display: 'grid', gap: 1 }}>
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
          <Typography variant="caption" sx={{ display: 'block', mt: 3, color: '#94A3B8' }}>
            Dữ liệu được làm mới lúc {new Date(dashboard.dataUpdatedAt).toLocaleTimeString('vi-VN')} · Số liệu lấy từ hệ thống quản lý.
          </Typography>
        )}
      </PageContent>
    </Box>
  );
}
export default DashboardPage;
