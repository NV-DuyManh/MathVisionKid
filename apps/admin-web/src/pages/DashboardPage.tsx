import { Box, Button, Card, CardContent, Chip, LinearProgress, Skeleton, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import PeopleOutline from '@mui/icons-material/PeopleAlt';
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
import { RequestError } from '../components/common/RequestError';
import { AuditEventChip } from '../components/common/AuditEventChip';
export function DashboardPage() {
  const { user } = useAuth();
  const dashboard = useQuery({ queryKey: ['admin-dashboard'], queryFn: adminService.getDashboard });
  const audit = useQuery({ queryKey: ['admin-recent-audit'], queryFn: () => adminService.getAudit({ page: 0, size: 5 }) });
  const data = dashboard.data;
  const metrics = [
    { label: 'Học sinh', value: data?.totalStudents, description: 'Tài khoản học sinh toàn hệ thống', icon: PeopleOutline, path: '/users?role=STUDENT', tone: '#EDE9FF', color: '#5637C9' },
    { label: 'Giáo viên', value: data?.totalTeachers, description: 'Đội ngũ giảng dạy', icon: SchoolOutlined, path: '/users?role=TEACHER', tone: '#EAF5F1', color: '#267757' },
    { label: 'Lớp học', value: data?.totalClasses, description: 'Lớp đã được tạo', icon: MeetingRoomOutlined, path: '/classes', tone: '#ECF1FC', color: '#4468A9' },
    { label: 'Tài khoản bị khóa', value: data && data.disabledStudents + data.disabledTeachers, description: 'Học sinh và giáo viên', icon: LockOutlined, path: '/users?active=false', tone: '#FFF3E6', color: '#946329' },
  ];
  return <Box>
    <AdminTopbar title="Tổng quan vận hành" subtitle="Tài khoản, lớp học và hoạt động quản trị" />
    <PageContent>
      <Box className="page-actions">
        <Box><Typography variant="overline" color="primary.dark" sx={{ fontWeight: 800,  letterSpacing: 1.5 }}>KHÔNG GIAN QUẢN TRỊ</Typography>
          <Typography component="h2" variant="h4" sx={{ mt: .5, mb: 1 }}>Xin chào, {user?.displayName || 'Quản trị viên'}!</Typography>
          <Typography color="text.secondary">Cùng chăm chút cho từng kết nối học tập hôm nay.</Typography></Box>
        <Button variant="outlined" startIcon={<Refresh />} disabled={dashboard.isFetching || audit.isFetching} onClick={() => { void dashboard.refetch(); void audit.refetch(); }}>Làm mới</Button>
      </Box>
      <Box component="section" aria-label="Chào mừng đến không gian quản trị" className="dashboard-hero">
        <Box sx={{ position: 'relative', zIndex: 1, maxWidth: 580 }}>
          <Typography variant="overline" color="primary.dark" sx={{ fontWeight: 800, letterSpacing: 1.4 }}>MATHVISION KIDS</Typography>
          <Typography component="h2" variant="h3" sx={{ fontSize: { xs: 26, sm: 32 }, lineHeight: 1.25, mt: 1, mb: 1.5 }}>Quản lý nhẹ nhàng,<br />kết nối học tập vững vàng.</Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 470, mb: 2.5 }}>Tài khoản, lớp học và hoạt động hệ thống trong một không gian gần gũi, rõ ràng.</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
            <Button component={Link} to="/users" variant="contained" startIcon={<PeopleOutline />}>Quản lý người dùng</Button>
            <Button component={Link} to="/classes" variant="outlined" sx={{ bgcolor: '#FFFFFFB3' }}>Xem lớp học</Button>
          </Box>
        </Box>
        <Box className="hero-illustration" aria-hidden="true"><Box component="img" src="/ui/mathvision-star.png" alt="" width={230} height={230} sx={{ width: '100%', height: 'auto', objectFit: 'contain' }} /></Box>
      </Box>
      <RequestError error={dashboard.error} retry={() => { void dashboard.refetch(); }} />
      <Box className="metric-grid" sx={{ mb: 3 }}>
        {metrics.map(({ label, value, description, icon: Icon, path, tone, color }) => <Card key={label}><CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700,  }}>{label}</Typography><Box sx={{ p: 1, borderRadius: 2, bgcolor: tone, color, display: 'flex' }}><Icon fontSize="small" /></Box>
          </Box>
          <Typography variant="h4" component="p" sx={{ fontSize: 36, fontVariantNumeric: 'tabular-nums', mb: .5 }}>{dashboard.isLoading ? <Skeleton width={70} /> : value?.toLocaleString('vi-VN') ?? '—'}</Typography>
          <Typography variant="caption" color="text.secondary">{description}</Typography>
          <Box sx={{ mt: 2, borderTop: '1px solid', borderColor: 'divider', pt: 1 }}>
            <Button component={Link} to={path} size="small" endIcon={<ArrowForward fontSize="small" />} sx={{ px: 0 }}>Xem danh sách</Button>
          </Box>
        </CardContent></Card>)}
      </Box>
      <Box className="dashboard-columns">
        <Card>
          <Box sx={{ p: 3, display: 'flex', justifyContent: 'space-between', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Box><Typography variant="h6" component="h2">Hoạt động gần đây</Typography><Typography variant="caption" color="text.secondary">Các sự kiện mới nhất được hệ thống ghi nhận</Typography></Box>
            <Button component={Link} to="/audit" size="small" endIcon={<ArrowForward />}>Tất cả nhật ký</Button>
          </Box>
          <Box sx={{ px: 3, pb: 2 }}><RequestError error={audit.error} retry={() => { void audit.refetch(); }} /></Box>
          {audit.isLoading ? <Box sx={{ px: 3, pb: 3 }}>{[0, 1, 2].map(i => <Skeleton height={64} key={i} />)}</Box> :
            audit.data?.content.length ? audit.data.content.map(event => <Box key={event.auditEventId} sx={{ px: 3, py: 2, borderTop: '1px solid', borderColor: 'divider', display: 'flex', gap: 2, alignItems: 'start' }}>
              <Box aria-hidden sx={{ mt: .8, width: 8, height: 8, borderRadius: '50%', flexShrink: 0, bgcolor: 'primary.main' }} />
              <Box sx={{ flex: 1, minWidth: 0 }}><AuditEventChip type={event.eventType} /><Typography variant="body2" sx={{ mt: .7, overflowWrap: 'anywhere' }}>{event.actorEmail || 'Hệ thống'}</Typography>
                <Typography variant="caption" color="text.secondary">{new Date(event.createdAt).toLocaleString('vi-VN')}</Typography></Box>
            </Box>) : !audit.error && <Typography color="text.secondary" sx={{ px: 3, pb: 4 }}>Chưa có hoạt động được ghi nhận.</Typography>}
        </Card>
        <Box sx={{ display: 'grid', gap: 3, alignContent: 'start' }}>
          <Card><CardContent>
            <Typography variant="h6" component="h2" sx={{ mb: 2 }}>Trạng thái tài khoản</Typography>
            {dashboard.isLoading ? <Skeleton height={100} /> : data ? [
              { label: 'Học sinh đang hoạt động', active: data.activeStudents, total: data.totalStudents, disabled: data.disabledStudents },
              { label: 'Giáo viên đang hoạt động', active: data.activeTeachers, total: data.totalTeachers, disabled: data.disabledTeachers },
            ].map(item => <Box key={item.label} sx={{ mt: 2.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1, mb: 1 }}><Typography variant="body2">{item.label}</Typography><Typography variant="body2" sx={{ fontWeight: 800,  }}>{item.active}/{item.total}</Typography></Box>
              <LinearProgress color={item.label.startsWith('Giáo viên') ? 'success' : 'primary'} variant="determinate" value={item.total ? item.active / item.total * 100 : 0} aria-label={item.label} sx={{ height: 6, borderRadius: 4, bgcolor: '#EEE9F5' }} />
              <Typography variant="caption" color="text.secondary">{item.disabled} tài khoản bị khóa</Typography>
            </Box>) : <Typography color="text.secondary">Chưa tải được trạng thái.</Typography>}
            <Chip label="Theo dữ liệu tài khoản hiện tại" size="small" variant="outlined" sx={{ mt: 3, maxWidth: '100%' }} />
          </CardContent></Card>
          <Card sx={{ bgcolor: '#F0EDFF' }}><CardContent>
            <Typography component="h2" variant="h6" sx={{ mb: 1 }}>Bắt đầu công việc</Typography><Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>Tạo tài khoản và tổ chức lớp học trong vài bước.</Typography>
            <Box sx={{ display: 'grid', gap: 1 }}>
              <Button component={Link} to="/users?create=true" variant="contained" startIcon={<Add />}>Tạo người dùng</Button>
              <Button component={Link} to="/classes?create=true" variant="outlined" startIcon={<Add />}>Tạo lớp học</Button>
            </Box>
          </CardContent></Card>
        </Box>
      </Box>
      {dashboard.dataUpdatedAt > 0 && <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3 }}>Dữ liệu được làm mới lúc {new Date(dashboard.dataUpdatedAt).toLocaleTimeString('vi-VN')} · Số liệu lấy từ hệ thống quản lý.</Typography>}
    </PageContent>
  </Box>;
}
