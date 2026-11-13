import {
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Typography,
  Avatar,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import DashboardOutlined from '@mui/icons-material/DashboardOutlined';
import SchoolOutlined from '@mui/icons-material/SchoolOutlined';
import AssignmentOutlined from '@mui/icons-material/AssignmentOutlined';
import FactCheckOutlined from '@mui/icons-material/FactCheckOutlined';
import SettingsOutlined from '@mui/icons-material/SettingsOutlined';
import ChevronLeft from '@mui/icons-material/ChevronLeft';
import ChevronRight from '@mui/icons-material/ChevronRight';
import Close from '@mui/icons-material/Close';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { appConfig } from '../../config/runtime';

const items = [
  { path: '/dashboard', label: 'Tổng quan', icon: DashboardOutlined, group: 'VẬN HÀNH GIẢNG DẠY' },
  { path: '/classes', label: 'Lớp học', icon: SchoolOutlined },
  { path: '/assignments', label: 'Bài tập', icon: AssignmentOutlined },
  { path: '/batches', label: 'Đợt chấm bài', icon: FactCheckOutlined },
  { path: '/settings', label: 'Cài đặt tài khoản', icon: SettingsOutlined, group: 'HỆ THỐNG' },
];

export interface SidebarProps {
  open: boolean;
  onClose: () => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ open, onClose, collapsed, onToggle }: SidebarProps) {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  const compact = desktop && collapsed;
  const width = compact ? 72 : 226;

  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.email || 'Giáo viên');
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <Drawer
      id="workspace-navigation"
      variant={desktop ? 'permanent' : 'temporary'}
      open={desktop || open}
      onClose={onClose}
      slotProps={{ paper: { 'aria-label': 'Điều hướng giáo viên' } }}
      sx={{
        width: desktop ? width : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          bgcolor: '#FCFDFB',
          color: 'text.primary',
          borderRight: 1,
          borderColor: 'divider',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          transition: 'width 200ms cubic-bezier(0.16, 1, 0.3, 1)',
          '&::-webkit-scrollbar': { display: 'none', width: 0, height: 0 },
        },
      }}
    >
      {/* Brand Header */}
      <Box sx={{ mx: 1.5, px: compact ? 0 : 1, height: 76, borderBottom: 1, borderColor: 'divider',
        display: 'flex', alignItems: 'center', justifyContent: compact ? 'center' : 'flex-start', gap: 1 }}>
        <Box
          component="img"
          src="/ui/mathvision-star.png"
          alt={compact ? 'MathVision Kids' : ''}
          width={36}
          height={36}
          sx={{ objectFit: 'contain', flexShrink: 0 }}
        />
        {!compact && (
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography sx={{ fontWeight: 800, fontSize: 15, lineHeight: 1.3, color: 'text.primary' }}>
              MathVision Kids
            </Typography>
            <Typography variant="caption" sx={{ color: 'primary.dark' }}>Cổng giáo viên</Typography>
          </Box>
        )}
        {!desktop && (
          <IconButton aria-label="Đóng điều hướng" onClick={onClose} sx={{ color: '#64748B', ml: 'auto' }}>
            <Close fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Navigation List */}
      <Box component="nav" aria-label="Điều hướng giáo viên" sx={{ px: compact ? 1 : 1.5, flex: 1 }}>
        <List disablePadding>
          {items.map((item) => {
            const active = pathname === item.path || pathname.startsWith(`${item.path}/`)
              || (item.path === '/batches' && pathname.startsWith('/submissions/'));
            const Icon = item.icon;
            return (
              <Box component="li" key={item.path} sx={{ listStyle: 'none' }}>
                {item.group && (
                  <Typography
                    sx={{
                      px: 1.5,
                      mt: item.path === '/dashboard' ? 1 : 2.5,
                      mb: 0.75,
                      fontSize: '0.68rem',
                      fontWeight: 800,
                      letterSpacing: '0.05em',
                      color: '#64748B',
                      height: compact ? 4 : 'auto',
                    }}
                  >
                    {!compact && item.group}
                  </Typography>
                )}
                <Tooltip title={compact ? item.label : ''} placement="right">
                  <ListItemButton
                    component={Link}
                    to={item.path}
                    onClick={(event) => {
                      const sameTab = event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
                      if (!sameTab) return;
                      onClose();
                    }}
                    selected={active}
                    aria-label={item.label}
                    aria-current={active ? 'page' : undefined}
                    sx={{
                      minHeight: 44,
                      px: 1.5,
                      gap: compact ? 0 : 0.5,
                      justifyContent: compact ? 'center' : 'flex-start',
                      mb: 0.5,
                      borderRadius: '8px',
                      borderInlineStart: '3px solid',
                      borderInlineStartColor: active ? 'primary.main' : 'transparent',
                      '&.Mui-selected': { bgcolor: 'primary.light', color: 'primary.dark' },
                      '&:hover': {
                        bgcolor: active ? 'primary.light' : '#F1F5F9',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: compact ? 0 : 32,
                        color: active ? 'primary.dark' : 'text.secondary',
                        justifyContent: 'center',
                      }}
                    >
                      <Icon fontSize="small" />
                    </ListItemIcon>
                    {!compact && (
                      <ListItemText
                        primary={item.label}
                        slotProps={{
                          primary: {
                            sx: {
                              fontWeight: active ? 800 : 600,
                              fontSize: '0.875rem',
                              color: active ? 'primary.dark' : 'text.primary',
                            },
                          },
                        }}
                      />
                    )}
                  </ListItemButton>
                </Tooltip>
              </Box>
            );
          })}
        </List>
      </Box>

      {/* Teacher User Badge & Link to Portal */}
      <Box sx={{ p: compact ? 1 : 1.5, borderTop: '1px solid #E2E8F0', mt: 2 }}>
        {!compact && (
          <Box
            sx={{
              p: 1.25,
              mb: 1.25,
              borderRadius: 2.5,
              bgcolor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              display: 'flex',
              alignItems: 'center',
              gap: 1.25,
            }}
          >
            <Avatar
              sx={{
                width: 34,
                height: 34,
                bgcolor: 'primary.main',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 800,
                boxShadow: '0 1px 3px rgba(5, 150, 105, 0.25)',
              }}
            >
              {initial}
            </Avatar>
            <Box sx={{ minWidth: 0, flexGrow: 1 }}>
              <Typography
                noWrap
                variant="body2"
                sx={{ fontWeight: 800, color: '#0F172A', fontSize: '0.8125rem' }}
              >
                {displayName}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block', fontSize: '0.72rem' }}>
                Giáo viên phụ trách
              </Typography>
            </Box>
          </Box>
        )}

        {/* Portal origin link */}
        {!compact && (
          <ListItemButton
            component="a"
            href={appConfig.portalOrigin}
            sx={{
              minHeight: 38,
              borderRadius: 2,
              px: 1.5,
              mb: 1,
              '&:hover': { bgcolor: '#F1F5F9' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 28, color: '#64748B' }}>
              <HomeOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary="Về MathVision Kids"
              slotProps={{
                primary: { sx: { fontSize: '0.8125rem', fontWeight: 700, color: 'primary.dark' } },
              }}
            />
          </ListItemButton>
        )}

        {desktop && (
          <Tooltip title={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}>
            <IconButton
              onClick={onToggle}
              aria-label={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}
              sx={{
                color: '#64748B',
                width: '100%',
                borderRadius: 2,
                bgcolor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                '&:hover': { bgcolor: '#F1F5F9', color: '#0F172A' },
              }}
            >
              {compact ? <ChevronRight fontSize="small" /> : <ChevronLeft fontSize="small" />}
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Drawer>
  );
}
