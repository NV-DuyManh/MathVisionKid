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
} from '@mui/material';
import { Outlet, Link as RouterLink, useNavigate } from 'react-router-dom';
import LogoutIcon from '@mui/icons-material/Logout';
import SchoolIcon from '@mui/icons-material/School';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { RoleBadge } from '../common/RoleBadge';
import { authService, type UserProfile } from '../../services/authService';
import { tokenStore } from '../../services/apiClient';

export const PortalLayout: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const navigate = useNavigate();
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';

  useEffect(() => {
    if (tokenStore.hasTokens()) {
      authService.getMe().then(setUser).catch(() => {
        tokenStore.clearTokens();
        setUser(null);
      });
    }
  }, []);

  const handleLogout = () => {
    navigate('/logout');
  };

  const isStudent = user && (user.role || '').toUpperCase().replace('ROLE_', '') === 'STUDENT';

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="sticky" elevation={0} sx={{ bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ justifyContent: 'space-between', height: 70 }}>
            {/* Brand Logo & Name */}
            <Box
              component={RouterLink}
              to="/"
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                textDecoration: 'none',
              }}
            >
              <Box
                component="img"
                src="/logo.svg"
                alt="MathVision Kids"
                sx={{ width: 38, height: 38, borderRadius: 2 }}
              />
              <Box>
                <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 800, lineHeight: 1.2 }}>
                  MathVision Kids
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', fontWeight: 500 }}>
                  Trợ lý học tập và chấm bài viết tay
                </Typography>
              </Box>
            </Box>

            {/* Authenticated Student or Dev Navigation */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {isStudent && (
                <Button
                  component={RouterLink}
                  to="/student"
                  startIcon={<SchoolIcon />}
                  sx={{ color: '#475569', fontWeight: 600, '&:hover': { bgcolor: '#F1F5F9', color: '#0F172A' } }}
                >
                  Không gian Học sinh
                </Button>
              )}
              {showDevTools && (
                <Button
                  component={RouterLink}
                  to="/dev/mobile"
                  startIcon={<DeveloperModeIcon />}
                  color="warning"
                  sx={{ fontWeight: 600 }}
                >
                  Dev Tools
                </Button>
              )}
            </Box>

            {/* Auth State & Action */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {user && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Avatar sx={{ bgcolor: '#4F46E5', width: 36, height: 36, fontSize: '0.9rem', fontWeight: 700 }}>
                    {user.displayName ? user.displayName.charAt(0).toUpperCase() : 'U'}
                  </Avatar>
                  <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                    <Typography variant="subtitle2" sx={{ color: '#0F172A', fontWeight: 700, lineHeight: 1.2 }}>
                      {user.displayName}
                    </Typography>
                    <RoleBadge role={user.role} />
                  </Box>
                  <Tooltip title="Đăng xuất khỏi hệ thống">
                    <IconButton onClick={handleLogout} color="default" sx={{ ml: 0.5 }}>
                      <LogoutIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              )}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Main Content Area */}
      <Box component="main" sx={{ flexGrow: 1, py: { xs: 3, md: 5 } }}>
        <Outlet />
      </Box>

      {/* Product-Facing Professional Educational Footer */}
      <Box
        component="footer"
        sx={{
          py: 3.5,
          px: 2,
          mt: 'auto',
          bgcolor: '#FFFFFF',
          borderTop: '1px solid #E2E8F0',
          textAlign: 'center',
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.75 }}>
            <Typography variant="body2" sx={{ color: '#334155', fontWeight: 600 }}>
              © 2026 MathVision Kids — Trợ lý học tập và chấm bài viết tay cho giáo dục tiểu học
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Phiên bản thử nghiệm (v1.0)
            </Typography>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default PortalLayout;
