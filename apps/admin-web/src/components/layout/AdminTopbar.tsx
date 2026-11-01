import { useContext } from 'react';
import { AppBar, Avatar, Box, Breadcrumbs, Chip, IconButton, Link, Toolbar, Tooltip, Typography } from '@mui/material';
import Menu from '@mui/icons-material/Menu';
import Logout from '@mui/icons-material/Logout';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { AdminNavigation } from './NavigationContext';
export function AdminTopbar({ title, subtitle }: { title?: string; subtitle?: string }) {
  const { user, logout } = useAuth();
  const navigation = useContext(AdminNavigation);
  const { pathname } = useLocation();
  const parent = pathname.startsWith('/users/') ? { path: '/users', name: 'Người dùng' } : pathname.startsWith('/classes/') ? { path: '/classes', name: 'Lớp học' } : null;
  return <AppBar position="sticky" elevation={0} sx={{ bgcolor: '#FFFFFFF5', color: 'text.primary', borderBottom: '1px solid', borderColor: 'divider' }}>
    <Toolbar sx={{ gap: { xs: 1, sm: 2 }, px: { xs: 2, sm: 3, lg: 4 }, minHeight: '84px !important', py: 1.5 }}>
      <IconButton aria-label="Mở điều hướng quản trị" aria-controls="workspace-navigation" aria-expanded={navigation.open} onClick={navigation.show} sx={{ display: { md: 'none' } }}><Menu /></IconButton>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Breadcrumbs aria-label="Đường dẫn trang" sx={{ mb: .4, '& .MuiTypography-root, & a': { fontSize: 12 } }}>
          <Link component={RouterLink} to="/dashboard" underline="hover" color="text.secondary">Quản trị</Link>
          {parent && <Link component={RouterLink} to={parent.path} underline="hover" color="text.secondary">{parent.name}</Link>}
          <Typography color="text.secondary">{title}</Typography>
        </Breadcrumbs>
        <Typography component="h1" variant="h6" sx={{ fontSize: { xs: 17, sm: 21 }, lineHeight: 1.35, overflowWrap: 'anywhere' }}>{title}</Typography>
        {subtitle && <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>{subtitle}</Typography>}
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'block', sm: 'none' }, maxWidth: 76, textAlign: 'right', overflowWrap: 'anywhere' }}>{user?.displayName} · ADMIN</Typography>
      <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'right', maxWidth: 230 }}>
        <Typography variant="body2" noWrap sx={{ fontWeight: 800,  }}>{user?.displayName}</Typography>
        <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', lg: 'block' }, overflowWrap: 'anywhere' }}>{user?.email}</Typography>
      </Box>
      <Avatar aria-hidden sx={{ width: 40, height: 40, bgcolor: 'primary.light', color: 'primary.dark', fontWeight: 800, display: { xs: 'none', sm: 'flex' } }}>{user?.displayName?.slice(0, 1) || 'A'}</Avatar>
      <Chip label="ADMIN" size="small" sx={{ bgcolor: 'primary.light', color: 'primary.dark', fontSize: 10, letterSpacing: '.08em', display: { xs: 'none', sm: 'flex' } }} />
      <Tooltip title="Đăng xuất"><IconButton aria-label="Đăng xuất" onClick={() => { void logout(); }}><Logout fontSize="small" /></IconButton></Tooltip>
    </Toolbar>
  </AppBar>;
}
