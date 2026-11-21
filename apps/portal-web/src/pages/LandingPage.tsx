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
    <Box sx={{ width: '100%', bgcolor: '#FAF9FE', color: '#1E1B4B', overflowX: 'hidden' }}>

      {/* ========================================================================= */}
      {/* 1. HERO SECTION                                                          */}
      {/* ========================================================================= */}
      <Box
        id="hero"
        sx={{
          pt: { xs: 5, md: 8 },
          pb: { xs: 4, md: 6 },
          background: 'linear-gradient(180deg, #F8F6FE 0%, #FFFFFF 100%)',
          position: 'relative',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Grid container spacing={{ xs: 4, md: 6 }} sx={{ alignItems: 'center' }}>
            
            {/* Hero Left Content */}
            <Grid size={{ xs: 12, md: 7 }}>
              <Typography
                variant="h1"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontSize: { xs: '2.5rem', sm: '3.2rem', md: '3.75rem' },
                  fontWeight: 900,
                  color: '#1E1B4B',
                  lineHeight: 1.18,
                  letterSpacing: '-0.025em',
                  mb: 2.5,
                }}
              >
                Cùng{' '}
                <Box component="span" sx={{ color: '#F59E0B' }}>
                  MathVisionKid
                </Box>
                <br />
                Khám Phá Toán Nhẹ Nhàng!
              </Typography>

              <Typography
                sx={{
                  color: '#475569',
                  fontSize: { xs: '1rem', md: '1.1rem' },
                  lineHeight: 1.65,
                  maxWidth: 540,
                  mb: 4,
                  fontWeight: 500,
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
                    fontWeight: 800,
                    fontSize: '1rem',
                    borderRadius: '9999px',
                    px: 4,
                    py: 1.35,
                    textTransform: 'none',
                    boxShadow: '0 6px 18px rgba(251, 191, 36, 0.4)',
                    transition: 'all 200ms ease',
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
                    fontSize: '1rem',
                    borderRadius: '9999px',
                    px: 3.5,
                    py: 1.35,
                    textTransform: 'none',
                    boxShadow: '0 6px 18px rgba(109, 40, 217, 0.3)',
                    transition: 'all 200ms ease',
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
                    top: 10,
                    right: { xs: -10, sm: -20 },
                    zIndex: 10,
                    bgcolor: '#FFFFFF',
                    border: '1.5px solid #E2E8F0',
                    boxShadow: '0 8px 24px rgba(109, 40, 217, 0.12)',
                    borderRadius: '16px',
                    px: 2,
                    py: 1,
                    textAlign: 'left',
                  }}
                >
                  <Typography sx={{ fontSize: '0.75rem', fontWeight: 800, color: '#1E1B4B' }}>
                    Bước nhỏ hôm nay
                  </Typography>
                  <Typography sx={{ fontSize: '0.7rem', fontWeight: 700, color: '#6D28D9' }}>
                    — Giỏi hơn ngày mai!
                  </Typography>
                </Box>

                {/* Mascot Image Container */}
                <Box
                  sx={{
                    position: 'relative',
                    width: '100%',
                    height: { xs: 260, sm: 300 },
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
                      filter: 'drop-shadow(0 15px 25px rgba(109, 40, 217, 0.2))',
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
                    p: 2,
                    border: '1.5px solid #E2E8F0',
                    boxShadow: '0 8px 20px rgba(0,0,0,0.06)',
                    textAlign: 'left',
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
            {/* Stepper link text */}
            <Typography
              sx={{
                color: '#6D28D9',
                fontWeight: 800,
                fontSize: '0.85rem',
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
              }}
            >
              <span>Ôn tập</span>
              <span>→</span>
              <span>Luyện tập</span>
              <span>→</span>
              <span>Khám phá</span>
              <span>→</span>
              <span>Kiểm tra</span>
            </Typography>

            <Box
              sx={{
                bgcolor: '#F3EEFF',
                borderRadius: '28px',
                p: { xs: 2.5, sm: 3 },
                border: '1px solid #E9DFFC',
              }}
            >
              <Grid container spacing={2.5}>
                {/* Card 1 */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '20px',
                      p: 2.2,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 200ms ease',
                      '&:hover': { transform: 'translateY(-3px)' },
                    }}
                  >
                    <Box>
                      <Box
                        sx={{
                          height: 70,
                          borderRadius: 2.5,
                          bgcolor: '#FEF3C7',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 1,
                          mb: 1.75,
                        }}
                      >
                        <Chip label="8" size="small" sx={{ bgcolor: '#F59E0B', color: '#FFF', fontWeight: 800 }} />
                        <Chip label="5" size="small" sx={{ bgcolor: '#F59E0B', color: '#FFF', fontWeight: 800 }} />
                        <Chip label="13" size="small" sx={{ bgcolor: '#D97706', color: '#FFF', fontWeight: 800 }} />
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.95rem', color: '#1E1B4B', mb: 0.5 }}>
                        Luyện tập tương tác
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Mỗi giờ, 100% điểm số!
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          bgcolor: '#EDE9FE',
                          color: '#6D28D9',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 800,
                          fontSize: '0.85rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 2 */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '20px',
                      p: 2.2,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 200ms ease',
                      '&:hover': { transform: 'translateY(-3px)' },
                    }}
                  >
                    <Box>
                      <Box
                        sx={{
                          height: 70,
                          borderRadius: 2.5,
                          bgcolor: '#E0E7FF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontFamily: 'monospace',
                          fontWeight: 900,
                          color: '#3730A3',
                          fontSize: '1rem',
                          mb: 1.75,
                        }}
                      >
                        8 + 5 = 13
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.95rem', color: '#1E1B4B', mb: 0.5 }}>
                        Bài tập đa dạng
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Từ cơ bản đến nâng cao.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          bgcolor: '#EDE9FE',
                          color: '#6D28D9',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 800,
                          fontSize: '0.85rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 3 */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '20px',
                      p: 2.2,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 200ms ease',
                      '&:hover': { transform: 'translateY(-3px)' },
                    }}
                  >
                    <Box>
                      <Box
                        sx={{
                          height: 70,
                          borderRadius: 2.5,
                          bgcolor: '#F1F5F9',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '1px solid #E2E8F0',
                          mb: 1.75,
                        }}
                      >
                        <Typography sx={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748B' }}>
                          Interactive minigames
                        </Typography>
                        <Typography sx={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '0.88rem', color: '#0F172A' }}>
                          8 + 5 = 13
                        </Typography>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.95rem', color: '#1E1B4B', mb: 0.5 }}>
                        Minigames thú vị
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Rèn luyện tư duy nhanh.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          bgcolor: '#EDE9FE',
                          color: '#6D28D9',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 800,
                          fontSize: '0.85rem',
                        }}
                      >
                        →
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Card 4 */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#FFFFFF',
                      borderRadius: '20px',
                      p: 2.2,
                      boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 200ms ease',
                      '&:hover': { transform: 'translateY(-3px)' },
                    }}
                  >
                    <Box>
                      <Box
                        sx={{
                          height: 70,
                          borderRadius: 2.5,
                          bgcolor: '#EDE9FE',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          p: 1,
                          mb: 1.75,
                        }}
                      >
                        <Typography sx={{ fontSize: '0.68rem', fontWeight: 800, color: '#6D28D9' }}>
                          Socratic guidance
                        </Typography>
                        <Typography sx={{ fontSize: '0.62rem', color: '#4C1D95', textAlign: 'center' }}>
                          Bạn cần học Toán? Để tôi giúp!
                        </Typography>
                      </Box>
                      <Typography sx={{ fontWeight: 800, fontSize: '0.95rem', color: '#1E1B4B', mb: 0.5 }}>
                        Hỗ trợ từ AI
                      </Typography>
                      <Typography sx={{ fontSize: '0.78rem', color: '#64748B' }}>
                        Gợi ý hướng dẫn và chấm điểm.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '50%',
                          bgcolor: '#EDE9FE',
                          color: '#6D28D9',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 800,
                          fontSize: '0.85rem',
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
      {/* 2. SECTION LỘ TRÌNH                                                       */}
      {/* ========================================================================= */}
      <Box id="lo-trinh" sx={{ py: { xs: 6, md: 10 }, bgcolor: '#FAF9FE' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          
          {/* Header Section */}
          <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.05em', textTransform: 'uppercase', mb: 1 }}>
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
              <Typography sx={{ color: '#64748B', fontSize: '0.95rem' }}>
                Từ những con số đầu tiên đến tư duy toán học vững chắc
              </Typography>
            </Box>
            <Typography sx={{ color: '#6D28D9', fontWeight: 700, fontSize: '0.85rem' }}>
              Dành cho học sinh tiểu học
            </Typography>
          </Box>

          {/* Grade Selector Bar */}
          <Box
            sx={{
              display: 'inline-flex',
              bgcolor: '#F1EDFD',
              borderRadius: '9999px',
              p: 0.6,
              mb: 5,
              width: '100%',
              maxWidth: 700,
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
                    py: 1,
                    borderRadius: '9999px',
                    fontWeight: 800,
                    fontSize: '0.88rem',
                    textTransform: 'none',
                    bgcolor: active ? '#7C3AED' : 'transparent',
                    color: active ? '#FFFFFF' : '#6D28D9',
                    boxShadow: active ? '0 4px 12px rgba(124, 58, 237, 0.3)' : 'none',
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
          <Grid container spacing={3.5} sx={{ mb: 4 }}>
            {/* Card 01 */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1,
                      bgcolor: '#FEF3C7',
                      color: '#D97706',
                      borderRadius: '9999px',
                      px: 2,
                      py: 0.6,
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      mb: 2.5,
                    }}
                  >
                    <span>01</span>
                    <span>BẮT ĐẦU TỪ ĐÂY</span>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Làm quen con số
                  </Typography>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Đếm, so sánh và khám phá các số trong phạm vi 10.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F1F5F9', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#64748B' }}>
                    6 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#EDE9FE',
                      color: '#6D28D9',
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
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1,
                      bgcolor: '#EDE9FE',
                      color: '#7C3AED',
                      borderRadius: '9999px',
                      px: 2,
                      py: 0.6,
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      mb: 2.5,
                    }}
                  >
                    <span>02</span>
                    <span>TIẾN BƯỚC VỮNG VÀNG</span>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Cộng trừ thật vui
                  </Typography>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Học phép tính qua hình ảnh và những câu chuyện gần gũi.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F1F5F9', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#64748B' }}>
                    8 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#EDE9FE',
                      color: '#6D28D9',
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
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 1,
                      bgcolor: '#CCFBF1',
                      color: '#0D9488',
                      borderRadius: '9999px',
                      px: 2,
                      py: 0.6,
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      mb: 2.5,
                    }}
                  >
                    <span>03</span>
                    <span>THỬ THÁCH LỚN</span>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.25rem', color: '#1E1B4B', mb: 1.25 }}>
                    Thế giới hình học
                  </Typography>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6 }}>
                    Nhận biết hình khối, vị trí và quy luật quanh em.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3, borderTop: '1px solid #F1F5F9', mt: 3 }}>
                  <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#64748B' }}>
                    5 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: '#EDE9FE',
                      color: '#6D28D9',
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

          {/* Stepper sub-bar below */}
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
              gap: 2,
              color: '#6D28D9',
              fontWeight: 800,
              fontSize: '0.88rem',
            }}
          >
            <span>01  Ôn tập</span>
            <span>→</span>
            <span>02  Luyện tập</span>
            <span>→</span>
            <span>03  Khám phá</span>
            <span>→</span>
            <span>04  Kiểm tra</span>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 3. SECTION TÍNH NĂNG (Bốn cách học vui, một hành trình tự tin)            */}
      {/* ========================================================================= */}
      <Box id="tinh-nang" sx={{ py: { xs: 6, md: 10 }, bgcolor: '#FFFFFF' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          
          {/* Header */}
          <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.05em', textTransform: 'uppercase', mb: 1 }}>
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
          <Typography sx={{ color: '#64748B', fontSize: '0.95rem', mb: 5 }}>
            Luyện tập, khám phá và ôn lại giờ theo cách của riêng em
          </Typography>

          {/* 2x2 Grid of Feature Cards */}
          <Grid container spacing={3.5}>
            
            {/* Feature 01: Luyện tập tương tác */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 3.5,
                  border: '1.5px solid #F1F5F9',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                    <Chip label="01" size="small" sx={{ bgcolor: '#FEF3C7', color: '#D97706', fontWeight: 900 }} />
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Luyện tập tương tác
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Chọn đáp án, nhận phản hồi và ôn lại kiến thức ngay lập tức qua trò chơi thú vị.
                  </Typography>

                  {/* Interactive box */}
                  <Box sx={{ bgcolor: '#F8F6FE', borderRadius: '18px', p: 3, mb: 2 }}>
                    <Typography sx={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 700, mb: 1 }}>
                      Chọn đáp án đúng
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.5rem', color: '#1E1B4B' }}>
                        8 + 5 = ?
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1.5 }}>
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
                                fontSize: '1rem',
                                bgcolor: active ? '#FDE047' : '#FFFFFF',
                                color: '#1E1B4B',
                                border: active ? '2px solid #F59E0B' : '1px solid #E2E8F0',
                                boxShadow: active ? '0 2px 8px rgba(245, 158, 11, 0.3)' : 'none',
                                '&:hover': { bgcolor: active ? '#FDE047' : '#F1F5F9' },
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
                  border: '1.5px solid #F1F5F9',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                    <Chip label="02" size="small" sx={{ bgcolor: '#EDE9FE', color: '#7C3AED', fontWeight: 900 }} />
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Bài tập đa dạng
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Từ cơ bản đến nâng cao, cho từng cấp độ, ôn đúng kiến thức, tiến bộ từng bước nhỏ.
                  </Typography>

                  {/* Inner list box */}
                  <Box sx={{ bgcolor: '#F8F6FE', borderRadius: '18px', p: 2.5, mb: 2, display: 'grid', gap: 1.5 }}>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.5, borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E2E8F0' }}>
                      <Typography sx={{ fontSize: '0.82rem', fontWeight: 700, color: '#1E1B4B' }}>
                        01  Đếm số còn thiếu
                      </Typography>
                      <Chip label="Cấp độ" size="small" sx={{ bgcolor: '#F1F5F9', color: '#64748B', fontSize: '0.72rem', fontWeight: 700 }} />
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.5, borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E2E8F0' }}>
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
                  border: '1.5px solid #F1F5F9',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                    <Chip label="03" size="small" sx={{ bgcolor: '#CCFBF1', color: '#0D9488', fontWeight: 900 }} />
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Minigames thú vị!
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Biến phép tính thành trò chơi hấp dẫn. Rèn phản xạ, tự duy nhanh và bền hơn.
                  </Typography>

                  {/* Interactive game box */}
                  <Box sx={{ bgcolor: '#F8F6FE', borderRadius: '18px', p: 3, mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography sx={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 700 }}>
                        Thử thách trong tuần
                      </Typography>
                      <Chip label="0/24" size="small" sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 900, fontSize: '0.72rem' }} />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.5rem', color: '#1E1B4B' }}>
                        6 + 7 =
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1.5 }}>
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
                                fontSize: '1rem',
                                bgcolor: active ? '#BBF7D0' : '#FFFFFF',
                                color: active ? '#166534' : '#1E1B4B',
                                border: active ? '2px solid #22C55E' : '1px solid #E2E8F0',
                                boxShadow: active ? '0 2px 8px rgba(34, 197, 94, 0.3)' : 'none',
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
                  border: '1.5px solid #F1F5F9',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.03)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                    <Chip label="04" size="small" sx={{ bgcolor: '#EDE9FE', color: '#7C3AED', fontWeight: 900 }} />
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.15rem', color: '#1E1B4B' }}>
                      Hỗ trợ từ AI
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6, mb: 3 }}>
                    Chưa rõ hoặc cần hỗ trợ? Hãy hỏi AI, giúp bạn và giải mọi thắc mắc, từng bước một.
                  </Typography>

                  {/* AI Chat box */}
                  <Box sx={{ bgcolor: '#F8F6FE', borderRadius: '18px', p: 2.5, mb: 2, display: 'grid', gap: 1.5 }}>
                    <Box sx={{ bgcolor: '#EDE9FE', p: 1.25, borderRadius: '10px', textAlign: 'center' }}>
                      <Typography sx={{ fontSize: '0.78rem', fontWeight: 800, color: '#6D28D9' }}>
                        Bài toán: 8 + 7 = ?
                      </Typography>
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.5, borderRadius: '12px', border: '1px solid #E2E8F0' }}>
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
      {/* 4. SECTION GIẢI ĐÁP CÙNG BA MẸ (FAQ) (Ảnh 2)                              */}
      {/* ========================================================================= */}
      <Box id="giai-dap" sx={{ py: { xs: 6, md: 10 }, bgcolor: '#FAF9FE' }}>
        <Container maxWidth="md" sx={{ px: { xs: 2.5, sm: 4 } }}>
          
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Typography sx={{ color: '#7C3AED', fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.05em', textTransform: 'uppercase', mb: 1 }}>
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
                border: '1px solid #E2E8F0',
                boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
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
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#64748B', fontSize: '0.9rem', lineHeight: 1.65 }}>
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
                border: '1px solid #E2E8F0',
                boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
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
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#64748B', fontSize: '0.9rem', lineHeight: 1.65 }}>
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
                border: '1px solid #E2E8F0',
                boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
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
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#64748B', fontSize: '0.9rem', lineHeight: 1.65 }}>
                    AI của MathVisionKid đóng vai trò người gia sư kiên nhẫn: phân tích từng nét chữ đặt tính trên vở ô ly, chỉ ra điểm nhầm lẫn và đặt câu hỏi gợi mở để con tự tìm ra cách giải, tuyệt đối không đưa sẵn đáp số.
                  </Typography>
                </Box>
              </Collapse>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 5. SECTION CTA BANNER (MỖI NGÀY MỘT CHÚT TỰ TIN) (Ảnh 2)                  */}
      {/* ========================================================================= */}
      <Box sx={{ py: { xs: 4, md: 8 }, bgcolor: '#FAF9FE' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Box
            sx={{
              bgcolor: '#F3EEFF',
              borderRadius: { xs: '28px', md: '36px' },
              py: { xs: 6, md: 8 },
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
                color: '#64748B',
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
                  fontSize: '1rem',
                  borderRadius: '9999px',
                  px: 4,
                  py: 1.4,
                  textTransform: 'none',
                  boxShadow: '0 6px 18px rgba(251, 191, 36, 0.4)',
                  transition: 'all 200ms ease',
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
                  fontSize: '1rem',
                  borderRadius: '9999px',
                  px: 4,
                  py: 1.4,
                  textTransform: 'none',
                  border: '1.5px solid #E2E8F0',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.03)',
                  transition: 'all 200ms ease',
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
      {/* 6. SECTION FOOTER (Ảnh 2)                                                 */}
      {/* ========================================================================= */}
      <Box
        component="footer"
        sx={{
          pt: { xs: 7, md: 9 },
          pb: 5,
          bgcolor: '#FFFFFF',
          borderTop: '1px solid #E2E8F0',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Grid container spacing={{ xs: 4, md: 6 }} sx={{ mb: 6 }}>
            {/* Col 1: Brand */}
            <Grid size={{ xs: 12, md: 5 }}>
              <Typography
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontWeight: 900,
                  fontSize: '1.35rem',
                  color: '#1E1B4B',
                  letterSpacing: '-0.02em',
                  mb: 1.25,
                }}
              >
                MathVisionKid
              </Typography>
              <Typography sx={{ color: '#64748B', fontSize: '0.88rem', lineHeight: 1.6, maxWidth: 300 }}>
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
                <Box component="a" href="#lo-trinh" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Lộ trình học
                </Box>
                <Box component="a" href="#tinh-nang" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
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
                <Box component="a" href="#giai-dap" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Dành cho phụ huynh
                </Box>
                <Box component="a" href="#giai-dap" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
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
                <Box component="a" href="#" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Quyền riêng tư
                </Box>
                <Box component="a" href="#" sx={{ color: '#64748B', fontSize: '0.86rem', textDecoration: 'none', '&:hover': { color: '#6D28D9' } }}>
                  Điều khoản
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Bottom Line */}
          <Box
            sx={{
              pt: 3.5,
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
