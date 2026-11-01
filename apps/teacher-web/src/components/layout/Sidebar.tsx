import {
  Box,
  Chip,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  DashboardOutlined,
  SchoolOutlined,
  AssignmentOutlined,
  FactCheckOutlined,
  SettingsOutlined,
  HomeOutlined,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { appConfig } from '../../config/runtime';
import { useAuth } from './AuthContext';

const NAV_ITEMS = [
  { text: 'Tổng quan', icon: <DashboardOutlined fontSize="small" />, path: '/dashboard' },
  { text: 'Lớp học', icon: <SchoolOutlined fontSize="small" />, path: '/classes' },
  { text: 'Bài tập', icon: <AssignmentOutlined fontSize="small" />, path: '/assignments' },
  { text: 'Đợt chấm bài', icon: <FactCheckOutlined fontSize="small" />, path: '/batches' },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  const { user } = useAuth();

  const teacherName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || 'Giáo viên');

  return (
    <Drawer
      id="workspace-navigation"
      variant={desktop ? 'permanent' : 'temporary'}
      open={desktop || open}
      onClose={onClose}
      slotProps={{ paper: { 'aria-label': 'Điều hướng giáo viên' } }}
      sx={{
        width: { md: 260 },
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 260,
          boxSizing: 'border-box',
          borderRight: '1px solid #E2E8F0',
          bgcolor: '#FFFFFF',
        },
      }}
    >
      {/* Brand Header */}
      <Box sx={{ p: 2.5, pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
          <Box
            component="img"
            src="/ui/mathvision-star.png"
            alt="MathVision Kids"
            sx={{ width: 28, height: 28 }}
            onError={(e: any) => {
              e.currentTarget.style.display = 'none';
            }}
          />
          <Typography
            component="div"
            sx={{
              fontWeight: 900,
              fontSize: 20,
              letterSpacing: '-0.025em',
              color: '#0F172A',
            }}
          >
            MathVision<span style={{ color: '#059669' }}>Kids</span>
          </Typography>
        </Box>
        <Chip
          label="CỔNG GIÁO VIÊN"
          size="small"
          sx={{
            mt: 1.25,
            height: 20,
            bgcolor: '#ECFDF5',
            color: '#059669',
            fontSize: '0.68rem',
            fontWeight: 800,
            letterSpacing: '0.04em',
            borderRadius: 1,
            border: '1px solid #A7F3D0',
          }}
        />
      </Box>

      {/* Main Navigation List */}
      <Box component="nav" aria-label="Điều hướng giáo viên" sx={{ px: 1.5, py: 1, flexGrow: 1 }}>
        <Typography
          variant="caption"
          sx={{
            px: 1.5,
            mb: 0.75,
            display: 'block',
            fontWeight: 800,
            color: '#64748B',
            letterSpacing: '0.05em',
            fontSize: '0.68rem',
          }}
        >
          VẬN HÀNH GIẢNG DẠY
        </Typography>

        <List disablePadding sx={{ mb: 2 }}>
          {NAV_ITEMS.map((item) => {
            const active = location.pathname.startsWith(item.path);
            return (
              <ListItemButton
                key={item.path}
                selected={active}
                aria-current={active ? 'page' : undefined}
                onClick={() => {
                  navigate(item.path);
                  onClose();
                }}
                sx={{
                  mb: 0.5,
                  px: 1.5,
                  minHeight: 40,
                  borderRadius: 2,
                  bgcolor: active ? 'rgba(5, 150, 105, 0.08) !important' : 'transparent',
                  color: active ? '#059669' : '#475569',
                  transition: 'all 140ms ease',
                  '&:hover': {
                    bgcolor: active ? 'rgba(5, 150, 105, 0.12)' : '#F1F5F9',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 32,
                    color: active ? '#059669' : '#64748B',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  slotProps={{
                    primary: {
                      sx: {
                        fontWeight: active ? 800 : 600,
                        fontSize: '0.875rem',
                        color: active ? '#059669' : '#334155',
                      },
                    },
                  }}
                />
              </ListItemButton>
            );
          })}
        </List>

        <Typography
          variant="caption"
          sx={{
            px: 1.5,
            mb: 0.75,
            display: 'block',
            fontWeight: 800,
            color: '#64748B',
            letterSpacing: '0.05em',
            fontSize: '0.68rem',
          }}
        >
          HỆ THỐNG
        </Typography>

        <List disablePadding>
          <ListItemButton
            selected={location.pathname.startsWith('/settings')}
            aria-current={location.pathname.startsWith('/settings') ? 'page' : undefined}
            onClick={() => {
              navigate('/settings');
              onClose();
            }}
            sx={{
              mb: 0.5,
              px: 1.5,
              minHeight: 40,
              borderRadius: 2,
              bgcolor: location.pathname.startsWith('/settings') ? 'rgba(5, 150, 105, 0.08) !important' : 'transparent',
              color: location.pathname.startsWith('/settings') ? '#059669' : '#475569',
              transition: 'all 140ms ease',
              '&:hover': {
                bgcolor: location.pathname.startsWith('/settings') ? 'rgba(5, 150, 105, 0.12)' : '#F1F5F9',
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 32,
                color: location.pathname.startsWith('/settings') ? '#059669' : '#64748B',
              }}
            >
              <SettingsOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Cài đặt tài khoản"
              slotProps={{
                primary: {
                  sx: {
                    fontWeight: location.pathname.startsWith('/settings') ? 800 : 600,
                    fontSize: '0.875rem',
                    color: location.pathname.startsWith('/settings') ? '#059669' : '#334155',
                  },
                },
              }}
            />
          </ListItemButton>
        </List>
      </Box>

      {/* Teacher Profile Info Footer */}
      <Box
        sx={{
          p: 1.5,
          m: 1.5,
          borderRadius: 2.5,
          bgcolor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          display: 'flex',
          alignItems: 'center',
          gap: 1.25,
        }}
      >
        <Box
          sx={{
            width: 34,
            height: 34,
            borderRadius: '50%',
            bgcolor: '#059669',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '0.85rem',
            boxShadow: '0 1px 3px rgba(5, 150, 105, 0.25)',
          }}
        >
          {teacherName.charAt(0).toUpperCase()}
        </Box>
        <Box sx={{ minWidth: 0, flexGrow: 1 }}>
          <Typography
            variant="caption"
            sx={{
              fontWeight: 800,
              color: '#0F172A',
              display: 'block',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              fontSize: '0.8125rem',
            }}
          >
            {teacherName}
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.72rem' }}>
            Giáo viên phụ trách
          </Typography>
        </Box>
      </Box>

      {/* Link back to portal */}
      <Box sx={{ p: 1.5, borderTop: '1px solid #E2E8F0' }}>
        <ListItemButton
          component="a"
          href={appConfig.portalOrigin}
          sx={{
            minHeight: 38,
            borderRadius: 2,
            px: 1.5,
            '&:hover': { bgcolor: '#F1F5F9' },
          }}
        >
          <ListItemIcon sx={{ minWidth: 28, color: '#64748B' }}>
            <HomeOutlined fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary="Trang chủ MathVision Kids"
            slotProps={{
              primary: { sx: { fontSize: '0.8125rem', fontWeight: 700, color: '#059669' } },
            }}
          />
        </ListItemButton>
      </Box>
    </Drawer>
  );
}
