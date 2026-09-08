import { AppBar, Toolbar, Typography, IconButton, Avatar, Box, Menu, MenuItem } from '@mui/material';
import { Notifications, Settings } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { useState } from 'react';

export default function Topbar() {
  const navigate = useNavigate();
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

  const displayName = user?.firstName ? `${user.lastName || ''} ${user.firstName}`.trim() : (user?.displayName || 'Giáo viên');
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <AppBar position="sticky" elevation={0} sx={{ backgroundColor: 'background.paper', borderBottom: '1px solid #E5E7EB' }}>
      <Toolbar>
        <Box sx={{ flexGrow: 1 }} />
        
        <IconButton aria-label="Notifications" sx={{ color: 'text.secondary', mr: 1 }}>
          <Notifications />
        </IconButton>
        
        <IconButton aria-label="Settings" sx={{ color: 'text.secondary', mr: 2 }} onClick={() => navigate('/settings')}>
          <Settings />
        </IconButton>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, cursor: 'pointer' }} onClick={handleMenu}>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.2 }}>
              {displayName}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>Giáo viên Toán</Typography>
          </Box>
          <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36 }}>{initial}</Avatar>
        </Box>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        >
          <MenuItem onClick={handleLogout}>Đăng xuất</MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
