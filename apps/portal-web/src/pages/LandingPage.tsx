import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
  Paper,
  Grid,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import LoginIcon from '@mui/icons-material/Login';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import LogoutIcon from '@mui/icons-material/Logout';
import { authService, type UserProfile } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const LandingPage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (tokenStore.hasTokens()) {
      authService.getMe().then(setUser).catch(() => setUser(null));
    }
  }, []);

  const getDestinationPath = (role?: string) => {
    const normalized = (role || '').toUpperCase().replace('ROLE_', '');
    if (normalized === 'STUDENT') return '/student';
    if (normalized === 'TEACHER') return '/teacher';
    if (normalized === 'ADMIN') return '/admin';
    return '/login';
  };

  return (
    <Container maxWidth="md">
      {/* Hero Section */}
      <Box sx={{ textAlign: 'center', py: { xs: 5, md: 8 }, maxWidth: 760, mx: 'auto' }}>
        <Box
          component="img"
          src="/logo.svg"
          alt="MathVision Kids"
          sx={{ width: 72, height: 72, mb: 2.5, borderRadius: 3, boxShadow: '0 6px 18px rgba(79, 70, 229, 0.15)' }}
        />

        <Box sx={{ mb: 2 }}>
          <Chip
            label="MathVision Kids — Giáo dục Tiểu học"
            color="primary"
            variant="outlined"
            sx={{ fontWeight: 600, bgcolor: '#EEF2FF', border: '1px solid #C7D2FE' }}
          />
        </Box>

        <Typography
          variant="h2"
          component="h1"
          sx={{
            color: '#0F172A',
            mb: 2,
            fontSize: { xs: '2.1rem', md: '2.9rem' },
            fontWeight: 800,
            letterSpacing: '-0.02em',
            lineHeight: 1.25,
          }}
        >
          Học tập & Chấm bài Số học Viết tay Thông minh
        </Typography>

        <Typography
          variant="h6"
          sx={{
            color: '#475569',
            fontWeight: 400,
            mb: 4.5,
            lineHeight: 1.6,
            fontSize: { xs: '1rem', md: '1.15rem' },
          }}
        >
          Trợ lý học tập và chấm bài viết tay dành cho giáo dục tiểu học. Hỗ trợ học sinh rèn luyện tư duy toán học và đồng hành cùng thầy cô, nhà trường.
        </Typography>

        {user ? (
          <Paper
            sx={{
              p: 3,
              borderRadius: 3.5,
              bgcolor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
              minWidth: 320,
            }}
          >
            <Typography variant="body1" sx={{ color: '#0F172A', fontWeight: 600 }}>
              Xin chào, <strong>{user.displayName}</strong>!
            </Typography>
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Button
                component={RouterLink}
                to={getDestinationPath(user.role)}
                variant="contained"
                color="primary"
                size="large"
                endIcon={<ArrowForwardIcon />}
                sx={{ px: 3.5, py: 1.2, borderRadius: 2.5, fontWeight: 700 }}
              >
                Tiếp tục phiên làm việc
              </Button>
              <Button
                component={RouterLink}
                to="/logout"
                variant="outlined"
                color="inherit"
                startIcon={<LogoutIcon />}
                sx={{ borderRadius: 2.5, color: '#64748B' }}
              >
                Đăng xuất
              </Button>
            </Box>
          </Paper>
        ) : (
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              component={RouterLink}
              to="/login"
              variant="contained"
              color="primary"
              size="large"
              startIcon={<LoginIcon />}
              sx={{
                px: 5,
                py: 1.6,
                fontSize: '1.1rem',
                borderRadius: 3,
                fontWeight: 700,
                boxShadow: '0 8px 24px rgba(79, 70, 229, 0.25)',
                '&:hover': {
                  bgcolor: '#4338CA',
                  boxShadow: '0 10px 28px rgba(79, 70, 229, 0.35)',
                },
              }}
            >
              Đăng nhập
            </Button>
          </Box>
        )}
      </Box>

      {/* Product Highlights — Educational, No Role Pickers */}
      <Grid container spacing={3} sx={{ mb: 8 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              height: '100%',
              borderRadius: 3.5,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              textAlign: 'center',
            }}
          >
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2.5,
                bgcolor: '#EEF2FF',
                color: '#4F46E5',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1.5,
              }}
            >
              <AutoAwesomeIcon sx={{ fontSize: 24 }} />
            </Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
              Chấm bài nhanh chóng
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
              Nhận diện chữ số và phép tính viết tay từ trang vở, hỗ trợ phát hiện kết quả tức thì.
            </Typography>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              height: '100%',
              borderRadius: 3.5,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              textAlign: 'center',
            }}
          >
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2.5,
                bgcolor: '#ECFDF5',
                color: '#059669',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1.5,
              }}
            >
              <MenuBookIcon sx={{ fontSize: 24 }} />
            </Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
              Hướng dẫn từng bước
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
              Giải thích phép tính rõ ràng, thân thiện với học sinh từ lớp 1 đến lớp 5.
            </Typography>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 4 }}>
          <Paper
            elevation={0}
            sx={{
              p: 3,
              height: '100%',
              borderRadius: 3.5,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              textAlign: 'center',
            }}
          >
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2.5,
                bgcolor: '#FEF3C7',
                color: '#D97706',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                mb: 1.5,
              }}
            >
              <TrendingUpIcon sx={{ fontSize: 24 }} />
            </Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
              Tự tin tiến bộ
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
              Giúp các em yêu thích môn Toán và hỗ trợ giáo viên theo dõi tiến trình học tập.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default LandingPage;
