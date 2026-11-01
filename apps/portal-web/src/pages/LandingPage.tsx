import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Chip,
  Grid,
  Tabs,
  Tab,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import SchoolIcon from '@mui/icons-material/School';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import LogoutIcon from '@mui/icons-material/Logout';
import SparklesIcon from '@mui/icons-material/AutoAwesome';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import MicIcon from '@mui/icons-material/Mic';
import HistoryEduIcon from '@mui/icons-material/HistoryEdu';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import { authService, type UserProfile } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const LandingPage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [gradeBand, setGradeBand] = useState<'early' | 'upper'>('upper'); // 'early' (Lớp 1-2) vs 'upper' (Lớp 3-5)
  const [demoTab, setDemoTab] = useState<number>(0);
  const [activeColumn, setActiveColumn] = useState<'all' | 'units' | 'tens' | 'hundreds'>('all');
  const [socraticStep, setSocraticStep] = useState<number>(0);

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

  const isStudent = user && (user.role || '').toUpperCase().replace('ROLE_', '') === 'STUDENT';

  return (
    <Box sx={{ width: '100%', overflowX: 'clip', bgcolor: '#FFFFFF' }}>
      {/* ========================================================================= */}
      {/* 1. HERO SECTION (KID-FIRST STAGE WITH COMPANION MASCOT) */}
      {/* ========================================================================= */}
      <Box
        className="hero-mesh"
        sx={{
          pt: { xs: 4, sm: 6, md: 8 },
          pb: { xs: 7, sm: 9, md: 11 },
          borderBottom: '1px solid #E2E8F0',
          position: 'relative',
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Grid container spacing={{ xs: 4, md: 6 }} sx={{ alignItems: 'center' }}>
            {/* Left Column: Kid-First Welcome & Narrative */}
            <Grid size={{ xs: 12, lg: 6 }}>
              <Box sx={{ maxWidth: 620 }}>
                {/* Cheerful Companion Mascot Greeting */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Box
                    component="img"
                    src="/ui/mathvision-star.png"
                    alt="Ngôi sao MathVision"
                    className="star-companion-float"
                    sx={{ width: 68, height: 68, flexShrink: 0, objectFit: 'contain' }}
                  />
                  <Box className="speech-bubble">
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 800,
                        color: '#0F172A',
                        fontSize: { xs: '0.85rem', sm: '0.92rem' },
                        lineHeight: 1.4,
                      }}
                    >
                      {user && isStudent
                        ? `Chào ${user.displayName}! Hôm nay em muốn giải toán gì cùng MathVision? ⭐`
                        : 'Xin chào các bạn nhỏ! Cùng khám phá góc học toán vui vẻ nhé! ⭐'}
                    </Typography>
                  </Box>
                </Box>

                {/* Catchy Kid-friendly Headline */}
                <Typography
                  variant="h1"
                  component="h1"
                  sx={{
                    fontSize: { xs: '2.2rem', sm: '2.8rem', md: '3.4rem' },
                    fontWeight: 900,
                    lineHeight: 1.15,
                    letterSpacing: '-0.03em',
                    color: '#0F172A',
                    mb: 2.5,
                  }}
                >
                  Cùng bé học toán vui trên từng trang{' '}
                  <Box
                    component="span"
                    sx={{
                      background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      display: 'inline',
                    }}
                  >
                    vở ô ly
                  </Box>
                </Typography>

                <Typography
                  variant="body1"
                  sx={{
                    color: '#475569',
                    fontSize: { xs: '1.05rem', md: '1.18rem' },
                    lineHeight: 1.68,
                    mb: 4,
                  }}
                >
                  Trợ lý AI nhận diện nét chữ số viết tay của bé, đồng hành gợi mở từng bước tính theo chương trình Tiểu học Việt Nam — <strong>tuyệt đối không giải hộ</strong>.
                </Typography>

                {/* Dynamic Auth Hub */}
                {user ? (
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 3.5,
                      bgcolor: '#FFFFFF',
                      border: '1.5px solid #BFDBFE',
                      boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.12)',
                      mb: 4,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                        <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#10B981' }} />
                        <Typography variant="body2" sx={{ color: '#0F172A', fontWeight: 800 }}>
                          Tài khoản: <strong>{user.displayName}</strong>
                        </Typography>
                      </Box>
                      <Button
                        component={RouterLink}
                        to="/logout"
                        size="small"
                        startIcon={<LogoutIcon fontSize="small" />}
                        sx={{ color: '#64748B', fontWeight: 700, textTransform: 'none', '&:hover': { color: '#EF4444' } }}
                      >
                        Đăng xuất
                      </Button>
                    </Box>

                    {isStudent ? (
                      /* Student Quick Launch Hub ("Hôm nay em muốn làm gì?") */
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#2563EB', letterSpacing: '0.04em', fontSize: '0.85rem' }}>
                            HÔM NAY EM MUỐN LÀM GÌ?
                          </Typography>
                          <Chip
                            label="Không gian học sinh"
                            size="small"
                            sx={{ height: 22, fontSize: '0.72rem', fontWeight: 800, bgcolor: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE' }}
                          />
                        </Box>

                        {/* Primary Dominant Kid Action: Chụp bài ngay */}
                        <Button
                          component={RouterLink}
                          to="/student"
                          fullWidth
                          variant="contained"
                          color="primary"
                          size="large"
                          startIcon={<CameraAltIcon sx={{ fontSize: '1.6rem !important' }} />}
                          sx={{
                            py: 1.8,
                            mb: 1.75,
                            borderRadius: 3,
                            fontWeight: 900,
                            fontSize: { xs: '1rem', sm: '1.08rem' },
                            boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.45)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 1,
                            letterSpacing: '-0.01em',
                          }}
                        >
                          Chụp bài ngay 📸
                        </Button>

                        {/* Supporting Kid Actions */}
                        <Grid container spacing={1.25}>
                          <Grid size={{ xs: 12, sm: 4 }}>
                            <Button
                              component={RouterLink}
                              to="/student"
                              fullWidth
                              variant="outlined"
                              startIcon={<UploadFileIcon />}
                              sx={{
                                py: 1.25,
                                borderRadius: 2.5,
                                fontWeight: 800,
                                fontSize: '0.86rem',
                                borderColor: '#BFDBFE',
                                color: '#1E40AF',
                                bgcolor: '#EFF6FF',
                                justifyContent: 'center',
                                px: 1.5,
                                whiteSpace: 'nowrap',
                                '&:hover': { bgcolor: '#DBEAFE', borderColor: '#2563EB' },
                              }}
                            >
                              Tải ảnh bài làm
                            </Button>
                          </Grid>
                          <Grid size={{ xs: 12, sm: 4 }}>
                            <Button
                              component={RouterLink}
                              to="/student"
                              fullWidth
                              variant="outlined"
                              startIcon={<MicIcon />}
                              sx={{
                                py: 1.25,
                                borderRadius: 2.5,
                                fontWeight: 800,
                                fontSize: '0.86rem',
                                borderColor: '#FDE68A',
                                color: '#B45309',
                                bgcolor: '#FFFBEB',
                                justifyContent: 'center',
                                px: 1.5,
                                whiteSpace: 'nowrap',
                                '&:hover': { bgcolor: '#FEF3C7', borderColor: '#F59E0B' },
                              }}
                            >
                              Hỏi bằng giọng nói
                            </Button>
                          </Grid>
                          <Grid size={{ xs: 12, sm: 4 }}>
                            <Button
                              component={RouterLink}
                              to="/student"
                              fullWidth
                              variant="outlined"
                              startIcon={<HistoryEduIcon />}
                              sx={{
                                py: 1.25,
                                borderRadius: 2.5,
                                fontWeight: 800,
                                fontSize: '0.86rem',
                                borderColor: '#A7F3D0',
                                color: '#065F46',
                                bgcolor: '#ECFDF5',
                                justifyContent: 'center',
                                px: 1.5,
                                whiteSpace: 'nowrap',
                                '&:hover': { bgcolor: '#D1FAE5', borderColor: '#10B981' },
                              }}
                            >
                              Xem bài đã nộp
                            </Button>
                          </Grid>
                        </Grid>
                      </Box>
                    ) : (
                      <Box sx={{ display: 'flex', gap: 1.5 }}>
                        <Button
                          component={RouterLink}
                          to={getDestinationPath(user.role)}
                          variant="contained"
                          color="primary"
                          endIcon={<ArrowForwardIcon />}
                          sx={{ px: 3, py: 1.2, fontWeight: 800, borderRadius: 2.5 }}
                        >
                          Vào không gian làm việc
                        </Button>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 4.5 }}>
                    <Button
                      component={RouterLink}
                      to="/login"
                      variant="contained"
                      color="primary"
                      size="large"
                      endIcon={<ArrowForwardIcon />}
                      sx={{
                        px: 4,
                        py: 1.6,
                        fontSize: '1.05rem',
                        fontWeight: 900,
                        borderRadius: 3,
                        boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.4)',
                      }}
                    >
                      Bắt đầu học ngay 🚀
                    </Button>
                    <Button
                      component="a"
                      href="#showcase"
                      variant="outlined"
                      size="large"
                      startIcon={<AutoFixHighIcon />}
                      sx={{
                        px: 3.5,
                        py: 1.6,
                        fontSize: '1rem',
                        fontWeight: 800,
                        borderRadius: 3,
                        borderColor: '#CBD5E1',
                        color: '#334155',
                        bgcolor: '#FFFFFF',
                        '&:hover': { borderColor: '#2563EB', bgcolor: '#EFF6FF', color: '#2563EB' },
                      }}
                    >
                      Khám phá thực nghiệm ✨
                    </Button>
                  </Box>
                )}

                {/* Practical Guarantees */}
                <Box
                  sx={{
                    pt: 3,
                    borderTop: '1px solid #E2E8F0',
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                    gap: 1.75,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <CheckCircleIcon sx={{ fontSize: 20, color: '#10B981', flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ color: '#334155', fontWeight: 800, fontSize: '0.88rem' }}>
                      Nhận diện chữ số ô ly Việt Nam
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <CheckCircleIcon sx={{ fontSize: 20, color: '#10B981', flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ color: '#334155', fontWeight: 800, fontSize: '0.88rem' }}>
                      Bảo vệ riêng tư học sinh an toàn
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <CheckCircleIcon sx={{ fontSize: 20, color: '#10B981', flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ color: '#334155', fontWeight: 800, fontSize: '0.88rem' }}>
                      Gợi mở từng bước · Tuyệt đối không làm hộ
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <CheckCircleIcon sx={{ fontSize: 20, color: '#10B981', flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ color: '#334155', fontWeight: 800, fontSize: '0.88rem' }}>
                      Chuẩn chương trình Toán Lớp 1–5
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Right Column: Interactive Digital Notebook Preview Stage */}
            <Grid size={{ xs: 12, lg: 6 }} id="showcase">
              <Box
                className="hover-elevate"
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: 4,
                  border: '1.5px solid #CBD5E1',
                  boxShadow: '0 16px 40px -8px rgba(37, 99, 235, 0.12), 0 4px 12px -2px rgba(15, 23, 42, 0.04)',
                  overflow: 'hidden',
                }}
              >
                {/* Stage Header Toolbar */}
                <Box
                  sx={{
                    px: 3,
                    py: 2,
                    bgcolor: '#F8FAFC',
                    borderBottom: '1px solid #E2E8F0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 1.5,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
                    <Box
                      sx={{
                        width: 10,
                        height: 10,
                        borderRadius: '50%',
                        bgcolor: '#2563EB',
                        boxShadow: '0 0 0 3px rgba(37, 99, 235, 0.2)',
                      }}
                    />
                    <Typography variant="caption" sx={{ fontWeight: 900, color: '#0F172A', letterSpacing: '0.04em', fontSize: '0.82rem' }}>
                      PHÒNG THỰC NGHIỆM SỐ HỌC Ô LY
                    </Typography>
                  </Box>

                  {/* Grade-band perspective switcher */}
                  <Box sx={{ display: 'flex', gap: 0.75 }}>
                    <Button
                      size="small"
                      variant={gradeBand === 'early' ? 'contained' : 'outlined'}
                      onClick={() => { setGradeBand('early'); setActiveColumn('all'); setSocraticStep(0); }}
                      sx={{
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        py: 0.5,
                        px: 1.5,
                        minHeight: 30,
                        borderRadius: 2,
                        bgcolor: gradeBand === 'early' ? '#2563EB' : '#FFFFFF',
                        borderColor: gradeBand === 'early' ? '#2563EB' : '#CBD5E1',
                        color: gradeBand === 'early' ? '#FFFFFF' : '#475569',
                      }}
                    >
                      Lớp 1–2
                    </Button>
                    <Button
                      size="small"
                      variant={gradeBand === 'upper' ? 'contained' : 'outlined'}
                      onClick={() => { setGradeBand('upper'); setActiveColumn('all'); setSocraticStep(0); }}
                      sx={{
                        fontSize: '0.75rem',
                        fontWeight: 800,
                        py: 0.5,
                        px: 1.5,
                        minHeight: 30,
                        borderRadius: 2,
                        bgcolor: gradeBand === 'upper' ? '#2563EB' : '#FFFFFF',
                        borderColor: gradeBand === 'upper' ? '#2563EB' : '#CBD5E1',
                        color: gradeBand === 'upper' ? '#FFFFFF' : '#475569',
                      }}
                    >
                      Lớp 3–5
                    </Button>
                  </Box>
                </Box>

                {/* Sub-tabs: Notebook vs AI Recognition vs Socratic Guidance */}
                <Box sx={{ borderBottom: '1px solid #E2E8F0', px: { xs: 1, sm: 2 }, bgcolor: '#FAF8FF' }}>
                  <Tabs
                    value={demoTab}
                    onChange={(_, v) => setDemoTab(v)}
                    variant="scrollable"
                    scrollButtons="auto"
                    allowScrollButtonsMobile
                    sx={{
                      minHeight: 48,
                      '& .MuiTabs-indicator': {
                        height: 3,
                        borderRadius: '3px 3px 0 0',
                        bgcolor: '#2563EB',
                      },
                      '& .MuiTab-root': {
                        minHeight: 48,
                        py: 1.25,
                        px: { xs: 1.5, sm: 2.25 },
                        fontSize: { xs: '0.8rem', sm: '0.88rem' },
                        fontWeight: 800,
                        color: '#64748B',
                        whiteSpace: 'nowrap',
                        transition: 'color 140ms ease',
                        '&.Mui-selected': { color: '#2563EB' },
                      },
                    }}
                  >
                    <Tab label="1. Trang vở ô ly" />
                    <Tab label="2. AI nhận diện chữ số" />
                    <Tab label="3. Bước giải sư phạm" />
                  </Tabs>
                </Box>

                {/* Tab 0: Authentic Vietnamese Grid Paper with Interactive Column Inspection */}
                {demoTab === 0 && (
                  <Box sx={{ p: { xs: 2.5, sm: 3.5 }, bgcolor: '#FFFFFF' }}>
                    {/* Privacy Mask Notice — Friendly tone, zero tech jargon */}
                    <Box
                      sx={{
                        p: 1.5,
                        mb: 2.5,
                        borderRadius: 2.5,
                        bgcolor: '#EFF6FF',
                        border: '1px dashed #93C5FD',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.25,
                      }}
                    >
                      <SecurityIcon sx={{ fontSize: 20, color: '#2563EB', flexShrink: 0 }} />
                      <Box>
                        <Typography variant="caption" sx={{ color: '#1E40AF', fontWeight: 800, display: 'block', fontSize: '0.78rem' }}>
                          VÙNG BẢO VỆ RIÊNG TƯ HỌC SINH TỰ ĐỘNG
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#3B82F6', fontWeight: 700 }}>
                          Em: Nguyễn Bình M*** · Lớp: {gradeBand === 'early' ? '2A' : '3A'} · Trường Tiểu học Đ** B**
                        </Typography>
                      </Box>
                    </Box>

                    {/* Authentic Vietnamese O Ly Paper */}
                    <Box
                      className="oly-grid-paper"
                      sx={{
                        p: { xs: 3, sm: 4 },
                        pl: { xs: 6, sm: 7 },
                        borderRadius: 3,
                        border: '1px solid #CBD5E1',
                        position: 'relative',
                        boxShadow: 'inset 0 1px 4px rgba(0,0,0,0.03)',
                        userSelect: 'none',
                      }}
                    >
                      {/* Arithmetic Stage */}
                      {gradeBand === 'upper' ? (
                        /* Grade 3–5: 245 + 178 = 423 (Có nhớ 2 lần) */
                        <Box sx={{ maxWidth: 280, mx: 'auto', py: 1 }}>
                          {/* Carry reminder row */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px 50px', mb: 0.5, textAlign: 'center', color: '#DC2626', fontWeight: 800, fontSize: '0.85rem' }}>
                            <Box />
                            <Box sx={{ opacity: activeColumn === 'all' || activeColumn === 'hundreds' ? 1 : 0.2, transition: 'opacity 180ms ease' }}>
                              <Chip label="nhớ 1" size="small" sx={{ height: 18, fontSize: '0.65rem', bgcolor: '#FEE2E2', color: '#B91C1C', fontWeight: 800 }} />
                            </Box>
                            <Box sx={{ opacity: activeColumn === 'all' || activeColumn === 'tens' ? 1 : 0.2, transition: 'opacity 180ms ease' }}>
                              <Chip label="nhớ 1" size="small" sx={{ height: 18, fontSize: '0.65rem', bgcolor: '#FEE2E2', color: '#B91C1C', fontWeight: 800 }} />
                            </Box>
                            <Box />
                          </Box>

                          {/* First Addend: 245 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px 50px', textAlign: 'center', fontSize: '1.9rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box />
                            <Box sx={{ bgcolor: activeColumn === 'hundreds' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>2</Box>
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>4</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>5</Box>
                          </Box>

                          {/* Operator and Second Addend: + 178 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px 50px', textAlign: 'center', fontSize: '1.9rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box sx={{ color: '#2563EB' }}>+</Box>
                            <Box sx={{ bgcolor: activeColumn === 'hundreds' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>1</Box>
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>7</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>8</Box>
                          </Box>

                          {/* Divider Bar */}
                          <Box sx={{ height: 3, bgcolor: '#0F172A', my: 0.75, borderRadius: 1 }} />

                          {/* Sum: 423 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px 50px', textAlign: 'center', fontSize: '1.9rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box />
                            <Box sx={{ bgcolor: activeColumn === 'hundreds' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>4</Box>
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>2</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5, transition: 'background-color 160ms' }}>3</Box>
                          </Box>
                        </Box>
                      ) : (
                        /* Grade 1–2: 23 + 15 = 38 (Cộng không nhớ, trực quan) */
                        <Box sx={{ maxWidth: 240, mx: 'auto', py: 1 }}>
                          {/* First Addend: 23 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px', textAlign: 'center', fontSize: '2rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box />
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>2</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>3</Box>
                          </Box>

                          {/* Operator & Second Addend: + 15 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px', textAlign: 'center', fontSize: '2rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box sx={{ color: '#2563EB' }}>+</Box>
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>1</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>5</Box>
                          </Box>

                          {/* Divider Bar */}
                          <Box sx={{ height: 3, bgcolor: '#0F172A', my: 0.75, borderRadius: 1 }} />

                          {/* Sum: 38 */}
                          <Box sx={{ display: 'grid', gridTemplateColumns: '32px 50px 50px', textAlign: 'center', fontSize: '2rem', fontWeight: 900, color: '#0F172A', lineHeight: 1.4 }}>
                            <Box />
                            <Box sx={{ bgcolor: activeColumn === 'tens' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>3</Box>
                            <Box sx={{ bgcolor: activeColumn === 'units' ? 'rgba(37, 99, 235, 0.12)' : 'transparent', borderRadius: 1.5 }}>8</Box>
                          </Box>
                        </Box>
                      )}
                    </Box>

                    {/* Column Inspection Selector */}
                    <Box sx={{ mt: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1.5 }}>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          label="Cả phép tính"
                          size="small"
                          onClick={() => setActiveColumn('all')}
                          sx={{
                            fontWeight: 800,
                            cursor: 'pointer',
                            bgcolor: activeColumn === 'all' ? '#2563EB' : '#F1F5F9',
                            color: activeColumn === 'all' ? '#FFFFFF' : '#475569',
                          }}
                        />
                        <Chip
                          label={gradeBand === 'upper' ? 'Đơn vị (5+8)' : 'Đơn vị (3+5)'}
                          size="small"
                          onClick={() => setActiveColumn('units')}
                          sx={{
                            fontWeight: 800,
                            cursor: 'pointer',
                            bgcolor: activeColumn === 'units' ? '#10B981' : '#F1F5F9',
                            color: activeColumn === 'units' ? '#FFFFFF' : '#475569',
                          }}
                        />
                        <Chip
                          label={gradeBand === 'upper' ? 'Hàng chục (4+7)' : 'Hàng chục (2+1)'}
                          size="small"
                          onClick={() => setActiveColumn('tens')}
                          sx={{
                            fontWeight: 800,
                            cursor: 'pointer',
                            bgcolor: activeColumn === 'tens' ? '#F59E0B' : '#F1F5F9',
                            color: activeColumn === 'tens' ? '#FFFFFF' : '#475569',
                          }}
                        />
                        {gradeBand === 'upper' && (
                          <Chip
                            label="Hàng trăm (2+1)"
                            size="small"
                            onClick={() => setActiveColumn('hundreds')}
                            sx={{
                              fontWeight: 800,
                              cursor: 'pointer',
                              bgcolor: activeColumn === 'hundreds' ? '#8B5CF6' : '#F1F5F9',
                              color: activeColumn === 'hundreds' ? '#FFFFFF' : '#475569',
                            }}
                          />
                        )}
                      </Box>
                      <Chip
                        icon={<SparklesIcon sx={{ fontSize: '13px !important', color: '#10B981 !important' }} />}
                        label="Ô ly chuẩn Bộ Giáo dục"
                        size="small"
                        sx={{ height: 24, fontSize: '0.72rem', bgcolor: '#ECFDF5', color: '#047857', fontWeight: 800, border: '1px solid #A7F3D0' }}
                      />
                    </Box>
                  </Box>
                )}

                {/* Tab 1: AI Recognized Elements */}
                {demoTab === 1 && (
                  <Box sx={{ p: { xs: 2.5, sm: 3.5 }, bgcolor: '#F8FAFC' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                        {gradeBand === 'upper'
                          ? 'Cấu trúc nhận diện: Phép cộng đặt tính 3 chữ số (Có nhớ 2 lần)'
                          : 'Cấu trúc nhận diện: Phép cộng đặt tính 2 chữ số (Không nhớ)'}
                      </Typography>
                      <Chip label="Nhận diện ô ly tự động" size="small" sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 800, border: '1px solid #BBF7D0' }} />
                    </Box>

                    <Box sx={{ display: 'grid', gap: 1.5 }}>
                      <Box sx={{ p: 2, bgcolor: '#FFFFFF', borderRadius: 2.5, border: '1px solid #CBD5E1', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 800, textTransform: 'uppercase' }}>Số hạng thứ nhất</Typography>
                          <Typography variant="caption" sx={{ color: '#10B981', fontWeight: 800 }}>✓ Thẳng cột chuẩn mực</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
                          Giá trị trích xuất: <strong>{gradeBand === 'upper' ? '245' : '23'}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ p: 2, bgcolor: '#FFFFFF', borderRadius: 2.5, border: '1px solid #CBD5E1', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 800, textTransform: 'uppercase' }}>Toán tử & Số hạng thứ hai</Typography>
                          <Typography variant="caption" sx={{ color: '#10B981', fontWeight: 800 }}>✓ Nét dấu cộng ngay ngắn</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
                          Giá trị trích xuất: <strong>{gradeBand === 'upper' ? '+ 178' : '+ 15'}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ p: 2, bgcolor: '#F0FDF4', borderRadius: 2.5, border: '1px solid #86EFAC', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#047857', fontWeight: 800, textTransform: 'uppercase' }}>Kết quả bé ghi trên vở</Typography>
                          <Typography variant="caption" sx={{ color: '#047857', fontWeight: 800 }}>✓ Viết số đúng hàng ô ly</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#047857', mt: 0.5 }}>
                          Đáp số của bé: <strong>{gradeBand === 'upper' ? '423' : '38'}</strong>
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )}

                {/* Tab 2: Step-by-Step Socratic Guidance */}
                {demoTab === 2 && (
                  <Box sx={{ p: { xs: 2.5, sm: 3.5 }, bgcolor: '#FFFFFF' }}>
                    {/* Stepper controls */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 2.5 }}>
                      {(gradeBand === 'upper'
                        ? ['Bước 1: Hàng đơn vị', 'Bước 2: Hàng chục', 'Bước 3: Hàng trăm']
                        : ['Bước 1: Hàng đơn vị', 'Bước 2: Hàng chục']
                      ).map((label, idx) => (
                        <Button
                          key={label}
                          size="small"
                          variant={socraticStep === idx ? 'contained' : 'outlined'}
                          onClick={() => setSocraticStep(idx)}
                          sx={{
                            flex: 1,
                            fontSize: '0.8rem',
                            fontWeight: 800,
                            py: 0.8,
                            borderRadius: 2,
                            bgcolor: socraticStep === idx ? '#2563EB' : '#FFFFFF',
                            borderColor: socraticStep === idx ? '#2563EB' : '#E2E8F0',
                            color: socraticStep === idx ? '#FFFFFF' : '#475569',
                          }}
                        >
                          {label}
                        </Button>
                      ))}
                    </Box>

                    {/* Step Content */}
                    <Box sx={{ minHeight: 140 }}>
                      {gradeBand === 'upper' ? (
                        <>
                          {socraticStep === 0 && (
                            <Box sx={{ p: 2.25, borderRadius: 2.5, bgcolor: '#ECFDF5', border: '1px solid #A7F3D0' }}>
                              <Typography variant="caption" sx={{ fontWeight: 800, color: '#047857', textTransform: 'uppercase', display: 'block' }}>
                                Bước 1: Cộng hàng đơn vị (từ phải sang trái)
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#0F172A', mt: 1, fontSize: '0.95rem', lineHeight: 1.6 }}>
                                Bé lấy <strong>5 + 8 = 13</strong>. Viết chữ số <strong>3</strong> thẳng hàng đơn vị, sau đó <strong>nhớ 1</strong> sang hàng chục liền kề.
                              </Typography>
                              <Box sx={{ mt: 1.5, display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.5, bgcolor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #A7F3D0' }}>
                                <Typography variant="caption" sx={{ color: '#047857', fontWeight: 800 }}>
                                  Quy tắc: Nhớ 1 đơn vị sang hàng chục (+1)
                                </Typography>
                              </Box>
                            </Box>
                          )}

                          {socraticStep === 1 && (
                            <Box sx={{ p: 2.25, borderRadius: 2.5, bgcolor: '#EFF6FF', border: '1px solid #BFDBFE' }}>
                              <Typography variant="caption" sx={{ fontWeight: 800, color: '#1D4ED8', textTransform: 'uppercase', display: 'block' }}>
                                Bước 2: Cộng hàng chục & cộng thêm số nhớ
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#0F172A', mt: 1, fontSize: '0.95rem', lineHeight: 1.6 }}>
                                Bé lấy <strong>4 + 7 = 11</strong>, thêm 1 (nhớ từ hàng đơn vị) là <strong>12</strong>. Viết <strong>2</strong> thẳng cột hàng chục, <strong>nhớ 1</strong> sang hàng trăm.
                              </Typography>
                              <Box sx={{ mt: 1.5, display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.5, bgcolor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #BFDBFE' }}>
                                <Typography variant="caption" sx={{ color: '#1D4ED8', fontWeight: 800 }}>
                                  Quy tắc: 11 + 1 (nhớ) = 12 ➔ Viết 2, nhớ 1 sang hàng trăm
                                </Typography>
                              </Box>
                            </Box>
                          )}

                          {socraticStep === 2 && (
                            <Box sx={{ p: 2.25, borderRadius: 2.5, bgcolor: '#FFFBEB', border: '1px solid #FDE68A' }}>
                              <Typography variant="caption" sx={{ fontWeight: 800, color: '#B45309', textTransform: 'uppercase', display: 'block' }}>
                                Bước 3: Cộng hàng trăm & hoàn thành
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#0F172A', mt: 1, fontSize: '0.95rem', lineHeight: 1.6 }}>
                                Bé lấy <strong>2 + 1 = 3</strong>, thêm 1 (nhớ từ hàng chục) là <strong>4</strong>. Viết chữ số <strong>4</strong> ở hàng trăm. Kết quả cuối cùng là <strong>423</strong>!
                              </Typography>
                              <Box sx={{ mt: 1.5, display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.5, bgcolor: '#FFFFFF', borderRadius: 1.5, border: '1px solid #FDE68A' }}>
                                <Typography variant="caption" sx={{ color: '#B45309', fontWeight: 800 }}>
                                  Hoàn tất: 245 + 178 = 423 ⭐ Xuất sắc!
                                </Typography>
                              </Box>
                            </Box>
                          )}
                        </>
                      ) : (
                        <>
                          {socraticStep === 0 && (
                            <Box sx={{ p: 2.25, borderRadius: 2.5, bgcolor: '#ECFDF5', border: '1px solid #A7F3D0' }}>
                              <Typography variant="caption" sx={{ fontWeight: 800, color: '#047857', textTransform: 'uppercase', display: 'block' }}>
                                Bước 1: Cộng hàng đơn vị
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#0F172A', mt: 1, fontSize: '0.95rem', lineHeight: 1.6 }}>
                                Bé lấy <strong>3 + 5 = 8</strong>. Viết chữ số <strong>8</strong> thẳng cột hàng đơn vị.
                              </Typography>
                            </Box>
                          )}

                          {socraticStep === 1 && (
                            <Box sx={{ p: 2.25, borderRadius: 2.5, bgcolor: '#EFF6FF', border: '1px solid #BFDBFE' }}>
                              <Typography variant="caption" sx={{ fontWeight: 800, color: '#1D4ED8', textTransform: 'uppercase', display: 'block' }}>
                                Bước 2: Cộng hàng chục & có ngay kết quả
                              </Typography>
                              <Typography variant="body2" sx={{ color: '#0F172A', mt: 1, fontSize: '0.95rem', lineHeight: 1.6 }}>
                                Bé lấy <strong>2 + 1 = 3</strong>. Viết chữ số <strong>3</strong> thẳng cột hàng chục. Kết quả là <strong>38</strong>!
                              </Typography>
                            </Box>
                          )}
                        </>
                      )}
                    </Box>

                    {/* Companion Encouragement Note */}
                    <Box sx={{ mt: 2.5, p: 2, borderRadius: 2.5, bgcolor: '#FFFBEB', border: '1px solid #FDE68A', display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box component="img" src="/ui/mathvision-star.png" alt="Star" sx={{ width: 28, height: 28 }} />
                      <Typography variant="caption" sx={{ color: '#92400E', fontWeight: 800 }}>
                        💡 Ngôi sao MathVision nhắc: "Bé hãy tự nhẩm từng bước trước khi điền số nhé, em làm rất tốt đấy!"
                      </Typography>
                    </Box>
                  </Box>
                )}
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 2. CORE 4-STEP LEARNING JOURNEY & PHILOSOPHY */}
      {/* ========================================================================= */}
      <Box id="socratic" sx={{ py: { xs: 8, md: 11 }, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          {/* Section Header */}
          <Box sx={{ textAlign: 'center', maxWidth: 700, mx: 'auto', mb: 6 }}>
            <Chip
              label="HÀNH TRÌNH 4 BƯỚC HỌC TẬP"
              size="small"
              sx={{
                bgcolor: '#EFF6FF',
                color: '#2563EB',
                fontWeight: 900,
                fontSize: '0.76rem',
                letterSpacing: '0.04em',
                borderRadius: 1.5,
                mb: 2,
              }}
            />
            <Typography variant="h2" sx={{ mb: 2, fontSize: { xs: '2rem', md: '2.5rem' }, fontWeight: 900 }}>
              Bé hiểu bài thật sâu thay vì chép bài thụ động
            </Typography>
            <Typography variant="body1" sx={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.68 }}>
              Khác với ứng dụng thương mại giải hộ sẵn đáp án, MathVision Kids là người bạn gia sư kiên nhẫn gợi mở từng bước số học.
            </Typography>
          </Box>

          {/* 4-Step Cards */}
          <Grid container spacing={3} sx={{ mb: 7 }}>
            {[
              {
                step: '1',
                icon: <CameraAltIcon sx={{ fontSize: 28, color: '#2563EB' }} />,
                title: 'Chụp trang vở ô ly',
                desc: 'Bé đặt điện thoại hoặc máy tính bảng chụp trang vở bài tập ô ly ngay ngắn.',
                tag: 'Dễ dàng cho bé Lớp 1–5',
                bg: '#EFF6FF',
              },
              {
                step: '2',
                icon: <AutoStoriesIcon sx={{ fontSize: 28, color: '#F59E0B' }} />,
                title: 'AI nhận diện chữ viết',
                desc: 'Hệ thống bóc tách chữ số viết tay và phép đặt tính thẳng hàng theo chuẩn ô ly Việt Nam.',
                tag: 'Bảo vệ riêng tư tự động',
                bg: '#FFFBEB',
              },
              {
                step: '3',
                icon: <LightbulbIcon sx={{ fontSize: 28, color: '#10B981' }} />,
                title: 'Gợi mở từng bước',
                desc: 'Đặt câu hỏi gợi ý bước nhớ và phép tính thành phần để bé tự suy nghĩ tìm lời giải.',
                tag: 'Tuyệt đối không giải hộ',
                bg: '#ECFDF5',
              },
              {
                step: '4',
                icon: <SparklesIcon sx={{ fontSize: 28, color: '#F43F5E' }} />,
                title: 'Bé hiểu bài & tự tin',
                desc: 'Bé tự tin ghi đáp số vào vở, ghi nhớ kiến thức bền vững và yêu thích môn Toán.',
                tag: 'Tiến bộ vững chắc mỗi ngày',
                bg: '#FFF1F2',
              },
            ].map((item) => (
              <Grid size={{ xs: 12, sm: 6, lg: 3 }} key={item.step}>
                <Box
                  className="hover-elevate"
                  sx={{
                    p: 3.5,
                    borderRadius: 3.5,
                    bgcolor: '#FFFFFF',
                    border: '1.5px solid #E2E8F0',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Box sx={{ width: 50, height: 50, borderRadius: 2.5, bgcolor: item.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {item.icon}
                      </Box>
                      <Typography variant="h4" sx={{ fontWeight: 900, color: '#CBD5E1', fontSize: '1.8rem' }}>
                        0{item.step}
                      </Typography>
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A', mb: 1, fontSize: '1.1rem' }}>
                      {item.title}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, mb: 2.5 }}>
                      {item.desc}
                    </Typography>
                  </Box>
                  <Chip label={item.tag} size="small" sx={{ width: 'fit-content', fontWeight: 800, fontSize: '0.72rem', bgcolor: '#F8FAFC', color: '#475569', border: '1px solid #E2E8F0' }} />
                </Box>
              </Grid>
            ))}
          </Grid>

          {/* Socratic Contrast Box */}
          <Box
            sx={{
              p: { xs: 3, md: 4.5 },
              borderRadius: 4,
              bgcolor: '#F8FAFC',
              border: '1px solid #E2E8F0',
            }}
          >
            <Grid container spacing={3.5} sx={{ alignItems: 'center' }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 3, borderRadius: 3, bgcolor: '#FFF1F2', border: '1px solid #FECDD3' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#9F1239', mb: 0.75, display: 'flex', alignItems: 'center', gap: 1 }}>
                    ✕ Ứng dụng giải toán chụp ảnh thông thường
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#881337', lineHeight: 1.6 }}>
                    Đưa ngay kết quả số cuối cùng. Học sinh chỉ việc chép bài mà không hiểu tại sao phải nhớ số, làm trẻ mất đi khả năng tự suy luận và giải quyết vấn đề.
                  </Typography>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box sx={{ p: 3, borderRadius: 3, bgcolor: '#F0FDF4', border: '1px solid #BBF7D0', boxShadow: '0 4px 14px -2px rgba(16, 185, 129, 0.1)' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#166534', mb: 0.75, display: 'flex', alignItems: 'center', gap: 1 }}>
                    ✓ MathVision Kids — Người bạn đồng hành Socratic
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#14532D', lineHeight: 1.6 }}>
                    Phân tích từng bước tính, phát hiện lỗi sai ở từng cột (đơn vị, chục, trăm) và đặt câu hỏi gợi ý để bé tự tìm ra đáp án, nuôi dưỡng tình yêu toán học thực thụ.
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 3. THREE WORKSPACES (STUDENT, TEACHER, ADMIN) */}
      {/* ========================================================================= */}
      <Box id="workspaces" sx={{ py: { xs: 8, md: 11 }, bgcolor: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Box sx={{ mb: 6, maxWidth: 680 }}>
            <Chip
              label="HỆ SINH THÁI ĐỒNG BỘ"
              size="small"
              sx={{
                bgcolor: '#EFF6FF',
                color: '#2563EB',
                fontWeight: 900,
                fontSize: '0.74rem',
                letterSpacing: '0.04em',
                borderRadius: 1.5,
                mb: 1.5,
              }}
            />
            <Typography variant="h2" sx={{ mb: 1.5, fontSize: { xs: '2rem', md: '2.5rem' }, fontWeight: 900 }}>
              Ba không gian làm việc chuyên biệt
            </Typography>
            <Typography variant="body1" sx={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.65 }}>
              Thiết kế đúng tâm lý và nhiệm vụ của từng đối tượng: Vui vẻ cho học sinh, Hiệu quả cho giáo viên, Vững chắc cho quản trị.
            </Typography>
          </Box>

          <Grid container spacing={3.5}>
            {/* Bento Card 1: Student Workspace */}
            <Grid size={{ xs: 12, lg: 7 }}>
              <Box
                className="bento-card"
                sx={{
                  p: { xs: 3.5, sm: 5 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  background: 'linear-gradient(180deg, #FFFFFF 0%, #EFF6FF 100%)',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Box sx={{ width: 50, height: 50, borderRadius: 3, bgcolor: '#EFF6FF', color: '#2563EB', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <SchoolIcon sx={{ fontSize: 28 }} />
                    </Box>
                    <Chip label="Không gian Học sinh" size="small" sx={{ bgcolor: '#EFF6FF', color: '#2563EB', fontWeight: 900, borderRadius: 2 }} />
                  </Box>
                  <Typography variant="h4" sx={{ fontWeight: 900, mb: 1.5, color: '#0F172A', fontSize: { xs: '1.4rem', sm: '1.75rem' } }}>
                    Vui học đặt tính & Luyện tập cùng Ngôi sao MathVision
                  </Typography>
                  <Typography variant="body1" sx={{ color: '#475569', lineHeight: 1.65, mb: 3.5 }}>
                    Mô phỏng trang vở ô ly thân thuộc, phản hồi khuyến khích thân thiện và lời giải thích từng bước giúp các em từ lớp 1 đến lớp 5 không còn sợ môn Toán.
                  </Typography>

                  {/* Student mini mockup */}
                  <Box
                    sx={{
                      p: 2.5,
                      borderRadius: 3,
                      bgcolor: '#FFFFFF',
                      border: '1px solid #BFDBFE',
                      boxShadow: '0 4px 12px -2px rgba(37, 99, 235, 0.08)',
                      mb: 3,
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                      <Typography variant="caption" sx={{ fontWeight: 800, color: '#2563EB' }}>
                        ★ BÀI TẬP ĐANG LÀM · LỚP 3
                      </Typography>
                      <Chip label="Đang kiểm tra cột nhớ" size="small" sx={{ height: 20, fontSize: '0.68rem', bgcolor: '#FEF3C7', color: '#B45309', fontWeight: 800 }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#0F172A', fontWeight: 800 }}>
                      Phép tính: 356 + 289 = ?
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#059669', fontWeight: 700, display: 'block', mt: 0.5 }}>
                      💡 Gợi ý AI: "6 cộng 9 bằng 15, em viết 5 và nhớ 1 sang hàng chục nhé!"
                    </Typography>
                  </Box>
                </Box>

                <Button
                  component={RouterLink}
                  to="/student"
                  variant="contained"
                  color="primary"
                  endIcon={<ArrowForwardIcon />}
                  sx={{ width: 'fit-content', px: 3.5, py: 1.4, fontWeight: 900, borderRadius: 2.5 }}
                >
                  Vào không gian học sinh
                </Button>
              </Box>
            </Grid>

            {/* Bento Card 2: Teacher Workspace */}
            <Grid size={{ xs: 12, lg: 5 }}>
              <Box
                className="bento-card"
                sx={{
                  p: { xs: 3.5, sm: 5 },
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  background: 'linear-gradient(180deg, #FFFFFF 0%, #ECFDF5 100%)',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                    <Box sx={{ width: 50, height: 50, borderRadius: 3, bgcolor: '#ECFDF5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <MenuBookIcon sx={{ fontSize: 28 }} />
                    </Box>
                    <Chip label="Cổng Giáo viên" size="small" sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 900, borderRadius: 2 }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 900, mb: 1.5, color: '#0F172A', fontSize: { xs: '1.25rem', sm: '1.45rem' } }}>
                    Chấm bài theo đợt & Hàng đợi rà soát sư phạm
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.65, mb: 3.5 }}>
                    Tải lên toàn bộ bài thi hoặc bài tập của lớp trong một lần. Hệ thống tự động lọc các bài có độ tự tin thấp vào hàng đợi để giáo viên thẩm định cuối cùng.
                  </Typography>

                  {/* Teacher Queue Metric Mockup */}
                  <Box sx={{ p: 2, borderRadius: 2.5, bgcolor: '#FFFFFF', border: '1px solid #A7F3D0', mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" sx={{ fontWeight: 800, color: '#065F46' }}>
                        Tiến độ chấm đợt bài gần nhất
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 900, color: '#065F46' }}>
                        28/30 bài hoàn tất
                      </Typography>
                    </Box>
                    <Box sx={{ width: '100%', height: 6, bgcolor: '#D1FAE5', borderRadius: 1, mt: 1, overflow: 'hidden' }}>
                      <Box sx={{ width: '93%', height: '100%', bgcolor: '#059669', borderRadius: 1 }} />
                    </Box>
                  </Box>
                </Box>

                <Button
                  component={RouterLink}
                  to="/teacher-entry"
                  variant="outlined"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    width: 'fit-content',
                    px: 3.5,
                    py: 1.3,
                    fontWeight: 800,
                    borderRadius: 2.5,
                    borderColor: '#059669',
                    color: '#059669',
                    bgcolor: '#FFFFFF',
                    '&:hover': { borderColor: '#047857', bgcolor: '#ECFDF5' },
                  }}
                >
                  Vào cổng giáo viên
                </Button>
              </Box>
            </Grid>

            {/* Bento Card 3: Admin Workspace */}
            <Grid size={{ xs: 12 }}>
              <Box
                className="bento-card"
                sx={{
                  p: { xs: 3.5, sm: 4.5 },
                  background: 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
                  border: '1.5px solid #CBD5E1',
                }}
              >
                <Grid container spacing={3} sx={{ alignItems: 'center' }}>
                  <Grid size={{ xs: 12, md: 8 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <Box sx={{ width: 46, height: 46, borderRadius: 2.5, bgcolor: '#F1F5F9', color: '#0F172A', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <AdminPanelSettingsIcon sx={{ fontSize: 26 }} />
                      </Box>
                      <Chip label="Cổng Quản trị viên" size="small" sx={{ bgcolor: '#F1F5F9', color: '#0F172A', fontWeight: 900, borderRadius: 2, border: '1px solid #CBD5E1' }} />
                    </Box>
                    <Typography variant="h5" sx={{ fontWeight: 900, mb: 1, color: '#0F172A' }}>
                      Quản lý tài khoản toàn trường & Giám sát dữ liệu tập trung
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, maxWidth: 680 }}>
                      Phân quyền nghiêm ngặt giữa học sinh, giáo viên và cán bộ quản lý. Theo dõi nhật ký kiểm toán hệ thống theo thời gian thực và đảm bảo tuyệt đối an toàn thông tin trường học.
                    </Typography>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' } }}>
                    <Button
                      component={RouterLink}
                      to="/admin-entry"
                      variant="outlined"
                      endIcon={<ArrowForwardIcon />}
                      sx={{
                        px: 3.5,
                        py: 1.3,
                        fontWeight: 800,
                        borderRadius: 2.5,
                        borderColor: '#0F172A',
                        color: '#0F172A',
                        bgcolor: '#FFFFFF',
                        '&:hover': { borderColor: '#2563EB', color: '#2563EB', bgcolor: '#F1F5F9' },
                      }}
                    >
                      Vào cổng quản trị
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 4. PEDAGOGICAL & CHILD SAFETY ETHICS */}
      {/* ========================================================================= */}
      <Box id="principles" sx={{ py: { xs: 8, md: 11 }, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Box sx={{ mb: 6, maxWidth: 640 }}>
            <Chip
              label="TRÁCH NHIỆM & ĐẠO ĐỨC"
              size="small"
              sx={{
                bgcolor: '#EFF6FF',
                color: '#2563EB',
                fontWeight: 900,
                fontSize: '0.74rem',
                letterSpacing: '0.04em',
                borderRadius: 1.5,
                mb: 1.5,
              }}
            />
            <Typography variant="h2" sx={{ mb: 1.5, fontSize: { xs: '2rem', md: '2.5rem' }, fontWeight: 900 }}>
              Cam kết sư phạm và an toàn cho trẻ
            </Typography>
            <Typography variant="body1" sx={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.65 }}>
              Chúng tôi xây dựng MathVision Kids với kim chỉ nam phục vụ giáo dục tiểu học Việt Nam chuẩn mực, nhân văn và an toàn.
            </Typography>
          </Box>

          <Grid container spacing={3.5}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                className="hover-elevate"
                sx={{
                  p: 3.5,
                  borderRadius: 3.5,
                  bgcolor: '#EFF6FF',
                  border: '1px solid #BFDBFE',
                  height: '100%',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#DBEAFE', color: '#1D4ED8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <LightbulbIcon sx={{ fontSize: 24 }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Không giải hộ bài tập
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#334155', lineHeight: 1.68 }}>
                  Khác với các ứng dụng chụp ảnh giải bài ăn xổi, MathVision Kids hướng tới bồi dưỡng tư duy toán học độc lập. Trẻ được gợi mở từng bước để tự tìm ra kết quả đúng.
                </Typography>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                className="hover-elevate"
                sx={{
                  p: 3.5,
                  borderRadius: 3.5,
                  bgcolor: '#ECFDF5',
                  border: '1px solid #A7F3D0',
                  height: '100%',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#D1FAE5', color: '#047857', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <VerifiedUserIcon sx={{ fontSize: 24 }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Thầy cô là người định đoạt
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#334155', lineHeight: 1.68 }}>
                  AI đóng vai trò người trợ giảng chấm sơ bộ. Mọi bài thi hoặc bài tập có độ tin cậy thấp đều được chuyển đến giáo viên để thẩm định và phê duyệt điểm số cuối cùng.
                </Typography>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                className="hover-elevate"
                sx={{
                  p: 3.5,
                  borderRadius: 3.5,
                  bgcolor: '#FFFBEB',
                  border: '1px solid #FDE68A',
                  height: '100%',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#FEF3C7', color: '#B45309', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <SecurityIcon sx={{ fontSize: 24 }} />
                  </Box>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Bảo vệ dữ liệu học sinh
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#334155', lineHeight: 1.68 }}>
                  Thông tin định danh của bé (tên, trường, lớp) được che an toàn trực tiếp từ thiết bị. Không chứa quảng cáo, không cơ chế ép streak hay gamification gây nghiện.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 5. CONFIDENT CALL TO ACTION */}
      {/* ========================================================================= */}
      <Box
        sx={{
          py: { xs: 9, md: 12 },
          color: '#FFFFFF',
          position: 'relative',
          overflow: 'hidden',
          background: 'radial-gradient(ellipse 70% 60% at 50% -20%, rgba(37, 99, 235, 0.4), transparent 70%), #0F172A',
        }}
      >
        <Container maxWidth="md" sx={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <Chip
            label="BẮT ĐẦU CÙNG MATHVISION KIDS"
            size="small"
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.12)',
              color: '#EFF6FF',
              fontWeight: 800,
              fontSize: '0.74rem',
              letterSpacing: '0.04em',
              borderRadius: 1.5,
              mb: 3,
              border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
          />
          <Typography variant="h2" sx={{ fontWeight: 900, color: '#FFFFFF', mb: 2.5, fontSize: { xs: '2rem', sm: '2.75rem' }, lineHeight: 1.18 }}>
            Sẵn sàng đồng hành cùng bé chinh phục môn Toán?
          </Typography>
          <Typography variant="body1" sx={{ color: '#CBD5E1', mb: 5, maxWidth: 620, mx: 'auto', fontSize: '1.1rem', lineHeight: 1.68 }}>
            Đăng nhập để vào không gian học sinh, cổng giáo viên hoặc bảng quản trị nhà trường.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              component={RouterLink}
              to="/login"
              variant="contained"
              size="large"
              endIcon={<ArrowForwardIcon />}
              sx={{
                bgcolor: '#2563EB',
                color: '#FFFFFF',
                px: 4.5,
                py: 1.6,
                fontSize: '1.05rem',
                fontWeight: 900,
                borderRadius: 3,
                boxShadow: '0 8px 24px rgba(37, 99, 235, 0.45)',
                '&:hover': { bgcolor: '#1D4ED8' },
              }}
            >
              Bắt đầu học ngay 🚀
            </Button>
            <Button
              component={RouterLink}
              to="/teacher-entry"
              variant="outlined"
              size="large"
              sx={{
                borderColor: 'rgba(255, 255, 255, 0.35) !important',
                color: '#FFFFFF !important',
                bgcolor: 'rgba(255, 255, 255, 0.08) !important',
                px: 4,
                py: 1.6,
                fontSize: '1.02rem',
                fontWeight: 800,
                borderRadius: 3,
                backdropFilter: 'blur(8px)',
                '&:hover': {
                  borderColor: '#FFFFFF !important',
                  bgcolor: 'rgba(255, 255, 255, 0.18) !important',
                  color: '#FFFFFF !important',
                },
              }}
            >
              Dành cho giáo viên
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
