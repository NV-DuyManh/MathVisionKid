import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SmartphoneIcon from '@mui/icons-material/Smartphone';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import LogoutIcon from '@mui/icons-material/Logout';
import LoginIcon from '@mui/icons-material/Login';
import { RoleBadge } from '../components/common/RoleBadge';
import { authService, type UserProfile } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const StudentLandingPage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (tokenStore.hasTokens()) {
      authService.getMe().then(setUser).catch(() => setUser(null));
    }
  }, []);

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 3 }}>
        <Button
          component={RouterLink}
          to="/"
          startIcon={<ArrowBackIcon />}
          sx={{ color: '#64748B', fontWeight: 600 }}
        >
          Về màn hình chính
        </Button>
      </Box>

      {/* Main Student Card */}
      <Paper
        sx={{
          p: { xs: 3, sm: 5 },
          borderRadius: 5,
          boxShadow: '0 10px 30px rgba(79, 70, 229, 0.08)',
          border: '1px solid #E0E7FF',
          bgcolor: '#FFFFFF',
          mb: 4,
        }}
      >
        {/* Welcome Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 2,
            mb: 4,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2.5 }}>
            <Box
              sx={{
                width: 64,
                height: 64,
                borderRadius: 4,
                bgcolor: '#EEF2FF',
                color: '#4F46E5',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(79, 70, 229, 0.15)',
              }}
            >
              <SmartphoneIcon sx={{ fontSize: 36 }} />
            </Box>
            <Box>
              <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                {user ? `Chào mừng em, ${user.displayName}!` : 'MathVision Kids dành cho Học sinh'}
              </Typography>
              <Typography variant="body1" sx={{ color: '#475569', fontWeight: 500 }}>
                Chụp bài viết tay, xem kết quả và nhận hướng dẫn từng bước.
              </Typography>
            </Box>
          </Box>
          <RoleBadge role={user?.role || 'STUDENT'} size="medium" />
        </Box>

        {/* Truthful Product Bridge Card */}
        <Card
          sx={{
            mb: 4,
            borderRadius: 4,
            bgcolor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            p: { xs: 2.5, sm: 3.5 },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2.5 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 3,
                bgcolor: '#EEF2FF',
                color: '#4F46E5',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                mt: 0.5,
              }}
            >
              <SmartphoneIcon sx={{ fontSize: 26 }} />
            </Box>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" sx={{ color: '#0F172A', fontWeight: 700, mb: 0.75 }}>
                MathVision Kids dành cho học sinh được sử dụng trên điện thoại hoặc máy tính bảng.
              </Typography>
              <Typography variant="body1" sx={{ color: '#475569', lineHeight: 1.6, mb: 2.5 }}>
                Để chụp ảnh và chấm bài tập số học trực tiếp từ vở ô ly, em hãy mở ứng dụng MathVision Kids trên điện thoại hoặc máy tính bảng.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                {user ? (
                  <Button
                    component={RouterLink}
                    to="/logout"
                    variant="outlined"
                    startIcon={<LogoutIcon />}
                    sx={{ borderRadius: 3, px: 3, py: 1, fontWeight: 600, color: '#64748B' }}
                  >
                    Đăng xuất
                  </Button>
                ) : (
                  <Button
                    component={RouterLink}
                    to="/login"
                    variant="contained"
                    color="primary"
                    startIcon={<LoginIcon />}
                    sx={{ borderRadius: 3, px: 3, py: 1, fontWeight: 700 }}
                  >
                    Đăng nhập
                  </Button>
                )}
              </Box>
            </Box>
          </Box>
        </Card>

        {/* 3 Steps Guide */}
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A', mb: 2.5 }}>
          3 bước học toán thật vui cùng MathVision Kids
        </Typography>

        <Grid container spacing={2.5}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%', borderRadius: 3.5, border: '1px solid #E2E8F0', boxShadow: 'none', bgcolor: '#F8FAFC' }}>
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2.5,
                    bgcolor: '#EEF2FF',
                    color: '#4F46E5',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <PhotoCameraIcon />
                </Box>
                <Chip label="Bước 1" size="small" sx={{ fontWeight: 700, bgcolor: '#EEF2FF', color: '#4F46E5', mb: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
                  Chụp ảnh bài toán
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
                  Đặt vở bài tập ngay ngắn, đủ ánh sáng và chụp lại phép tính số học trên trang vở của em.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%', borderRadius: 3.5, border: '1px solid #E2E8F0', boxShadow: 'none', bgcolor: '#F8FAFC' }}>
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2.5,
                    bgcolor: '#ECFDF5',
                    color: '#059669',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <AutoAwesomeIcon />
                </Box>
                <Chip label="Bước 2" size="small" sx={{ fontWeight: 700, bgcolor: '#ECFDF5', color: '#059669', mb: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
                  Nhận hướng dẫn ngay
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
                  Hệ thống tự động chấm điểm và chỉ dẫn từng bước giải bài dễ hiểu, phù hợp với lứa tuổi tiểu học.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Card sx={{ height: '100%', borderRadius: 3.5, border: '1px solid #E2E8F0', boxShadow: 'none', bgcolor: '#F8FAFC' }}>
              <CardContent sx={{ p: 3 }}>
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2.5,
                    bgcolor: '#FFFBEB',
                    color: '#D97706',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <EmojiEventsIcon />
                </Box>
                <Chip label="Bước 3" size="small" sx={{ fontWeight: 700, bgcolor: '#FFFBEB', color: '#D97706', mb: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 1 }}>
                  Tự tin tiến bộ
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.6 }}>
                  Xem lại điểm số, nhận lời động viên và tiến bộ trong môn Toán qua từng ngày rèn luyện.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default StudentLandingPage;
