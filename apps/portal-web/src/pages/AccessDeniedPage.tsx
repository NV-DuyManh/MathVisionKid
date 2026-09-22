import React from 'react';
import { Container, Paper, Box, Typography, Button, Alert } from '@mui/material';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import BlockIcon from '@mui/icons-material/Block';
import HomeIcon from '@mui/icons-material/Home';
import LoginIcon from '@mui/icons-material/Login';

export const AccessDeniedPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const target = searchParams.get('target') || 'tài nguyên được yêu cầu';
  const current = searchParams.get('current') || 'hiện tại';

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 3, sm: 5 }, textAlign: 'center', borderRadius: 4 }}>
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: '#FEE2E2',
            color: '#DC2626',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          <BlockIcon sx={{ fontSize: 36 }} />
        </Box>

        <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 1 }}>
          Truy cập bị từ chối
        </Typography>

        <Alert severity="warning" sx={{ my: 3, textAlign: 'left', borderRadius: 2 }}>
          Tài khoản của bạn (vai trò <strong>{current}</strong>) không có quyền truy cập vào <strong>{target}</strong>. Hệ thống phân quyền nghiêm ngặt của MathVision Kids bảo vệ dữ liệu giữa Học sinh, Giáo viên và Quản trị viên.
        </Alert>

        <Typography variant="body2" sx={{ color: '#64748B', mb: 4 }}>
          Nếu bạn cần truy cập tài nguyên này, vui lòng đăng nhập bằng tài khoản có vai trò phù hợp.
        </Typography>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Button
            component={RouterLink}
            to="/"
            variant="outlined"
            startIcon={<HomeIcon />}
          >
            Về Trang chủ
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
