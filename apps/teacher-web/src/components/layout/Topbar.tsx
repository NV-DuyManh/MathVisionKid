import { AppBar, Toolbar, Typography, Avatar, Box, Menu, MenuItem, ListItemIcon, IconButton, ButtonBase } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { Logout, HomeOutlined } from '@mui/icons-material';
import { useAuth } from './AuthContext';
import { useState } from 'react';
import { appConfig } from '../../config/runtime';

export default function Topbar({ onMenuClick, navigationOpen }: { onMenuClick: () => void; navigationOpen: boolean }) {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleClose();
    logout();
  };

  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.email || 'Giáo viên');
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid #E2E8F0',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ minHeight: '64px !important', px: { xs: 2, md: 3.5 }, gap: 2 }}>
        <IconButton
          aria-label="Mở điều hướng giáo viên"
          aria-controls="workspace-navigation"
          aria-expanded={navigationOpen}
          onClick={onMenuClick}
          sx={{ display: { md: 'none' }, color: '#475569' }}
        >
          <MenuIcon />
        </IconButton>

        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 700, color: '#475569', fontSize: '0.875rem' }}>
            Không gian giáo viên
          </Typography>
        </Box>

        <ButtonBase
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.25,
            cursor: 'pointer',
            px: 1.25,
            py: 0.5,
            borderRadius: 1.5,
            transition: 'background-color 140ms',
            '&:hover': { bgcolor: '#F8FAFC' },
          }}
          onClick={handleMenu}
          aria-label="Tài khoản giáo viên"
          aria-controls={anchorEl ? 'teacher-account-menu' : undefined}
          aria-haspopup="menu"
          aria-expanded={Boolean(anchorEl)}
        >
          <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A', lineHeight: 1.2, fontSize: '0.875rem' }}>
              {displayName}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 500, fontSize: '0.72rem' }}>
              Giáo viên Toán
            </Typography>
          </Box>
          <Avatar
            sx={{
              bgcolor: '#059669',
              width: 34,
              height: 34,
              fontSize: '0.875rem',
              fontWeight: 700,
            }}
          >
            {initial}
          </Avatar>
        </ButtonBase>

        <Menu
          id="teacher-account-menu"
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          slotProps={{
            paper: {
              sx: {
                mt: 1,
                minWidth: 190,
                borderRadius: 2,
                boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                border: '1px solid #E2E8F0',
                p: 0.5,
              },
            },
          }}
        >
          <MenuItem
            component="a"
            href={appConfig.portalOrigin}
            onClick={handleClose}
            sx={{ borderRadius: 1.25, py: 1, fontSize: '0.875rem', fontWeight: 600, color: '#334155' }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: '#64748B' }}>
              <HomeOutlined fontSize="small" />
            </ListItemIcon>
            Về MathVision Kids
          </MenuItem>
          <MenuItem
            onClick={handleLogout}
            sx={{ borderRadius: 1.25, py: 1, fontSize: '0.875rem', fontWeight: 600, color: '#DC2626' }}
          >
            <ListItemIcon sx={{ minWidth: 32, color: '#DC2626' }}>
              <Logout fontSize="small" />
            </ListItemIcon>
            Đăng xuất
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
