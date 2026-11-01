import { Box, Button, Card, CardContent, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { appConfig } from '../config/runtime';
export function StatusPage({ code = '404' }: { code?: '403' | '404' | 'expired' }) {
  const title = code === '403' ? 'Bạn không có quyền truy cập' : code === 'expired' ? 'Phiên đăng nhập đã hết hạn' : 'Không tìm thấy trang';
  return <Box sx={{ p: 3, minHeight: '70vh', display: 'grid', placeItems: 'center' }}>
    <Card sx={{ maxWidth: 520, width: '100%' }}><CardContent sx={{ textAlign: 'center', p: { xs: 3, sm: 5 } }}>
      <Typography sx={{ fontSize: 56, fontWeight: 800, color: 'primary.main' }}>{code === 'expired' ? '↻' : code}</Typography>
      <Typography component="h1" variant="h5" sx={{ mb: 2 }}>{title}</Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>{code === '403' ? 'Không gian này dành cho quản trị viên có tài khoản đang hoạt động. Hãy đăng nhập bằng tài khoản phù hợp.' : code === 'expired' ? 'Vui lòng xác thực lại để tiếp tục công việc.' : 'Địa chỉ có thể đã thay đổi. Bạn có thể quay lại trang tổng quan.'}</Typography>
      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button component={Link} to="/dashboard" variant="outlined">Về tổng quan</Button>
        <Button component="a" href={`${appConfig.portalOrigin}/login`} variant="contained">Đăng nhập qua Portal</Button>
      </Box>
    </CardContent></Card>
  </Box>;
}
