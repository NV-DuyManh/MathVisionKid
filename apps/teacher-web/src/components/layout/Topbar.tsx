import { AppBar, Toolbar, Typography, Avatar, Box, Breadcrumbs, Link, IconButton, Tooltip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Logout from '@mui/icons-material/Logout';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import { appConfig } from '../../config/runtime';
import { useAuth } from './AuthContext';

const routes = [
  { pattern: /^\/classes\/[^/]+/, title: 'Chi tiết lớp học', parent: { name: 'Lớp học', path: '/classes' } },
  { pattern: /^\/classes/, title: 'Lớp học' },
  { pattern: /^\/assignments\/create/, title: 'Tạo bài tập', parent: { name: 'Bài tập', path: '/assignments' } },
  { pattern: /^\/assignments/, title: 'Bài tập' },
  { pattern: /^\/batches\/create/, title: 'Tải ảnh bài làm', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches\/[^/]+\/review/, title: 'Hàng đợi duyệt', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches\/[^/]+/, title: 'Chi tiết đợt chấm', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches/, title: 'Đợt chấm bài' },
  { pattern: /^\/submissions\/[^/]+/, title: 'Đánh giá bài làm', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/settings/, title: 'Cài đặt tài khoản' },
];

interface TopbarProps {
  onMenuClick: () => void;
  navigationOpen: boolean;
  confirmLogout: () => boolean;
}

export default function Topbar({ onMenuClick, navigationOpen, confirmLogout }: TopbarProps) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const route = routes.find((item) => item.pattern.test(pathname));
  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.email || 'Giáo viên');

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: { xs: 0.5, sm: 1 }, px: { xs: 1.5, sm: 3, lg: 4 }, minHeight: '56px !important' }}>
        <IconButton
          aria-label="Mở điều hướng giáo viên"
          aria-controls={navigationOpen ? 'workspace-navigation' : undefined}
          aria-expanded={navigationOpen}
          onClick={onMenuClick}
          sx={{ display: { md: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Breadcrumbs aria-label="Đường dẫn trang" sx={{
            '& .MuiBreadcrumbs-li': { minWidth: 0, overflowWrap: 'anywhere' },
            '& .MuiBreadcrumbs-separator': { mx: { xs: 0.5, sm: 1 } },
            ...(route && {
              '& .MuiBreadcrumbs-ol > li:nth-of-type(-n+2)': { display: { xs: 'none', sm: 'list-item' } },
            }),
          }}>
            {route && (
              <Link component={RouterLink} to="/dashboard" underline="hover" color="text.secondary" variant="body2">
                Tổng quan
              </Link>
            )}
            {route?.parent && (
              <Link component={RouterLink} to={route.parent.path} underline="hover" color="text.secondary" variant="body2"
                sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                {route.parent.name}
              </Link>
            )}
            <Typography variant="body2" aria-current="page" sx={{ color: 'text.primary', fontWeight: 800, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
              {route?.title ?? 'Tổng quan'}
            </Typography>
          </Breadcrumbs>
        </Box>

        <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 1, mr: 1, minWidth: 0 }}>
          <Avatar aria-hidden sx={{ width: 32, height: 32, bgcolor: 'primary.light', color: 'primary.dark', fontSize: 14, fontWeight: 800 }}>
            {displayName.charAt(0).toUpperCase()}
          </Avatar>
          <Typography variant="body2" noWrap sx={{ fontWeight: 700, maxWidth: { sm: 120, lg: 200 } }}>{displayName}</Typography>
        </Box>

        <Tooltip title="Về trang chủ MathVision Kids">
          <IconButton component="a" href={appConfig.portalOrigin} aria-label="Về trang chủ">
            <HomeOutlined fontSize="small" />
          </IconButton>
        </Tooltip>

        <Tooltip title="Đăng xuất">
          <IconButton
            aria-label="Đăng xuất"
            onClick={() => { if (confirmLogout()) void logout(); }}
            sx={{ '&:hover': { color: 'error.dark', bgcolor: 'error.light' } }}
          >
            <Logout fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
