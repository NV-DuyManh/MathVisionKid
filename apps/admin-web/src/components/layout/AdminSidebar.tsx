import { Box, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Tooltip, Typography, Avatar, useMediaQuery, useTheme } from '@mui/material';
import DashboardOutlined from '@mui/icons-material/DashboardOutlined';
import PeopleOutline from '@mui/icons-material/PeopleAlt';
import SchoolOutlined from '@mui/icons-material/SchoolOutlined';
import HistoryOutlined from '@mui/icons-material/HistoryOutlined';
import InsightsOutlined from '@mui/icons-material/InsightsOutlined';
import ChevronLeft from '@mui/icons-material/ChevronLeft';
import ChevronRight from '@mui/icons-material/ChevronRight';
import Close from '@mui/icons-material/Close';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
const items = [
  { path: '/dashboard', label: 'Tổng quan', icon: DashboardOutlined, group: 'KHÔNG GIAN LÀM VIỆC' },
  { path: '/users', label: 'Người dùng', icon: PeopleOutline },
  { path: '/classes', label: 'Lớp học', icon: SchoolOutlined },
  { path: '/audit', label: 'Nhật ký hệ thống', icon: HistoryOutlined, group: 'GIÁM SÁT & BÁO CÁO' },
  { path: '/recognition/analytics', label: 'Theo dõi nhận diện', icon: InsightsOutlined },
];
interface Props { open: boolean; onClose: () => void; collapsed: boolean; onToggle: () => void }
export function AdminSidebar({ open, onClose, collapsed, onToggle }: Props) {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  const compact = desktop && collapsed;
  const width = compact ? 88 : 268;
  return <Drawer id="workspace-navigation" variant={desktop ? 'permanent' : 'temporary'} open={desktop || open} onClose={onClose}
    sx={{ width: desktop ? width : 0, flexShrink: 0, '& .MuiDrawer-paper': { width, background: 'linear-gradient(180deg, #EEE7FF 0%, #F6EFFF 55%, #E9F6F1 100%)', color: 'text.primary', borderRight: '1px solid #E6DFF7', boxSizing: 'border-box', overflowX: 'hidden', scrollbarWidth: 'none', msOverflowStyle: 'none', '&::-webkit-scrollbar': { display: 'none', width: 0, height: 0 } } }}>
    <Box sx={{ px: compact ? 2.5 : 3, pt: 3.5, pb: 4, display: 'flex', alignItems: 'center', gap: 1.5 }}>
      <Box component="img" src="/ui/mathvision-star.png" alt="" sx={{ width: 44, height: 44, objectFit: 'contain', flexShrink: 0 }} />
      {!compact && <Box><Typography sx={{ fontWeight: 800, fontSize: 19, letterSpacing: '-.5px' }}>MathVisionKid</Typography><Typography sx={{ color: 'text.secondary', fontSize: 11, letterSpacing: '1.2px', mt: .3 }}>QUẢN TRỊ</Typography></Box>}
      {!desktop && <IconButton aria-label="Đóng điều hướng" onClick={onClose} sx={{ color: 'text.secondary', ml: 'auto' }}><Close /></IconButton>}
    </Box>
    <Box component="nav" aria-label="Điều hướng quản trị" sx={{ px: compact ? 1.5 : 2, flex: 1 }}>
      <List disablePadding>{items.map(item => {
        const active = pathname === item.path || pathname.startsWith(item.path + '/');
        const Icon = item.icon;
        return <Box key={item.path}>
          {item.group && <Typography sx={{ px: 1.5, mt: item.path === '/dashboard' ? 0 : 4, mb: 1.5, fontSize: 11, fontWeight: 800, letterSpacing: '.8px', color: 'text.secondary', height: compact ? 4 : 'auto' }}>{!compact && item.group}</Typography>}
          <Tooltip title={compact ? item.label : ''} placement="right">
            <ListItemButton component={Link} to={item.path} onClick={onClose} selected={active} aria-label={item.label} aria-current={active ? 'page' : undefined}
              sx={{ minHeight: 48, px: 1.5, mb: .6, borderRadius: '14px', color: active ? 'primary.dark' : 'text.secondary',
                '&.Mui-selected': { bgcolor: '#FFFFFF', color: 'primary.dark', boxShadow: '0 2px 8px rgba(112, 85, 246, 0.12), inset 3px 0 #7055F6' }, '&.Mui-selected:hover': { bgcolor: '#FFFFFF' }, '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.6)' } }}>
              <ListItemIcon sx={{ minWidth: compact ? 0 : 38, color: 'inherit' }}><Icon fontSize="small" /></ListItemIcon>
              {!compact && <ListItemText primary={item.label} slotProps={{ primary: { sx: { fontWeight: active ? 800 : 600, fontSize: '.91rem' } } }} />}
            </ListItemButton>
          </Tooltip>
        </Box>;
      })}</List>
    </Box>
    <Box sx={{ p: compact ? 1.5 : 2.5, borderTop: '1px solid #E6DFF7', mt: 3 }}>
      {!compact && <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.3, mb: 2 }}>
        <Avatar sx={{ bgcolor: '#FFFFFF', color: 'primary.dark', fontSize: 16, fontWeight: 800, border: '1px solid #E6DFF7' }}>{user?.displayName?.slice(0, 1) || 'A'}</Avatar>
        <Box sx={{ minWidth: 0 }}><Typography noWrap variant="body2" sx={{ fontWeight: 800 }}>{user?.displayName}</Typography><Typography variant="caption" sx={{ color: 'text.secondary' }}>Quản trị viên hệ thống</Typography></Box>
      </Box>}
      {desktop && <Tooltip title={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}><IconButton onClick={onToggle} aria-label={compact ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'} sx={{ color: 'primary.dark', width: '100%', borderRadius: 3, bgcolor: '#FFFFFF99', '&:hover': { bgcolor: '#FFFFFF' } }}>{compact ? <ChevronRight /> : <ChevronLeft />}</IconButton></Tooltip>}
    </Box>
  </Drawer>;
}
