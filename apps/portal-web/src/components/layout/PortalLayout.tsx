import React, { useEffect, useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Avatar,
  IconButton,
  Tooltip,
  Chip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import { Outlet, Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import LogoutIcon from '@mui/icons-material/Logout';
import SchoolIcon from '@mui/icons-material/School';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { RoleBadge } from '../common/RoleBadge';
import { authService, type UserProfile } from '../../services/authService';
import { tokenStore } from '../../services/apiClient';
import { showDevTools } from '../../config/runtime';

export const PortalLayout: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [portalsAnchor, setPortalsAnchor] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();
  const location = typeof useLocation === 'function' ? useLocation() : null;
  const isLandingPage = location ? location.pathname === '/' : (typeof window !== 'undefined' ? window.location.pathname === '/' : true);

  useEffect(() => {
    let active = true;
    let version = 0;
    const updateSession = () => {
      const request = ++version;
      setUser(null);
      if (tokenStore.hasTokens()) {
        authService
          .getMe()
          .then((profile) => {
            if (active && request === version && tokenStore.hasTokens()) setUser(profile);
          })
          .catch(() => {
            if (active && request === version) tokenStore.clearTokens();
          });
      }
    };
    window.addEventListener('portal_auth_changed', updateSession);
    updateSession();
    return () => {
      active = false;
      window.removeEventListener('portal_auth_changed', updateSession);
    };
  }, []);

  const handleLogout = () => {
    navigate('/logout');
  };

  const isStudent = user && (user.role || '').toUpperCase().replace('ROLE_', '') === 'STUDENT';
  const isTeacher = user && (user.role || '').toUpperCase().replace('ROLE_', '') === 'TEACHER';
  const isAdmin = user && (user.role || '').toUpperCase().replace('ROLE_', '') === 'ADMIN';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: '#F8FAFC' }}>
      <a href="#main-content" className="skip-link">
        Đến nội dung chính
      </a>

      {/* Top Banner / Announcement — Kid Safety & Pedagogical Standard */}
      <Box
        sx={{
          bgcolor: '#0F172A',
          color: '#F8FAFC',
          py: 0.85,
          px: 2,
          fontSize: '0.8125rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          position: 'relative',
          zIndex: 1101,
        }}
      >
        <Container maxWidth="xl" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1.5 }}>
          <Chip
            size="small"
            icon={
              <Box
                component="span"
                aria-hidden="true"
                sx={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', ml: 0.5, color: '#FBBF24' }}
              >
                ★
              </Box>
            }
            label="TIÊU CHUẨN SƯ PHẠM TIỂU HỌC"
            sx={{
              height: 22,
              bgcolor: 'rgba(255, 255, 255, 0.09)',
              color: '#F1F5F9',
              fontWeight: 800,
              fontSize: '0.68rem',
              letterSpacing: '0.04em',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              borderRadius: 1,
              '& .MuiChip-icon': { ml: 0.8 },
              '& .MuiChip-label': { px: 0.8 },
            }}
          />
          <Typography
            variant="caption"
            sx={{
              color: '#E2E8F0',
              fontWeight: 600,
              fontSize: '0.8125rem',
              display: { xs: 'none', sm: 'inline' },
            }}
          >
            Bảo vệ quyền riêng tư học sinh & ứng dụng AI gợi mở tư duy cho giáo dục tiểu học Việt Nam
          </Typography>
        </Container>
      </Box>

      {/* Main Navbar */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: 'rgba(255, 255, 255, 0.94)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid rgba(226, 232, 240, 0.9)',
          zIndex: 1100,
          transition: 'all 200ms ease',
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 4 } }}>
          <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: { xs: 64, sm: 74 }, gap: 1 }}>
            {/* Brand Logo & Name */}
            <Box
              component={RouterLink}
              to="/"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 0.75, sm: 1.5 },
                minWidth: 0,
                textDecoration: 'none',
                transition: 'transform 160ms ease, opacity 160ms ease',
                '&:hover': { transform: 'scale(1.02)' },
                '&:active': { transform: 'scale(0.98)' },
              }}
            >
              <Box
                component="img"
                src="/ui/mathvision-star.png"
                alt="Biểu trưng Ngôi sao MathVision Kids"
                className="star-companion-float"
                sx={{
                  width: { xs: 34, sm: 42 },
                  height: { xs: 34, sm: 42 },
                  flexShrink: 0,
                  objectFit: 'contain',
                }}
                onError={(e: any) => {
                  e.currentTarget.src = '/logo.svg';
                }}
              />
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography
                    variant="h6"
                    sx={{
                      color: '#0F172A',
                      fontWeight: 900,
                      lineHeight: 1.15,
                      fontSize: { xs: 'clamp(0.95rem, 4.4vw, 1.2rem)', sm: '1.3rem' },
                      letterSpacing: '-0.025em',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    MathVision<span style={{ color: '#2563EB' }}>Kids</span>
                  </Typography>
                  <Chip
                    label="Tiểu học"
                    size="small"
                    sx={{
                      display: { xs: 'none', lg: 'inline-flex' },
                      height: 22,
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      bgcolor: '#EFF6FF',
                      color: '#2563EB',
                      borderRadius: 1.5,
                      border: '1px solid #BFDBFE',
                    }}
                  />
                </Box>
                <Typography
                  variant="caption"
                  sx={{ color: '#64748B', display: { xs: 'none', sm: 'block' }, fontWeight: 700, fontSize: '0.75rem', letterSpacing: '-0.01em' }}
                >
                  Trợ lý số học viết tay & gia sư thông minh
                </Typography>
              </Box>
            </Box>

            {/* In-page navigation (only visible on landing page on desktop) */}
            {isLandingPage && (
              <Box
                sx={{
                  display: { xs: 'none', md: user ? 'none' : 'flex', lg: 'flex' },
                  alignItems: 'center',
                  gap: 0.75,
                }}
              >
                <Button
                  component="a"
                  href="#showcase"
                  size="small"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    borderRadius: 2,
                    px: 1.75,
                    minHeight: 38,
                    whiteSpace: 'nowrap',
                    transition: 'all 160ms ease',
                    '&:hover': { color: '#2563EB', bgcolor: 'rgba(37, 99, 235, 0.06)' },
                  }}
                >
                  Thực nghiệm ô ly
                </Button>
                <Button
                  component="a"
                  href="#socratic"
                  size="small"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    borderRadius: 2,
                    px: 1.75,
                    minHeight: 38,
                    whiteSpace: 'nowrap',
                    transition: 'all 160ms ease',
                    '&:hover': { color: '#2563EB', bgcolor: 'rgba(37, 99, 235, 0.06)' },
                  }}
                >
                  Quy trình gợi mở
                </Button>
                <Button
                  component="a"
                  href="#workspaces"
                  size="small"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    borderRadius: 2,
                    px: 1.75,
                    minHeight: 38,
                    whiteSpace: 'nowrap',
                    transition: 'all 160ms ease',
                    '&:hover': { color: '#2563EB', bgcolor: 'rgba(37, 99, 235, 0.06)' },
                  }}
                >
                  Hệ sinh thái
                </Button>
                <Button
                  component="a"
                  href="#principles"
                  size="small"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    borderRadius: 2,
                    px: 1.75,
                    minHeight: 38,
                    whiteSpace: 'nowrap',
                    transition: 'all 160ms ease',
                    '&:hover': { color: '#2563EB', bgcolor: 'rgba(37, 99, 235, 0.06)' },
                  }}
                >
                  Chuẩn mực an toàn
                </Button>
              </Box>
            )}

            {/* Right Action & Auth Area */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexShrink: 0 }}>
              {/* Portals menu button for quick navigation */}
              <Button
                variant="outlined"
                color="inherit"
                size="small"
                onClick={(e) => setPortalsAnchor(e.currentTarget)}
                endIcon={<span style={{ fontSize: '0.72rem', marginLeft: 4 }}>▼</span>}
                sx={{
                  display: { xs: 'none', sm: 'inline-flex' },
                  color: '#334155',
                  borderColor: '#CBD5E1',
                  fontWeight: 700,
                  fontSize: '0.86rem',
                  borderRadius: 2,
                  px: 1.75,
                  minHeight: 40,
                  whiteSpace: 'nowrap',
                  bgcolor: '#FFFFFF',
                  '&:hover': { borderColor: '#2563EB', bgcolor: '#EFF6FF', color: '#2563EB' },
                }}
              >
                Cổng làm việc
              </Button>
              <Menu
                anchorEl={portalsAnchor}
                open={Boolean(portalsAnchor)}
                onClose={() => setPortalsAnchor(null)}
                slotProps={{
                  paper: {
                    sx: {
                      borderRadius: 3,
                      p: 1,
                      minWidth: 260,
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 12px 32px -4px rgba(15, 23, 42, 0.12)',
                    },
                  },
                }}
              >
                <MenuItem
                  component={RouterLink}
                  to="/student"
                  onClick={() => setPortalsAnchor(null)}
                  sx={{ borderRadius: 2, py: 1.25 }}
                >
                  <ListItemIcon sx={{ color: '#2563EB' }}>
                    <SchoolIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Không gian Học sinh"
                    secondary="Luyện tập & xem hướng dẫn từng bước"
                    slotProps={{
                      primary: { sx: { fontWeight: 800, fontSize: '0.9rem', color: '#0F172A' } },
                      secondary: { sx: { fontSize: '0.75rem', color: '#64748B' } },
                    }}
                  />
                </MenuItem>
                <MenuItem
                  component={RouterLink}
                  to="/teacher-entry"
                  onClick={() => setPortalsAnchor(null)}
                  sx={{ borderRadius: 2, py: 1.25 }}
                >
                  <ListItemIcon sx={{ color: '#059669', minWidth: 32 }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    </svg>
                  </ListItemIcon>
                  <ListItemText
                    primary="Cổng Giáo viên"
                    secondary="Chấm bài theo đợt & quản lý lớp"
                    slotProps={{
                      primary: { sx: { fontWeight: 800, fontSize: '0.9rem', color: '#0F172A' } },
                      secondary: { sx: { fontSize: '0.75rem', color: '#64748B' } },
                    }}
                  />
                </MenuItem>
                <MenuItem
                  component={RouterLink}
                  to="/admin-entry"
                  onClick={() => setPortalsAnchor(null)}
                  sx={{ borderRadius: 2, py: 1.25 }}
                >
                  <ListItemIcon sx={{ color: '#0F172A', minWidth: 32 }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                  </ListItemIcon>
                  <ListItemText
                    primary="Cổng Quản trị viên"
                    secondary="Vận hành tài khoản & kiểm toán"
                    slotProps={{
                      primary: { sx: { fontWeight: 800, fontSize: '0.9rem', color: '#0F172A' } },
                      secondary: { sx: { fontSize: '0.75rem', color: '#64748B' } },
                    }}
                  />
                </MenuItem>
              </Menu>

              {showDevTools && (
                <Button
                  component={RouterLink}
                  to="/dev/mobile"
                  startIcon={<DeveloperModeIcon />}
                  color="warning"
                  size="small"
                  sx={{ fontWeight: 700, borderRadius: 2 }}
                >
                  Dev Tools
                </Button>
              )}

              {/* User profile or Login CTA */}
              {user ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  {isStudent && (
                    <Button
                      component={RouterLink}
                      to="/student"
                      variant="contained"
                      color="primary"
                      size="small"
                      startIcon={<SchoolIcon />}
                      sx={{
                        display: { xs: 'none', sm: 'inline-flex' },
                        whiteSpace: 'nowrap',
                        fontWeight: 800,
                        borderRadius: 2.5,
                      }}
                    >
                      Bài học của tôi
                    </Button>
                  )}
                  {isTeacher && (
                    <Button
                      component={RouterLink}
                      to="/teacher-entry"
                      variant="outlined"
                      size="small"
                      startIcon={
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                        </svg>
                      }
                      sx={{ display: { xs: 'none', sm: 'inline-flex' }, whiteSpace: 'nowrap', fontWeight: 800 }}
                    >
                      Vào lớp giảng dạy
                    </Button>
                  )}
                  {isAdmin && (
                    <Button
                      component={RouterLink}
                      to="/admin-entry"
                      variant="outlined"
                      size="small"
                      startIcon={
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="3" />
                          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                        </svg>
                      }
                      sx={{ display: { xs: 'none', sm: 'inline-flex' }, whiteSpace: 'nowrap', fontWeight: 800 }}
                    >
                      Bảng quản trị
                    </Button>
                  )}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.25,
                      bgcolor: '#FFFFFF',
                      border: '1px solid #E2E8F0',
                      px: 1.5,
                      py: 0.6,
                      borderRadius: 2.5,
                      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                    }}
                  >
                    <Avatar
                      sx={{
                        bgcolor: '#2563EB',
                        width: 32,
                        height: 32,
                        fontSize: '0.85rem',
                        fontWeight: 800,
                      }}
                    >
                      {user.displayName ? user.displayName.charAt(0).toUpperCase() : 'U'}
                    </Avatar>
                    <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'left' }}>
                      <Typography
                        variant="subtitle2"
                        sx={{ color: '#0F172A', fontWeight: 800, lineHeight: 1.1, fontSize: '0.84rem' }}
                      >
                        {user.displayName}
                      </Typography>
                      <RoleBadge role={user.role} />
                    </Box>
                    <Tooltip title="Đăng xuất khỏi hệ thống">
                      <IconButton onClick={handleLogout} size="small" aria-label="Đăng xuất" sx={{ ml: 0.5, color: '#64748B', '&:hover': { color: '#EF4444' } }}>
                        <LogoutIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              ) : (
                <Button
                  component={RouterLink}
                  to="/login"
                  variant="contained"
                  color="primary"
                  endIcon={<span aria-hidden="true" style={{ fontSize: '14px', marginLeft: 4 }}>→</span>}
                  sx={{
                    fontWeight: 800,
                    px: { xs: 1.5, sm: 2.75 },
                    minHeight: 44,
                    fontSize: { xs: '0.85rem', sm: '0.95rem' },
                    whiteSpace: 'nowrap',
                    '& .MuiButton-endIcon': { display: { xs: 'none', sm: 'inline-flex' } },
                    borderRadius: 2.5,
                  }}
                >
                  Đăng nhập
                </Button>
              )}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Main Content Area */}
      <Box component="main" id="main-content" sx={{ flexGrow: 1 }}>
        <Outlet />
      </Box>

      {/* Authentic Professional Educational Footer */}
      <Box
        component="footer"
        sx={{
          pt: 7,
          pb: 5,
          px: 2,
          mt: 'auto',
          bgcolor: '#FFFFFF',
          borderTop: '1px solid #E2E8F0',
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 4 } }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '2.2fr 1fr 1fr 1.2fr' },
              gap: { xs: 4, md: 5 },
              mb: 5,
            }}
          >
            {/* Col 1: Brand & Sứ mệnh */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 1.5 }}>
                <Box
                  component="img"
                  src="/ui/mathvision-star.png"
                  alt="Biểu trưng Ngôi sao MathVision Kids"
                  sx={{ width: 36, height: 36 }}
                  onError={(e: any) => {
                    e.currentTarget.src = '/logo.svg';
                  }}
                />
                <Typography variant="h6" sx={{ fontWeight: 900, color: '#0F172A', fontSize: '1.25rem', letterSpacing: '-0.02em' }}>
                  MathVision<span style={{ color: '#2563EB' }}>Kids</span>
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.65, mb: 2.5, pr: { md: 4 } }}>
                Nền tảng học toán số học và gợi mở tư duy trên trang vở ô ly, thiết kế chuyên biệt cho học sinh tiểu học Việt Nam từ Lớp 1 đến Lớp 5, đồng hành cùng thầy cô và phụ huynh.
              </Typography>
              <Chip
                icon={<span aria-hidden="true" style={{ fontSize: '14px' }}>🛡️</span>}
                label="Bảo vệ quyền riêng tư học sinh theo chuẩn giáo dục"
                variant="outlined"
                sx={{
                  bgcolor: '#F8FAFC',
                  borderColor: '#E2E8F0',
                  fontWeight: 700,
                  fontSize: '0.78rem',
                  color: '#334155',
                  borderRadius: 1.5,
                }}
              />
            </Box>

            {/* Col 2: Không gian hệ sinh thái */}
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A', mb: 2, letterSpacing: '0.04em' }}>
                KHÔNG GIAN HỌC TẬP
              </Typography>
              <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'grid', gap: 1.25 }}>
                <li>
                  <Typography
                    component={RouterLink}
                    to="/student"
                    variant="body2"
                    sx={{ color: '#475569', textDecoration: 'none', fontWeight: 600, '&:hover': { color: '#2563EB' } }}
                  >
                    Không gian Học sinh
                  </Typography>
                </li>
                <li>
                  <Typography
                    component={RouterLink}
                    to="/teacher-entry"
                    variant="body2"
                    sx={{ color: '#475569', textDecoration: 'none', fontWeight: 600, '&:hover': { color: '#2563EB' } }}
                  >
                    Cổng Giáo viên (Chấm bài & Lớp)
                  </Typography>
                </li>
                <li>
                  <Typography
                    component={RouterLink}
                    to="/admin-entry"
                    variant="body2"
                    sx={{ color: '#475569', textDecoration: 'none', fontWeight: 600, '&:hover': { color: '#2563EB' } }}
                  >
                    Cổng Quản trị viên (Vận hành & Audit)
                  </Typography>
                </li>
                <li>
                  <Typography
                    component={RouterLink}
                    to="/login"
                    variant="body2"
                    sx={{ color: '#475569', textDecoration: 'none', fontWeight: 600, '&:hover': { color: '#2563EB' } }}
                  >
                    Trang đăng nhập tài khoản
                  </Typography>
                </li>
              </Box>
            </Box>

            {/* Col 3: Năng lực sư phạm */}
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A', mb: 2, letterSpacing: '0.04em' }}>
                NĂNG LỰC SƯ PHẠM
              </Typography>
              <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'grid', gap: 1.25 }}>
                <li>
                  <Typography variant="body2" sx={{ color: '#475569', fontWeight: 600 }}>
                    Nhận diện chữ số & phép tính ô ly
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" sx={{ color: '#475569', fontWeight: 600 }}>
                    Bảo vệ vùng thông tin cá nhân của bé
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" sx={{ color: '#475569', fontWeight: 600 }}>
                    Gợi mở từng bước tính · Không làm hộ
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" sx={{ color: '#475569', fontWeight: 600 }}>
                    Chấm bài theo đợt tự động cho giáo viên
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" sx={{ color: '#475569', fontWeight: 600 }}>
                    Hàng đợi rà soát sư phạm minh bạch
                  </Typography>
                </li>
              </Box>
            </Box>

            {/* Col 4: Cam kết đạo đức AI */}
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A', mb: 2, letterSpacing: '0.04em' }}>
                CAM KẾT GIÁO DỤC
              </Typography>
              <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, mb: 1.5 }}>
                MathVision Kids kiên định nguyên tắc: AI là người bạn đồng hành gợi mở, không giải hộ để bé tự tư duy. Mọi thẩm định sư phạm chính thức luôn thuộc về thầy cô giáo.
              </Typography>
              <Typography variant="caption" sx={{ color: '#94A3B8', display: 'block', fontWeight: 600 }}>
                Hỗ trợ trọn vẹn chương trình Toán Lớp 1 đến Lớp 5.
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ borderColor: '#E2E8F0', mb: 3 }} />

          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
              © 2026 MathVision Kids. Tất cả các quyền được bảo lưu.
            </Typography>
            <Typography variant="caption" sx={{ color: '#94A3B8' }}>
              Nền tảng AI trợ lý toán học tiểu học Việt Nam
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default PortalLayout;
