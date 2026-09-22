import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Typography, Box, Chip } from '@mui/material';
import { Dashboard, School, Assignment, FactCheck, Settings, Home } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';

const DRAWER_WIDTH = 250;

const MENU_ITEMS = [
  { text: 'Tổng quan', icon: <Dashboard sx={{ fontSize: 20 }} />, path: '/dashboard' },
  { text: 'Lớp học', icon: <School sx={{ fontSize: 20 }} />, path: '/classes' },
  { text: 'Bài tập', icon: <Assignment sx={{ fontSize: 20 }} />, path: '/assignments' },
  { text: 'Đợt chấm', icon: <FactCheck sx={{ fontSize: 20 }} />, path: '/batches' },
  { text: 'Cài đặt', icon: <Settings sx={{ fontSize: 20 }} />, path: '/settings' },
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
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          borderRight: '1px solid #E2E8F0',
          backgroundColor: '#FFFFFF',
        },
      }}
    >
      <Box sx={{ p: 2.5, pb: 2, borderBottom: '1px solid #F1F5F9' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 800, color: '#2563EB', letterSpacing: '-0.02em', fontSize: '1.25rem' }}>
            MathVision<span style={{ color: '#0D9488' }}>Kids</span>
          </Typography>
        </Box>
        <Chip
          label="CỔNG GIÁO VIÊN"
          size="small"
          sx={{
            mt: 1,
            fontWeight: 700,
            fontSize: '0.6875rem',
            height: 20,
            backgroundColor: '#EFF6FF',
            color: '#1D4ED8',
            border: '1px solid #BFDBFE',
            letterSpacing: '0.04em',
          }}
        />
      </Box>

      <List sx={{ px: 1.5, py: 2 }}>
        {MENU_ITEMS.map((item) => {
          const active = location.pathname.startsWith(item.path);
          return (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={active}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 1.5,
                  py: 1,
                  px: 1.5,
                  transition: 'all 150ms ease',
                  '&.Mui-selected': {
                    backgroundColor: '#EFF6FF',
                    color: '#2563EB',
                    '& .MuiListItemIcon-root': { color: '#2563EB' },
                    '&:hover': { backgroundColor: '#DBEAFE' },
                  },
                  '&:hover': {
                    backgroundColor: '#F8FAFC',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 34, color: active ? '#2563EB' : '#64748B' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography sx={{ fontWeight: active ? 700 : 500, fontSize: '0.875rem', color: active ? '#2563EB' : '#334155' }}>
                      {item.text}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ p: 2, borderTop: '1px solid #F1F5F9', mt: 'auto' }}>
        <ListItemButton
          component="a"
          href="http://localhost:5172"
          sx={{
            borderRadius: 1.5,
            py: 1,
            px: 1.5,
            color: '#64748B',
            transition: 'all 150ms ease',
            '&:hover': { bgcolor: '#F8FAFC', color: '#4F46E5' },
          }}
        >
          <ListItemIcon sx={{ minWidth: 34, color: 'inherit' }}>
            <Home sx={{ fontSize: 20 }} />
          </ListItemIcon>
          <ListItemText
            primary={
              <Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                Trang chủ MathVision Kids
              </Typography>
            }
          />
        </ListItemButton>
      </Box>
    </Drawer>
  );
}
