import { AppBar, Toolbar, Typography, Avatar, Box, Breadcrumbs, Link, Chip, IconButton, Tooltip } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Logout from '@mui/icons-material/Logout';
import HomeOutlined from '@mui/icons-material/HomeOutlined';
import { useAuth } from './AuthContext';
import { useLocation, Link as RouterLink } from 'react-router-dom';
import { appConfig } from '../../config/runtime';

interface RouteMeta {
  pattern: RegExp;
  title: string;
  subtitle: string;
  parent?: { name: string; path: string };
}

const ROUTE_META: RouteMeta[] = [
  { pattern: /^\/dashboard/, title: 'Tổng quan vận hành', subtitle: 'Tổng quan tiến độ chấm bài và các mục cần giáo viên xử lý hôm nay' },
  { pattern: /^\/classes/, title: 'Quản lý lớp học', subtitle: 'Danh sách các lớp học được phân công và sĩ số học sinh' },
  { pattern: /^\/assignments\/create/, title: 'Tạo bài tập mới', subtitle: 'Thiết lập phép tính ô ly và hạn nộp cho lớp học', parent: { name: 'Bài tập', path: '/assignments' } },
  { pattern: /^\/assignments/, title: 'Quản lý bài tập', subtitle: 'Giao bài tập và theo dõi tiến độ nộp bài của học sinh' },
  { pattern: /^\/batches\/create/, title: 'Tạo đợt chấm mới', subtitle: 'Tải lên hàng loạt ảnh bài làm ô ly để AI phân tích sơ bộ', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches\/[^/]+\/review/, title: 'Hàng đợi rà soát', subtitle: 'Thẩm định các bài thi hoặc bài tập cần giáo viên phê duyệt', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches\/[^/]+/, title: 'Chi tiết đợt chấm', subtitle: 'Danh sách bài làm và trạng thái thẩm định', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/batches/, title: 'Đợt chấm bài', subtitle: 'Quản lý các đợt tải bài làm ô ly của học sinh theo lớp' },
  { pattern: /^\/submissions\/[^/]+/, title: 'Đánh giá bài làm', subtitle: 'Chi tiết bài giải ô ly và phản hồi sư phạm cho học sinh', parent: { name: 'Đợt chấm bài', path: '/batches' } },
  { pattern: /^\/settings/, title: 'Cài đặt tài khoản', subtitle: 'Thông tin cá nhân và cấu hình phiên làm việc' },
];

export interface TopbarProps {
  onMenuClick: () => void;
  navigationOpen: boolean;
  confirmLogout?: () => boolean;
  title?: string;
  subtitle?: string;
}

export default function Topbar({ onMenuClick, navigationOpen, confirmLogout, title: propTitle, subtitle: propSubtitle }: TopbarProps) {
  const { user, logout } = useAuth();
  const location = useLocation();


  const matchedMeta = ROUTE_META.find((item) => item.pattern.test(location.pathname));
  const title = propTitle || matchedMeta?.title || 'Không gian giáo viên';
  const subtitle = propSubtitle || matchedMeta?.subtitle;
  const parent = matchedMeta?.parent;

  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.email || 'Giáo viên');
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        backgroundColor: '#FFFFFF',
        color: '#0F172A',
        borderBottom: '1px solid #E2E8F0',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: { xs: 1, sm: 2 }, px: { xs: 2, sm: 3, lg: 3.5 }, minHeight: '64px !important', py: 1 }}>
        <IconButton
          aria-label="Mở điều hướng giáo viên"
          aria-controls="workspace-navigation"
          aria-expanded={navigationOpen}
          onClick={onMenuClick}
          sx={{ display: { md: 'none' }, color: '#475569' }}
        >
          <MenuIcon />
        </IconButton>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Breadcrumbs
            aria-label="Đường dẫn trang"
            sx={{ mb: 0.25, '& .MuiTypography-root, & a': { fontSize: '0.75rem' } }}
          >
            <Link component={RouterLink} to="/dashboard" underline="hover" color="text.secondary">
              Giáo viên
            </Link>
            {parent && (
              <Link component={RouterLink} to={parent.path} underline="hover" color="text.secondary">
                {parent.name}
              </Link>
            )}
            <Typography sx={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600 }}>{title}</Typography>
          </Breadcrumbs>
          <Typography
            component="div"
            variant="h6"
            sx={{ fontSize: { xs: 16, sm: 18 }, fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography
              variant="caption"
              sx={{ color: '#64748B', display: { xs: 'none', sm: 'block' }, fontSize: '0.75rem' }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>

        <Typography
          variant="caption"
          sx={{
            display: { xs: 'block', sm: 'none' },
            maxWidth: 80,
            textAlign: 'right',
            color: '#64748B',
            fontSize: '0.72rem',
          }}
        >
          {displayName} · GV
        </Typography>

        <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'right', maxWidth: 230 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 800, color: '#0F172A', fontSize: '0.875rem' }}>
            {displayName}
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B', display: { xs: 'none', lg: 'block' }, fontSize: '0.72rem', fontWeight: 600 }}>
            Giáo viên phụ trách
          </Typography>
        </Box>

        <Avatar
          aria-hidden
          sx={{
            width: 34,
            height: 34,
            bgcolor: '#059669',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '0.875rem',
            display: { xs: 'none', sm: 'flex' },
          }}
        >
          {initial}
        </Avatar>

        <Chip
          label="GIÁO VIÊN"
          size="small"
          sx={{
            bgcolor: '#ECFDF5',
            color: '#059669',
            border: '1px solid #A7F3D0',
            fontSize: '0.68rem',
            fontWeight: 800,
            letterSpacing: '0.04em',
            display: { xs: 'none', sm: 'flex' },
            borderRadius: 1,
            height: 22,
          }}
        />

        <Tooltip title="Về trang chủ MathVision Kids">
          <IconButton
            component="a"
            href={appConfig.portalOrigin}
            aria-label="Về trang chủ"
            sx={{ color: '#64748B', '&:hover': { color: '#059669', bgcolor: '#ECFDF5' } }}
          >
            <HomeOutlined fontSize="small" />
          </IconButton>
        </Tooltip>

        <Tooltip title="Đăng xuất">
          <IconButton
            aria-label="Đăng xuất"
            onClick={() => {
              if (confirmLogout?.() !== false) void logout();
            }}
            sx={{ color: '#64748B', '&:hover': { color: '#DC2626', bgcolor: '#FEF2F2' } }}
          >
            <Logout fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
