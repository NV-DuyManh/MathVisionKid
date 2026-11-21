import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Chip,
  Collapse,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

export const LandingPage: React.FC = () => {
  // State for Grade Tabs in "LỘ TRÌNH"
  const [selectedGrade, setSelectedGrade] = useState<number>(1);

  // State for Interactive math cards
  const [mathAnswer1, setMathAnswer1] = useState<number>(13);
  const [mathAnswer2, setMathAnswer2] = useState<number>(13);

  // State for FAQ Accordion
  const [faqOpen, setFaqOpen] = useState<{ [key: number]: boolean }>({
    1: true,
    2: false,
    3: false,
  });

  const toggleFaq = (index: number) => {
    setFaqOpen((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const grades = [
    { id: 1, label: 'Lớp 1' },
    { id: 2, label: 'Lớp 2' },
    { id: 3, label: 'Lớp 3' },
    { id: 4, label: 'Lớp 4' },
    { id: 5, label: 'Lớp 5' },
  ];

  return (
    <Box sx={{ width: '100%', bgcolor: '#FAF8FE', color: '#1E1B4B', overflowX: 'hidden' }}>

      {/* ========================================================================= */}
      {/* 1. HERO SECTION (Ảnh 1)                                                   */}
      {/* ========================================================================= */}
      <Box
        id="hero"
        sx={{
          pt: { xs: 5, md: 7 },
          pb: { xs: 4, md: 6 },
          background: 'radial-gradient(ellipse at 50% 10%, #FDFBFF 0%, #F5EEFF 50%, #FAF8FE 100%)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Soft Lavender Cloud Silhouettes in background */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: -100,
            width: 400,
            height: 250,
            borderRadius: '50%',
            bgcolor: 'rgba(237, 233, 254, 0.45)',
            filter: 'blur(50px)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            top: 20,
            right: -80,
            width: 450,
            height: 300,
            borderRadius: '50%',
            bgcolor: 'rgba(243, 238, 255, 0.6)',
            filter: 'blur(60px)',
            pointerEvents: 'none',
            zIndex: 0,
          }}
        />

        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 }, position: 'relative', zIndex: 1 }}>
          <Grid container spacing={{ xs: 4, md: 5 }} sx={{ alignItems: 'center' }}>
            
            {/* Hero Left Content */}
            <Grid size={{ xs: 12, md: 7 }}>
              <Typography
                variant="h1"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontSize: { xs: '2.5rem', sm: '3.15rem', md: '3.5rem' },
                  fontWeight: 900,
                  color: '#1E1B4B',
                  lineHeight: 1.2,
                  letterSpacing: '-0.025em',
                  mb: 2.5,
                }}
              >
                Cùng{' '}
                <Box component="span" sx={{ color: '#FBBF24' }}>
                  MathVisionKid
                </Box>
                <br />
                Khám Phá Toán Nhẹ Nhàng!
              </Typography>

              <Typography
                sx={{
                  color: '#1E1B4B',
                  fontSize: { xs: '1rem', md: '1.05rem' },
                  lineHeight: 1.6,
                  maxWidth: 540,
                  mb: 4,
                  fontWeight: 600,
                }}
              >
                Cùng MathVisionKid rèn luyện tư duy nhanh nhạy, Toán điểm trở thành hành trình thú vị hơn bao giờ hết!
              </Typography>

              <Box sx={{ flexWrap: 'wrap', display: 'flex', gap: 2, mb: 4 }}>
                <Button
                  component={RouterLink}
                  to="/login"
                  sx={{
                    bgcolor: '#FBBF24',
                    color: '#1E1B4B',
                    fontWeight: 900,
                    fontSize: '0.98rem',
                    borderRadius: '9999px',
                    px: 3.8,
                    py: 1.3,
                    textTransform: 'none',
                    boxShadow: '0 4px 16px rgba(251, 191, 36, 0.35)',
                    transition: 'all 180ms ease',
                    '&:hover': { bgcolor: '#F59E0B', transform: 'translateY(-2px)' },
                  }}
                >
                  Học ngay →
                </Button>
                <Button
                  component={RouterLink}
                  to="/login"
                  sx={{
                    bgcolor: '#6D28D9',
                    color: '#FFFFFF',
                    fontWeight: 800,
                    fontSize: '0.98rem',
                    borderRadius: '9999px',
                    px: 3.5,
                    py: 1.3,
                    textTransform: 'none',
                    boxShadow: '0 4px 16px rgba(109, 40, 217, 0.25)',
                    transition: 'all 180ms ease',
                    '&:hover': { bgcolor: '#5B21B6', transform: 'translateY(-2px)' },
                  }}
                >
                  Chụp bài, hỏi AI
                </Button>
              </Box>
            </Grid>

            {/* Hero Right Mascot & Notebook */}
            <Grid size={{ xs: 12, md: 5 }} sx={{ display: 'flex', justifyContent: 'center' }}>
              <Box sx={{ position: 'relative', width: { xs: 280, sm: 340, md: 380 }, textAlign: 'center' }}>
                
                {/* Speech Bubble */}
                <Box
                  sx={{
                    position: 'absolute',
                    top: 15,
                    right: { xs: -10, sm: -15 },
                    zIndex: 10,
                    bgcolor: '#FFFFFF',
                    border: '1.5px solid #E2E8F0',
                    boxShadow: '0 6px 20px rgba(109, 40, 217, 0.1)',
                    borderRadius: '16px',
                    px: 2,
                    py: 1,
                    textAlign: 'left',
                  }}
                >
                  <Typography sx={{ fontSize: '0.76rem', fontWeight: 800, color: '#1E1B4B', lineHeight: 1.25 }}>
                    Bước nhỏ hôm nay
                  </Typography>
                  <Typography sx={{ fontSize: '0.72rem', fontWeight: 800, color: '#1E1B4B', lineHeight: 1.25 }}>
                    — Giỏi hơn ngày mai!
                  </Typography>
                </Box>

                {/* Mascot Image Container */}
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    height: { xs: 250, sm: 290 },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Box
                    component="img"
                    src="/ui/robot-mascot.webp"
                    alt="Robot Sao Nhỏ"
                    sx={{
                      width: { xs: 200, sm: 240, md: 260 },
                      height: 'auto',
                      objectFit: 'contain',
                      filter: 'drop-shadow(0 15px 25px rgba(109, 40, 217, 0.18))',
                    }}
                  />
                </Box>

                {/* Notebook simulation beside mascot */}
                <Box
                  sx={{
                    mt: -2,
                    mx: 'auto',
                    maxWidth: 240,
                    bgcolor: '#FFFFFF',
                    borderRadius: 3,
                    p: 1.75,
                    border: '1.5px solid #E2E8F0',
                    boxShadow: '0 6px 18px rgba(0,0,0,0.05)',
                    textAlign: 'left',
                    position: 'relative',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography sx={{ fontSize: '0.68rem', fontWeight: 700, color: '#94A3B8' }}>
                      Vở Toán Ô Ly
                    </Typography>
                    <Box component="span" sx={{ fontSize: '0.8rem' }}>✏️</Box>
                  </Box>
                  <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B' }}>
                    8 + 5 = 13
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Dải 4 thẻ tổng quan dưới Hero (Under-Hero 4 Cards) */}
          <Box sx={{ mt: { xs: 6, md: 8 } }}>
            <Box
              sx={{
                bgcolor: '#F3EEFF',
                borderRadius: '26px',
                p: { xs: 2.5, sm: 3 },
                border: '1px solid #E9DFFC',
              }}
            >
              {/* Stepper link text */}
              <Typography
                sx={{
                  color: '#1E1B4B',
                  fontWeight: 800,
                  fontSize: '0.9rem',
                  mb: 2.25,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  pl: 0.5,
                }}
              >
                <span>Ôn tập</span>
                <span style={{ color: '#7C3AED' }}>→</span>
                <span>Luyện tập</span>
                <span style={{ color: '#7C3AED' }}>→</span>
                <span>Khám phá</span>
                <span style={{ color: '#7C3AED' }}>→</span>
                <span>Kiểm tra</span>
              </Typography>

              <Grid container spacing={2.25}>
                {/* Card 1: Luyện tập tương tác */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '18px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #F1F5F9',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Image Preview: Cartoon fruit game */}
                      <Box
                        sx={{
                          height: 76,
                          borderRadius: '14px',
                          background: 'linear-gradient(180deg, #A7F3D0 0%, #6EE7B7 40%, #FDE047 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 1.25,
                          mb: 1.75,
                          position: 'relative',
                          overflow: 'hidden',
                          border: '1px solid #A7F3D0',
                        }}
                      >
                        <Box sx={{ bgcolor: '#EF4444', color: '#FFF', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 900 }}>3</Box>
                        <Box sx={{ bgcolor: '#EF4444', color: '#FFF', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 900 }}>9</Box>
                        <Box sx={{ bgcolor: '#EF4444', color: '#FFF', borderRadius: '50%', width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 900 }}>15</Box>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.94rem', color: '#1E1B4B', mb: 0.5 }}>
                        Luyện tập tương tác
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Mỗi giờ, 100% điểm số!
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 26,
                          height: 26,
                          borderRadius: '50%',
                          bgcolor: '#A855F7',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.75rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 2: Bài tập đa dạng */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '18px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #F1F5F9',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Image Preview: Cosmic Starry Game */}
                      <Box
                        sx={{
                          height: 76,
                          borderRadius: '14px',
                          background: 'linear-gradient(180deg, #1E1B4B 0%, #312E81 100%)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 1.25,
                          mb: 1.75,
                          position: 'relative',
                          border: '1px solid #4338CA',
                        }}
                      >
                        <Box sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#FDE047', borderRadius: '8px', px: 1, py: 0.25, fontSize: '11px', fontWeight: 900 }}>0</Box>
                        <Box sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#FDE047', borderRadius: '8px', px: 1, py: 0.25, fontSize: '11px', fontWeight: 900 }}>3</Box>
                        <Box sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#FDE047', borderRadius: '8px', px: 1, py: 0.25, fontSize: '11px', fontWeight: 900 }}>21</Box>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.94rem', color: '#1E1B4B', mb: 0.5 }}>
                        Bài tập đa dạng
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Từ cơ bản đến nâng cao.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 26,
                          height: 26,
                          borderRadius: '50%',
                          bgcolor: '#A855F7',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.75rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 3: Minigames thú vị */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '18px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #F1F5F9',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Image Preview: Interactive minigames & ô ly */}
                      <Box
                        sx={{
                          height: 76,
                          borderRadius: '14px',
                          bgcolor: '#FFFFFF',
                          border: '1px solid #E2E8F0',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mb: 1.75,
                          backgroundImage: `
                            linear-gradient(to right, #F1F5F9 1px, transparent 1px),
                            linear-gradient(to bottom, #F1F5F9 1px, transparent 1px)
                          `,
                          backgroundSize: '12px 12px',
                        }}
                      >
                        <Typography sx={{ fontSize: '0.65rem', fontWeight: 700, color: '#64748B', mb: 0.25 }}>
                          Interactive minigames
                        </Typography>
                        <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '0.95rem', color: '#1E1B4B' }}>
                          8 + 5 = 13
                        </Typography>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.94rem', color: '#1E1B4B', mb: 0.5 }}>
                        Minigames thú vị
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Rèn luyện tư duy nhanh.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 26,
                          height: 26,
                          borderRadius: '50%',
                          bgcolor: '#A855F7',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.75rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 4: Hỗ trợ từ AI */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '18px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #F1F5F9',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Image Preview: Socratic guidance */}
                      <Box
                        sx={{
                          height: 76,
                          borderRadius: '14px',
                          bgcolor: '#F3EEFF',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          p: 1,
                          mb: 1.75,
                          border: '1px solid #E9DFFC',
                        }}
                      >
                        <Typography sx={{ fontSize: '0.65rem', fontWeight: 800, color: '#6D28D9', mb: 0.25 }}>
                          Socratic guidance
                        </Typography>
                        <Box sx={{ bgcolor: '#EDE9FE', borderRadius: '6px', px: 1, py: 0.25, fontSize: '0.62rem', color: '#4C1D95', fontWeight: 700 }}>
                          Bạn cần học Toán? Tớ giúp! 💡
                        </Box>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.94rem', color: '#1E1B4B', mb: 0.5 }}>
                        Hỗ trợ từ AI
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Gợi ý, hướng dẫn và chấm điểm.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 26,
                          height: 26,
                          borderRadius: '50%',
                          bgcolor: '#A855F7',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.75rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 2. SECTION LỘ TRÌNH (Ảnh 2)                                               */}
      {/* ========================================================================= */}
      <Box id="lo-trinh" sx={{ py: { xs: 6, md: 9 }, bgcolor: '#FFFFFF' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          
          {/* Header Section */}
          <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.82rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 1 }}>
            LỘ TRÌNH
          </Typography>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-end', gap: 2, mb: 4 }}>
            <Box>
              <Typography
                variant="h2"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontWeight: 900,
                  fontSize: { xs: '1.85rem', sm: '2.25rem' },
                  color: '#1E1B4B',
                  lineHeight: 1.25,
                  mb: 0.75,
                }}
              >
                Mỗi bước nhỏ, một khám phá lớn
              </Typography>
              <Typography sx={{ color: '#475569', fontSize: '0.95rem' }}>
                Từ những con số đầu tiên đến tư duy toán học vững chắc
              </Typography>
            </Box>
            <Typography sx={{ color: '#7C3AED', fontWeight: 600, fontSize: '0.85rem' }}>
              Dành cho học sinh tiểu học
            </Typography>
          </Box>

          {/* Grade Selector Capsule Bar */}
          <Box
            sx={{
              display: 'inline-flex',
              bgcolor: '#F3EEFF',
              borderRadius: '9999px',
              p: 0.5,
              mb: 5,
              width: '100%',
              maxWidth: 720,
              justifyContent: 'space-between',
            }}
          >
            {grades.map((grade) => {
              const active = selectedGrade === grade.id;
              return (
                <Button
                  key={grade.id}
                  onClick={() => setSelectedGrade(grade.id)}
                  sx={{
                    flex: 1,
                    py: 0.9,
                    borderRadius: '9999px',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textTransform: 'none',
                    bgcolor: active ? '#7C3AED' : 'transparent',
                    color: active ? '#FFFFFF' : '#1E1B4B',
                    boxShadow: active ? '0 4px 12px rgba(124, 58, 237, 0.25)' : 'none',
                    '&:hover': {
                      bgcolor: active ? '#7C3AED' : 'rgba(124, 58, 237, 0.08)',
                    },
                  }}
                >
                  {grade.label}
                </Button>
              );
            })}
          </Box>

          {/* 3 Roadmap Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {/* Card 01 */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
                    <Box
                      sx={{
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        bgcolor: '#FEF3C7',
                        color: '#D97706',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.78rem',
                        fontWeight: 900,
                      }}
                    >
                      01
                    </Box>
                    <Typography sx={{ color: '#D97706', fontWeight: 800, fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                      BẮT ĐẦU TỪ ĐÂY
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Làm quen con số
                  </Typography>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Đếm, so sánh và khám phá các số trong phạm vi 10.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F8FAFC', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.84rem', fontWeight: 600, color: '#475569' }}>
                    6 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#F3EEFF',
                      color: '#7C3AED',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                    }}
                  >
                    →
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Card 02 */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
                    <Box
                      sx={{
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        bgcolor: '#EDE9FE',
                        color: '#7C3AED',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.78rem',
                        fontWeight: 900,
                      }}
                    >
                      02
                    </Box>
                    <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                      TIẾN BƯỚC VỮNG VÀNG
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Cộng trừ thật vui
                  </Typography>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Học phép tính qua hình ảnh và những câu chuyện gần gũi.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F8FAFC', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.84rem', fontWeight: 600, color: '#475569' }}>
                    8 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#F3EEFF',
                      color: '#7C3AED',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                    }}
                  >
                    →
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Card 03 */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
                    <Box
                      sx={{
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        bgcolor: '#DCFCE7',
                        color: '#059669',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.78rem',
                        fontWeight: 900,
                      }}
                    >
                      03
                    </Box>
                    <Typography sx={{ color: '#059669', fontWeight: 800, fontSize: '0.72rem', letterSpacing: '0.04em' }}>
                      THỬ THÁCH LỚN
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Thế giới hình học
                  </Typography>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Nhận biết hình khối, vị trí và quy luật quanh em.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F8FAFC', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.84rem', fontWeight: 600, color: '#475569' }}>
                    5 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#F3EEFF',
                      color: '#7C3AED',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                    }}
                  >
                    →
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Stepper capsule bar below */}
          <Box
            sx={{
              bgcolor: '#F3EEFF',
              borderRadius: '9999px',
              py: 1.5,
              px: 4,
              textAlign: 'center',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ color: '#7C3AED', fontWeight: 900, fontSize: '0.88rem' }}>01</Typography>
              <Typography sx={{ color: '#1E1B4B', fontWeight: 800, fontSize: '0.88rem' }}>Ôn tập</Typography>
            </Box>
            <Typography sx={{ color: '#7C3AED', fontWeight: 800 }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ color: '#7C3AED', fontWeight: 900, fontSize: '0.88rem' }}>02</Typography>
              <Typography sx={{ color: '#1E1B4B', fontWeight: 800, fontSize: '0.88rem' }}>Luyện tập</Typography>
            </Box>
            <Typography sx={{ color: '#7C3AED', fontWeight: 800 }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ color: '#7C3AED', fontWeight: 900, fontSize: '0.88rem' }}>03</Typography>
              <Typography sx={{ color: '#1E1B4B', fontWeight: 800, fontSize: '0.88rem' }}>Khám phá</Typography>
            </Box>
            <Typography sx={{ color: '#7C3AED', fontWeight: 800 }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ color: '#7C3AED', fontWeight: 900, fontSize: '0.88rem' }}>04</Typography>
              <Typography sx={{ color: '#1E1B4B', fontWeight: 800, fontSize: '0.88rem' }}>Kiểm tra</Typography>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 3. SECTION TÍNH NĂNG (Ảnh 3)                                              */}
      {/* ========================================================================= */}
      <Box id="tinh-nang" sx={{ py: { xs: 6, md: 9 }, bgcolor: '#FAF8FE' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          
          {/* Header */}
          <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.82rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 1 }}>
            TÍNH NĂNG
          </Typography>

          <Typography
            variant="h2"
            sx={{
              fontFamily: 'Nunito, sans-serif',
              fontWeight: 900,
              fontSize: { xs: '1.85rem', sm: '2.25rem' },
              color: '#1E1B4B',
              lineHeight: 1.25,
              mb: 1,
            }}
          >
            Bốn cách học vui, một hành trình tự tin
          </Typography>
          <Typography sx={{ color: '#475569', fontSize: '0.95rem', mb: 4.5 }}>
            Luyện tập, khám phá và ôn lại giờ theo cách của riêng em.
          </Typography>

          {/* 2x2 Grid of Feature Cards */}
          <Grid container spacing={3}>
            
            {/* Feature 01: Luyện tập tương tác */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                    <Box
                      sx={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        bgcolor: '#FEF3C7',
                        color: '#D97706',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 900,
                      }}
                    >
                      01
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Luyện tập tương tác
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Chọn đáp án, nhận phản hồi và ôn lại kiến thức ngay lập tức qua trò chơi thú vị.
                  </Typography>

                  {/* Interactive box */}
                  <Box sx={{ bgcolor: '#F5EEFF', borderRadius: '18px', p: 2.5, mb: 2 }}>
                    <Typography sx={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 700, mb: 1 }}>
                      Chọn đáp án đúng
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.5rem', color: '#1E1B4B' }}>
                        8 + 5 = ?
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1.25 }}>
                        {[12, 13, 14].map((num) => {
                          const active = mathAnswer1 === num;
                          return (
                            <Button
                              key={num}
                              onClick={() => setMathAnswer1(num)}
                              sx={{
                                minWidth: 44,
                                height: 40,
                                borderRadius: '12px',
                                fontWeight: 900,
                                fontSize: '0.95rem',
                                bgcolor: active ? '#FBBF24' : '#FFFFFF',
                                color: '#1E1B4B',
                                border: active ? '1.5px solid #F59E0B' : '1px solid #E2E8F0',
                                boxShadow: active ? '0 2px 8px rgba(245, 158, 11, 0.25)' : 'none',
                                '&:hover': { bgcolor: active ? '#FBBF24' : '#F1F5F9' },
                              }}
                            >
                              {num}
                            </Button>
                          );
                        })}
                      </Box>
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6D28D9',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Luyện tập ngay →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 02: Bài tập đa dạng */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                    <Box
                      sx={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        bgcolor: '#EDE9FE',
                        color: '#7C3AED',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 900,
                      }}
                    >
                      02
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Bài tập đa dạng
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Từ cơ bản đến nâng cao, cho từng cấp độ, ôn đúng kiến thức, tiến bộ từng bước nhỏ.
                  </Typography>

                  {/* Inner list box */}
                  <Box sx={{ bgcolor: '#F5EEFF', borderRadius: '18px', p: 2, mb: 2, display: 'grid', gap: 1.25 }}>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.25, borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E2E8F0' }}>
                      <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#1E1B4B' }}>
                        01  Đếm số còn thiếu
                      </Typography>
                      <Chip label="Cấp độ" size="small" sx={{ bgcolor: '#F1F5F9', color: '#64748B', fontSize: '0.72rem', fontWeight: 700 }} />
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.25, borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E2E8F0' }}>
                      <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#1E1B4B' }}>
                        02  Giải toán có lời văn
                      </Typography>
                      <Chip label="Vận dụng" size="small" sx={{ bgcolor: '#F1F5F9', color: '#64748B', fontSize: '0.72rem', fontWeight: 700 }} />
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6D28D9',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Khám phá bài tập →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 03: Minigames thú vị! */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                    <Box
                      sx={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        bgcolor: '#DCFCE7',
                        color: '#059669',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 900,
                      }}
                    >
                      03
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Minigames thú vị!
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Biến phép tính thành trò chơi hấp dẫn. Rèn phản xạ, tư duy nhanh và bền hơn.
                  </Typography>

                  {/* Interactive game box */}
                  <Box sx={{ bgcolor: '#F5EEFF', borderRadius: '18px', p: 2.5, mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography sx={{ color: '#475569', fontSize: '0.75rem', fontWeight: 700 }}>
                        Thử thách trong tuần
                      </Typography>
                      <Chip label="0/24" size="small" sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 900, fontSize: '0.72rem' }} />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.5rem', color: '#1E1B4B' }}>
                        6 + 7 =
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1.25 }}>
                        {[11, 12, 13].map((num) => {
                          const active = mathAnswer2 === num;
                          return (
                            <Button
                              key={num}
                              onClick={() => setMathAnswer2(num)}
                              sx={{
                                minWidth: 44,
                                height: 40,
                                borderRadius: '12px',
                                fontWeight: 900,
                                fontSize: '0.95rem',
                                bgcolor: active ? '#BBF7D0' : '#FFFFFF',
                                color: active ? '#14532D' : '#1E1B4B',
                                border: active ? '1.5px solid #22C55E' : '1px solid #E2E8F0',
                                boxShadow: active ? '0 2px 8px rgba(34, 197, 94, 0.25)' : 'none',
                                '&:hover': { bgcolor: active ? '#BBF7D0' : '#F1F5F9' },
                              }}
                            >
                              {num}
                            </Button>
                          );
                        })}
                      </Box>
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6D28D9',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Chơi thử minigame →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 04: Hỗ trợ từ AI */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #EDE9FE',
                  boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                    <Box
                      sx={{
                        width: 26,
                        height: 26,
                        borderRadius: '50%',
                        bgcolor: '#EDE9FE',
                        color: '#7C3AED',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 900,
                      }}
                    >
                      04
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Hỗ trợ từ AI
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Chưa rõ hoặc cần hỗ trợ? Hãy hỏi AI, giúp bạn và giải mọi thắc mắc, từng bước một.
                  </Typography>

                  {/* AI Chat box */}
                  <Box sx={{ bgcolor: '#F5EEFF', borderRadius: '18px', p: 2, mb: 2, display: 'grid', gap: 1.25 }}>
                    <Box sx={{ bgcolor: '#EDE9FE', p: 1, borderRadius: '10px', textAlign: 'center' }}>
                      <Typography sx={{ fontSize: '0.78rem', fontWeight: 800, color: '#6D28D9' }}>
                        Bài toán: 8 + 7 = ?
                      </Typography>
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.25, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
                      <Typography sx={{ fontSize: '0.8rem', color: '#94A3B8' }}>
                        Em hãy trả lời: 8 + 7 bằng bao nhiêu?
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6D28D9',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Chụp bài, hỏi AI →
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 4. SECTION GIẢI ĐÁP CÙNG BA MẸ (FAQ)                                      */}
      {/* ========================================================================= */}
      <Box id="giai-dap" sx={{ py: { xs: 6, md: 9 }, bgcolor: '#FFFFFF' }}>
        <Container maxWidth="md" sx={{ px: { xs: 2.5, sm: 4 } }}>
          
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.82rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 1 }}>
              GIẢI ĐÁP CÙNG BA MẸ
            </Typography>
            <Typography
              variant="h2"
              sx={{
                fontFamily: 'Nunito, sans-serif',
                fontWeight: 900,
                fontSize: { xs: '1.85rem', sm: '2.25rem' },
                color: '#1E1B4B',
              }}
            >
              Một chút băn khoăn? Có mình đây!
            </Typography>
          </Box>

          {/* Accordion List */}
          <Box sx={{ display: 'grid', gap: 2.5 }}>
            
            {/* FAQ 1 */}
            <Box
              sx={{
                bgcolor: '#FFFFFF',
                borderRadius: '20px',
                p: { xs: 2.5, sm: 3 },
                border: '1.5px solid #EDE9FE',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
              }}
              onClick={() => toggleFaq(1)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '0.95rem', sm: '1.05rem' }, color: '#1E1B4B' }}>
                  MathVisionKid phù hợp với học sinh lớp mấy?
                </Typography>
                <Typography sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#64748B', lineHeight: 1 }}>
                  {faqOpen[1] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[1]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F8FAFC', mt: 2 }}>
                  <Typography sx={{ color: '#475569', fontSize: '0.9rem', lineHeight: 1.65 }}>
                    Các hoạt động được thiết kế cho học sinh tiểu học từ lớp 1 đến lớp 5.<br />
                    Ba mẹ có thể chọn lớp phù hợp để con bắt đầu từ những kiến thức quen thuộc.
                  </Typography>
                </Box>
              </Collapse>
            </Box>

            {/* FAQ 2 */}
            <Box
              sx={{
                bgcolor: '#FFFFFF',
                borderRadius: '20px',
                p: { xs: 2.5, sm: 3 },
                border: '1.5px solid #EDE9FE',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
              }}
              onClick={() => toggleFaq(2)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '0.95rem', sm: '1.05rem' }, color: '#1E1B4B' }}>
                  Con cần học bao lâu mỗi ngày?
                </Typography>
                <Typography sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#64748B', lineHeight: 1 }}>
                  {faqOpen[2] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[2]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F8FAFC', mt: 2 }}>
                  <Typography sx={{ color: '#475569', fontSize: '0.9rem', lineHeight: 1.65 }}>
                    Chỉ cần 15 đến 20 phút mỗi ngày. Các bài tập được chia nhỏ thành các thử thách ngắn giúp bé hào hứng học mà không bị mỏi mệt.
                  </Typography>
                </Box>
              </Collapse>
            </Box>

            {/* FAQ 3 */}
            <Box
              sx={{
                bgcolor: '#FFFFFF',
                borderRadius: '20px',
                p: { xs: 2.5, sm: 3 },
                border: '1.5px solid #EDE9FE',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
              }}
              onClick={() => toggleFaq(3)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '0.95rem', sm: '1.05rem' }, color: '#1E1B4B' }}>
                  AI sẽ giúp con học như thế nào?
                </Typography>
                <Typography sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#64748B', lineHeight: 1 }}>
                  {faqOpen[3] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[3]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F8FAFC', mt: 2 }}>
                  <Typography sx={{ color: '#475569', fontSize: '0.9rem', lineHeight: 1.65 }}>
                    AI của MathVisionKid đóng vai trò người gia sư kiên nhẫn: phân tích từng nét chữ đặt tính trên vở ô ly, chỉ ra điểm nhầm lẫn và đặt câu hỏi gợi mở để con tự tìm ra cách giải, tuyệt đối không đưa sẵn đáp số.
                  </Typography>
                </Box>
              </Collapse>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 5. SECTION CTA BANNER (MỖI NGÀY MỘT CHÚT TỰ TIN)                          */}
      {/* ========================================================================= */}
      <Box sx={{ py: { xs: 4, md: 7 }, bgcolor: '#FAF8FE' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          <Box
            sx={{
              bgcolor: '#F3EEFF',
              borderRadius: { xs: '26px', md: '34px' },
              py: { xs: 5, md: 7 },
              px: { xs: 3, sm: 6 },
              textAlign: 'center',
              border: '1px solid #E9DFFC',
            }}
          >
            <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.78rem', letterSpacing: '0.06em', textTransform: 'uppercase', mb: 1.5 }}>
              MỖI NGÀY MỘT CHÚT TỰ TIN
            </Typography>

            <Typography
              variant="h2"
              sx={{
                fontFamily: 'Nunito, sans-serif',
                fontWeight: 900,
                fontSize: { xs: '1.85rem', sm: '2.4rem' },
                color: '#1E1B4B',
                lineHeight: 1.25,
                mb: 1.5,
              }}
            >
              Sẵn sàng cho chuyến phiêu lưu toán học?
            </Typography>

            <Typography
              sx={{
                color: '#475569',
                fontSize: { xs: '0.95rem', md: '1.05rem' },
                maxWidth: 600,
                mx: 'auto',
                mb: 4,
              }}
            >
              Cùng MathVisionKid biến “con chưa biết” thành “con làm được rồi!”
            </Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 2.5 }}>
              <Button
                component={RouterLink}
                to="/login"
                sx={{
                  bgcolor: '#FBBF24',
                  color: '#1E1B4B',
                  fontWeight: 900,
                  fontSize: '0.98rem',
                  borderRadius: '9999px',
                  px: 4,
                  py: 1.35,
                  textTransform: 'none',
                  boxShadow: '0 4px 16px rgba(251, 191, 36, 0.35)',
                  transition: 'all 180ms ease',
                  '&:hover': { bgcolor: '#F59E0B', transform: 'translateY(-2px)' },
                }}
              >
                Bắt đầu học ngay →
              </Button>
              <Button
                component="a"
                href="#lo-trinh"
                sx={{
                  bgcolor: '#FFFFFF',
                  color: '#1E1B4B',
                  fontWeight: 800,
                  fontSize: '0.98rem',
                  borderRadius: '9999px',
                  px: 4,
                  py: 1.35,
                  textTransform: 'none',
                  border: '1.5px solid #E2E8F0',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                  transition: 'all 180ms ease',
                  '&:hover': { bgcolor: '#F8FAFC', transform: 'translateY(-2px)' },
                }}
              >
                Khám phá lộ trình
              </Button>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 6. SECTION FOOTER                                                         */}
      {/* ========================================================================= */}
      <Box
        component="footer"
        sx={{
          pt: { xs: 6, md: 8 },
          pb: 4.5,
          bgcolor: '#FFFFFF',
          borderTop: '1px solid #EDE9FE',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          <Grid container spacing={{ xs: 4, md: 5 }} sx={{ mb: 5 }}>
            {/* Col 1: Brand */}
            <Grid size={{ xs: 12, md: 5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.25 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: '#EDE9FE',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.15rem',
                  }}
                >
                  🪐
                </Box>
                <Typography
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    fontWeight: 900,
                    fontSize: '1.35rem',
                    color: '#1E1B4B',
                    letterSpacing: '-0.02em',
                  }}
                >
                  MathVisionKid
                </Typography>
              </Box>
              <Typography sx={{ color: '#475569', fontSize: '0.88rem', lineHeight: 1.6, maxWidth: 320 }}>
                Nuôi dưỡng niềm vui học toán,<br />
                chắp cánh những khám phá nhỏ.
              </Typography>
            </Grid>

            {/* Col 2: Khám phá */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '0.92rem', color: '#1E1B4B', mb: 2 }}>
                Khám phá
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.2 }}>
                <Box component="a" href="#lo-trinh" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Lộ trình học
                </Box>
                <Box component="a" href="#tinh-nang" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Bài tập & trò chơi
                </Box>
              </Box>
            </Grid>

            {/* Col 3: Đồng hành */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '0.92rem', color: '#1E1B4B', mb: 2 }}>
                Đồng hành
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.2 }}>
                <Box component="a" href="#giai-dap" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Dành cho phụ huynh
                </Box>
                <Box component="a" href="#giai-dap" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Câu hỏi thường gặp
                </Box>
              </Box>
            </Grid>

            {/* Col 4: Thông tin */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '0.92rem', color: '#1E1B4B', mb: 2 }}>
                Thông tin
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.2 }}>
                <Box component="a" href="#" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Quyền riêng tư
                </Box>
                <Box component="a" href="#" sx={{ color: '#475569', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Điều khoản
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Bottom Line */}
          <Box
            sx={{
              pt: 3,
              borderTop: '1px solid #F1F5F9',
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 1.5,
              color: '#94A3B8',
              fontSize: '0.82rem',
            }}
          >
            <Typography sx={{ fontSize: 'inherit', color: 'inherit' }}>
              © 2026 MathVisionKid. Cùng con yêu toán hơn mỗi ngày.
            </Typography>
            <Typography sx={{ fontSize: 'inherit', color: 'inherit' }}>
              Học nhẹ nhàng. Khám phá tự tin.
            </Typography>
          </Box>
        </Container>
      </Box>

    </Box>
  );
};

export default LandingPage;
