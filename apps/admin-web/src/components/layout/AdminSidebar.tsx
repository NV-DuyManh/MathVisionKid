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
  Chip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import DashboardOutlined from '@mui/icons-material/DashboardOutlined';
import PeopleOutline from '@mui/icons-material/PeopleAltOutlined';
import SchoolOutlined from '@mui/icons-material/SchoolOutlined';
import HistoryOutlined from '@mui/icons-material/HistoryOutlined';
import InsightsOutlined from '@mui/icons-material/InsightsOutlined';
import ChevronLeft from '@mui/icons-material/ChevronLeft';
import ChevronRight from '@mui/icons-material/ChevronRight';
import Close from '@mui/icons-material/Close';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { appConfig } from '../../config/runtime';

const items = [
  { path: '/dashboard', label: 'Tổng quan', icon: DashboardOutlined, group: 'KHÔNG GIAN LÀM VIỆC' },
  { path: '/users', label: 'Người dùng', icon: PeopleOutline },
  { path: '/classes', label: 'Lớp học', icon: SchoolOutlined },
  { path: '/audit', label: 'Nhật ký hệ thống', icon: HistoryOutlined, group: 'GIÁM SÁT & BÁO CÁO' },
  { path: '/recognition/analytics', label: 'Theo dõi nhận diện', icon: InsightsOutlined },
];

interface Props {
  open: boolean;
  onClose: () => void;
  collapsed: boolean;
  onToggle: () => void;
}

export function AdminSidebar({ open, onClose, collapsed, onToggle }: Props) {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  const compact = desktop && collapsed;
  const width = compact ? 80 : 260;

  return (
    <Drawer
      id="workspace-navigation"
      variant={desktop ? 'permanent' : 'temporary'}
      open={desktop || open}
      onClose={onClose}
      sx={{
        width: desktop ? width : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          bgcolor: '#FFFFFF',
          color: '#0F172A',
          borderRight: '1px solid #E2E8F0',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          '&::-webkit-scrollbar': { display: 'none', width: 0, height: 0 },
        },
      }}
    >
      {/* Brand Header */}
      <Box sx={{ px: compact ? 2 : 2.5, pt: 2.5, pb: 2, display: 'flex', alignItems: 'center', gap: 1.25 }}>
        <Box
          component="img"
          src="/ui/mathvision-star.png"
          alt="MathVision Kids"
          sx={{ width: 28, height: 28, objectFit: 'contain', flexShrink: 0 }}
          onError={(e: any) => {
            e.currentTarget.style.display = 'none';
          }}
        />
        {!compact && (
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography sx={{ fontWeight: 900, fontSize: 20, letterSpacing: '-0.025em', color: '#0F172A' }}>
              MathVision<span style={{ color: '#2563EB' }}>Kids</span>
            </Typography>
            <Chip
              label="CỔNG QUẢN TRỊ"
              size="small"
              sx={{
                mt: 0.75,
                height: 20,
                bgcolor: '#F1F5F9',
                color: '#0F172A',
                fontSize: '0.68rem',
                fontWeight: 800,
                letterSpacing: '0.04em',
                borderRadius: 1,
                border: '1px solid #CBD5E1',
              }}
            />
          </Box>
        )}
        {!desktop && (
          <IconButton aria-label="Đóng điều hướng" onClick={onClose} sx={{ color: '#64748B', ml: 'auto' }}>
            <Close fontSize="small" />
          </IconButton>
        )}
      </Box>

      {/* Navigation List */}
      <Box component="nav" aria-label="Điều hướng quản trị" sx={{ px: compact ? 1 : 1.5, flex: 1 }}>
        <List disablePadding>
          {items.map((item) => {
            const active = pathname === item.path || pathname.startsWith(item.path + '/');
            const Icon = item.icon;
            return (
              <Box key={item.path}>
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
                    onClick={onClose}
                    selected={active}
                    aria-label={item.label}
                    aria-current={active ? 'page' : undefined}
                    sx={{
                      minHeight: 40,
                      px: compact ? 1.5 : 1.5,
                      justifyContent: compact ? 'center' : 'flex-start',
                      mb: 0.5,
                      borderRadius: 2,
                      bgcolor: active ? 'rgba(15, 23, 42, 0.08) !important' : 'transparent',
                      color: active ? '#0F172A' : '#475569',
                      transition: 'all 140ms ease',
                      '&:hover': {
                        bgcolor: active ? 'rgba(15, 23, 42, 0.12)' : '#F1F5F9',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: compact ? 0 : 32,
                        color: active ? '#0F172A' : '#64748B',
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
                              color: active ? '#0F172A' : '#334155',
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

      {/* Admin User Badge & Link to Portal */}
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
                bgcolor: '#0F172A',
                color: '#FFFFFF',
                fontSize: '0.85rem',
                fontWeight: 800,
                boxShadow: '0 1px 3px rgba(15, 23, 42, 0.25)',
              }}
            >
              {user?.displayName?.slice(0, 1) || 'A'}
            </Avatar>
            <Box sx={{ minWidth: 0, flexGrow: 1 }}>
              <Typography
                noWrap
                variant="body2"
                sx={{ fontWeight: 800, color: '#0F172A', fontSize: '0.8125rem' }}
              >
                {user?.displayName || 'Quản trị viên'}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B', display: 'block', fontSize: '0.72rem' }}>
                Quản trị viên hệ thống
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
                primary: { sx: { fontSize: '0.8125rem', fontWeight: 700, color: '#2563EB' } },
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
export default AdminSidebar;
