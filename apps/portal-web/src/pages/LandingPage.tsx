import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
  Grid,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import GoogleIcon from '@mui/icons-material/Google';
import FacebookIcon from '@mui/icons-material/Facebook';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import HighlightOffOutlinedIcon from '@mui/icons-material/HighlightOffOutlined';
import { authService, type UserProfile } from '../services/authService';
import { tokenStore } from '../services/apiClient';

interface GradeDemoData {
  gradeLabel: string;
  className: string;
  studentName: string;
  row1: string[];
  row2: string[];
  operator: string;
  resultRow: string[];
  activeCol: number;
  errorCol?: number;
  speechText: string;
  answerText: string;
  replyResponse: string;
}

const GRADE_DATA: Record<number, GradeDemoData> = {
  1: {
    gradeLabel: 'Lớp 1',
    className: 'Lớp 1A',
    studentName: 'Nguyễn B***',
    row1: ['3', '5'],
    row2: ['2', '4'],
    operator: '+',
    resultRow: ['5', '9'],
    activeCol: 1,
    speechText: 'Chào con! Cô thấy con viết 35 + 24. Mình cùng tính nhé. Bắt đầu từ cột đơn vị: 5 + 4 bằng mấy?',
    answerText: 'Con trả lời: 5 + 4 = 9',
    replyResponse: 'Chính xác! Con viết 9 vào cột đơn vị, rồi tính tiếp 3 + 2 = 5 ở cột chục nhé!',
  },
  2: {
    gradeLabel: 'Lớp 2',
    className: 'Lớp 2B',
    studentName: 'Nguyễn B***',
    row1: ['4', '8'],
    row2: ['3', '5'],
    operator: '+',
    resultRow: ['8', '3'],
    activeCol: 1,
    speechText: 'Chào con! Cô thấy con viết 48 + 35. Mình cùng kiểm tra nhé: 8 + 5 = 13, con viết 3 và nhớ mấy sang hàng chục?',
    answerText: 'Con trả lời: Viết 3 nhớ 1',
    replyResponse: 'Giỏi lắm! Con nhớ 1 sang hàng chục: 4 + 3 = 7, thêm 1 nhớ là 8. Kết quả bằng 83!',
  },
  3: {
    gradeLabel: 'Lớp 3',
    className: 'Lớp 3A',
    studentName: 'Nguyễn B***',
    row1: ['2', '4', '5'],
    row2: ['1', '7', '8'],
    operator: '+',
    resultRow: ['4', '1', '3'],
    activeCol: 1,
    errorCol: 1,
    speechText: 'Chào con! Cô thấy con viết 245 + 178 = 413. Mình cùng kiểm tra từng cột nhé. Bắt đầu từ cột đơn vị: 5 + 8 bằng mấy?',
    answerText: 'Con trả lời: 5 + 8 = 13',
    replyResponse: 'Đúng rồi! 5 + 8 = 13, viết 3 nhớ 1. Ở hàng chục: 4 + 7 = 11, thêm 1 nhớ bằng mấy nhỉ?',
  },
  4: {
    gradeLabel: 'Lớp 4',
    className: 'Lớp 4C',
    studentName: 'Nguyễn B***',
    row1: ['1', '2', '5'],
    row2: ['', '', '4'],
    operator: '×',
    resultRow: ['5', '0', '0'],
    activeCol: 2,
    speechText: 'Chào con! Cô thấy con tính 125 × 4. Mình cùng nhân từ hàng đơn vị nhé: 4 × 5 bằng mấy?',
    answerText: 'Con trả lời: 4 × 5 = 20',
    replyResponse: 'Tuyệt vời! Viết 0 nhớ 2. Tiếp theo: 4 × 2 = 8, thêm 2 nhớ là 10, viết 0 nhớ 1 nhé!',
  },
  5: {
    gradeLabel: 'Lớp 5',
    className: 'Lớp 5A',
    studentName: 'Nguyễn B***',
    row1: ['3', '5', ',', '4'],
    row2: ['1', '8', ',', '7'],
    operator: '+',
    resultRow: ['5', '4', ',', '1'],
    activeCol: 3,
    speechText: 'Chào con! Cô thấy con đặt tính số thập phân 35,4 + 18,7. Mình cùng kiểm tra phần thập phân trước: 4 + 7 bằng mấy?',
    answerText: 'Con trả lời: 4 + 7 = 11',
    replyResponse: 'Rất đúng! Viết 1 nhớ 1 qua hàng đơn vị và hạ dấu phẩy thẳng cột con nhé!',
  },
};

const GRADE_COLORS: Record<number, { bg: string; hover: string; text: string }> = {
  1: { bg: '#EF4444', hover: '#DC2626', text: '#FFFFFF' },
  2: { bg: '#F59E0B', hover: '#D97706', text: '#1E1B4B' },
  3: { bg: '#10B981', hover: '#059669', text: '#FFFFFF' },
  4: { bg: '#06B6D4', hover: '#0891B2', text: '#FFFFFF' },
  5: { bg: '#6366F1', hover: '#4F46E5', text: '#FFFFFF' },
};

export const LandingPage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [selectedGrade, setSelectedGrade] = useState<number>(3);
  const [answeredSpeech, setAnsweredSpeech] = useState<boolean>(false);

  useEffect(() => {
    if (tokenStore.hasTokens()) {
      authService.getMe().then(setUser).catch(() => setUser(null));
    }
  }, []);

  const getDestinationPath = (role?: string) => {
    const normalized = (role || '').toUpperCase().replace('ROLE_', '');
    if (normalized === 'STUDENT') return '/student';
    if (normalized === 'TEACHER') return '/teacher-entry';
    if (normalized === 'ADMIN') return '/admin-entry';
    return '/login';
  };

  const handleSelectGrade = (grade: number) => {
    setSelectedGrade(grade);
    setAnsweredSpeech(false);
  };

  const currentDemo = GRADE_DATA[selectedGrade] || GRADE_DATA[3];

  return (
    <Box
      component="main"
      id="main-content"
      sx={{
        width: '100%',
        bgcolor: '#FFFFFF',
        color: '#1E1B4B',
        overflowX: 'clip',
        '@keyframes floatSlow': {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(-8px) rotate(3deg)' },
        },
        '@keyframes floatReverse': {
          '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
          '50%': { transform: 'translateY(8px) rotate(-3deg)' },
        },
        '@keyframes floatGentle': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        '@media (prefers-reduced-motion: reduce)': {
          '*': {
            animationDuration: '0.01ms !important',
            animationIterationCount: '1 !important',
            transitionDuration: '0.01ms !important',
          },
        },
      }}
    >
      {/* ========================================================================= */}
      {/* 1. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <Box
        sx={{
          pt: { xs: 5, md: 8 },
          pb: { xs: 6, md: 8 },
          background: `
            radial-gradient(circle at 6% 92%, rgba(254, 240, 138, 0.65) 0%, rgba(254, 240, 138, 0.22) 32%, transparent 58%),
            radial-gradient(circle at 94% 8%, rgba(221, 214, 254, 0.75) 0%, rgba(237, 233, 254, 0.3) 36%, transparent 62%),
            linear-gradient(135deg, #F8FAFC 0%, #FAF8FF 45%, #F5F3FF 100%)
          `,
          borderBottom: '1px solid #F1F0FB',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Grid container spacing={{ xs: 4, lg: 6 }} sx={{ alignItems: 'center' }}>
            {/* Left Hero Narrative */}
            <Grid size={{ xs: 12, lg: 6 }}>
              <Box sx={{ maxWidth: 620 }}>
                {/* Badge: Mới Gia sư gợi mở cho học sinh lớp 1 đến lớp 5 */}
                <Box
                  sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 1.5,
                    px: 2.2,
                    py: 1,
                    mb: 3,
                    borderRadius: 999,
                    bgcolor: '#FFFBEB',
                    border: '1.5px solid #FDE68A',
                  }}
                >
                  <Chip
                    label="Mới"
                    size="small"
                    sx={{
                      height: 28,
                      fontSize: '0.9rem',
                      fontWeight: 900,
                      bgcolor: '#F59E0B',
                      color: '#FFFFFF',
                      borderRadius: 999,
                      px: 0.5,
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#92400E', fontWeight: 800, fontSize: '1.08rem' }}>
                    Gia sư gợi mở cho học sinh lớp 1 đến lớp 5
                  </Typography>
                </Box>

                {/* H1 Heading with rotated yellow badge on "từng bước" */}
                <Typography
                  variant="h1"
                  sx={{
                    fontSize: { xs: '2.9rem', sm: '3.8rem', lg: '4.4rem' },
                    fontWeight: 900,
                    lineHeight: 1.18,
                    letterSpacing: '-0.035em',
                    color: '#1E1B4B',
                    mb: 3,
                  }}
                >
                  Mở vở ô ly, học<br />
                  toán{' '}
                  <Box
                    component="span"
                    sx={{
                      display: 'inline-block',
                      bgcolor: '#FDE047',
                      color: '#1E1B4B',
                      px: { xs: 2.2, sm: 2.8 },
                      py: 0.5,
                      borderRadius: 3.5,
                      boxShadow: '0 4px 14px rgba(253, 224, 71, 0.45)',
                      mx: 0.5,
                    }}
                  >
                    từng bước
                  </Box>
                </Typography>

                {/* Subtitle */}
                <Typography
                  variant="body1"
                  sx={{
                    color: '#475569',
                    fontSize: { xs: '1.22rem', md: '1.35rem' },
                    lineHeight: 1.75,
                    mb: 4.5,
                  }}
                >
                  Chụp bài toán viết tay và cùng robot MathVisionKids tìm ra lời giải qua từng câu hỏi gợi mở. Bé tự nghĩ, tự làm, tự tin hơn mỗi ngày.
                </Typography>

                {/* Action Buttons */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1.5, sm: 2.5 }, flexWrap: 'wrap', mb: 5 }}>
                  <Button
                    component={RouterLink}
                    to={user ? getDestinationPath(user.role) : '/login'}
                    variant="contained"
                    size="large"
                    sx={{
                      bgcolor: '#5D38DE',
                      color: '#FFFFFF',
                      px: { xs: 3.5, sm: 4.5 },
                      py: { xs: 1.6, sm: 1.8 },
                      borderRadius: 999,
                      fontSize: { xs: '1.1rem', sm: '1.18rem' },
                      fontWeight: 800,
                      textTransform: 'none',
                      width: { xs: '100%', sm: 'auto' },
                      boxShadow: '0 6px 18px rgba(93, 56, 222, 0.35)',
                      transition: 'background-color 160ms ease, transform 160ms ease, box-shadow 160ms ease',
                      '&:hover': {
                        bgcolor: '#4E2DBE',
                        transform: 'translateY(-2px)',
                        boxShadow: '0 8px 24px rgba(93, 56, 222, 0.45)',
                      },
                      '&:active': { transform: 'translateY(0)' },
                    }}
                  >
                    {user ? 'Vào lớp học' : 'Đăng nhập để bắt đầu'}
                  </Button>
                  <Button
                    component="a"
                    href="#phuong-phap"
                    variant="outlined"
                    size="large"
                    sx={{
                      borderColor: '#0F172A',
                      color: '#0F172A',
                      px: { xs: 3.5, sm: 4 },
                      py: { xs: 1.6, sm: 1.8 },
                      borderRadius: 999,
                      fontSize: { xs: '1.1rem', sm: '1.18rem' },
                      fontWeight: 800,
                      textTransform: 'none',
                      bgcolor: '#FFFFFF',
                      borderWidth: 1.5,
                      width: { xs: '100%', sm: 'auto' },
                      transition: 'background-color 160ms ease, border-color 160ms ease, color 160ms ease',
                      '&:hover': {
                        borderColor: '#5D38DE',
                        color: '#5D38DE',
                        bgcolor: '#FAF8FF',
                        borderWidth: 1.5,
                      },
                    }}
                  >
                    Xem cách hoạt động
                  </Button>
                </Box>

                {/* 4 Value Pills */}
                <Box
                  sx={{
                    pt: 2.5,
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: { xs: 1.5, sm: 2 },
                  }}
                >
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1.4,
                      px: { xs: 2.4, sm: 3 },
                      py: { xs: 1.1, sm: 1.25 },
                      borderRadius: 999,
                      bgcolor: '#FFFFFF',
                      border: '1.5px solid #CBD5E1',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                      width: { xs: '100%', sm: 'auto' },
                    }}
                  >
                    <span style={{ fontSize: '1.65rem' }}>📷</span>
                    <Typography variant="caption" sx={{ fontWeight: 800, color: '#1E1B4B', fontSize: { xs: '1.05rem', sm: '1.12rem' } }}>
                      Nhận diện chữ số ô ly Việt Nam
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1.4,
                      px: { xs: 2.4, sm: 3 },
                      py: { xs: 1.1, sm: 1.25 },
                      borderRadius: 999,
                      bgcolor: '#FFFFFF',
                      border: '1.5px solid #CBD5E1',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                      width: { xs: '100%', sm: 'auto' },
                    }}
                  >
                    <span style={{ fontSize: '1.65rem' }}>🛡️</span>
                    <Typography variant="caption" sx={{ fontWeight: 800, color: '#1E1B4B', fontSize: { xs: '1.05rem', sm: '1.12rem' } }}>
                      Bảo vệ riêng tư học sinh
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1.4,
                      px: { xs: 2.4, sm: 3 },
                      py: { xs: 1.1, sm: 1.25 },
                      borderRadius: 999,
                      bgcolor: '#FFFFFF',
                      border: '1.5px solid #CBD5E1',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                      width: { xs: '100%', sm: 'auto' },
                    }}
                  >
                    <span style={{ fontSize: '1.65rem' }}>💡</span>
                    <Typography variant="caption" sx={{ fontWeight: 800, color: '#1E1B4B', fontSize: { xs: '1.05rem', sm: '1.12rem' } }}>
                      Gợi mở, không làm hộ
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1.4,
                      px: { xs: 2.4, sm: 3 },
                      py: { xs: 1.1, sm: 1.25 },
                      borderRadius: 999,
                      bgcolor: '#FFFFFF',
                      border: '1.5px solid #CBD5E1',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                      width: { xs: '100%', sm: 'auto' },
                    }}
                  >
                    <span style={{ fontSize: '1.65rem' }}>📚</span>
                    <Typography variant="caption" sx={{ fontWeight: 800, color: '#1E1B4B', fontSize: { xs: '1.05rem', sm: '1.12rem' } }}>
                      Chuẩn chương trình Toán 1–5
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Right Hero Visual Card with 3D Floating Badges & Slender Vertical Silhouette */}
            <Grid size={{ xs: 12, lg: 6 }}>
              <Box
                sx={{
                  position: 'relative',
                  maxWidth: { xs: 335, sm: 380, md: 430, lg: 450 },
                  mx: 'auto',
                  transform: 'rotate(3deg)',
                  transformOrigin: 'center center',
                  transition: 'transform 320ms ease',
                  '&:hover': {
                    transform: 'rotate(1.5deg) scale(1.015)',
                  },
                }}
              >
                {/* Floating Badge 1: Red "+" square (Top-Left, overlapping top bar corner) */}
                <Box
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    top: { xs: -12, sm: -16, md: -18 },
                    left: { xs: -10, sm: -14, md: -18 },
                    width: { xs: 50, sm: 58, md: 64 },
                    height: { xs: 50, sm: 58, md: 64 },
                    borderRadius: { xs: 2.5, sm: 3, md: 3.5 },
                    bgcolor: '#EF4444',
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: { xs: '2rem', sm: '2.3rem', md: '2.5rem' },
                    fontWeight: 900,
                    boxShadow: '0 10px 24px rgba(239, 68, 68, 0.45)',
                    transform: 'rotate(-12deg)',
                    zIndex: 4,
                    animation: 'floatSlow 4.5s ease-in-out infinite',
                    userSelect: 'none',
                  }}
                >
                  +
                </Box>

                {/* Floating Badge 2: Green "×" square (Right Edge near dialogue) */}
                <Box
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    bottom: { xs: 80, sm: 95, md: 105 },
                    right: { xs: -10, sm: -16, md: -20 },
                    width: { xs: 46, sm: 54, md: 60 },
                    height: { xs: 46, sm: 54, md: 60 },
                    borderRadius: { xs: 2.5, sm: 3, md: 3.5 },
                    bgcolor: '#10B981',
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: { xs: '1.8rem', sm: '2.1rem', md: '2.3rem' },
                    fontWeight: 900,
                    boxShadow: '0 10px 24px rgba(16, 185, 129, 0.4)',
                    transform: 'rotate(10deg)',
                    zIndex: 4,
                    animation: 'floatReverse 4.8s ease-in-out infinite',
                    userSelect: 'none',
                  }}
                >
                  ×
                </Box>

                {/* Floating Badge 3: Yellow "=" circle (Bottom-Left corner) */}
                <Box
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    bottom: { xs: -12, sm: -16, md: -18 },
                    left: { xs: 12, sm: 16, md: 18 },
                    width: { xs: 50, sm: 58, md: 64 },
                    height: { xs: 50, sm: 58, md: 64 },
                    borderRadius: '50%',
                    bgcolor: '#F59E0B',
                    color: '#1E1B4B',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: { xs: '2rem', sm: '2.3rem', md: '2.5rem' },
                    fontWeight: 900,
                    boxShadow: '0 10px 24px rgba(245, 158, 11, 0.45)',
                    zIndex: 4,
                    animation: 'floatSlow 3.8s ease-in-out infinite',
                    userSelect: 'none',
                  }}
                >
                  =
                </Box>

                {/* Main Card Container */}
                <Box
                  sx={{
                    position: 'relative',
                    bgcolor: '#FFFFFF',
                    borderRadius: { xs: 5, sm: 6 },
                    boxShadow: '0 25px 60px -12px rgba(93, 56, 222, 0.22)',
                    overflow: 'hidden',
                    border: '1.5px solid #E2E8F0',
                  }}
                >
                  {/* Top Header Bar: 3 dots & class info */}
                  <Box
                    sx={{
                      px: { xs: 2.5, sm: 3 },
                      py: { xs: 1.6, sm: 2 },
                      background: 'linear-gradient(90deg, #6366F1 0%, #3B82F6 40%, #38BDF8 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      position: 'relative',
                      zIndex: 2,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                      {/* Window dots */}
                      <Box sx={{ display: 'flex', gap: 0.7 }}>
                        <Box sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: 'rgba(255, 255, 255, 0.75)' }} />
                        <Box sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: 'rgba(255, 255, 255, 0.75)' }} />
                        <Box sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: 'rgba(255, 255, 255, 0.75)' }} />
                      </Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#FFFFFF', fontSize: { xs: '1.05rem', sm: '1.2rem' } }}>
                        Bài của bé · {currentDemo.className}
                      </Typography>
                    </Box>

                    <Chip
                      label="Đã che thông tin"
                      size="small"
                      sx={{
                        bgcolor: 'rgba(255, 255, 255, 0.25)',
                        color: '#FFFFFF',
                        fontWeight: 800,
                        fontSize: { xs: '0.88rem', sm: '0.96rem' },
                        px: 1.4,
                        py: 0.6,
                        borderRadius: 2,
                      }}
                    />
                  </Box>

                  {/* O Ly Grid Body covering the ENTIRE board directly with NO inner rounded border */}
                  <Box
                    sx={{
                      position: 'relative',
                      bgcolor: '#FFFFFF',
                      backgroundImage:
                        'linear-gradient(rgba(186, 214, 255, 0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(186, 214, 255, 0.5) 1px, transparent 1px)',
                      backgroundSize: { xs: '26px 26px', sm: '30px 30px', md: '32px 32px' },
                      pt: { xs: 2.2, sm: 3.5 },
                      pb: { xs: 3.2, sm: 4.5 },
                      px: { xs: 2, sm: 3 },
                      minHeight: { xs: 530, sm: 610 },
                    }}
                  >
                    {/* Vertical Red Margin running from top to bottom through the whole paper */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 0,
                        bottom: 0,
                        left: { xs: 26, sm: 38, md: 44 },
                        width: '2px',
                        bgcolor: 'rgba(239, 68, 68, 0.55)',
                      }}
                    />

                    {/* Student Name directly on the paper */}
                    <Box sx={{ pl: { xs: 2, sm: 3, md: 3.5 }, mb: { xs: 2.2, sm: 3.5 } }}>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#1E1B4B',
                          fontWeight: 800,
                          fontSize: { xs: '1.05rem', sm: '1.16rem', md: '1.22rem' },
                        }}
                      >
                        Họ và tên: {currentDemo.studentName}
                      </Typography>
                    </Box>

                    {/* Math Calculation with Individual Pill Highlight Capsules */}
                    <Box sx={{ maxWidth: { xs: 290, sm: 320 }, mx: 'auto', textAlign: 'center', position: 'relative', zIndex: 1, my: { xs: 2.2, sm: 3.5 } }}>
                      <Box
                        sx={{
                          display: 'inline-flex',
                          flexDirection: 'column',
                          alignItems: 'flex-end',
                          fontFamily: 'monospace, sans-serif',
                          fontSize: { xs: '2.6rem', sm: '3.2rem', md: '3.6rem' },
                          fontWeight: 900,
                          lineHeight: 1.3,
                          position: 'relative',
                        }}
                      >
                        {/* Row 1 */}
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%' }}>
                          {currentDemo.row1.map((char, idx) => {
                            const isActive = idx === currentDemo.activeCol;
                            return (
                              <Box
                                key={idx}
                                sx={{
                                  width: { xs: 46, sm: 58, md: 66 },
                                  textAlign: 'center',
                                  color: '#1E1B4B',
                                  position: 'relative',
                                  zIndex: 1,
                                  py: 0.6,
                                }}
                              >
                                {isActive && (
                                  <Box
                                    aria-hidden="true"
                                    sx={{
                                      position: 'absolute',
                                      top: 2,
                                      bottom: 2,
                                      left: 3,
                                      right: 3,
                                      bgcolor: '#EEF2F6',
                                      borderRadius: '16px',
                                      zIndex: -1,
                                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                    }}
                                  />
                                )}
                                {char}
                              </Box>
                            );
                          })}
                        </Box>

                        {/* Row 2 with Operator */}
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%', position: 'relative' }}>
                          <Box sx={{ position: 'absolute', left: { xs: -30, sm: -40, md: -46 }, color: '#1E1B4B', fontWeight: 900 }}>
                            {currentDemo.operator}
                          </Box>
                          {currentDemo.row2.map((char, idx) => {
                            const isActive = idx === currentDemo.activeCol;
                            return (
                              <Box
                                key={idx}
                                sx={{
                                  width: { xs: 46, sm: 58, md: 66 },
                                  textAlign: 'center',
                                  color: '#1E1B4B',
                                  position: 'relative',
                                  zIndex: 1,
                                  py: 0.6,
                                }}
                              >
                                {isActive && (
                                  <Box
                                    aria-hidden="true"
                                    sx={{
                                      position: 'absolute',
                                      top: 2,
                                      bottom: 2,
                                      left: 3,
                                      right: 3,
                                      bgcolor: '#EEF2F6',
                                      borderRadius: '16px',
                                      zIndex: -1,
                                      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                                    }}
                                  />
                                )}
                                {char}
                              </Box>
                            );
                          })}
                        </Box>

                        {/* Horizontal divider line matching Image 1 */}
                        <Box
                          sx={{
                            width: 'calc(100% + 40px)',
                            height: '3.5px',
                            bgcolor: '#4F46E5',
                            my: 0.8,
                            alignSelf: 'flex-end',
                          }}
                        />

                        {/* Result Row with Red Error Capsule matching Image 1 */}
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%', pt: 0.6 }}>
                          {currentDemo.resultRow.map((char, idx) => {
                            const isError = idx === currentDemo.errorCol;
                            return (
                              <Box
                                key={idx}
                                sx={{
                                  width: { xs: 46, sm: 58, md: 66 },
                                  textAlign: 'center',
                                  color: isError ? '#EF4444' : '#1E1B4B',
                                  fontWeight: 900,
                                  position: 'relative',
                                  zIndex: 1,
                                  py: 0.6,
                                }}
                              >
                                {isError && (
                                  <Box
                                    aria-hidden="true"
                                    sx={{
                                      position: 'absolute',
                                      top: 2,
                                      bottom: 2,
                                      left: 3,
                                      right: 3,
                                      bgcolor: '#FEE2E2',
                                      borderBottom: '4px solid #EF4444',
                                      borderRadius: '16px',
                                      zIndex: -1,
                                      boxShadow: '0 4px 12px rgba(239, 68, 68, 0.22)',
                                    }}
                                  />
                                )}
                                {char}
                              </Box>
                            );
                          })}
                        </Box>
                      </Box>
                    </Box>

                    {/* Robot Dialogue Bubble directly on the notebook paper */}
                    <Box
                      sx={{
                        p: { xs: 2.2, sm: 2.6 },
                        mt: { xs: 3, sm: 3.8 },
                        borderRadius: 3.5,
                        bgcolor: '#FEF3C7',
                        border: '1px solid #FDE68A',
                        position: 'relative',
                        zIndex: 1,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
                        <Box
                          component="img"
                          src="/ui/robot-mascot.webp"
                          alt="Robot MathVisionKids"
                          sx={{ width: { xs: 38, sm: 44 }, height: { xs: 38, sm: 44 }, flexShrink: 0, objectFit: 'contain', mt: 0.2 }}
                        />
                        <Typography
                          variant="body2"
                          sx={{ color: '#92400E', fontWeight: 800, fontSize: { xs: '1.05rem', sm: '1.16rem' }, lineHeight: 1.65 }}
                        >
                          {answeredSpeech ? currentDemo.replyResponse : currentDemo.speechText}
                        </Typography>
                      </Box>
                    </Box>

                    {/* Child Reply Button placed directly on the notebook paper at bottom right */}
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2.2, position: 'relative', zIndex: 1 }}>
                      <Button
                        size="small"
                        onClick={() => setAnsweredSpeech((prev) => !prev)}
                        sx={{
                          borderRadius: 999,
                          px: { xs: 2.8, sm: 3.6 },
                          py: { xs: 1, sm: 1.2 },
                          fontSize: { xs: '1rem', sm: '1.12rem' },
                          fontWeight: 800,
                          textTransform: 'none',
                          bgcolor: answeredSpeech ? '#5D38DE' : '#FFFFFF',
                          color: answeredSpeech ? '#FFFFFF' : '#5D38DE',
                          border: '1.5px solid #5D38DE',
                          boxShadow: '0 2px 8px rgba(93, 56, 222, 0.15)',
                          transition: 'background-color 160ms ease, color 160ms ease, transform 160ms ease',
                          '&:hover': {
                            bgcolor: answeredSpeech ? '#4E2DBE' : '#5D38DE',
                            color: '#FFFFFF',
                            transform: 'translateY(-1px)',
                          },
                        }}
                      >
                        {answeredSpeech ? '✓ Đã kiểm tra lại' : currentDemo.answerText}
                      </Button>
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* 5 Grade Selector Buttons (Always vividly colored matching Image 1) */}
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: { xs: 1.2, sm: 2.2 }, flexWrap: 'wrap', mt: { xs: 4, md: 6 } }}>
            {[1, 2, 3, 4, 5].map((grade) => {
              const isSelected = selectedGrade === grade;
              const colorInfo = GRADE_COLORS[grade] || GRADE_COLORS[3];
              return (
                <Button
                  key={grade}
                  onClick={() => handleSelectGrade(grade)}
                  sx={{
                    px: { xs: 2.6, sm: 4.6 },
                    py: { xs: 1.1, sm: 1.5 },
                    borderRadius: 999,
                    fontWeight: 900,
                    fontSize: { xs: '1.08rem', sm: '1.22rem' },
                    textTransform: 'none',
                    bgcolor: colorInfo.bg,
                    color: colorInfo.text,
                    border: '2px solid transparent',
                    transform: isSelected ? 'scale(1.12)' : 'scale(1)',
                    boxShadow: isSelected ? `0 8px 24px ${colorInfo.bg}80` : '0 2px 8px rgba(0,0,0,0.12)',
                    outline: isSelected ? '3px solid #1E1B4B' : 'none',
                    outlineOffset: '2px',
                    zIndex: isSelected ? 2 : 1,
                    transition: 'transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease',
                    '&:hover': {
                      bgcolor: colorInfo.hover,
                      transform: isSelected ? 'scale(1.15)' : 'scale(1.06)',
                      boxShadow: `0 8px 24px ${colorInfo.bg}99`,
                    },
                  }}
                >
                  Lớp {grade}
                </Button>
              );
            })}
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 2. PHƯƠNG PHÁP SOCRATIC                                                   */}
      {/* ========================================================================= */}
      <Box id="phuong-phap" component="section" sx={{ py: { xs: 8, md: 10 }, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          {/* Section Header */}
          <Box sx={{ textAlign: 'left', mb: { xs: 4.5, md: 6 } }}>
            <Box
              sx={{
                display: 'inline-block',
                color: '#6D28D9',
                fontWeight: 700,
                fontSize: '0.9rem',
                bgcolor: '#EDE9FE',
                px: 2.2,
                py: 0.65,
                borderRadius: 999,
                mb: 2,
              }}
            >
              Phương pháp Socratic
            </Box>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', sm: '2.5rem', md: '2.8rem' },
                fontWeight: 900,
                letterSpacing: '-0.025em',
                lineHeight: 1.22,
                color: '#0F172A',
                mb: 2,
              }}
            >
              Bé hiểu bài thật sâu, thay vì chép<br />
              bài thụ động
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: '#64748B',
                fontSize: { xs: '1.02rem', md: '1.08rem' },
                lineHeight: 1.68,
                maxWidth: 780,
              }}
            >
              Khác với ứng dụng giải hộ chỉ đưa ra đáp số, MathVisionKids là người gia sư<Box component="br" sx={{ display: { xs: 'none', md: 'block' } }} />
              kiên nhẫn: chỉ ra đúng điểm nhầm lẫn và gợi mở để bé tự suy luận.
            </Typography>
          </Box>

          {/* 3 Step Cards Row with Giant Watermark Numbers & Circular Icons matching Image 2 */}
          <Grid container spacing={3.5} sx={{ mb: 3.5, alignItems: 'stretch' }}>
            {/* Card 1: Chụp trang vở ô ly */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  position: 'relative',
                  p: { xs: 3.5, sm: 4.5 },
                  height: '100%',
                  bgcolor: '#FFE4E6',
                  borderRadius: 5,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  overflow: 'hidden',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-6px)',
                    boxShadow: '0 14px 30px rgba(244, 63, 94, 0.15)',
                  },
                }}
              >
                {/* Giant watermark number */}
                <Typography
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    top: 10,
                    right: 20,
                    fontSize: { xs: '6.8rem', sm: '8rem' },
                    fontWeight: 900,
                    color: 'rgba(255, 255, 255, 0.88)',
                    lineHeight: 1,
                    userSelect: 'none',
                    pointerEvents: 'none',
                  }}
                >
                  1
                </Typography>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  {/* Circular Icon Container matching Image 2 */}
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: '50%',
                      bgcolor: 'rgba(244, 63, 94, 0.16)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.2rem', sm: '2.6rem' },
                      mb: 3,
                    }}
                  >
                    📸
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.65rem' } }}>
                    Chụp trang vở ô ly
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    Bé đặt điện thoại ngay ngắn, chụp trang vở bài làm mà không cần phụ huynh thao tác phức tạp.
                  </Typography>
                </Box>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Chip
                    label="Che thông tin riêng tư"
                    size="small"
                    sx={{
                      bgcolor: '#FFFFFF',
                      color: '#1E1B4B',
                      fontWeight: 800,
                      fontSize: '1.02rem',
                      py: 0.8,
                      px: 1.4,
                      borderRadius: 999,
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                    }}
                  />
                </Box>
              </Box>
            </Grid>

            {/* Card 2: Bóc tách nét viết tay */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  position: 'relative',
                  p: { xs: 3.5, sm: 4.5 },
                  height: '100%',
                  bgcolor: '#D1FAE5',
                  borderRadius: 5,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  overflow: 'hidden',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-6px)',
                    boxShadow: '0 14px 30px rgba(16, 185, 129, 0.15)',
                  },
                }}
              >
                {/* Giant watermark number */}
                <Typography
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    top: 10,
                    right: 20,
                    fontSize: { xs: '6.8rem', sm: '8rem' },
                    fontWeight: 900,
                    color: 'rgba(255, 255, 255, 0.88)',
                    lineHeight: 1,
                    userSelect: 'none',
                    pointerEvents: 'none',
                  }}
                >
                  2
                </Typography>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  {/* Circular Icon Container matching Image 2 */}
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: '50%',
                      bgcolor: 'rgba(16, 185, 129, 0.22)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.2rem', sm: '2.6rem' },
                      mb: 3,
                    }}
                  >
                    ✍️
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.65rem' } }}>
                    Bóc tách nét viết tay
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    AI chuyên biệt cho chữ số tiểu học Việt Nam nhận diện từng chữ số, đặt đúng tính thẳng hàng.
                  </Typography>
                </Box>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Chip
                    label="Chuẩn ô ly Việt Nam"
                    size="small"
                    sx={{
                      bgcolor: '#FFFFFF',
                      color: '#1E1B4B',
                      fontWeight: 800,
                      fontSize: '1.02rem',
                      py: 0.8,
                      px: 1.4,
                      borderRadius: 999,
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                    }}
                  />
                </Box>
              </Box>
            </Grid>

            {/* Card 3: Gợi mở bằng câu hỏi */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  position: 'relative',
                  p: { xs: 3.5, sm: 4.5 },
                  height: '100%',
                  bgcolor: '#DBEAFE',
                  borderRadius: 5,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  overflow: 'hidden',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-6px)',
                    boxShadow: '0 14px 30px rgba(37, 99, 235, 0.15)',
                  },
                }}
              >
                {/* Giant watermark number */}
                <Typography
                  aria-hidden="true"
                  sx={{
                    position: 'absolute',
                    top: 10,
                    right: 20,
                    fontSize: { xs: '6.8rem', sm: '8rem' },
                    fontWeight: 900,
                    color: 'rgba(255, 255, 255, 0.88)',
                    lineHeight: 1,
                    userSelect: 'none',
                    pointerEvents: 'none',
                  }}
                >
                  3
                </Typography>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  {/* Circular Icon Container matching Image 2 */}
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: '50%',
                      bgcolor: 'rgba(59, 130, 246, 0.22)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.2rem', sm: '2.6rem' },
                      mb: 3,
                    }}
                  >
                    💡
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.65rem' } }}>
                    Gợi mở bằng câu hỏi
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    Phát hiện ngay vị trí nhầm hoặc quên nhớ, đặt câu hỏi gợi mở thay vì giải hộ.
                  </Typography>
                </Box>

                <Box sx={{ position: 'relative', zIndex: 1 }}>
                  <Chip
                    label="Tuyệt đối không giải hộ"
                    size="small"
                    sx={{
                      bgcolor: '#FFFFFF',
                      color: '#1E1B4B',
                      fontWeight: 800,
                      fontSize: '1.02rem',
                      py: 0.8,
                      px: 1.4,
                      borderRadius: 999,
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                    }}
                  />
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Full-width Banner 1: Bé hiểu sâu, tự tin (Blue Gradient Banner matching Image 2) */}
          <Box
            sx={{
              p: { xs: 4, sm: 5.5 },
              mb: 3,
              borderRadius: { xs: 4.5, sm: 5.5 },
              background: 'linear-gradient(90deg, #7040EC 0%, #46ACFF 100%)',
              color: '#FFFFFF',
              display: 'flex',
              alignItems: 'center',
              gap: { xs: 2.5, sm: 3.5 },
              boxShadow: '0 12px 32px rgba(112, 64, 236, 0.28)',
            }}
          >
            <Box
              sx={{
                width: { xs: 72, sm: 84 },
                height: { xs: 72, sm: 84 },
                borderRadius: '50%',
                bgcolor: 'rgba(255, 255, 255, 0.22)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: { xs: '2.6rem', sm: '3.2rem' },
                flexShrink: 0,
              }}
            >
              🌟
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 900, color: '#FFFFFF', mb: 0.75, fontSize: { xs: '1.55rem', sm: '1.8rem' } }}>
                Bé hiểu sâu, tự tin
              </Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.95)', fontSize: { xs: '1.14rem', sm: '1.24rem' }, lineHeight: 1.7 }}>
                Bé tự sửa được bài, ghi nhớ phương pháp tư duy bền vững và hào hứng tích lũy sao học tập.
              </Typography>
            </Box>
          </Box>

          {/* Full-width Banner 2: Mẹo của robot (Soft Yellow Banner) */}
          <Box
            sx={{
              p: 2.75,
              px: 3.5,
              borderRadius: 4,
              bgcolor: '#FEF3C7',
              border: '1px solid #FDE68A',
              display: 'flex',
              alignItems: 'center',
              gap: 2.5,
            }}
          >
            <Typography sx={{ fontSize: '2.2rem' }}>🔦</Typography>
            <Typography variant="body2" sx={{ color: '#92400E', fontWeight: 800, fontSize: '1.18rem', lineHeight: 1.65 }}>
              Mẹo của robot: giữ máy song song với trang vở, trong phòng có đủ ánh sáng để chữ hiện rõ nét nhất nhé!
            </Typography>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 3. SO SÁNH TRIẾT LÝ TIẾP CẬN                                              */}
      {/* ========================================================================= */}
      <Box id="khac-gi" component="section" sx={{ py: { xs: 8, md: 10 }, bgcolor: '#FAF8FF', borderBottom: '1px solid #F1F0FB' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          {/* Section Header */}
          <Box sx={{ textAlign: 'left', mb: { xs: 4.5, md: 6 } }}>
            <Box
              sx={{
                display: 'inline-block',
                color: '#6D28D9',
                fontWeight: 700,
                fontSize: '0.9rem',
                bgcolor: '#EDE9FE',
                px: 2.2,
                py: 0.65,
                borderRadius: 999,
                mb: 2,
              }}
            >
              So sánh triết lý tiếp cận
            </Box>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', sm: '2.5rem', md: '2.8rem' },
                fontWeight: 900,
                letterSpacing: '-0.025em',
                lineHeight: 1.22,
                color: '#0F172A',
              }}
            >
              Tại sao gợi mở tư duy tốt hơn<br />
              đưa sẵn đáp số?
            </Typography>
          </Box>

          <Grid container spacing={4} sx={{ alignItems: 'stretch' }}>
            {/* Card 1: Giải bài hộ thương mại */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  p: { xs: 3.5, sm: 5 },
                  borderRadius: 5,
                  bgcolor: '#FFFFFF',
                  border: '1.5px solid #FDA4AF',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 8px 24px rgba(225, 29, 72, 0.06)',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 32px rgba(225, 29, 72, 0.1)',
                  },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', fontSize: { xs: '1.45rem', sm: '1.65rem' } }}>
                      Giải bài hộ thương mại
                    </Typography>
                    <Chip
                      label="Ăn xổi, thụ động"
                      size="small"
                      sx={{ bgcolor: '#F8FAFC', color: '#64748B', fontWeight: 800, fontSize: '1.02rem', py: 0.8, px: 1.4, border: '1px solid #E2E8F0', borderRadius: 999 }}
                    />
                  </Box>

                  {/* Highlight Box matching Image 3 */}
                  <Box sx={{ p: 2.2, px: 3, mb: 3.5, borderRadius: 3, bgcolor: '#FFF1F2', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography sx={{ color: '#EF4444', fontWeight: 900, fontSize: '2.4rem', lineHeight: 1 }}>
                      423
                    </Typography>
                    <Typography sx={{ color: '#64748B', fontWeight: 800, fontSize: '1.18rem' }}>
                      chép vào vở
                    </Typography>
                  </Box>

                  <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'grid', gap: 2.4 }}>
                    <Typography component="li" variant="body2" sx={{ color: '#475569', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <HighlightOffOutlinedIcon sx={{ color: '#EF4444', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Đưa ngay đáp án số cuối cùng, bé chỉ việc chép vào vở.
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ color: '#475569', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <HighlightOffOutlinedIcon sx={{ color: '#EF4444', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Bé không hiểu bản chất bước tính hay quy tắc cộng có nhớ.
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ color: '#475569', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <HighlightOffOutlinedIcon sx={{ color: '#EF4444', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Dần mất khả năng suy luận và tự giải quyết vấn đề khi gặp dạng bài mới.
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Card 2: Đồng hành Socratic */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  p: { xs: 3.5, sm: 5 },
                  borderRadius: 5,
                  bgcolor: '#FFFFFF',
                  border: '2px solid #10B981',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 10px 30px rgba(16, 185, 129, 0.12)',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 14px 36px rgba(16, 185, 129, 0.18)',
                  },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', fontSize: { xs: '1.45rem', sm: '1.65rem' } }}>
                      Đồng hành Socratic
                    </Typography>
                    <Chip
                      label="Chuẩn sư phạm Việt Nam"
                      size="small"
                      sx={{ bgcolor: '#F8FAFC', color: '#64748B', fontWeight: 800, fontSize: '1.02rem', py: 0.8, px: 1.4, border: '1px solid #E2E8F0', borderRadius: 999 }}
                    />
                  </Box>

                  {/* Highlight Box matching Image 3 */}
                  <Box sx={{ p: 2.4, mb: 3.5, borderRadius: 3, bgcolor: '#FEF3C7' }}>
                    <Typography sx={{ color: '#1E1B4B', fontWeight: 900, fontSize: '1.38rem', lineHeight: 1.4 }}>
                      “Số nhớ ở cột đơn vị đang ở đâu nhỉ?”
                    </Typography>
                  </Box>

                  <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'grid', gap: 2.4 }}>
                    <Typography component="li" variant="body2" sx={{ color: '#334155', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <CheckCircleOutlinedIcon sx={{ color: '#10B981', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Phân tích từng bước đặt tính ở ô ly, khoanh vùng chính xác điểm nhầm lẫn: cột đơn vị, cột chục, số nhớ.
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ color: '#334155', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <CheckCircleOutlinedIcon sx={{ color: '#10B981', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Đặt câu hỏi gợi mở để bé tự nhẩm tính và tìm ra kết quả đúng.
                    </Typography>
                    <Typography component="li" variant="body2" sx={{ color: '#334155', fontSize: '1.16rem', lineHeight: 1.75, display: 'flex', gap: 1.6, alignItems: 'flex-start' }}>
                      <CheckCircleOutlinedIcon sx={{ color: '#10B981', fontSize: 28, mt: 0.2, flexShrink: 0 }} />
                      Trẻ nhớ lâu và hào hứng tự học.
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 4. TRÁCH NHIỆM VÀ ĐẠO ĐỨC                                                 */}
      {/* ========================================================================= */}
      <Box id="an-toan" component="section" sx={{ py: { xs: 8, md: 10 }, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          {/* Section Header */}
          <Box sx={{ textAlign: 'left', mb: { xs: 4.5, md: 6 } }}>
            <Box
              sx={{
                display: 'inline-block',
                color: '#6D28D9',
                fontWeight: 700,
                fontSize: '0.9rem',
                bgcolor: '#EDE9FE',
                px: 2.2,
                py: 0.65,
                borderRadius: 999,
                mb: 2,
              }}
            >
              Trách nhiệm và đạo đức
            </Box>
            <Typography
              variant="h2"
              sx={{
                fontSize: { xs: '2rem', sm: '2.5rem', md: '2.8rem' },
                fontWeight: 900,
                letterSpacing: '-0.025em',
                lineHeight: 1.22,
                color: '#0F172A',
                mb: 2,
              }}
            >
              Cam kết sư phạm và an toàn cho<br />
              trẻ
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: '#64748B',
                fontSize: { xs: '1.02rem', md: '1.08rem' },
                lineHeight: 1.68,
                maxWidth: 780,
              }}
            >
              Chúng tôi xây dựng MathVisionKids với kim chỉ nam phục vụ giáo dục tiểu học<Box component="br" sx={{ display: { xs: 'none', md: 'block' } }} />
              Việt Nam chuẩn mực, nhân văn và an toàn.
            </Typography>
          </Box>

          <Grid container spacing={3.5}>
            {/* Card 1: Không giải hộ bài tập */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  p: { xs: 3.5, sm: 4.5 },
                  borderRadius: 5,
                  bgcolor: '#F8FAFC',
                  border: '1.5px solid #E2E8F0',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 28px rgba(0, 0, 0, 0.08)',
                  },
                }}
              >
                <Box>
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: { xs: '18px', sm: '22px' },
                      bgcolor: '#F9C93D',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.4rem', sm: '2.8rem' },
                      mb: 3,
                      transform: 'rotate(-8deg)',
                      boxShadow: '0 8px 20px rgba(249, 201, 61, 0.35)',
                      transition: 'transform 200ms ease, box-shadow 200ms ease',
                      '&:hover': {
                        transform: 'rotate(0deg) scale(1.08)',
                        boxShadow: '0 12px 24px rgba(249, 201, 61, 0.45)',
                      },
                    }}
                  >
                    🧩
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.6rem' } }}>
                    Không giải hộ bài tập
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    Khác với các ứng dụng chụp ảnh giải bài ăn xổi, MathVisionKids hướng tới bồi dưỡng tư duy toán học độc lập. Trẻ được gợi mở từng bước để tự tìm ra kết quả đúng.
                  </Typography>
                </Box>
                <Chip
                  label="Không đưa đáp án sẵn"
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: '#FFFFFF',
                    color: '#1E1B4B',
                    fontWeight: 800,
                    fontSize: '1.02rem',
                    py: 0.8,
                    px: 1.4,
                    borderRadius: 999,
                    border: '1px solid #CBD5E1',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                  }}
                />
              </Box>
            </Grid>

            {/* Card 2: Thầy cô là người định đoạt */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  p: { xs: 3.5, sm: 4.5 },
                  borderRadius: 5,
                  bgcolor: '#F8FAFC',
                  border: '1.5px solid #E2E8F0',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 28px rgba(0, 0, 0, 0.08)',
                  },
                }}
              >
                <Box>
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: { xs: '18px', sm: '22px' },
                      bgcolor: '#27D69A',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.4rem', sm: '2.8rem' },
                      mb: 3,
                      transform: 'rotate(-8deg)',
                      boxShadow: '0 8px 20px rgba(39, 214, 154, 0.35)',
                      transition: 'transform 200ms ease, box-shadow 200ms ease',
                      '&:hover': {
                        transform: 'rotate(0deg) scale(1.08)',
                        boxShadow: '0 12px 24px rgba(39, 214, 154, 0.45)',
                      },
                    }}
                  >
                    🧑‍🏫
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.6rem' } }}>
                    Thầy cô là người định đoạt
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    AI đóng vai trò người trợ giảng chấm sơ bộ. Mọi bài thi hoặc bài tập có độ tin cậy thấp đều được chuyển đến giáo viên để thẩm định và phê duyệt điểm số cuối cùng.
                  </Typography>
                </Box>
                <Chip
                  label="Giáo viên phê duyệt 100%"
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: '#FFFFFF',
                    color: '#1E1B4B',
                    fontWeight: 800,
                    fontSize: '1.02rem',
                    py: 0.8,
                    px: 1.4,
                    borderRadius: 999,
                    border: '1px solid #CBD5E1',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                  }}
                />
              </Box>
            </Grid>

            {/* Card 3: Bảo vệ dữ liệu học sinh */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  p: { xs: 3.5, sm: 4.5 },
                  borderRadius: 5,
                  bgcolor: '#F8FAFC',
                  border: '1.5px solid #E2E8F0',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 200ms ease, box-shadow 200ms ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 12px 28px rgba(0, 0, 0, 0.08)',
                  },
                }}
              >
                <Box>
                  <Box
                    sx={{
                      width: { xs: 68, sm: 76 },
                      height: { xs: 68, sm: 76 },
                      borderRadius: { xs: '18px', sm: '22px' },
                      bgcolor: '#3DB8FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: { xs: '2.4rem', sm: '2.8rem' },
                      mb: 3,
                      transform: 'rotate(-8deg)',
                      boxShadow: '0 8px 20px rgba(61, 184, 255, 0.35)',
                      transition: 'transform 200ms ease, box-shadow 200ms ease',
                      '&:hover': {
                        transform: 'rotate(0deg) scale(1.08)',
                        boxShadow: '0 12px 24px rgba(61, 184, 255, 0.45)',
                      },
                    }}
                  >
                    🛡️
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, color: '#1E1B4B', mb: 1.5, fontSize: { xs: '1.45rem', sm: '1.6rem' } }}>
                    Bảo vệ dữ liệu học sinh
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', fontSize: { xs: '1.08rem', sm: '1.18rem' }, lineHeight: 1.72, mb: 3.5 }}>
                    Thông tin định danh của bé (tên, trường, lớp) được che an toàn trước khi tiếp từ thiết bị. Không chứa quảng cáo, không cơ chế ép streak hay gamification gây nghiện.
                  </Typography>
                </Box>
                <Chip
                  label="Xem lại vùng che trước khi gửi"
                  size="small"
                  sx={{
                    alignSelf: 'flex-start',
                    bgcolor: '#FFFFFF',
                    color: '#1E1B4B',
                    fontWeight: 800,
                    fontSize: '1.02rem',
                    py: 0.8,
                    px: 1.4,
                    borderRadius: 999,
                    border: '1px solid #CBD5E1',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
                  }}
                />
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 5. CALL TO ACTION SECTION                                                 */}
      {/* ========================================================================= */}
      <Box component="section" sx={{ py: { xs: 8, md: 12 }, px: { xs: 2, sm: 3, md: 4 }, bgcolor: '#FAF8FF' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 0, sm: 1 } }}>
          <Box
            sx={{
              position: 'relative',
              borderRadius: { xs: 5, sm: 6 },
              p: { xs: 5, sm: 8, md: 10 },
              minHeight: { xs: 350, sm: 420, md: 460 },
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
              color: '#FFFFFF',
              overflow: 'hidden',
              background: 'linear-gradient(135deg, #6366F1 0%, #3B82F6 50%, #4F46E5 100%)',
              boxShadow: '0 24px 50px -10px rgba(99, 102, 241, 0.35)',
            }}
          >
            {/* Floating Badge "+" (Top-Left) */}
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                top: { xs: 18, sm: 28 },
                left: { xs: 18, sm: 36 },
                width: { xs: 48, sm: 64 },
                height: { xs: 48, sm: 64 },
                borderRadius: { xs: 2.5, sm: 3 },
                bgcolor: '#EF4444',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: { xs: '2rem', sm: '2.5rem' },
                fontWeight: 900,
                boxShadow: '0 8px 20px rgba(239, 68, 68, 0.4)',
                transform: 'rotate(-10deg)',
                animation: 'floatSlow 4.2s ease-in-out infinite',
                userSelect: 'none',
              }}
            >
              +
            </Box>

            {/* Floating Badge "%" (Top-Right) */}
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                top: { xs: 20, sm: 32 },
                right: { xs: 20, sm: 42 },
                width: { xs: 50, sm: 66 },
                height: { xs: 50, sm: 66 },
                borderRadius: '50%',
                bgcolor: '#FBBF24',
                color: '#1E1B4B',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: { xs: '1.8rem', sm: '2.2rem' },
                fontWeight: 900,
                boxShadow: '0 8px 20px rgba(245, 158, 11, 0.4)',
                animation: 'floatReverse 4.6s ease-in-out infinite',
                userSelect: 'none',
              }}
            >
              %
            </Box>

            {/* Floating Badge "−" (Bottom-Right) */}
            <Box
              aria-hidden="true"
              sx={{
                position: 'absolute',
                bottom: { xs: 18, sm: 28 },
                right: { xs: 22, sm: 52 },
                width: { xs: 48, sm: 64 },
                height: { xs: 48, sm: 64 },
                borderRadius: { xs: 2.5, sm: 3 },
                bgcolor: '#10B981',
                color: '#FFFFFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: { xs: '2.1rem', sm: '2.6rem' },
                fontWeight: 900,
                boxShadow: '0 8px 20px rgba(16, 185, 129, 0.4)',
                transform: 'rotate(8deg)',
                animation: 'floatSlow 3.9s ease-in-out infinite',
                userSelect: 'none',
              }}
            >
              −
            </Box>

            <Typography
              variant="h2"
              sx={{
                fontWeight: 900,
                color: '#FFFFFF',
                mb: 2.5,
                fontSize: { xs: '2.2rem', sm: '3.1rem', md: '3.8rem' },
                lineHeight: 1.2,
                letterSpacing: '-0.025em',
                maxWidth: 960,
                position: 'relative',
                zIndex: 1,
              }}
            >
              Sẵn sàng đồng hành cùng bé chinh phục môn Toán?
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255, 255, 255, 0.94)',
                mb: 5,
                maxWidth: 720,
                mx: 'auto',
                fontSize: { xs: '1.16rem', sm: '1.32rem', md: '1.42rem' },
                lineHeight: 1.72,
                position: 'relative',
                zIndex: 1,
              }}
            >
              Đăng nhập bằng tài khoản Google hoặc Facebook của bạn.
            </Typography>

            <Box
              sx={{
                display: 'flex',
                gap: 2.5,
                justifyContent: 'center',
                flexWrap: 'wrap',
                alignItems: 'center',
                position: 'relative',
                zIndex: 1,
              }}
            >
              <Button
                component={RouterLink}
                to="/login"
                variant="contained"
                size="large"
                startIcon={<GoogleIcon sx={{ fontSize: '1.5rem' }} />}
                sx={{
                  bgcolor: '#FBBF24',
                  color: '#1E1B4B',
                  px: { xs: 3.5, sm: 5 },
                  py: { xs: 1.7, sm: 2 },
                  fontSize: { xs: '1.1rem', sm: '1.22rem' },
                  fontWeight: 900,
                  borderRadius: 999,
                  textTransform: 'none',
                  width: { xs: '100%', sm: 'auto' },
                  boxShadow: '0 6px 18px rgba(245, 158, 11, 0.4)',
                  transition: 'background-color 160ms ease, transform 160ms ease, box-shadow 160ms ease',
                  '&:hover': {
                    bgcolor: '#F59E0B',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 24px rgba(245, 158, 11, 0.5)',
                  },
                }}
              >
                Tiếp tục với Google
              </Button>
              <Button
                component={RouterLink}
                to="/login"
                variant="outlined"
                size="large"
                startIcon={<FacebookIcon sx={{ fontSize: '1.5rem' }} />}
                sx={{
                  borderColor: 'rgba(255, 255, 255, 0.85)',
                  color: '#FFFFFF',
                  bgcolor: 'rgba(255, 255, 255, 0.08)',
                  px: { xs: 3.5, sm: 5 },
                  py: { xs: 1.7, sm: 2 },
                  fontSize: { xs: '1.1rem', sm: '1.22rem' },
                  fontWeight: 800,
                  borderRadius: 999,
                  textTransform: 'none',
                  borderWidth: 1.5,
                  width: { xs: '100%', sm: 'auto' },
                  transition: 'background-color 160ms ease, border-color 160ms ease, transform 160ms ease',
                  '&:hover': {
                    borderColor: '#FFFFFF',
                    bgcolor: 'rgba(255, 255, 255, 0.18)',
                    borderWidth: 1.5,
                    transform: 'translateY(-2px)',
                  },
                }}
              >
                Tiếp tục với Facebook
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 6. FOOTER                                                                 */}
      {/* ========================================================================= */}
      <Box component="footer" sx={{ py: 6, px: 2, bgcolor: '#FFFFFF', borderTop: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', md: 'center' },
              gap: 3,
            }}
          >
            {/* Left Brand & Description */}
            <Box sx={{ maxWidth: 620 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.4, mb: 1.5 }}>
                <Box
                  component="img"
                  src="/ui/robot-mascot.webp"
                  alt="Robot MathVisionKids"
                  sx={{ width: 38, height: 38, objectFit: 'contain' }}
                />
                <Typography variant="h6" sx={{ fontWeight: 900, color: '#1E1B4B', letterSpacing: '-0.02em', fontSize: '1.45rem' }}>
                  MathVisionKids
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ color: '#475569', fontSize: '1.14rem', lineHeight: 1.75 }}>
                Nền tảng học toán sơ học và gợi mở tư duy trên trang vở ô ly, thiết kế chuyên biệt cho học sinh tiểu học Việt Nam từ Lớp 1 đến Lớp 5, đồng hành cùng thầy cô và phụ huynh.
              </Typography>
            </Box>

            {/* Right Copyright & Tagline */}
            <Box sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 800, fontSize: '1.02rem', display: 'block', mb: 0.5 }}>
                © 2026 MathVisionKids. Tất cả quyền được bảo lưu.
              </Typography>
              <Typography variant="caption" sx={{ color: '#94A3B8', fontSize: '0.96rem' }}>
                Nền tảng AI trợ lý toán học tiểu học Việt Nam
              </Typography>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
