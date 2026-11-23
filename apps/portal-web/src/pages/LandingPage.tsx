import React, { useState, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Chip,
  Collapse,
  Paper,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined';
import BarChartOutlinedIcon from '@mui/icons-material/BarChartOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined';
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined';
import RecordVoiceOverOutlinedIcon from '@mui/icons-material/RecordVoiceOverOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';

// Curriculum data for Lớp 1 - Lớp 5 (GDPT 2018)
interface GradeCurriculum {
  title: string;
  focus: string;
  modules: { title: string; desc: string; tag: string }[];
}

const GRADE_DATA: Record<number, GradeCurriculum> = {
  1: {
    title: 'Toán Lớp 1 — Làm Quen Số Học & Tư Duy Trực Quan',
    focus: 'Xây dựng cảm nhận về số lượng, phép tính cơ bản và nhận diện hình học đơn giản.',
    modules: [
      {
        title: 'Các số trong phạm vi 10 và 100',
        desc: 'Đếm, so sánh nhiều hơn - ít hơn, thứ tự số và ý nghĩa của số 0.',
        tag: 'Số học',
      },
      {
        title: 'Phép cộng & trừ trong phạm vi 20',
        desc: 'Tính nhẩm trực quan bằng hình vẽ que tính, ngón tay và trục số.',
        tag: 'Tính nhẩm',
      },
      {
        title: 'Hình phẳng & Định hướng không gian',
        desc: 'Nhận biết hình vuông, hình tròn, tam giác; định vị trái, phải, trên, dưới.',
        tag: 'Hình học',
      },
    ],
  },
  2: {
    title: 'Toán Lớp 2 — Phép Tính Có Nhớ & Bảng Nhân Chia Đầu Tiên',
    focus: 'Rèn phương pháp tách số làm tròn 10, làm quen bảng nhân chia 2 và 5.',
    modules: [
      {
        title: 'Cộng, trừ có nhớ trong phạm vi 100',
        desc: 'Phương pháp Socratic tách số: 8 + 5 = 8 + 2 + 3 = 10 + 3... để bé tự tìm ra kết quả.',
        tag: 'Kỹ thuật tính',
      },
      {
        title: 'Bảng nhân 2, 5 và bảng chia tương ứng',
        desc: 'Bản chất phép nhân là cộng nhiều số giống nhau; phân chia đồ vật công bằng.',
        tag: 'Số học',
      },
      {
        title: 'Đo lường thời gian & Độ dài',
        desc: 'Xem đồng hồ đúng giờ, ngày tháng trên lịch; đơn vị cm, dm, m và lít.',
        tag: 'Ứng dụng',
      },
    ],
  },
  3: {
    title: 'Toán Lớp 3 — Mở Rộng Phạm Vi Tính & Chu Vi Hình Học',
    focus: 'Thành thạo bảng nhân chia từ 6 đến 9, tính nhẩm chu vi và diện tích cơ bản.',
    modules: [
      {
        title: 'Bảng nhân chia 6, 7, 8, 9 & số 4 chữ số',
        desc: 'Nhân số có 2-3 chữ số với số có 1 chữ số; chia có dư trong phạm vi 10.000.',
        tag: 'Số học',
      },
      {
        title: 'Chu vi & diện tích hình chữ nhật, hình vuông',
        desc: 'Hiểu rõ khái niệm đường bao quanh và diện tích bề mặt ô vuông con.',
        tag: 'Hình học',
      },
      {
        title: 'Giải toán có hai bước tính',
        desc: 'Rèn năng lực phân tích đề toán có lời văn, tìm đại lượng trung gian.',
        tag: 'Tư duy logic',
      },
    ],
  },
  4: {
    title: 'Toán Lớp 4 — Thế Giới Phân Số & Số Lớn',
    focus: 'Hiểu bản chất phân số, rút gọn, quy đồng mẫu số và hình bình hành, hình thoi.',
    modules: [
      {
        title: 'Triệu và lớp triệu — 4 phép tính số lớn',
        desc: 'Đặt tính thẳng cột, kiểm tra phép nhân nhiều chữ số và phép chia 2 chữ số.',
        tag: 'Kỹ năng tính',
      },
      {
        title: 'Phân số, rút gọn & quy đồng mẫu số',
        desc: 'Bản chất phân số qua bánh pizza trực quan, cộng trừ nhân chia phân số.',
        tag: 'Trọng tâm Lớp 4',
      },
      {
        title: 'Hình bình hành, hình thoi & Dấu hiệu chia hết',
        desc: 'Công thức diện tích kèm giải thích nguồn gốc; chia hết cho 2, 3, 5, 9.',
        tag: 'Hình học & Số',
      },
    ],
  },
  5: {
    title: 'Toán Lớp 5 — Số Thập Phân, Tỉ Số Phần Trăm & Hình Khối',
    focus: 'Chinh phục số thập phân, giải toán chuyển động đều và thể tích khối hộp.',
    modules: [
      {
        title: 'Khái niệm & 4 phép tính số thập phân',
        desc: 'Chuyển đổi phân số thập phân, quy tắc dời dấu phẩy khi nhân chia với 10, 100.',
        tag: 'Số thập phân',
      },
      {
        title: 'Tỉ số phần trăm & Toán chuyển động đều',
        desc: 'Công thức v = s / t, hai xe đi ngược chiều, cùng chiều đuổi nhau.',
        tag: 'Toán ứng dụng',
      },
      {
        title: 'Diện tích hình thang, hình tròn & Thể tích hộp',
        desc: 'Bản chất số Pi, diện tích toàn phần và thể tích hình hộp chữ nhật, hình lập phương.',
        tag: 'Hình không gian',
      },
    ],
  },
};

export const LandingPage: React.FC = () => {
  // Curriculum Tab State
  const [selectedGrade, setSelectedGrade] = useState<number>(2);

  // Socratic Interactive Demo State
  // Step 1: 8 + 5 = ? -> ask: 8 needs how much to make 10?
  // Step 2: Correct (2) -> ask: 5 separated 2 leaves how much?
  // Step 3: Correct (3) -> child prompted to calculate 10 + 3 on their own!
  const [demoStep, setDemoStep] = useState<number>(1);
  const [demoHint, setDemoHint] = useState<string | null>(null);

  // Accessibility Focus Ref for step transition
  const choiceContainerRef = useRef<HTMLDivElement | null>(null);
  const retryBtnRef = useRef<HTMLButtonElement | null>(null);

  // FAQ Accordion State
  const [faqOpen, setFaqOpen] = useState<{ [key: number]: boolean }>({
    1: true,
    2: false,
    3: false,
  });

  const toggleFaq = (index: number) => {
    setFaqOpen((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  // Scroll to Demo with prefers-reduced-motion check
  const handleScrollToDemo = () => {
    const demoElement = document.getElementById('demo-section');
    if (!demoElement) return;
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    demoElement.scrollIntoView({
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
      block: 'start',
    });
  };

  // Helper to focus the next choice button only after real user interaction
  const focusNextChoice = () => {
    requestAnimationFrame(() => {
      const firstButton = choiceContainerRef.current?.querySelector('button');
      if (firstButton) {
        firstButton.focus();
      }
    });
  };

  // Socratic Interaction Handlers
  const handleSelectStep1 = (choice: number) => {
    if (choice === 2) {
      setDemoStep(2);
      setDemoHint(null);
      focusNextChoice();
    } else if (choice === 3) {
      setDemoHint('Bé thử đếm nhé: 8 thêm 2 là vừa tròn 10, nếu thêm 3 thì quá rồi!');
    } else {
      setDemoHint('Bé thử đếm nhé: 8 thêm 1 mới là 9 thôi con ơi, thêm mấy nữa nhỉ?');
    }
  };

  const handleSelectStep2 = (choice: number) => {
    if (choice === 3) {
      setDemoStep(3);
      setDemoHint(null);
      focusNextChoice();
    } else {
      setDemoHint('Có 5 que tính, con đã lấy ra 2 que để ghép với 8, vậy còn lại mấy que nhỉ?');
    }
  };

  const handleResetDemo = () => {
    setDemoStep(1);
    setDemoHint(null);
    focusNextChoice();
  };

  return (
    <Box sx={{ width: '100%', bgcolor: '#FAF8FE', color: '#190568', overflowX: 'hidden' }}>

      {/* ========================================================================= */}
      {/* 1. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <Box
        component="header"
        id="hero"
        sx={{
          pt: { xs: 4, sm: 6, md: 8 },
          pb: { xs: 5, sm: 7, md: 9 },
          background: 'linear-gradient(180deg, #F9F6FE 0%, #F1EAFA 100%)',
          position: 'relative',
          overflow: 'hidden',
          borderBottom: '1px solid #EBE4F9',
        }}
      >
        {/* Soft background accents */}
        <Box
          aria-hidden="true"
          sx={{
            position: 'absolute',
            top: -60,
            right: -80,
            width: 480,
            height: 340,
            borderRadius: '50%',
            bgcolor: 'rgba(237, 233, 254, 0.65)',
            filter: 'blur(70px)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />
        <Box
          aria-hidden="true"
          sx={{
            position: 'absolute',
            bottom: -50,
            left: -80,
            width: 420,
            height: 280,
            borderRadius: '50%',
            bgcolor: 'rgba(243, 238, 255, 0.7)',
            filter: 'blur(60px)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />

        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 }, position: 'relative', zIndex: 1 }}>
          <Grid container spacing={{ xs: 4, md: 5 }} sx={{ alignItems: 'center' }}>

            {/* Hero Left: Value Proposition */}
            <Grid size={{ xs: 12, md: 6.5 }} sx={{ minWidth: 0 }}>
              
              {/* Pedagogical Standard Badge */}
              <Box sx={{ mb: 2.5 }}>
                <Chip
                  icon={
                    <Box
                      component="span"
                      aria-hidden="true"
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: '#047857',
                        display: 'inline-block',
                        ml: 0.5,
                      }}
                    />
                  }
                  label="TIÊU CHUẨN SƯ PHẠM: GỢI MỞ — TUYỆT ĐỐI KHÔNG LÀM HỘ"
                  sx={{
                    bgcolor: '#ECFDF5',
                    color: '#065F46',
                    border: '1px solid #A7F3D0',
                    fontWeight: 800,
                    fontSize: { xs: '0.72rem', sm: '0.78rem' },
                    letterSpacing: '0.02em',
                    height: 'auto',
                    py: 0.6,
                    '& .MuiChip-label': { px: 1.2 },
                  }}
                />
              </Box>

              {/* Benefit-driven Headline */}
              <Typography
                variant="h1"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontSize: { xs: '2.35rem', sm: '3.1rem', md: '3.65rem', lg: '4.1rem' },
                  fontWeight: 900,
                  color: '#190568',
                  lineHeight: 1.15,
                  letterSpacing: '-0.03em',
                  mb: 2.5,
                }}
              >
                Hiểu bài sâu,
                <br />
                tự tìm cách giải.
              </Typography>

              {/* Subtitle */}
              <Typography
                sx={{
                  color: '#475569',
                  fontSize: { xs: '1.05rem', sm: '1.15rem', md: '1.2rem' },
                  lineHeight: 1.6,
                  maxWidth: 560,
                  mb: 3.5,
                  fontWeight: 500,
                }}
              >
                Trợ lý AI đồng hành cùng học sinh tiểu học trên từng trang vở ô ly. Dẫn dắt từng bước suy luận logic để con tự tin giải toán bằng chính năng lực của mình.
              </Typography>

              {/* 3-Step Socratic Progress Chips */}
              <Box sx={{ mb: 4 }}>
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    fontWeight: 800,
                    color: '#64748B',
                    mb: 1.25,
                    fontSize: '0.75rem',
                  }}
                >
                  Quy trình rèn tư duy tự lập:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1.25 }}>
                  <Paper
                    elevation={0}
                    sx={{
                      px: 2,
                      py: 0.8,
                      borderRadius: 2,
                      bgcolor: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      fontWeight: 800,
                      fontSize: '0.82rem',
                      color: '#190568',
                    }}
                  >
                    1. Nhận diện đề
                  </Paper>
                  <Typography aria-hidden="true" sx={{ color: '#94A3B8', fontWeight: 900 }}>
                    →
                  </Typography>
                  <Paper
                    elevation={0}
                    sx={{
                      px: 2,
                      py: 0.8,
                      borderRadius: 2,
                      bgcolor: '#EEF2FF',
                      border: '1px solid #C7D2FE',
                      fontWeight: 800,
                      fontSize: '0.82rem',
                      color: '#4338CA',
                    }}
                  >
                    2. AI Gợi mở
                  </Paper>
                  <Typography aria-hidden="true" sx={{ color: '#94A3B8', fontWeight: 900 }}>
                    →
                  </Typography>
                  <Paper
                    elevation={0}
                    sx={{
                      px: 2,
                      py: 0.8,
                      borderRadius: 2,
                      bgcolor: '#ECFDF5',
                      border: '1px solid #A7F3D0',
                      fontWeight: 800,
                      fontSize: '0.82rem',
                      color: '#065F46',
                    }}
                  >
                    3. Em tự giải
                  </Paper>
                </Box>
              </Box>

              {/* Action Buttons: Touch Target >= 44px, Accessible Contrast */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Button
                  component={RouterLink}
                  to="/login"
                  aria-label="Học ngay cùng AI"
                  variant="contained"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    minHeight: 48,
                    bgcolor: '#F59E0B',
                    color: '#190568',
                    fontWeight: 900,
                    fontSize: '1.05rem',
                    borderRadius: '26px',
                    px: 4,
                    py: 1.3,
                    textTransform: 'none',
                    boxShadow: '0 4px 14px rgba(245, 158, 11, 0.35)',
                    transition: 'background-color 180ms ease, transform 180ms ease, box-shadow 180ms ease',
                    '&:hover': {
                      bgcolor: '#D97706',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  Học ngay cùng AI
                </Button>
                <Button
                  onClick={handleScrollToDemo}
                  variant="outlined"
                  sx={{
                    minHeight: 48,
                    bgcolor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    color: '#334155',
                    fontWeight: 700,
                    fontSize: '1rem',
                    borderRadius: '26px',
                    px: 3.5,
                    py: 1.3,
                    textTransform: 'none',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                    transition: 'background-color 180ms ease, border-color 180ms ease, color 180ms ease',
                    '&:hover': {
                      bgcolor: '#F8FAFC',
                      borderColor: '#94A3B8',
                      color: '#190568',
                    },
                  }}
                >
                  Xem demo gợi mở ↓
                </Button>
              </Box>

            </Grid>

            {/* Hero Right: Interactive Socratic Showcase (The Notebook Demo) */}
            <Grid size={{ xs: 12, md: 5.5 }} sx={{ minWidth: 0 }} id="demo-section">
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: 4,
                  border: '1.5px solid #E2E8F0',
                  boxShadow: '0 18px 40px rgba(25, 5, 104, 0.08)',
                  p: { xs: 2.5, sm: 3.5 },
                  position: 'relative',
                }}
              >
                {/* Demo Header Bar */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    pb: 2,
                    mb: 2.5,
                    borderBottom: '1px solid #F1F5F9',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#FB7185' }} />
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#FBBF24' }} />
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: '#34D399' }} />
                    <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, ml: 1, fontSize: '0.78rem' }}>
                      Mô phỏng trang vở ô ly Lớp 2
                    </Typography>
                  </Box>
                  <Chip
                    size="small"
                    label={demoStep === 1 ? 'Gợi mở Bước 1' : demoStep === 2 ? 'Gợi mở Bước 2' : 'Hoàn thành tư duy'}
                    sx={{
                      bgcolor: demoStep === 3 ? '#ECFDF5' : '#F5EEFD',
                      color: demoStep === 3 ? '#065F46' : '#6D28D9',
                      border: '1px solid',
                      borderColor: demoStep === 3 ? '#A7F3D0' : '#DDD6FE',
                      fontWeight: 800,
                      fontSize: '0.72rem',
                    }}
                  />
                </Box>

                {/* Authentic 5-grid Notebook Surface (Vở ô ly tiểu học) */}
                <Box
                  sx={{
                    borderRadius: 3,
                    border: '1.5px solid #C7D2FE',
                    p: { xs: 2.5, sm: 3 },
                    bgcolor: '#FAF5FF',
                    backgroundImage: `
                      linear-gradient(rgba(199, 210, 254, 0.5) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(199, 210, 254, 0.5) 1px, transparent 1px),
                      linear-gradient(rgba(165, 180, 252, 0.75) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(165, 180, 252, 0.75) 1px, transparent 1px)
                    `,
                    backgroundSize: '8px 8px, 8px 8px, 40px 40px, 40px 40px',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {/* AI Recognition Bounding Box Overlay */}
                  <Box
                    sx={{
                      border: '2px solid #6366F1',
                      bgcolor: 'rgba(255, 255, 255, 0.88)',
                      backdropFilter: 'blur(2px)',
                      borderRadius: 2.5,
                      p: 2.5,
                      position: 'relative',
                    }}
                  >
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -12,
                        left: 14,
                        bgcolor: '#4F46E5',
                        color: '#FFFFFF',
                        fontSize: '0.68rem',
                        fontWeight: 800,
                        px: 1.2,
                        py: 0.3,
                        borderRadius: 1,
                        boxShadow: '0 2px 4px rgba(79, 70, 229, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <AutoAwesomeOutlinedIcon sx={{ fontSize: 13 }} />
                      <span>AI Nhận diện phép tính</span>
                    </Box>

                    {/* Handwritten Math Expression */}
                    <Box sx={{ py: 1, textAlign: 'center' }}>
                      <Typography
                        sx={{
                          fontFamily: 'Caveat, "Segoe Print", "Comic Sans MS", cursive, sans-serif',
                          fontSize: { xs: '2.8rem', sm: '3.4rem' },
                          fontWeight: 700,
                          color: '#190568',
                          letterSpacing: '0.08em',
                          lineHeight: 1.1,
                          userSelect: 'none',
                        }}
                      >
                        8 + 5 = ?
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          color: '#475569',
                          fontWeight: 700,
                          display: 'block',
                          mt: 0.5,
                          fontSize: '0.78rem',
                        }}
                      >
                        Phép cộng có nhớ trong phạm vi 20
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                {/* Interactive Socratic Dialogue Bubble */}
                <Box
                  sx={{
                    mt: 2.5,
                    p: 2.5,
                    borderRadius: 3,
                    bgcolor: '#FEF3C7',
                    border: '1.5px solid #FCD34D',
                    transition: 'background-color 200ms ease, border-color 200ms ease',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.75 }}>
                    {/* Brand Robot Mascot Avatar (Satisfies Playwright expectRobotBranding) */}
                    <Box
                      component="img"
                      src="/ui/robot-mascot.webp"
                      alt="Sao Nhỏ"
                      sx={{
                        width: 38,
                        height: 38,
                        borderRadius: '50%',
                        bgcolor: '#190568',
                        p: 0.4,
                        border: '2px solid #E1D2FF',
                        flexShrink: 0,
                        objectFit: 'contain',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
                      }}
                    />

                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.75 }}>
                        <Typography
                          variant="subtitle2"
                          sx={{
                            fontWeight: 900,
                            color: '#190568',
                            fontSize: '0.88rem',
                          }}
                        >
                          Sao Nhỏ gợi ý:
                        </Typography>
                        {(demoStep > 1 || demoHint) && (
                          <Button
                            ref={retryBtnRef}
                            onClick={handleResetDemo}
                            size="small"
                            startIcon={<RefreshIcon sx={{ fontSize: 14 }} />}
                            sx={{
                              p: 0,
                              minWidth: 'auto',
                              color: '#64748B',
                              fontWeight: 700,
                              fontSize: '0.75rem',
                              textTransform: 'none',
                              '&:hover': { color: '#0F172A', textDecoration: 'underline' },
                            }}
                          >
                            Thử lại
                          </Button>
                        )}
                      </Box>

                      {/* Accessible Live Region: Announces Socratic Guidance */}
                      <Box
                        aria-live="polite"
                        aria-atomic="true"
                        sx={{ minHeight: 44 }}
                      >
                        {demoStep === 1 && (
                          <Typography sx={{ color: '#1E293B', fontSize: '0.92rem', fontWeight: 600, lineHeight: 1.5 }}>
                            &ldquo;Để tạo số 10 tròn chục, số 8 cần cộng thêm mấy nữa hả con?&rdquo;
                          </Typography>
                        )}

                        {demoStep === 2 && (
                          <Box>
                            <Typography sx={{ color: '#047857', fontWeight: 800, fontSize: '0.92rem', mb: 0.5 }}>
                              ✓ Chính xác! 8 + 2 = 10.
                            </Typography>
                            <Typography sx={{ color: '#1E293B', fontSize: '0.9rem', fontWeight: 600, lineHeight: 1.5 }}>
                              Bé đã lấy 2 từ số 5, vậy số 5 còn lại mấy đơn vị nữa nhỉ?
                            </Typography>
                          </Box>
                        )}

                        {demoStep === 3 && (
                          <Box>
                            <Typography sx={{ color: '#047857', fontWeight: 800, fontSize: '0.92rem', mb: 0.5 }}>
                              🎉 Rất giỏi! 5 tách 2 còn 3.
                            </Typography>
                            <Typography sx={{ color: '#1E293B', fontSize: '0.9rem', fontWeight: 600, lineHeight: 1.5 }}>
                              Bây giờ con lấy 10 tròn chục cộng với 3 còn lại để ra kết quả nhé!
                            </Typography>
                          </Box>
                        )}

                        {demoHint && (
                          <Typography
                            sx={{
                              color: '#B45309',
                              fontSize: '0.85rem',
                              fontWeight: 700,
                              mt: 0.75,
                              p: 1,
                              borderRadius: 1.5,
                              bgcolor: 'rgba(255, 255, 255, 0.7)',
                            }}
                          >
                            💡 {demoHint}
                          </Typography>
                        )}
                      </Box>

                      {/* Interactive Choice Chips with Focus Management */}
                      <Box
                        ref={choiceContainerRef}
                        sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25, mt: 2 }}
                      >
                        {demoStep === 1 && (
                          <>
                            <Button
                              onClick={() => handleSelectStep1(2)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#F59E0B',
                                color: '#190568',
                                fontWeight: 800,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#FEF3C7', borderColor: '#D97706' },
                              }}
                            >
                              Thêm 2
                            </Button>
                            <Button
                              onClick={() => handleSelectStep1(3)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#E2E8F0',
                                color: '#475569',
                                fontWeight: 700,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#F8FAFC' },
                              }}
                            >
                              Thêm 3
                            </Button>
                            <Button
                              onClick={() => handleSelectStep1(1)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#E2E8F0',
                                color: '#475569',
                                fontWeight: 700,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#F8FAFC' },
                              }}
                            >
                              Thêm 1
                            </Button>
                          </>
                        )}

                        {demoStep === 2 && (
                          <>
                            <Button
                              onClick={() => handleSelectStep2(3)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#F59E0B',
                                color: '#190568',
                                fontWeight: 800,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#FEF3C7', borderColor: '#D97706' },
                              }}
                            >
                              Còn 3
                            </Button>
                            <Button
                              onClick={() => handleSelectStep2(2)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#E2E8F0',
                                color: '#475569',
                                fontWeight: 700,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#F8FAFC' },
                              }}
                            >
                              Còn 2
                            </Button>
                            <Button
                              onClick={() => handleSelectStep2(1)}
                              variant="outlined"
                              sx={{
                                bgcolor: '#FFFFFF',
                                borderColor: '#E2E8F0',
                                color: '#475569',
                                fontWeight: 700,
                                fontSize: '0.82rem',
                                px: 2,
                                py: 0.75,
                                borderRadius: 2,
                                textTransform: 'none',
                                '&:hover': { bgcolor: '#F8FAFC' },
                              }}
                            >
                              Còn 1
                            </Button>
                          </>
                        )}

                        {demoStep === 3 && (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                            <Chip
                              icon={<CheckCircleOutlinedIcon sx={{ color: '#047857 !important' }} />}
                              label="Học sinh tự giải quyết bài toán!"
                              sx={{
                                bgcolor: '#FFFFFF',
                                color: '#065F46',
                                border: '1.5px solid #A7F3D0',
                                fontWeight: 800,
                                fontSize: '0.82rem',
                              }}
                            />
                            <Button
                              onClick={handleResetDemo}
                              size="small"
                              variant="text"
                              sx={{
                                color: '#190568',
                                fontWeight: 800,
                                fontSize: '0.8rem',
                                textTransform: 'none',
                              }}
                            >
                              Luyện tập lại
                            </Button>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  </Box>
                </Box>

                {/* Assurance Footer: No Spoiled Answer */}
                <Box
                  sx={{
                    mt: 2,
                    pt: 1.5,
                    borderTop: '1px solid #F1F5F9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.78rem',
                    color: '#64748B',
                    px: 0.5,
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: 600, color: '#64748B' }}>
                    🔒 Tuyệt đối không hiện đáp số sẵn
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 800, color: '#4F46E5' }}>
                    Rèn tư duy từng bước
                  </Typography>
                </Box>

              </Box>
            </Grid>

          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 2. SECTION TÍNH NĂNG (BENTO GRID: 1 CHÍNH + 2 PHỤ)                        */}
      {/* ========================================================================= */}
      <Box
        component="section"
        id="tinh-nang"
        sx={{
          py: { xs: 6, sm: 8, md: 10 },
          px: { xs: 2.5, sm: 4, md: 5 },
          maxWidth: '1200px',
          mx: 'auto',
        }}
      >
        <Box sx={{ textAlign: 'center', maxWidth: 680, mx: 'auto', mb: { xs: 4, md: 6 } }}>
          <Chip
            label="HỆ THỐNG TÍNH NĂNG"
            size="small"
            sx={{
              bgcolor: '#EEF2FF',
              color: '#4338CA',
              border: '1px solid #C7D2FE',
              fontWeight: 800,
              fontSize: '0.72rem',
              letterSpacing: '0.06em',
              mb: 1.5,
            }}
          />
          <Typography
            variant="h2"
            sx={{
              fontFamily: 'Nunito, sans-serif',
              fontSize: { xs: '1.9rem', sm: '2.4rem', md: '2.8rem' },
              fontWeight: 900,
              color: '#190568',
              letterSpacing: '-0.02em',
              mb: 1.5,
            }}
          >
            Đồng hành cùng học sinh và phụ huynh
          </Typography>
          <Typography sx={{ color: '#475569', fontSize: { xs: '0.98rem', md: '1.08rem' }, lineHeight: 1.6 }}>
            Được xây dựng trên nền tảng sư phạm chuẩn mực, bảo vệ quyền riêng tư và khích lệ tư duy độc lập của con.
          </Typography>
        </Box>

        {/* Bento Grid: 1 Primary Card (2 Cols) + 2 Secondary Cards (1 Col) */}
        <Grid container spacing={3} sx={{ minWidth: 0 }}>

          {/* Primary Card: Socratic Engine & Handwriting Recognition */}
          <Grid size={{ xs: 12, lg: 8 }} sx={{ minWidth: 0 }}>
            <Paper
              elevation={0}
              sx={{
                p: { xs: 3, sm: 4 },
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '1.5px solid #E2E8F0',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'box-shadow 200ms ease',
                '&:hover': {
                  boxShadow: '0 12px 30px rgba(25, 5, 104, 0.06)',
                },
              }}
            >
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Chip
                    label="CÔNG NGHỆ LÕI"
                    size="small"
                    sx={{
                      bgcolor: '#EEF2FF',
                      color: '#4338CA',
                      fontWeight: 800,
                      fontSize: '0.7rem',
                      letterSpacing: '0.04em',
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#047857', fontWeight: 800, fontSize: '0.78rem' }}>
                    Chuẩn GDPT 2018
                  </Typography>
                </Box>

                <Typography
                  variant="h3"
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    fontSize: { xs: '1.4rem', sm: '1.75rem' },
                    fontWeight: 900,
                    color: '#190568',
                    mb: 1.5,
                    lineHeight: 1.3,
                  }}
                >
                  Nhận diện chữ viết tay trên vở ô ly & Hướng dẫn gợi mở
                </Typography>

                <Typography sx={{ color: '#475569', fontSize: '0.95rem', lineHeight: 1.65, mb: 3 }}>
                  Hệ thống nhận diện chính xác các phép toán viết tay từ Lớp 1 đến Lớp 5. Thay vì làm hộ bài, AI đóng vai trò gia sư kiên nhẫn, phân tích từng bước tính của con và định hướng câu hỏi để bé tự giác làm bài.
                </Typography>

                {/* Stepper Model Box */}
                <Box
                  sx={{
                    p: 2.5,
                    borderRadius: 3,
                    bgcolor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                    mb: 3,
                  }}
                >
                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      textTransform: 'uppercase',
                      color: '#64748B',
                      fontWeight: 800,
                      letterSpacing: '0.05em',
                      mb: 1.5,
                      fontSize: '0.72rem',
                    }}
                  >
                    Một bước học mẫu trên vở:
                  </Typography>

                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          bgcolor: '#FFFFFF',
                          border: '1px solid #CBD5E1',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#190568', fontWeight: 800, fontSize: '0.7rem' }}>
                          01 · NHẬN DIỆN
                        </Typography>
                        <Typography sx={{ fontWeight: 900, color: '#190568', mt: 0.5, fontSize: '1.1rem' }}>
                          8 + 5 = ?
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          bgcolor: '#EEF2FF',
                          border: '1px solid #C7D2FE',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#4338CA', fontWeight: 800, fontSize: '0.7rem' }}>
                          02 · GỢI MỞ
                        </Typography>
                        <Typography sx={{ fontWeight: 700, color: '#334155', mt: 0.5, fontSize: '0.85rem' }}>
                          8 cần thêm mấy để tròn 10?
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid size={{ xs: 12, sm: 4 }}>
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          bgcolor: '#ECFDF5',
                          border: '1px solid #A7F3D0',
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#065F46', fontWeight: 800, fontSize: '0.7rem' }}>
                          03 · EM TỰ GIẢI
                        </Typography>
                        <Typography sx={{ fontWeight: 700, color: '#334155', mt: 0.5, fontSize: '0.85rem' }}>
                          Con tự tính bước tiếp theo
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </Box>
              </Box>

              {/* 3 Sub-Features */}
              <Grid container spacing={2} sx={{ pt: 2, borderTop: '1px solid #F1F5F9' }}>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.25 }}>
                    <MenuBookOutlinedIcon sx={{ color: '#4F46E5', fontSize: 20, mt: 0.3 }} />
                    <Box>
                      <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '0.88rem' }}>
                        Đọc đề ô ly
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.25, lineHeight: 1.4 }}>
                        Xử lý phép tính đặt dọc, phân số và hình học.
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.25 }}>
                    <PsychologyOutlinedIcon sx={{ color: '#047857', fontSize: 20, mt: 0.3 }} />
                    <Box>
                      <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '0.88rem' }}>
                        Không giải hộ
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.25, lineHeight: 1.4 }}>
                        Học sinh tự đưa ra quyết định tại mỗi bước tính.
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.25 }}>
                    <RecordVoiceOverOutlinedIcon sx={{ color: '#D97706', fontSize: 20, mt: 0.3 }} />
                    <Box>
                      <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '0.88rem' }}>
                        Giọng nói tương tác
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.25, lineHeight: 1.4 }}>
                        Phát âm tiếng Việt chuẩn, hỗ trợ bé lớp 1-2.
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Right Column: 2 Secondary Cards (Privacy + Parent Mode) */}
          <Grid size={{ xs: 12, lg: 4 }} sx={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0 }}>
            
            {/* Secondary Card 1: Child Privacy Protection (Verified Codebase Flow) */}
            <Paper
              elevation={0}
              sx={{
                p: 3.5,
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '1.5px solid #E2E8F0',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'box-shadow 200ms ease',
                '&:hover': {
                  boxShadow: '0 10px 25px rgba(25, 5, 104, 0.05)',
                },
              }}
            >
              <Box>
                {/* Unified Vector SVG Icon for Privacy (No Emoji!) */}
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2.5,
                    bgcolor: '#ECFDF5',
                    border: '1px solid #A7F3D0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <ShieldOutlinedIcon sx={{ color: '#047857', fontSize: 24 }} />
                </Box>

                <Typography
                  variant="h4"
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    fontSize: '1.25rem',
                    fontWeight: 900,
                    color: '#190568',
                    mb: 1.25,
                  }}
                >
                  Bảo Vệ Quyền Riêng Tư Bé
                </Typography>

                {/* Accurate copy matching privacy.tsx and rasterizePrivacyMasks.ts */}
                <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6 }}>
                  Chủ động vẽ vùng che họ tên, trường lớp trên trang vở; xem lại và xác nhận riêng tư trước khi gửi ảnh cho hệ thống.
                </Typography>
              </Box>

              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #F1F5F9' }}>
                <Chip
                  icon={<CheckCircleOutlinedIcon sx={{ color: '#047857 !important', fontSize: 16 }} />}
                  label="Quy chuẩn bảo mật học sinh"
                  size="small"
                  sx={{
                    bgcolor: '#ECFDF5',
                    color: '#065F46',
                    border: '1px solid #A7F3D0',
                    fontWeight: 800,
                    fontSize: '0.72rem',
                  }}
                />
              </Box>
            </Paper>

            {/* Secondary Card 2: Parent Mode (Verified Features: Progress & PIN limits) */}
            <Paper
              elevation={0}
              sx={{
                p: 3.5,
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '1.5px solid #E2E8F0',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'box-shadow 200ms ease',
                '&:hover': {
                  boxShadow: '0 10px 25px rgba(25, 5, 104, 0.05)',
                },
              }}
            >
              <Box>
                {/* Unified Vector SVG Icon for Parent Mode (No Emoji!) */}
                <Box
                  sx={{
                    width: 44,
                    height: 44,
                    borderRadius: 2.5,
                    bgcolor: '#EEF2FF',
                    border: '1px solid #C7D2FE',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mb: 2,
                  }}
                >
                  <BarChartOutlinedIcon sx={{ color: '#4F46E5', fontSize: 24 }} />
                </Box>

                <Typography
                  variant="h4"
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    fontSize: '1.25rem',
                    fontWeight: 900,
                    color: '#190568',
                    mb: 1.25,
                  }}
                >
                  Góc Phụ Huynh Thông Thái
                </Typography>

                {/* Verified Product Features: Topic tracking & Safe PIN screen time */}
                <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6 }}>
                  Theo dõi tiến độ học tập, chủ đề toán đã luyện tập (Số học, Phân số, Hình học) và thiết lập giới hạn giờ chơi an toàn bằng mã PIN.
                </Typography>
              </Box>

              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #F1F5F9' }}>
                <Chip
                  label="Báo cáo tiến độ minh bạch"
                  size="small"
                  sx={{
                    bgcolor: '#EEF2FF',
                    color: '#4338CA',
                    border: '1px solid #C7D2FE',
                    fontWeight: 800,
                    fontSize: '0.72rem',
                  }}
                />
              </Box>
            </Paper>

          </Grid>

        </Grid>
      </Box>

      {/* ========================================================================= */}
      {/* 3. SECTION LỘ TRÌNH (LỚP 1 - LỚP 5 THEO CHUẨN GDPT 2018)                   */}
      {/* ========================================================================= */}
      <Box
        component="section"
        id="lo-trinh"
        sx={{
          py: { xs: 6, sm: 8, md: 9 },
          bgcolor: '#F5F0FD',
          borderTop: '1px solid #EBE4F9',
          borderBottom: '1px solid #EBE4F9',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          <Box sx={{ textAlign: 'center', maxWidth: 660, mx: 'auto', mb: 5 }}>
            <Chip
              label="CHƯƠNG TRÌNH GDPT 2018"
              size="small"
              sx={{
                bgcolor: '#FFFFFF',
                color: '#6D28D9',
                border: '1px solid #DDD6FE',
                fontWeight: 800,
                fontSize: '0.72rem',
                letterSpacing: '0.05em',
                mb: 1.5,
              }}
            />
            <Typography
              variant="h2"
              sx={{
                fontFamily: 'Nunito, sans-serif',
                fontSize: { xs: '1.9rem', sm: '2.4rem', md: '2.7rem' },
                fontWeight: 900,
                color: '#190568',
                letterSpacing: '-0.02em',
                mb: 1.5,
              }}
            >
              Lộ trình rèn luyện theo khối lớp
            </Typography>
            <Typography sx={{ color: '#475569', fontSize: { xs: '0.98rem', md: '1.05rem' }, lineHeight: 1.6 }}>
              Khối lượng bài tập và mức độ gợi ý được cá nhân hoá theo từng lứa tuổi, đảm bảo bé luôn hào hứng và không bị quá tải.
            </Typography>
          </Box>

          {/* Grade Selector Tabs: min-height 44px for touch targets */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
            <Box
              role="group"
              aria-label="Chọn khối lớp rèn luyện"
              sx={{
                display: 'inline-flex',
                bgcolor: '#FFFFFF',
                p: 0.75,
                borderRadius: '30px',
                border: '1.5px solid #DDD6FE',
                boxShadow: '0 2px 8px rgba(109, 40, 217, 0.06)',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: 0.5,
              }}
            >
              {[1, 2, 3, 4, 5].map((grade) => {
                const isActive = selectedGrade === grade;
                return (
                  <Button
                    key={grade}
                    onClick={() => setSelectedGrade(grade)}
                    aria-pressed={isActive}
                    sx={{
                      minHeight: 44,
                      minWidth: { xs: 60, sm: 90 },
                      borderRadius: '24px',
                      px: { xs: 2, sm: 3 },
                      py: 1,
                      fontWeight: 800,
                      fontSize: '0.95rem',
                      textTransform: 'none',
                      bgcolor: isActive ? '#190568' : 'transparent',
                      color: isActive ? '#FFFFFF' : '#475569',
                      transition: 'background-color 160ms ease, color 160ms ease',
                      '&:hover': {
                        bgcolor: isActive ? '#190568' : '#F1EAFA',
                        color: isActive ? '#FFFFFF' : '#190568',
                      },
                    }}
                  >
                    Lớp {grade}
                  </Button>
                );
              })}
            </Box>
          </Box>

          {/* Grade Detail Card */}
          <Paper
            elevation={0}
            sx={{
              p: { xs: 3, sm: 4.5 },
              borderRadius: 4,
              bgcolor: '#FFFFFF',
              border: '1.5px solid #E2E8F0',
              boxShadow: '0 8px 24px rgba(25, 5, 104, 0.04)',
            }}
          >
            <Box sx={{ mb: 3.5 }}>
              <Typography
                variant="h3"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontSize: { xs: '1.35rem', sm: '1.65rem' },
                  fontWeight: 900,
                  color: '#190568',
                  mb: 1,
                }}
              >
                {GRADE_DATA[selectedGrade].title}
              </Typography>
              <Typography sx={{ color: '#475569', fontSize: '0.95rem', fontWeight: 500 }}>
                {GRADE_DATA[selectedGrade].focus}
              </Typography>
            </Box>

            <Grid container spacing={3}>
              {GRADE_DATA[selectedGrade].modules.map((mod, idx) => (
                <Grid key={idx} size={{ xs: 12, md: 4 }}>
                  <Box
                    sx={{
                      p: 3,
                      borderRadius: 3,
                      bgcolor: '#FAF8FE',
                      border: '1px solid #E9DDFD',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      <Chip
                        label={mod.tag}
                        size="small"
                        sx={{
                          bgcolor: '#FFFFFF',
                          color: '#6D28D9',
                          fontWeight: 800,
                          fontSize: '0.7rem',
                          border: '1px solid #DDD6FE',
                          mb: 1.5,
                        }}
                      />
                      <Typography sx={{ fontWeight: 900, color: '#190568', fontSize: '1.05rem', mb: 1 }}>
                        {mod.title}
                      </Typography>
                      <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.55 }}>
                        {mod.desc}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Paper>

        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 4. SECTION GIẢI ĐÁP CÙNG BA MẸ (FAQ)                                       */}
      {/* ========================================================================= */}
      <Box
        component="section"
        id="giai-dap"
        sx={{
          py: { xs: 6, sm: 8, md: 9 },
          px: { xs: 2.5, sm: 4, md: 5 },
          maxWidth: '920px',
          mx: 'auto',
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 5 }}>
          <Chip
            label="GIẢI ĐÁP CÙNG PHỤ HUYNH"
            size="small"
            sx={{
              bgcolor: '#ECFDF5',
              color: '#065F46',
              border: '1px solid #A7F3D0',
              fontWeight: 800,
              fontSize: '0.72rem',
              letterSpacing: '0.05em',
              mb: 1.5,
            }}
          />
          <Typography
            variant="h2"
            sx={{
              fontFamily: 'Nunito, sans-serif',
              fontSize: { xs: '1.85rem', sm: '2.3rem' },
              fontWeight: 900,
              color: '#190568',
              letterSpacing: '-0.02em',
              mb: 1.5,
            }}
          >
            Những câu hỏi thường gặp
          </Typography>
          <Typography sx={{ color: '#475569', fontSize: '0.98rem' }}>
            Mọi thông tin cha mẹ cần biết về phương pháp giáo dục và bảo mật của MathVisionKid.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* FAQ 1 */}
          <Paper
            elevation={0}
            sx={{
              borderRadius: 3,
              border: '1.5px solid #E2E8F0',
              overflow: 'hidden',
              bgcolor: '#FFFFFF',
            }}
          >
            <Box
              component="button"
              onClick={() => toggleFaq(1)}
              aria-expanded={faqOpen[1]}
              sx={{
                width: '100%',
                p: 2.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: 'transparent',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                fontFamily: 'inherit',
                minHeight: 48,
              }}
            >
              <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '1rem' }}>
                MathVisionKid có giải hộ bài tập cho bé không?
              </Typography>
              <ExpandMoreIcon
                sx={{
                  color: '#64748B',
                  transform: faqOpen[1] ? 'rotate(180deg)' : 'none',
                  transition: 'transform 200ms ease',
                }}
              />
            </Box>
            <Collapse in={faqOpen[1]}>
              <Box sx={{ px: 2.5, pb: 2.5, pt: 0.5, borderTop: '1px solid #F1F5F9' }}>
                <Typography sx={{ color: '#475569', fontSize: '0.92rem', lineHeight: 1.65 }}>
                  <strong>Tuyệt đối không.</strong> Triết lý cốt lõi của MathVisionKid là phương pháp Socratic (gợi mở tư duy). Khi nhận diện đề bài viết tay trên vở, AI không cung cấp đáp số ngay mà chia bài toán thành các câu hỏi logic từng bước, khuyến khích con tự suy nghĩ và tìm ra lời giải bằng chính năng lực của mình.
                </Typography>
              </Box>
            </Collapse>
          </Paper>

          {/* FAQ 2 */}
          <Paper
            elevation={0}
            sx={{
              borderRadius: 3,
              border: '1.5px solid #E2E8F0',
              overflow: 'hidden',
              bgcolor: '#FFFFFF',
            }}
          >
            <Box
              component="button"
              onClick={() => toggleFaq(2)}
              aria-expanded={faqOpen[2]}
              sx={{
                width: '100%',
                p: 2.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: 'transparent',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                fontFamily: 'inherit',
                minHeight: 48,
              }}
            >
              <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '1rem' }}>
                Ứng dụng bảo vệ quyền riêng tư học sinh như thế nào?
              </Typography>
              <ExpandMoreIcon
                sx={{
                  color: '#64748B',
                  transform: faqOpen[2] ? 'rotate(180deg)' : 'none',
                  transition: 'transform 200ms ease',
                }}
              />
            </Box>
            <Collapse in={faqOpen[2]}>
              <Box sx={{ px: 2.5, pb: 2.5, pt: 0.5, borderTop: '1px solid #F1F5F9' }}>
                <Typography sx={{ color: '#475569', fontSize: '0.92rem', lineHeight: 1.65 }}>
                  Chúng tôi tuân thủ nghiêm ngặt chuẩn bảo vệ an toàn cho trẻ nhỏ. Khi chụp bài vở, học sinh và phụ huynh chủ động vẽ các vùng che họ tên, trường lớp trực tiếp trên màn hình; sau đó xem lại và bấm xác nhận trước khi ảnh được gửi về hệ thống để xử lý toán học.
                </Typography>
              </Box>
            </Collapse>
          </Paper>

          {/* FAQ 3 */}
          <Paper
            elevation={0}
            sx={{
              borderRadius: 3,
              border: '1.5px solid #E2E8F0',
              overflow: 'hidden',
              bgcolor: '#FFFFFF',
            }}
          >
            <Box
              component="button"
              onClick={() => toggleFaq(3)}
              aria-expanded={faqOpen[3]}
              sx={{
                width: '100%',
                p: 2.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                bgcolor: 'transparent',
                border: 'none',
                textAlign: 'left',
                cursor: 'pointer',
                fontFamily: 'inherit',
                minHeight: 48,
              }}
            >
              <Typography sx={{ fontWeight: 800, color: '#190568', fontSize: '1rem' }}>
                Học sinh lớp 1-2 chưa đọc thạo có dùng được không?
              </Typography>
              <ExpandMoreIcon
                sx={{
                  color: '#64748B',
                  transform: faqOpen[3] ? 'rotate(180deg)' : 'none',
                  transition: 'transform 200ms ease',
                }}
              />
            </Box>
            <Collapse in={faqOpen[3]}>
              <Box sx={{ px: 2.5, pb: 2.5, pt: 0.5, borderTop: '1px solid #F1F5F9' }}>
                <Typography sx={{ color: '#475569', fontSize: '0.92rem', lineHeight: 1.65 }}>
                  Hoàn toàn được. MathVisionKid tích hợp trợ lý giọng nói tiếng Việt chuẩn, tự động đọc đề bài và đọc từng câu hỏi gợi mở với ngữ điệu nhẹ nhàng, ấm áp như một người bạn đồng hành bên bàn học.
                </Typography>
              </Box>
            </Collapse>
          </Paper>
        </Box>
      </Box>

      {/* ========================================================================= */}
      {/* 5. BOTTOM CTA BANNER                                                      */}
      {/* ========================================================================= */}
      <Box
        component="section"
        sx={{
          py: { xs: 6, md: 8 },
          px: { xs: 2.5, sm: 4, md: 5 },
          bgcolor: '#190568',
          color: '#FFFFFF',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1 }}>
          <Typography
            variant="h2"
            sx={{
              fontFamily: 'Nunito, sans-serif',
              fontSize: { xs: '2rem', sm: '2.6rem', md: '3rem' },
              fontWeight: 900,
              letterSpacing: '-0.02em',
              mb: 2,
              color: '#FFFFFF',
            }}
          >
            Sẵn sàng đồng hành cùng con?
          </Typography>
          <Typography
            sx={{
              color: '#CBD5E1',
              fontSize: { xs: '1rem', md: '1.15rem' },
              maxWidth: 580,
              mx: 'auto',
              mb: 4,
              lineHeight: 1.6,
            }}
          >
            Tạo thói quen tư duy chủ động, để mỗi giờ làm bài tập trở thành niềm hứng khởi tự nhiên.
          </Typography>
          <Button
            component={RouterLink}
            to="/login"
            aria-label="Học ngay cùng AI"
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            sx={{
              minHeight: 50,
              bgcolor: '#F59E0B',
              color: '#190568',
              fontWeight: 900,
              fontSize: '1.1rem',
              borderRadius: '28px',
              px: 5,
              py: 1.5,
              textTransform: 'none',
              boxShadow: '0 6px 20px rgba(245, 158, 11, 0.45)',
              transition: 'background-color 180ms ease, transform 180ms ease, box-shadow 180ms ease',
              '&:hover': {
                bgcolor: '#D97706',
                transform: 'translateY(-2px)',
              },
            }}
          >
            Học ngay cùng AI
          </Button>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 6. FOOTER                                                                 */}
      {/* ========================================================================= */}
      <Box
        component="footer"
        sx={{
          bgcolor: '#FFFFFF',
          borderTop: '1px solid #E2E8F0',
          py: 4,
          px: { xs: 2.5, sm: 4, md: 5 },
          textAlign: 'center',
        }}
      >
        <Typography sx={{ fontWeight: 700, color: '#190568', fontSize: '0.88rem' }}>
          © 2026 MathVision Kids — Nền tảng AI trợ lý toán học tiểu học Việt Nam
        </Typography>
        <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.75, fontSize: '0.78rem' }}>
          Chuẩn GDPT 2018 • Tôn trọng quyền riêng tư học sinh • Gợi mở tư duy độc lập
        </Typography>
      </Box>

    </Box>
  );
};

export default LandingPage;
