import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography, Box } from '@mui/material';
import { Dashboard, Class, Assignment, Assessment, Report } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';

const DRAWER_WIDTH = 260;

const MENU_ITEMS = [
  { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Lớp học', icon: <Class />, path: '/classes' },
  { text: 'Bài tập', icon: <Assignment />, path: '/assignments' },
  { text: 'Lượt chấm', icon: <Assessment />, path: '/batches' },
  { text: 'Báo cáo', icon: <Report />, path: '/reports' },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: 'border-box', borderRight: '1px solid #E5E7EB' },
      }}
    >
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center' }}>
        <Typography variant="h5" color="primary" sx={{ fontWeight: 800 }}>
          MathVision<span style={{ color: '#14B8A6' }}>Kids</span>
        </Typography>
      </Box>
      <List sx={{ px: 2 }}>
        {MENU_ITEMS.map((item) => {
          const active = location.pathname.startsWith(item.path);
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={active}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    color: 'primary.main',
                    '& .MuiListItemIcon-root': { color: 'primary.main' },
                    '&:hover': { backgroundColor: 'primary.light' },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: active ? 'primary.main' : 'text.secondary' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={<Typography sx={{ fontWeight: active ? 600 : 500, color: active ? 'primary.main' : 'text.primary' }}>{item.text}</Typography>} 
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Drawer>
  );
}
