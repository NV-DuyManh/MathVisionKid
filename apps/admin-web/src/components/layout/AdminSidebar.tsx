import {
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Typography,
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
import { Link, useLocation } from 'react-router-dom';

const groups = [
  {
    label: 'Quản lý',
    items: [
      { path: '/dashboard', label: 'Tổng quan', icon: DashboardOutlined },
      { path: '/users', label: 'Người dùng', icon: PeopleOutline },
      { path: '/classes', label: 'Lớp học', icon: SchoolOutlined },
    ],
  },
  {
    label: 'Giám sát',
    items: [
      { path: '/audit', label: 'Nhật ký hệ thống', icon: HistoryOutlined },
      { path: '/recognition/analytics', label: 'Theo dõi nhận diện', icon: InsightsOutlined },
    ],
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
  collapsed: boolean;
  onToggle: () => void;
}

export function AdminSidebar({ open, onClose, collapsed, onToggle }: Props) {
  const { pathname } = useLocation();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  const compact = desktop && collapsed;
  const width = compact ? 76 : 230;

  return (
    <Drawer
      variant={desktop ? 'permanent' : 'temporary'}
      open={desktop || open}
      onClose={onClose}
      slotProps={{ paper: { id: 'workspace-navigation', 'aria-label': 'Điều hướng quản trị' } }}
      sx={{
        width: desktop ? width : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          bgcolor: 'background.paper',
          color: 'text.primary',
          borderRight: '1px solid',
          borderColor: 'divider',
          overflowX: 'hidden',
        },
      }}
    >
      <Box sx={{ px: 1.5, minHeight: 72, display: 'flex', alignItems: 'center', gap: 0.25, borderBottom: 1, borderColor: 'divider' }}>
        <Box
          component={Link}
          to="/dashboard"
          onClick={onClose}
          aria-label="MathVision Kids, Tổng quan quản trị"
          sx={{
            display: 'flex', flex: 1, minWidth: 0, gap: 0.75, p: 0.5, borderRadius: 1,
            alignItems: 'center', justifyContent: compact ? 'center' : 'flex-start',
            color: 'text.primary', textDecoration: 'none', '&:hover': { textDecoration: 'none' },
          }}
        >
          <Box component="img" src="/ui/mathvision-star.png" alt="" width={34} height={34} sx={{ flexShrink: 0, objectFit: 'contain' }} />
          {!compact && (
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: '0.95rem', fontWeight: 800, lineHeight: 1.3, whiteSpace: 'nowrap' }}>
                MathVision Kids
              </Typography>
              <Typography variant="caption" color="text.secondary">Cổng quản trị</Typography>
            </Box>
          )}
        </Box>
        {!desktop && <IconButton aria-label="Đóng điều hướng" onClick={onClose}><Close fontSize="small" /></IconButton>}
      </Box>

      <Box component="nav" aria-label="Điều hướng quản trị" sx={{ px: 1.5, flex: 1 }}>
        {groups.map((group) => (
          <Box key={group.label} sx={{ mt: 2, '& + &': { pt: 2, borderTop: 1, borderColor: 'divider' } }}>
            {!compact && <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mx: 1.25, mb: 0.75, fontWeight: 700 }}>{group.label}</Typography>}
            <List disablePadding aria-label={group.label}>
              {group.items.map(({ path, label, icon: Icon }) => {
                const active = pathname === path || pathname.startsWith(path + '/');
                return (
                  <ListItem key={path} disablePadding sx={{ mb: 0.5 }}>
                    <Tooltip title={compact ? label : ''} placement="right">
                      <ListItemButton
                        component={Link}
                        to={path}
                        onClick={onClose}
                        selected={active}
                        aria-label={label}
                        aria-current={active ? 'page' : undefined}
                        sx={{
                          minHeight: 44, px: 1.25, gap: 1.25,
                          justifyContent: compact ? 'center' : 'flex-start',
                          color: active ? 'primary.main' : 'text.secondary',
                          border: '1px solid',
                          borderColor: active ? '#DCD9FF' : 'transparent',
                          '&:hover': { textDecoration: 'none' },
                          '&.Mui-focusVisible': { outline: '3px solid #1D4ED8', outlineOffset: 1 },
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 0, color: 'inherit' }}><Icon fontSize="small" /></ListItemIcon>
                        {!compact && <ListItemText primary={label} slotProps={{ primary: { sx: { fontSize: '0.875rem', fontWeight: active ? 800 : 600 } } }} />}
                      </ListItemButton>
                    </Tooltip>
                  </ListItem>
                );
              })}
            </List>
          </Box>
        ))}
      </Box>

      {desktop && (
        <Box sx={{ p: 1.5, borderTop: 1, borderColor: 'divider', mt: 2 }}>
          <Tooltip title={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}>
            <IconButton
              onClick={onToggle}
              aria-label={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}
              aria-expanded={!compact}
              aria-controls="workspace-navigation"
              sx={{ color: 'text.secondary', width: '100%' }}
            >
              {compact ? <ChevronRight fontSize="small" /> : <ChevronLeft fontSize="small" />}
              {!compact && <Typography variant="body2" sx={{ ml: 0.5 }}>Thu gọn thanh bên</Typography>}
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Drawer>
  );
}
