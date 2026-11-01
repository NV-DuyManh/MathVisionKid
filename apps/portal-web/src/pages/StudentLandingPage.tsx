import React, { useEffect } from 'react';
import { Box, CircularProgress, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const StudentLandingPage: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    authService.getMe().then(user => {
      if (!active) return;
      if (user.role.toUpperCase().replace('ROLE_', '') === 'STUDENT' && user.active !== false) {
        window.location.replace('/study/');
      } else {
        navigate('/access-denied', { replace: true });
      }
    }).catch(() => {
      if (active) {
        tokenStore.clearTokens();
        navigate('/session-expired', { replace: true });
      }
    });
    return () => { active = false; };
  }, [navigate]);

  return (
    <Box
      sx={{
        textAlign: 'center',
        py: { xs: 8, md: 12 },
        px: 3,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
      }}
    >
      <Box
        component="img"
        src="/ui/mathvision-star.png"
        alt="Ngôi sao MathVision"
        className="star-companion-float"
        sx={{ width: 88, height: 88, mb: 3, objectFit: 'contain' }}
        onError={(e: any) => { e.currentTarget.style.display = 'none'; }}
      />
      <Typography variant="h4" sx={{ fontWeight: 900, color: '#0F172A', mb: 1 }}>
        Đang mở bàn học cho em… ⭐
      </Typography>
      <Typography variant="body1" sx={{ color: '#475569', mb: 3, maxWidth: 440 }}>
        Chờ bạn Ngôi sao MathVision chuẩn bị trang vở và thước kẻ một chút nhé!
      </Typography>
      <CircularProgress size={36} sx={{ color: '#2563EB', mb: 3 }} />
      <Button
        component="a"
        href="/study/"
        variant="outlined"
        color="primary"
        sx={{
          borderRadius: 2.5,
          fontWeight: 800,
          px: 3,
          borderColor: '#BFDBFE',
          color: '#1D4ED8',
          bgcolor: '#EFF6FF',
          '&:hover': { bgcolor: '#DBEAFE', borderColor: '#2563EB' },
        }}
      >
        Vào bàn học ngay 🚀
      </Button>
    </Box>
  );
};

export default StudentLandingPage;
