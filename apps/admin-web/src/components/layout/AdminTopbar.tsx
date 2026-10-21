import { useContext } from 'react';
import { AppBar, Box, Chip, IconButton, Toolbar, Typography } from '@mui/material';
import { AdminPanelSettings, Menu, Logout } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { AdminNavigation } from './NavigationContext';

interface AdminTopbarProps { title?: string; subtitle?: string }
export const AdminTopbar: React.FC<AdminTopbarProps> = ({ title, subtitle }) => {
  const { user, logout } = useAuth();
  const navigation = useContext(AdminNavigation);
  return <AppBar position="sticky" elevation={0} sx={{ bgcolor: 'background.paper', color: 'text.primary', borderBottom: '1px solid', borderColor: 'divider' }}>
    <Toolbar sx={{ justifyContent: 'space-between', gap: 2, px: { xs: 2, md: 4 }, minHeight: '82px !important' }}>
      <IconButton aria-label="Mở điều hướng quản trị" aria-controls="workspace-navigation" aria-expanded={navigation.open} onClick={navigation.show} sx={{ display: { md: 'none' } }}><Menu /></IconButton>
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
        {title && <Typography variant="h6" component="h1" sx={{ fontWeight: 800, lineHeight: 1.35, fontSize: { xs: '1.05rem', sm: '1.12rem' }, overflowWrap: 'anywhere' }}>{title}</Typography>}
        {subtitle && <Typography variant="caption" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' }, overflowWrap: 'anywhere' }}>{subtitle}</Typography>}
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Typography variant="body2" sx={{ fontWeight: 800, display: { xs: 'none', sm: 'block' }, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.displayName || 'Quản trị viên'}</Typography>
        <Chip icon={<AdminPanelSettings sx={{ fontSize: '16px !important' }} />} label="Quản trị" size="small" sx={{ bgcolor: 'primary.light', color: 'primary.dark', display: { xs: 'none', sm: 'flex' } }} />
        <Typography variant="body2" sx={{ color: 'text.secondary', display: { xs: 'none', lg: 'block' } }}>{user?.email}</Typography>
        <IconButton aria-label="Đăng xuất" onClick={async () => { await logout(); }} sx={{ display: { md: 'none' } }}><Logout fontSize="small" /></IconButton>
      </Box>
    </Toolbar>
  </AppBar>;
};
