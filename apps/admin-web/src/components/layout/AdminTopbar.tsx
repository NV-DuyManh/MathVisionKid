import { useContext } from 'react';
import { AppBar, Avatar, Box, Breadcrumbs, IconButton, Link, Toolbar, Tooltip, Typography } from '@mui/material';
import Menu from '@mui/icons-material/Menu';
import Logout from '@mui/icons-material/Logout';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { AdminNavigation } from './NavigationContext';
import { appConfig } from '../../config/runtime';

export function AdminTopbar({ title }: { title: string }) {
  const { user, logout } = useAuth();
  const navigation = useContext(AdminNavigation);
  const { pathname } = useLocation();
  const parent = pathname.startsWith('/users/')
    ? { path: '/users', name: 'Người dùng' }
    : pathname.startsWith('/classes/')
      ? { path: '/classes', name: 'Lớp học' }
      : null;

  return (
    <AppBar position="static" elevation={0} sx={{ bgcolor: 'background.paper', color: 'text.primary', borderBottom: 1, borderColor: 'divider' }}>
      <Toolbar sx={{ gap: { xs: 0.5, sm: 1.5 }, px: { xs: 1.5, sm: 3, lg: 4 }, minHeight: '72px !important', py: 1 }}>
        <IconButton
          aria-label="Mở điều hướng quản trị"
          aria-controls="workspace-navigation"
          aria-expanded={navigation.open}
          onClick={navigation.show}
          sx={{ display: { md: 'none' }, color: 'text.secondary' }}
        >
          <Menu />
        </IconButton>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Breadcrumbs
            aria-label="Đường dẫn trang"
            sx={{
              '& .MuiTypography-root, & a': { fontSize: '0.875rem' },
              '& ol': { rowGap: 0.25 },
              '& .MuiBreadcrumbs-separator': { mx: 0.75 },
              '& li:nth-of-type(-n+2)': { display: { xs: 'none', sm: 'list-item' } },
            }}
          >
            <Link component={RouterLink} to="/dashboard" underline="hover" color="text.secondary">
              Quản trị
            </Link>
            {parent && (
              <Link component={RouterLink} to={parent.path} underline="hover" color="text.secondary">
                {parent.name}
              </Link>
            )}
            <Typography aria-current="page" sx={{ color: 'text.primary', fontWeight: 700, overflowWrap: 'anywhere' }}>{title}</Typography>
          </Breadcrumbs>
        </Box>
        <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 1, minWidth: 0 }}>
          <Avatar aria-hidden sx={{ width: 34, height: 34, bgcolor: 'var(--admin-tint)', color: 'primary.main', fontWeight: 800, fontSize: '0.875rem' }}>
            {user?.displayName?.slice(0, 1) || 'A'}
          </Avatar>
          <Box sx={{ display: { sm: 'none', lg: 'block' }, minWidth: 0, maxWidth: 180 }}>
            <Typography variant="body2" noWrap sx={{ fontWeight: 800, color: 'text.primary' }}>{user?.displayName}</Typography>
            <Typography variant="caption" color="text.secondary">Quản trị viên</Typography>
          </Box>
        </Box>
        <Tooltip title="Về trang MathVision Kids">
          <IconButton component="a" href={appConfig.portalOrigin} aria-label="Về trang MathVision Kids" sx={{ color: 'text.secondary' }}>
            <HomeOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Đăng xuất">
          <IconButton aria-label="Đăng xuất" onClick={() => { void logout(); }} sx={{ color: 'text.secondary', '&:hover': { color: 'error.main', bgcolor: 'error.light' } }}>
            <Logout fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
