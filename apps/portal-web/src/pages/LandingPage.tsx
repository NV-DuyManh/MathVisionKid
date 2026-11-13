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
  Card,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import SecurityIcon from '@mui/icons-material/Security';
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
import { WEB_DESIGN } from '../../../../packages/ui-brand/src/web-design';

export const LandingPage: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [gradeBand, setGradeBand] = useState<'early' | 'upper'>('upper');
  const [demoTab, setDemoTab] = useState<number>(0);
  const [activeColumn, setActiveColumn] = useState<'all' | 'units' | 'tens' | 'hundreds'>('all');
  const [socraticStep, setSocraticStep] = useState<number>(0);
  const [activeWorkflowStep, setActiveWorkflowStep] = useState<number>(0);

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

  const columnOptions = [
    { column: 'all', label: 'Cả phép tính', fill: WEB_DESIGN.colors.blue, text: WEB_DESIGN.colors.white },
    { column: 'units', label: gradeBand === 'upper' ? 'Đơn vị (5+8)' : 'Đơn vị (3+5)', fill: WEB_DESIGN.colors.green, text: WEB_DESIGN.colors.white },
    { column: 'tens', label: gradeBand === 'upper' ? 'Hàng chục (4+7)' : 'Hàng chục (2+1)', fill: WEB_DESIGN.colors.star, text: WEB_DESIGN.colors.ink },
    { column: 'hundreds', label: 'Hàng trăm (2+1)', fill: WEB_DESIGN.colors.blue, text: WEB_DESIGN.colors.white },
  ] as const;

  const WORKFLOW_STEPS = [
    {
      step: '01',
      title: 'Chụp trang vở ô ly',
      subtitle: 'Bé đặt điện thoại ngay ngắn, chụp trang vở bài làm mà không cần phụ huynh thao tác phức tạp.',
      tag: 'Che thông tin riêng tư',
      icon: <CameraAltIcon sx={{ fontSize: 26, color: '#2563EB' }} />,
      detail: 'Trước khi gửi, em có thể đánh dấu vùng tên, trường hoặc lớp cần che, rồi xác nhận lại ảnh.',
      badgeColor: '#EFF6FF',
    },
    {
      step: '02',
      title: 'Bóc tách nét chữ viết tay',
      subtitle: 'AI chuyên biệt cho chữ số tiểu học Việt Nam nhận diện từng chữ số đặt tính thẳng hàng.',
      tag: 'Chuẩn ô ly Việt Nam',
      icon: <AutoStoriesIcon sx={{ fontSize: 26, color: '#F59E0B' }} />,
      detail: 'Bóc tách chính xác từng số hạng, dấu phép tính (+, -) và đường kẻ ngang, phân loại từng cột: đơn vị, hàng chục, hàng trăm.',
      badgeColor: '#FFFBEB',
    },
    {
      step: '03',
      title: 'Gợi mở câu hỏi Socratic',
      subtitle: 'Phát hiện ngay vị trí bước tính nhầm hoặc quên nhớ số, đặt câu hỏi gợi mở thay vì giải hộ.',
      tag: 'Tuyệt đối không giải hộ',
      icon: <LightbulbIcon sx={{ fontSize: 26, color: '#10B981' }} />,
      detail: 'Đặt câu hỏi nhỏ khuyến khích bé tự nhẩm tính: "5 cộng 8 bằng 13, bé viết mấy và nhớ mấy sang hàng chục?" để bé tự tìm lời giải.',
      badgeColor: '#ECFDF5',
    },
    {
      step: '04',
      title: 'Bé hiểu sâu & tự tin tiến bộ',
      subtitle: 'Bé tự sửa được bài, ghi nhớ phương pháp tư duy bền vững và hào hứng tích lũy sao học tập.',
      tag: 'Ghi nhớ kiến thức lâu bền',
      icon: <SparklesIcon sx={{ fontSize: 26, color: '#F43F5E' }} />,
      detail: 'Bé ghi đáp số chính xác vào trang vở của mình, nhận ngôi sao khích lệ và sẵn sàng tự tin bước vào các bài toán tiếp theo.',
      badgeColor: '#FFF1F2',
    },
  ];

  return (
    <Box sx={{ width: '100%', overflowX: 'clip', bgcolor: '#FFFFFF' }}>
      {/* ========================================================================= */}
      {/* 1. HERO SECTION (INTERACTIVE STAGE WITH DIGITAL O LY NOTEBOOK) */}
      {/* ========================================================================= */}
      <Box
        sx={{
          py: { xs: 4, sm: 6, md: 8 },
          borderBottom: `1px solid ${WEB_DESIGN.colors.paperLine}`,
          bgcolor: WEB_DESIGN.colors.paper,
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Grid container spacing={{ xs: 4, lg: 7 }} sx={{ alignItems: 'start' }}>
            {/* Left Column: Narrative & Action Launchpad */}
            <Grid size={{ xs: 12, lg: 6 }}>
              <Box sx={{ maxWidth: 620 }}>
                {/* Companion Mascot Speech Bubble */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box
                    component="img"
                    src="/ui/mathvision-star.webp"
                    alt="Ngôi sao MathVision"
                    sx={{ width: { xs: 58, md: 82 }, height: { xs: 58, md: 82 }, flexShrink: 0, objectFit: 'contain' }}
                  />
                  <Box sx={{ maxWidth: 280 }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 800,
                        color: WEB_DESIGN.colors.mutedInk,
                        fontSize: { xs: '0.875rem', sm: '1rem' },
                        lineHeight: 1.4,
                      }}
                    >
                      {user && isStudent
                        ? `Chào ${user.displayName}! Hôm nay em muốn giải toán gì cùng MathVision?`
                        : 'Cùng Ngôi sao MathVision mở trang vở hôm nay nhé!'}
                    </Typography>
                  </Box>
                </Box>

                {/* Catchy Headline */}
                <Typography
                  variant="h1"
                  component="h1"
                  sx={{
                    fontSize: { xs: '2.125rem', sm: '2.85rem', lg: '3.25rem' },
                    fontWeight: 900,
                    lineHeight: 1.15,
                    letterSpacing: '-0.03em',
                    color: WEB_DESIGN.colors.ink,
                    textWrap: 'balance',
                    mb: 2.5,
                  }}
                >
                  Mở vở ô ly,{' '}
                  <Box
                    component="span"
                    sx={{ color: WEB_DESIGN.colors.blue }}
                  >
                    học toán từng bước
                  </Box>
                </Typography>

                <Typography
                  variant="body1"
                  sx={{
                    color: '#475569',
                    fontSize: { xs: '1.05rem', md: '1.18rem' },
                    lineHeight: 1.68,
                    mb: 3,
                  }}
                >
                  Chụp bài toán viết tay và cùng Ngôi sao tìm ra lời giải qua từng câu hỏi gợi mở. Dành cho học sinh lớp 1 đến lớp 5.
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
                            sx={{ height: 22, fontSize: '0.72rem', fontWeight: 800, bgcolor: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 1 }}
                          />
                        </Box>

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
                          Tiếp tục
                        </Button>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Box>
                    <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mb: 3 }}>
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
                      Đăng nhập
                    </Button>
                    </Box>
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
                      Gợi mở từng bước · Không làm hộ
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
            <Grid size={{ xs: 12, lg: 6 }} id="showcase" sx={{ minWidth: 0, scrollMarginTop: 96 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: `${WEB_DESIGN.components.notebook.radius}px`,
                  border: `1px solid ${WEB_DESIGN.components.notebook.borderColor}`,
                  overflow: 'hidden',
                }}
              >
                {/* Stage Header Toolbar */}
                <Box
                  sx={{
                    px: { xs: 2, sm: 3 },
                    py: 2,
                    bgcolor: WEB_DESIGN.colors.blueLight,
                    borderBottom: `1px solid ${WEB_DESIGN.colors.line}`,
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
                      onClick={() => {
                        setGradeBand('early');
                        setActiveColumn('all');
                        setSocraticStep(0);
                      }}
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
                      onClick={() => {
                        setGradeBand('upper');
                        setActiveColumn('all');
                        setSocraticStep(0);
                      }}
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
                <Box sx={{ borderBottom: '1px solid #E2E8F0', px: { xs: 0.5, sm: 2 }, bgcolor: '#F8FAFC' }}>
                  <Tabs
                    value={demoTab}
                    onChange={(_, v) => setDemoTab(v)}
                    aria-label="Chế độ xem thực nghiệm số học ô ly"
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
                        px: { xs: 1.25, sm: 2.25 },
                        fontSize: { xs: '0.78rem', sm: '0.88rem' },
                        fontWeight: 800,
                        color: '#64748B',
                        whiteSpace: 'nowrap',
                        transition: 'color 140ms ease',
                        '&.Mui-selected': { color: '#2563EB' },
                      },
                    }}
                  >
                    <Tab label="1. Trang vở ô ly" />
                    <Tab label="2. AI nhận diện" />
                    <Tab label="3. Bước giải sư phạm" />
                  </Tabs>
                </Box>

                {/* Tab 0: Authentic Vietnamese Grid Paper with Interactive Column Inspection */}
                {demoTab === 0 && (
                  <Box sx={{ p: { xs: 2.5, sm: 3.5 }, bgcolor: '#FFFFFF' }}>
                    {/* Privacy Mask Notice */}
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
                        {columnOptions.map(({ column, label, fill, text }) => {
                          if (column === 'hundreds' && gradeBand !== 'upper') return null;
                          const selected = activeColumn === column;
                          return (
                            <Chip
                              key={column}
                              label={label}
                              size="small"
                              onClick={() => setActiveColumn(column)}
                              aria-pressed={selected}
                              sx={{
                                fontWeight: 800, borderRadius: 1.5, transition: 'none',
                                bgcolor: selected ? fill : '#F1F5F9',
                                color: selected ? text : WEB_DESIGN.colors.mutedInk,
                                '&.MuiChip-clickable:hover, &.Mui-focusVisible': {
                                  bgcolor: selected ? fill : WEB_DESIGN.colors.blueLight,
                                },
                              }}
                            />
                          );
                        })}
                      </Box>
                      <Chip
                        icon={<SparklesIcon sx={{ fontSize: '13px !important', color: '#059669 !important' }} />}
                        label="Ô ly chuẩn Bộ Giáo dục"
                        size="small"
                        sx={{ height: 24, fontSize: '0.72rem', bgcolor: '#ECFDF5', color: '#047857', fontWeight: 800, border: '1px solid #A7F3D0', borderRadius: 1.5 }}
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
                      <Chip label="Nhận diện ô ly tự động" size="small" sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0', borderRadius: 1.5 }} />
                    </Box>

                    <Box sx={{ display: 'grid', gap: 1.5 }}>
                      <Box sx={{ p: 2, bgcolor: '#FFFFFF', borderRadius: 2.5, border: '1px solid #E2E8F0', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 800, textTransform: 'uppercase' }}>Số hạng thứ nhất</Typography>
                          <Typography variant="caption" sx={{ color: '#10B981', fontWeight: 800 }}>✓ Thẳng cột chuẩn mực</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
                          Giá trị trích xuất: <strong>{gradeBand === 'upper' ? '245' : '23'}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ p: 2, bgcolor: '#FFFFFF', borderRadius: 2.5, border: '1px solid #E2E8F0', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 800, textTransform: 'uppercase' }}>Toán tử & Số hạng thứ hai</Typography>
                          <Typography variant="caption" sx={{ color: '#10B981', fontWeight: 800 }}>✓ Nét dấu cộng ngay ngắn</Typography>
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
                          Giá trị trích xuất: <strong>{gradeBand === 'upper' ? '+ 178' : '+ 15'}</strong>
                        </Typography>
                      </Box>
                      <Box sx={{ p: 2, bgcolor: '#ECFDF5', borderRadius: 2.5, border: '1px solid #A7F3D0', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
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

                    {/* Mascot Note */}
                    <Box sx={{ mt: 2.5, p: 2, borderRadius: 2.5, bgcolor: '#FFFBEB', border: '1px solid #FDE68A', display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box component="img" src="/ui/mathvision-star.webp" alt="Star" sx={{ width: 28, height: 28 }} />
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
      {/* 2. THE SOCRATIC DIFFERENCE — SCREEN-LED INTERACTIVE FLOW */}
      {/* ========================================================================= */}
      <Box id="socratic" sx={{ py: { xs: 8, md: 11 }, bgcolor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          {/* Section Header */}
          <Box sx={{ textAlign: 'center', maxWidth: 740, mx: 'auto', mb: 6 }}>
            <Chip
              label="PHƯƠNG PHÁP SOCRATIC ĐỘC BẢN"
              size="small"
              sx={{
                bgcolor: '#EFF6FF',
                color: '#2563EB',
                fontWeight: 900,
                fontSize: '0.74rem',
                letterSpacing: '0.04em',
                borderRadius: 1.5,
                mb: 2,
              }}
            />
            <Typography variant="h2" sx={{ mb: 2, fontSize: { xs: '2rem', md: '2.5rem' }, fontWeight: 900, letterSpacing: '-0.02em' }}>
              Bé hiểu bài thật sâu thay vì chép bài thụ động
            </Typography>
            <Typography variant="body1" sx={{ color: '#475569', fontSize: '1.05rem', lineHeight: 1.68 }}>
              Khác với ứng dụng giải hộ thương mại đưa sẵn đáp số, MathVision Kids là người gia sư kiên nhẫn chỉ ra đúng điểm nhầm lẫn và gợi mở để bé tự suy luận.
            </Typography>
          </Box>

          {/* Interactive Screen-Led Workflow Timeline */}
          <Grid container spacing={4} sx={{ mb: 7, alignItems: 'stretch' }}>
            {/* Left: Step Selection Cards */}
            <Grid size={{ xs: 12, lg: 5 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%', justifyContent: 'space-between' }}>
                {WORKFLOW_STEPS.map((step, idx) => {
                  const isActive = activeWorkflowStep === idx;
                  return (
                    <Box
                      key={step.step}
                      onClick={() => setActiveWorkflowStep(idx)}
                      sx={{
                        p: 2.5,
                        borderRadius: 3,
                        cursor: 'pointer',
                        border: '1.5px solid',
                        borderColor: isActive ? '#2563EB' : '#E2E8F0',
                        bgcolor: isActive ? '#F8FAFC' : '#FFFFFF',
                        boxShadow: isActive ? '0 8px 24px -4px rgba(37, 99, 235, 0.12)' : 'none',
                        transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                        display: 'flex',
                        gap: 2,
                        alignItems: 'flex-start',
                        '&:hover': {
                          borderColor: isActive ? '#2563EB' : '#CBD5E1',
                          bgcolor: '#F8FAFC',
                        },
                      }}
                    >
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 2.5,
                          bgcolor: step.badgeColor,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        {step.icon}
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 900, color: isActive ? '#2563EB' : '#0F172A', fontSize: '0.98rem' }}>
                            {step.step}. {step.title}
                          </Typography>
                          <Chip
                            label={step.tag}
                            size="small"
                            sx={{
                              height: 20,
                              fontSize: '0.68rem',
                              fontWeight: 800,
                              bgcolor: isActive ? '#EFF6FF' : '#F1F5F9',
                              color: isActive ? '#2563EB' : '#64748B',
                            }}
                          />
                        </Box>
                        <Typography variant="body2" sx={{ color: '#475569', fontSize: '0.86rem', lineHeight: 1.55 }}>
                          {step.subtitle}
                        </Typography>
                      </Box>
                    </Box>
                  );
                })}
              </Box>
            </Grid>

            {/* Right: Live Step Spotlight Stage */}
            <Grid size={{ xs: 12, lg: 7 }}>
              <Card
                sx={{
                  height: '100%',
                  p: { xs: 3.5, sm: 4.5 },
                  borderRadius: 4,
                  border: '1.5px solid #CBD5E1',
                  bgcolor: '#F8FAFC',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 12px 32px -4px rgba(15, 23, 42, 0.06)',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1.5, mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#10B981' }} />
                      <Typography variant="caption" sx={{ fontWeight: 900, color: '#0F172A', letterSpacing: '0.04em', fontSize: '0.82rem' }}>
                        CHI TIẾT TRẢI NGHIỆM · BƯỚC {WORKFLOW_STEPS[activeWorkflowStep].step}
                      </Typography>
                    </Box>
                    <Chip
                      label={WORKFLOW_STEPS[activeWorkflowStep].tag}
                      size="small"
                      sx={{ bgcolor: '#ECFDF5', color: '#047857', fontWeight: 800, border: '1px solid #A7F3D0', borderRadius: 1.5 }}
                    />
                  </Box>

                  <Typography variant="h4" sx={{ fontWeight: 900, color: '#0F172A', mb: 1.5, fontSize: { xs: '1.4rem', sm: '1.8rem' } }}>
                    {WORKFLOW_STEPS[activeWorkflowStep].title}
                  </Typography>

                  <Typography variant="body1" sx={{ color: '#334155', lineHeight: 1.7, mb: 3.5, fontSize: '1.02rem' }}>
                    {WORKFLOW_STEPS[activeWorkflowStep].detail}
                  </Typography>

                  {/* Socratic Demonstration Box */}
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 3,
                      bgcolor: '#FFFFFF',
                      border: '1px solid #E2E8F0',
                      boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                      <Box component="img" src="/ui/mathvision-star.webp" alt="Star mascot" sx={{ width: 32, height: 32 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#0F172A' }}>
                        Lời khuyên của Ngôi sao MathVision
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6 }}>
                      {activeWorkflowStep === 0 && '“Bé hãy giữ máy chụp song song với trang vở, trong phòng có đủ ánh sáng để trang vở hiện rõ nét nhất nhé!”'}
                      {activeWorkflowStep === 1 && '“AI nhận diện theo đúng tỷ lệ ô ly 2x2mm và 5x5mm của các nhà xuất bản sách giáo khoa tại Việt Nam.”'}
                      {activeWorkflowStep === 2 && '“Nếu bé quên cộng số nhớ ở hàng chục, hệ thống sẽ khoanh tròn nhẹ nhàng cột chục và hỏi: ‘Số nhớ 1 ở hàng đơn vị đâu rồi nhỉ?’.”'}
                      {activeWorkflowStep === 3 && '“Mỗi lần bé tự mình tìm ra đáp án đúng, một ngôi sao vàng sẽ được tặng vào sổ tích lũy tiến bộ của bé!”'}
                    </Typography>
                  </Box>
                </Box>

                {/* Progress Indicators & Step Advancement */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 2,
                    mt: 4,
                    pt: 2.5,
                    borderTop: '1px solid #E2E8F0',
                  }}
                >
                  <Box sx={{ display: 'flex', gap: 1, flex: 1, minWidth: 160 }}>
                    {WORKFLOW_STEPS.map((_, idx) => (
                      <Box
                        key={idx}
                        onClick={() => setActiveWorkflowStep(idx)}
                        role="button"
                        aria-label={`Xem bước ${idx + 1}`}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setActiveWorkflowStep(idx);
                          }
                        }}
                        sx={{
                          flex: 1,
                          height: 6,
                          borderRadius: 1,
                          bgcolor: activeWorkflowStep === idx ? '#2563EB' : '#CBD5E1',
                          cursor: 'pointer',
                          transition: 'background-color 200ms ease',
                          '&:focus-visible': { outline: '2px solid #2563EB' },
                        }}
                      />
                    ))}
                  </Box>
                  <Button
                    size="small"
                    variant="text"
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => setActiveWorkflowStep((prev) => (prev + 1) % WORKFLOW_STEPS.length)}
                    sx={{ fontWeight: 800, color: '#2563EB', '&:hover': { bgcolor: '#EFF6FF' } }}
                  >
                    {activeWorkflowStep === WORKFLOW_STEPS.length - 1 ? 'Xem lại từ đầu' : 'Bước tiếp theo'}
                  </Button>
                </Box>
              </Card>
            </Grid>
          </Grid>

          {/* Socratic Contrast Comparison Box */}
          <Box
            sx={{
              p: { xs: 3, md: 4.5 },
              borderRadius: 4,
              bgcolor: '#F8FAFC',
              border: '1.5px solid #E2E8F0',
            }}
          >
            <Box sx={{ mb: 3, textAlign: 'center' }}>
              <Typography variant="overline" sx={{ fontWeight: 800, color: '#64748B', letterSpacing: '0.06em', fontSize: '0.75rem' }}>
                SO SÁNH TRIẾT LÝ TIẾP CẬN
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 900, color: '#0F172A', mt: 0.5 }}>
                Tại sao gợi mở tư duy tốt hơn đưa sẵn đáp số?
              </Typography>
            </Box>
            <Grid container spacing={3} sx={{ alignItems: 'stretch' }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box
                  sx={{
                    p: 3,
                    borderRadius: 3,
                    bgcolor: '#FFFFFF',
                    border: '1.5px solid #FECDD3',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5, flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 900, color: '#BE123C', display: 'flex', alignItems: 'center', gap: 1 }}>
                        ✕ Giải bài hộ thương mại
                      </Typography>
                      <Chip label="Ăn xổi · Thụ động" size="small" sx={{ height: 20, fontSize: '0.68rem', fontWeight: 800, bgcolor: '#FFF1F2', color: '#BE123C', border: '1px solid #FECDD3' }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.65 }}>
                      Đưa ngay đáp án số cuối cùng. Học sinh chỉ việc chép vào vở mà không hiểu bản chất bước tính hay quy tắc cộng số nhớ. Trẻ dần mất đi khả năng tự suy luận và tự giải quyết vấn đề khi gặp dạng đề mới.
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <Box
                  sx={{
                    p: 3,
                    borderRadius: 3,
                    bgcolor: '#FFFFFF',
                    border: '2px solid #10B981',
                    boxShadow: '0 8px 24px -4px rgba(16, 185, 129, 0.14)',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5, flexWrap: 'wrap', gap: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 900, color: '#047857', display: 'flex', alignItems: 'center', gap: 1 }}>
                        ✓ Đồng hành Socratic (MathVision Kids)
                      </Typography>
                      <Chip label="Chuẩn Sư Phạm Việt Nam" size="small" sx={{ height: 20, fontSize: '0.68rem', fontWeight: 800, bgcolor: '#ECFDF5', color: '#047857', border: '1px solid #A7F3D0' }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#334155', lineHeight: 1.65 }}>
                      Phân tích từng bước đặt tính ô ly, khoanh vùng chính xác điểm nhầm lẫn (cột đơn vị, cột chục, số nhớ) và đặt câu hỏi gợi mở để bé tự nhẩm tính và tìm ra kết quả đúng. Trẻ nhớ lâu và hào hứng tự học.
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Box>
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
            <Typography variant="h2" sx={{ mb: 1.5, fontSize: { xs: '2rem', md: '2.5rem' }, fontWeight: 900, letterSpacing: '-0.02em' }}>
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
                  borderRadius: 4,
                  bgcolor: '#FFFFFF',
                  border: '1.5px solid #E2E8F0',
                  borderTop: '3.5px solid #2563EB',
                  boxShadow: '0 4px 20px -4px rgba(15, 23, 42, 0.05)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 16px 32px -4px rgba(15, 23, 42, 0.08)',
                    borderColor: '#CBD5E1',
                  },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#EFF6FF', color: '#2563EB', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <LightbulbIcon sx={{ fontSize: 24 }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                      Không giải hộ bài tập
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.68, mb: 2.5 }}>
                    Khác với các ứng dụng chụp ảnh giải bài ăn xổi, MathVision Kids hướng tới bồi dưỡng tư duy toán học độc lập. Trẻ được gợi mở từng bước để tự tìm ra kết quả đúng.
                  </Typography>
                </Box>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9' }}>
                  <Chip
                    label="Không đưa đáp án sẵn"
                    size="small"
                    sx={{ height: 22, fontSize: '0.72rem', fontWeight: 800, bgcolor: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE', borderRadius: 1 }}
                  />
                </Box>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                className="hover-elevate"
                sx={{
                  p: 3.5,
                  borderRadius: 4,
                  bgcolor: '#FFFFFF',
                  border: '1.5px solid #E2E8F0',
                  borderTop: '3.5px solid #059669',
                  boxShadow: '0 4px 20px -4px rgba(15, 23, 42, 0.05)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 16px 32px -4px rgba(15, 23, 42, 0.08)',
                    borderColor: '#CBD5E1',
                  },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#ECFDF5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <VerifiedUserIcon sx={{ fontSize: 24 }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                      Thầy cô là người định đoạt
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.68, mb: 2.5 }}>
                    AI đóng vai trò người trợ giảng chấm sơ bộ. Mọi bài thi hoặc bài tập có độ tin cậy thấp đều được chuyển đến giáo viên để thẩm định và phê duyệt điểm số cuối cùng.
                  </Typography>
                </Box>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9' }}>
                  <Chip
                    label="Giáo viên phê duyệt 100%"
                    size="small"
                    sx={{ height: 22, fontSize: '0.72rem', fontWeight: 800, bgcolor: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0', borderRadius: 1 }}
                  />
                </Box>
              </Box>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                className="hover-elevate"
                sx={{
                  p: 3.5,
                  borderRadius: 4,
                  bgcolor: '#FFFFFF',
                  border: '1.5px solid #E2E8F0',
                  borderTop: '3.5px solid #D97706',
                  boxShadow: '0 4px 20px -4px rgba(15, 23, 42, 0.05)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 16px 32px -4px rgba(15, 23, 42, 0.08)',
                    borderColor: '#CBD5E1',
                  },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box sx={{ width: 44, height: 44, borderRadius: 2.5, bgcolor: '#FFFBEB', color: '#B45309', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <SecurityIcon sx={{ fontSize: 24 }} />
                    </Box>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                      Bảo vệ dữ liệu học sinh
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.68, mb: 2.5 }}>
                    Thông tin định danh của bé (tên, trường, lớp) được che an toàn trực tiếp từ thiết bị. Không chứa quảng cáo, không cơ chế ép streak hay gamification gây nghiện.
                  </Typography>
                </Box>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9' }}>
                  <Chip
                    label="Xem lại vùng che trước khi gửi"
                    size="small"
                    sx={{ height: 22, fontSize: '0.72rem', fontWeight: 800, bgcolor: '#FFFBEB', color: '#B45309', border: '1px solid #FDE68A', borderRadius: 1 }}
                  />
                </Box>
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
          <Typography variant="h2" sx={{ fontWeight: 900, color: '#FFFFFF', mb: 2.5, fontSize: { xs: '2rem', sm: '2.75rem' }, lineHeight: 1.18, letterSpacing: '-0.02em' }}>
            Sẵn sàng đồng hành cùng bé chinh phục môn Toán?
          </Typography>
          <Typography variant="body1" sx={{ color: '#CBD5E1', mb: 5, maxWidth: 620, mx: 'auto', fontSize: '1.1rem', lineHeight: 1.68 }}>
            Đăng nhập bằng tài khoản MathVision của bạn.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap', alignItems: 'center' }}>
            {user ? (
              <>
                <Button
                  component={RouterLink}
                  to={getDestinationPath(user.role)}
                  variant="contained"
                  size="large"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    bgcolor: isStudent ? '#2563EB' : user.role?.includes('TEACHER') ? '#059669' : '#0F172A',
                    color: '#FFFFFF',
                    px: 4.5,
                    py: 1.6,
                    fontSize: '1.05rem',
                    fontWeight: 900,
                    borderRadius: 3,
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
                    border: user.role?.includes('ADMIN') ? '1px solid #334155' : undefined,
                    '&:hover': {
                      bgcolor: isStudent ? '#1D4ED8' : user.role?.includes('TEACHER') ? '#047857' : '#1E293B',
                    },
                  }}
                >
                  Tiếp tục
                </Button>
                <Button
                  component={RouterLink}
                  to="/logout"
                  variant="outlined"
                  size="large"
                  sx={{
                    borderColor: 'rgba(255, 255, 255, 0.35) !important',
                    color: '#FFFFFF !important',
                    bgcolor: 'rgba(255, 255, 255, 0.08) !important',
                    px: 3.5,
                    py: 1.6,
                    fontSize: '1rem',
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
                  Đăng xuất
                </Button>
              </>
            ) : (
              <>
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
                  Đăng nhập
                </Button>
              </>
            )}
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
