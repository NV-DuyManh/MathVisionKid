import { AppBar, Toolbar, Typography, IconButton, Avatar, Box } from '@mui/material';
import { Notifications, Settings } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export default function Topbar() {
  const navigate = useNavigate();
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
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, cursor: 'pointer' }} onClick={() => navigate('/login')}>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'text.primary', lineHeight: 1.2 }}>Cô Lan</Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>Giáo viên Toán</Typography>
          </Box>
          <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36 }}>L</Avatar>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
