import { useContext } from 'react';
import { AppBar, Avatar, Box, Breadcrumbs, Chip, IconButton, Link, Toolbar, Tooltip, Typography } from '@mui/material';
import Menu from '@mui/icons-material/Menu';
import Logout from '@mui/icons-material/Logout';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { AdminNavigation } from './NavigationContext';
import { appConfig } from '../../config/runtime';

export function AdminTopbar({ title, subtitle }: { title?: string; subtitle?: string }) {
  const { user, logout } = useAuth();
  const navigation = useContext(AdminNavigation);
  const { pathname } = useLocation();
  const parent = pathname.startsWith('/users/')
    ? { path: '/users', name: 'Người dùng' }
    : pathname.startsWith('/classes/')
    ? { path: '/classes', name: 'Lớp học' }
    : null;

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: '#FFFFFF',
        color: '#0F172A',
        borderBottom: '1px solid #E2E8F0',
      }}
    >
      <Toolbar sx={{ gap: { xs: 1, sm: 2 }, px: { xs: 2, sm: 3, lg: 3.5 }, minHeight: '64px !important', py: 1 }}>
        <IconButton
          aria-label="Mở điều hướng quản trị"
          aria-controls="workspace-navigation"
          aria-expanded={navigation.open}
          onClick={navigation.show}
          sx={{ display: { md: 'none' }, color: '#475569' }}
        >
          <Menu />
        </IconButton>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Breadcrumbs
            aria-label="Đường dẫn trang"
            sx={{ mb: 0.25, '& .MuiTypography-root, & a': { fontSize: '0.75rem' } }}
          >
            <Link component={RouterLink} to="/dashboard" underline="hover" color="text.secondary">
              Quản trị
            </Link>
            {parent && (
              <Link component={RouterLink} to={parent.path} underline="hover" color="text.secondary">
                {parent.name}
              </Link>
            )}
            <Typography sx={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>{title}</Typography>
          </Breadcrumbs>
          <Typography
            component="div"
            variant="h6"
            sx={{ fontSize: { xs: 16, sm: 18 }, fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={{ color: '#64748B', display: { xs: 'none', sm: 'block' }, fontSize: '0.75rem' }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <Typography
          variant="caption"
          sx={{
            display: { xs: 'block', sm: 'none' },
            maxWidth: 80,
            textAlign: 'right',
            color: '#64748B',
            fontSize: '0.72rem',
          }}
        >
          {user?.displayName} · ADMIN
        </Typography>
        <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'right', maxWidth: 230 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 800, color: '#0F172A', fontSize: '0.875rem' }}>
            {user?.displayName}
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B', display: { xs: 'none', lg: 'block' }, fontSize: '0.72rem', fontWeight: 600 }}>
            Quản trị viên hệ thống
          </Typography>
        </Box>
        <Avatar
          aria-hidden
          sx={{
            width: 34,
            height: 34,
            bgcolor: '#0F172A',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '0.875rem',
            display: { xs: 'none', sm: 'flex' },
          }}
        >
          {user?.displayName?.slice(0, 1) || 'A'}
        </Avatar>
        <Chip
          label="ADMIN"
          size="small"
          sx={{
            bgcolor: '#F1F5F9',
            color: '#0F172A',
            border: '1px solid #CBD5E1',
            fontSize: '0.68rem',
            fontWeight: 800,
            letterSpacing: '0.04em',
            display: { xs: 'none', sm: 'flex' },
            borderRadius: 1,
            height: 22,
          }}
        />
        <Tooltip title="Về trang MathVision Kids">
          <IconButton
            component="a"
            href={appConfig.portalOrigin}
            aria-label="Về trang MathVision Kids"
            sx={{ color: '#64748B', '&:hover': { color: '#2563EB', bgcolor: '#EFF6FF' } }}
          >
            <HomeOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Đăng xuất">
          <IconButton
            aria-label="Đăng xuất"
            onClick={() => {
              void logout();
            }}
            sx={{ color: '#64748B', '&:hover': { color: '#DC2626', bgcolor: '#FEF2F2' } }}
          >
            <Logout fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
export default AdminTopbar;
