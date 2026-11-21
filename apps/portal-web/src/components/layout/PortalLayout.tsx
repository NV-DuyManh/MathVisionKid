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
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
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
          bgcolor: 'background.paper',
          borderBottom: '1px solid',
          borderColor: 'divider',
          zIndex: 1100,
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
                gap: { xs: 0.75, sm: 1.25 },
                minWidth: 0,
                textDecoration: 'none',
                transition: 'transform 160ms ease, opacity 160ms ease',
                '&:hover': { transform: 'scale(1.02)' },
                '&:active': { transform: 'scale(0.98)' },
                '@media (prefers-reduced-motion: reduce)': { transition: 'none', '&:hover, &:active': { transform: 'none' } },
              }}
            >
              <Box
                sx={{
                  width: { xs: 32, sm: 38 },
                  height: { xs: 32, sm: 38 },
                  borderRadius: '50%',
                  bgcolor: '#EDE9FE',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  boxShadow: '0 2px 6px rgba(109, 40, 217, 0.15)',
                }}
              >
                🪐
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    color: '#1E1B4B',
                    fontWeight: 900,
                    lineHeight: 1.15,
                    fontSize: { xs: '1.1rem', sm: '1.35rem' },
                    letterSpacing: '-0.025em',
                  }}
                >
                  MathVisionKid
                </Typography>
                {!isLandingPage && (
                  <Typography
                    variant="caption"
                    sx={{ color: '#64748B', display: { xs: 'none', sm: 'block' }, fontWeight: 700, fontSize: '0.75rem', letterSpacing: '-0.01em' }}
                  >
                    Trợ lý số học viết tay & gia sư thông minh
                  </Typography>
                )}
              </Box>
            </Box>

            {/* In-page navigation (matching Image 1) */}
            {isLandingPage && (
              <Box
                sx={{
                  display: { xs: 'none', md: 'flex' },
                  alignItems: 'center',
                  gap: 3,
                }}
              >
                <Box
                  component="a"
                  href="#"
                  sx={{
                    color: '#6D28D9',
                    fontWeight: 800,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    borderBottom: '2.5px solid #6D28D9',
                  }}
                >
                  Trang chủ
                </Box>
                <Box
                  component="a"
                  href="#lo-trinh"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6D28D9' },
                  }}
                >
                  Lộ trình
                </Box>
                <Box
                  component="a"
                  href="#tinh-nang"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6D28D9' },
                  }}
                >
                  Tính năng
                </Box>
                <Box
                  component="a"
                  href="#giai-dap"
                  sx={{
                    color: '#475569',
                    fontWeight: 700,
                    fontSize: '0.92rem',
                    textDecoration: 'none',
                    py: 1,
                    transition: 'color 160ms ease',
                    '&:hover': { color: '#6D28D9' },
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
                      bgcolor: '#5B21B6',
                      '&:hover': { bgcolor: '#4C1D95' },
                      color: '#FFFFFF',
                      fontWeight: 800,
                      px: { xs: 2, sm: 2.75 },
                      minHeight: 40,
                      borderRadius: '9999px',
                      textTransform: 'none',
                      whiteSpace: 'nowrap',
                      boxShadow: '0 4px 12px rgba(91, 33, 182, 0.25)',
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
                        bgcolor: '#5B21B6',
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
                  variant="contained"
                  sx={{
                    bgcolor: '#5B21B6',
                    '&:hover': { bgcolor: '#4C1D95' },
                    color: '#FFFFFF',
                    fontWeight: 800,
                    px: { xs: 2.25, sm: 3 },
                    py: 1,
                    minHeight: 40,
                    borderRadius: '9999px',
                    textTransform: 'none',
                    fontSize: '0.92rem',
                    whiteSpace: 'nowrap',
                    boxShadow: '0 4px 14px rgba(91, 33, 182, 0.3)',
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
      <Box component="main" id="main-content" tabIndex={-1} sx={{ flexGrow: 1, scrollMarginTop: 76 }}>
        <Outlet />
      </Box>

      {/* Authentic Professional Educational Footer (Only on non-landing pages) */}
      {!isLandingPage && (
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
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '2fr 1fr 1fr' },
              gap: { xs: 4, md: 5 },
              mb: 5,
            }}
          >
            {/* Col 1: Brand & Sứ mệnh */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 1.5 }}>
                <Box
                  component="img"
                  src="/ui/robot-mascot.webp"
                  alt="Robot MathVisionKid"
                  sx={{ width: 36, height: 36 }}
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

            {/* Năng lực sư phạm */}
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

            {/* Cam kết đạo đức AI */}
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
      )}
    </Box>
  );
};

export default PortalLayout;
