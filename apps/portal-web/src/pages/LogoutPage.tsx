import React, { useEffect, useState } from 'react';
import { Container, Paper, Box, Typography, Button, Alert, CircularProgress } from '@mui/material';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LoginIcon from '@mui/icons-material/Login';
import HomeIcon from '@mui/icons-material/Home';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const LogoutPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const source = searchParams.get('source');
  const [cleared, setCleared] = useState(false);

  let sourceTitle = 'hệ thống MathVision Kids';
  if (source === 'teacher') {
    sourceTitle = 'Không gian Giáo viên';
  } else if (source === 'admin') {
    sourceTitle = 'Không gian Quản trị viên';
  }

  useEffect(() => {
    const performUnifiedLogout = async () => {
      try {
        if (tokenStore.hasTokens()) {
          await authService.logout();
        }
      } catch {
        // Ignore network errors on logout to ensure local cleanup
      } finally {
        tokenStore.clearTokens();
        setCleared(true);
      }
    };

    performUnifiedLogout();
  }, []);

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 3, sm: 5 }, textAlign: 'center', borderRadius: 4 }}>
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: '#ECFDF5',
            color: '#059669',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          {cleared ? (
            <CheckCircleIcon sx={{ fontSize: 36 }} />
          ) : (
            <CircularProgress size={32} sx={{ color: '#059669' }} />
          )}
        </Box>

        <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 1 }}>
          Đăng xuất thành công
        </Typography>

        <Alert severity="success" sx={{ my: 3, textAlign: 'left', borderRadius: 2 }}>
          Bạn đã đăng xuất an toàn khỏi <strong>{sourceTitle}</strong> và Cổng chung MathVision Kids. Toàn bộ mã xác thực và phiên làm việc cục bộ đã được xóa sạch.
        </Alert>

        <Typography variant="body2" sx={{ color: '#64748B', mb: 4 }}>
          Cảm ơn bạn đã sử dụng nền tảng MathVision Kids. Bạn có thể quay về Trang chủ hoặc đăng nhập lại bằng tài khoản khác.
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            component={RouterLink}
            to="/"
            variant="outlined"
            startIcon={<HomeIcon />}
          >
            Trang chủ
          </Button>
          <Button
            component={RouterLink}
            to="/login"
            variant="contained"
            color="primary"
            startIcon={<LoginIcon />}
          >
            Đăng nhập lại
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};
