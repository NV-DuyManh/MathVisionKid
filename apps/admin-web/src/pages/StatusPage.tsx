import { Box, Button, Card, CardContent, Typography } from '@mui/material';
import LockOutlined from '@mui/icons-material/LockOutlined';
import ScheduleOutlined from '@mui/icons-material/ScheduleOutlined';
import SearchOffOutlined from '@mui/icons-material/SearchOffOutlined';
import { Link } from 'react-router-dom';
import { appConfig } from '../config/runtime';

const statuses = {
  '403': {
    title: 'Bạn không có quyền truy cập',
    description: 'Hãy đăng nhập bằng tài khoản quản trị viên đang hoạt động.',
    icon: LockOutlined,
  },
  expired: {
    title: 'Phiên đăng nhập đã hết hạn',
    description: 'Vui lòng xác thực lại để tiếp tục công việc.',
    icon: ScheduleOutlined,
  },
  '404': {
    title: 'Không tìm thấy trang',
    description: 'Địa chỉ có thể đã thay đổi. Bạn có thể quay lại trang tổng quan.',
    icon: SearchOffOutlined,
  },
};

export function StatusPage({ code = '404' }: { code?: keyof typeof statuses }) {
  const { title, description, icon: Icon } = statuses[code];
  return (
    <Box className="admin-auth admin-status">
      <Card sx={{ maxWidth: 560, width: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2.5, py: 1.25, bgcolor: 'var(--admin-paper)', borderBottom: 1, borderColor: 'var(--admin-paper-line)' }}>
          <Box component="img" src="/ui/mathvision-star.png" alt="" width={30} height={30} sx={{ objectFit: 'contain' }} />
          <Typography variant="body2" sx={{ color: 'text.primary', fontWeight: 800 }}>MathVision Kids</Typography>
        </Box>
        <CardContent sx={{ p: { xs: 2.5, sm: 4 }, '&:last-child': { pb: { xs: 2.5, sm: 4 } } }}>
          <Box sx={{ width: 48, height: 48, display: 'grid', placeItems: 'center', bgcolor: 'var(--admin-tint)', color: 'primary.main', borderRadius: 1, mb: 2 }}>
            <Icon />
          </Box>
          <Typography component="h1" variant="h2" sx={{ mb: 1 }}>{title}</Typography>
          <Typography color="text.secondary" sx={{ mb: 3 }}>{description}</Typography>
          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            <Button component={Link} to="/dashboard" variant={code === '404' ? 'contained' : 'outlined'}>Về tổng quan</Button>
            <Button component="a" href={`${appConfig.portalOrigin}/login`} variant={code === '404' ? 'outlined' : 'contained'}>Đăng nhập qua Portal</Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
