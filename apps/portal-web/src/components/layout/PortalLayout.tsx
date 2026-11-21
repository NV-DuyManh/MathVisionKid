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
  Divider,
} from '@mui/material';
import { Outlet, Link as RouterLink, useNavigate, useLocation } from 'react-router-dom';
import LogoutIcon from '@mui/icons-material/Logout';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { RoleBadge } from '../common/RoleBadge';
import { authService, type UserProfile } from '../../services/authService';
import { tokenStore } from '../../services/apiClient';
import { showDevTools } from '../../config/runtime';

export const PortalLayout: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: '#FFFFFF' }}>
      <a href="#main-content" className="skip-link">
        Đến nội dung chính
      </a>

      {/* Top Banner / Announcement — Kid Safety & Pedagogical Standard (Only for non-landing pages) */}
      {!isLandingPage && (
        <Box
          sx={{
            display: { xs: 'none', md: 'block' },
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
      )}

      {/* Main Navbar */}
      <AppBar
        position="sticky"
        elevation={0}
        sx={{
          bgcolor: '#FFFFFF',
          borderBottom: '1px solid',
          borderColor: '#D5C7F8',
          zIndex: 1100,
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 5 } }}>
          <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: { xs: 64, sm: 72 }, gap: 1 }}>
            {/* Brand Logo & Name */}
            <Box
              component={RouterLink}
              to="/"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.25,
                minWidth: 0,
                textDecoration: 'none',
                transition: 'transform 160ms ease',
                '&:hover': { transform: 'scale(1.02)' },
              }}
            >
              <Box
                sx={{
                  width: { xs: 34, sm: 38 },
                  height: { xs: 34, sm: 38 },
                  borderRadius: '50%',
                  bgcolor: '#EDE9FE',
                  border: '1px solid #DDD6FE',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                }}
              >
                🪐
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    color: '#190568',
                    fontWeight: 900,
                    lineHeight: 1.15,
                    fontSize: { xs: '1.2rem', sm: '1.35rem' },
                    letterSpacing: '-0.02em',
                  }}
                >
                  MathVisionKid
                </Typography>
                {!isLandingPage && (
                  <Typography
                    variant="caption"
                    sx={{ color: '#64748B', display: { xs: 'none', sm: 'block' }, fontWeight: 700, fontSize: '0.75rem' }}
                  >
                    Trợ lý số học viết tay & gia sư thông minh
                  </Typography>
                )}
              </Box>
            </Box>

            {/* In-page navigation (matching Figma 2:3) */}
            {isLandingPage && (
              <Box
                sx={{
                  display: { xs: 'none', md: 'flex' },
                  alignItems: 'center',
                  gap: 3.5,
                }}
              >
                <Box sx={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Box
                    component="a"
                    href="#"
                    sx={{
                      color: '#190568',
                      fontWeight: 800,
                      fontSize: '0.92rem',
                      textDecoration: 'none',
                      pb: 0.6,
                    }}
                  >
                    Trang chủ
                  </Box>
                  <Box sx={{ width: 57, height: 3, bgcolor: '#E6D5FF', borderRadius: '2px' }} />
                </Box>
                <Box
                  component="a"
                  href="#lo-trinh"
                  sx={{
                    color: '#190568',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6500EF' },
                  }}
                >
                  Lộ trình
                </Box>
                <Box
                  component="a"
                  href="#tinh-nang"
                  sx={{
                    color: '#190568',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6500EF' },
                  }}
                >
                  Tính năng
                </Box>
                <Box
                  component="a"
                  href="#giai-dap"
                  sx={{
                    color: '#190568',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6500EF' },
                  }}
                >
                  Giải đáp
                </Box>
              </Box>
            )}

            {/* Right Action & Auth Area */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
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

              {/* User profile or Vào lớp học CTA */}
              {user ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Button
                    component={RouterLink}
                    to={isStudent ? '/student' : isTeacher ? '/teacher-entry' : '/admin-entry'}
                    variant="contained"
                    sx={{
                      bgcolor: '#F5EFFF',
                      '&:hover': { bgcolor: '#E1D2FF' },
                      color: '#190568',
                      border: '1px solid #E1D2FF',
                      fontWeight: 800,
                      px: { xs: 2.25, sm: 2.85 },
                      minHeight: 37,
                      borderRadius: '20px',
                      textTransform: 'none',
                      whiteSpace: 'nowrap',
                      fontSize: '0.92rem',
                    }}
                  >
                    Vào lớp học →
                  </Button>
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
                        bgcolor: '#6D28D9',
                        width: 30,
                        height: 30,
                        fontSize: '0.82rem',
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
                  sx={{
                    bgcolor: '#F5EFFF',
                    '&:hover': { bgcolor: '#E1D2FF' },
                    color: '#190568',
                    border: '1px solid #E1D2FF',
                    fontWeight: 800,
                    px: { xs: 2.25, sm: 3 },
                    py: 0.85,
                    minHeight: 37,
                    borderRadius: '20px',
                    textTransform: 'none',
                    fontSize: '0.92rem',
                    whiteSpace: 'nowrap',
                    transition: 'all 160ms ease',
                    '&:active': { transform: 'scale(0.98)' },
                  }}
                >
                  Vào lớp học →
                </Button>
              )}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Main Content Area */}
      <Box component="main" id="main-content" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </Box>

      {/* Default Footer for non-landing pages */}
      {!isLandingPage && (
        <Box
          component="footer"
          sx={{
            py: 4,
            px: 2,
            mt: 'auto',
            bgcolor: 'background.paper',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Container maxWidth="xl">
            <Typography variant="body2" color="text.secondary" align="center">
              © {new Date().getFullYear()} MathVisionKid — Nền tảng học toán tương tác cho học sinh tiểu học Việt Nam
            </Typography>
            <Divider sx={{ my: 1.5, opacity: 0.6 }} />
            <Typography variant="caption" color="text.secondary" align="center" sx={{ display: 'block' }}>
              Chuẩn chương trình Giáo dục Phổ thông 2018 • Cam kết bảo mật & quyền riêng tư học sinh
            </Typography>
          </Container>
        </Box>
      )}
    </Box>
  );
};

export default PortalLayout;
