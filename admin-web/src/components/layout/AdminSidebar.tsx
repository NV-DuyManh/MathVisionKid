import React from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import SchoolIcon from '@mui/icons-material/School';
import HistoryIcon from '@mui/icons-material/History';
import LogoutIcon from '@mui/icons-material/Logout';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const DRAWER_WIDTH = 260;

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Tổng quan', icon: <DashboardIcon /> },
  { path: '/users', label: 'Người dùng', icon: <PeopleAltIcon /> },
  { path: '/classes', label: 'Lớp học', icon: <SchoolIcon /> },
  { path: '/audit', label: 'Nhật ký hệ thống', icon: <HistoryIcon /> },
];

export const AdminSidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          bgcolor: '#0F172A', // Slate 900
          color: '#F8FAFC',
          borderRight: '1px solid #1E293B',
        },
      }}
    >
      {/* Brand Header */}
      <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              bgcolor: '#2563EB',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
            }}
          >
            <AdminPanelSettingsIcon fontSize="small" />
          </Box>
          <Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              MathVision Kids
            </Typography>
            <Typography variant="caption" sx={{ color: '#94A3B8', fontWeight: 500 }}>
              Cổng Quản Trị
            </Typography>
          </Box>
        </Box>
        <Chip
          label="ADMIN LITE v1.0"
          size="small"
          sx={{
            width: 'fit-content',
            height: 20,
            fontSize: '0.65rem',
            fontWeight: 700,
            bgcolor: '#1E293B',
            color: '#38BDF8',
            border: '1px solid #334155',
          }}
        />
      </Box>

      <Divider sx={{ borderColor: '#1E293B' }} />

      {/* Navigation List */}
      <List sx={{ px: 1.5, py: 2, flexGrow: 1 }}>
        {NAV_ITEMS.map((item) => {
          const isActive =
            item.path === '/dashboard'
              ? location.pathname === '/dashboard'
              : location.pathname.startsWith(item.path);

          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 1.5,
                  py: 1,
                  px: 2,
                  bgcolor: isActive ? '#1E293B' : 'transparent',
                  color: isActive ? '#FFFFFF' : '#94A3B8',
                  borderLeft: isActive ? '3px solid #38BDF8' : '3px solid transparent',
                  '&:hover': {
                    bgcolor: '#1E293B',
                    color: '#F8FAFC',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 36,
                    color: isActive ? '#38BDF8' : '#64748B',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography sx={{ fontSize: '0.9rem', fontWeight: isActive ? 600 : 500 }}>
                      {item.label}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ borderColor: '#1E293B' }} />

      {/* User Identity & Logout */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', bgcolor: '#020617' }}>
        <Box sx={{ overflow: 'hidden', pr: 1 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 600, color: '#F8FAFC' }}>
            {user?.displayName || 'Administrator'}
          </Typography>
          <Typography variant="caption" noWrap sx={{ color: '#94A3B8', display: 'block' }}>
            {user?.email || 'admin@mathvision.local'}
          </Typography>
        </Box>
        <Tooltip title="Đăng xuất">
          <IconButton onClick={handleLogout} sx={{ color: '#94A3B8', '&:hover': { color: '#EF4444' } }}>
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Drawer>
  );
};
