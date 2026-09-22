import { AppBar, Toolbar, Typography, Avatar, Box, Menu, MenuItem, ListItemIcon } from '@mui/material';
import { Logout, Person, Home } from '@mui/icons-material';
import { useAuth } from './AuthContext';
import { useState } from 'react';

export default function Topbar() {
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
      <Toolbar sx={{ minHeight: '56px !important', px: 3 }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, color: '#64748B' }}>
            Hệ thống hỗ trợ chấm bài tập Toán tiểu học
          </Typography>
        </Box>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            cursor: 'pointer',
            px: 1.5,
            py: 0.75,
            borderRadius: 2,
            transition: 'background-color 150ms',
            '&:hover': { bgcolor: '#F8FAFC' },
          }}
          onClick={handleMenu}
          aria-label="Tài khoản giáo viên"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === 'Enter') handleMenu(e as any); }}
        >
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A', lineHeight: 1.2 }}>
              {displayName}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 500 }}>
              Giáo viên Toán
            </Typography>
          </Box>
          <Avatar
            sx={{
              bgcolor: '#2563EB',
              width: 34,
              height: 34,
              fontSize: '0.875rem',
              fontWeight: 700,
            }}
          >
            {initial}
          </Avatar>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          slotProps={{
            paper: {
              sx: {
                mt: 1,
                minWidth: 180,
                boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
                border: '1px solid #E2E8F0',
                borderRadius: 2,
              },
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid #F1F5F9' }}>
            <Typography variant="body2" sx={{ fontWeight: 700 }}>{displayName}</Typography>
            <Typography variant="caption" color="text.secondary">{user?.email || '—'}</Typography>
          </Box>
          <MenuItem onClick={handleClose} sx={{ py: 1, mt: 0.5, fontSize: '0.875rem' }}>
            <ListItemIcon><Person fontSize="small" /></ListItemIcon>
            Hồ sơ cá nhân
          </MenuItem>
          <MenuItem
            component="a"
            href="http://localhost:5172"
            onClick={handleClose}
            sx={{ py: 1, fontSize: '0.875rem', color: '#4F46E5' }}
          >
            <ListItemIcon><Home fontSize="small" sx={{ color: '#4F46E5' }} /></ListItemIcon>
            Về MathVision Kids
          </MenuItem>
          <MenuItem onClick={handleLogout} sx={{ py: 1, color: '#DC2626', fontSize: '0.875rem' }}>
            <ListItemIcon><Logout fontSize="small" sx={{ color: '#DC2626' }} /></ListItemIcon>
            Đăng xuất
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
