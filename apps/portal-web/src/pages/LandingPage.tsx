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
    <Box sx={{ width: '100%', bgcolor: '#FAF8FE', color: '#190568', overflowX: 'hidden' }}>

      {/* ========================================================================= */}
      {/* 1. HERO SECTION (Ảnh 1 & Figma 2:4)                                       */}
      {/* ========================================================================= */}
      <Box
        id="hero"
        sx={{
          pt: { xs: 5, md: 6.5 },
          pb: { xs: 4, md: 5 },
          background: 'linear-gradient(180deg, #F8F5FE 0%, #F1EAFA 100%)',
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
          <Grid container spacing={{ xs: 4, md: 3 }} sx={{ alignItems: 'center' }}>
            
            {/* Hero Left Content */}
            <Grid size={{ xs: 12, md: 6.2 }}>
              <Typography
                variant="h1"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontSize: { xs: '2.75rem', sm: '3.6rem', md: '4.2rem', lg: '4.65rem' },
                  fontWeight: 900,
                  color: '#190568',
                  lineHeight: 1.15,
                  letterSpacing: '-0.03em',
                  mb: 2.5,
                }}
              >
                Cùng{' '}
                <Box component="span" sx={{ color: '#FFB11B' }}>
                  MathVisionKid
                </Box>
                <br />
                Khám Phá Toán Nhẹ Nhàng!
              </Typography>

              <Typography
                sx={{
                  color: '#190568',
                  fontSize: { xs: '1.12rem', md: '1.22rem' },
                  lineHeight: 1.6,
                  maxWidth: 580,
                  mb: 4.5,
                  fontWeight: 600,
                }}
              >
                Cùng MathVisionKid rèn luyện tư duy nhanh nhạy, Toán điểm trở thành hành trình thú vị hơn bao giờ hết!
              </Typography>

              <Box sx={{ flexWrap: 'wrap', display: 'flex', gap: 2.25, mb: { xs: 4, md: 1 } }}>
                <Button
                  component={RouterLink}
                  to="/login"
                  sx={{
                    bgcolor: '#FFD747',
                    color: '#190568',
                    fontWeight: 900,
                    fontSize: '1.12rem',
                    borderRadius: '26px',
                    px: 4.5,
                    py: 1.4,
                    textTransform: 'none',
                    boxShadow: '0 4px 14px rgba(255, 215, 71, 0.4)',
                    transition: 'all 180ms ease',
                    '&:hover': { bgcolor: '#F5CE38', transform: 'translateY(-2px)' },
                  }}
                >
                  Học ngay →
                </Button>
                <Button
                  component={RouterLink}
                  to="/login"
                  sx={{
                    bgcolor: '#6C2BD9',
                    color: '#FFFFFF',
                    fontWeight: 800,
                    fontSize: '1.12rem',
                    borderRadius: '26px',
                    px: 4.2,
                    py: 1.4,
                    textTransform: 'none',
                    boxShadow: '0 4px 14px rgba(108, 43, 217, 0.35)',
                    transition: 'all 180ms ease',
                    '&:hover': { bgcolor: '#5B21B6', transform: 'translateY(-2px)' },
                  }}
                >
                  Chụp bài, hỏi AI
                </Button>
              </Box>
            </Grid>

            {/* Hero Right Mascot & Notebook Artwork */}
            <Grid size={{ xs: 12, md: 5.8 }} sx={{ display: 'flex', justifyContent: { xs: 'center', md: 'flex-end' }, alignItems: 'center' }}>
              <Box
                sx={{
                  position: 'relative',
                  width: { xs: '100%', sm: 480, md: 540, lg: 600 },
                  maxWidth: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'transform 240ms ease',
                  '&:hover': { transform: 'scale(1.02)' },
                }}
              >
                <Box
                  component="img"
                  src="/ui/robot-mascot.webp"
                  alt="Robot MathVisionKid"
                  sx={{
                    width: '100%',
                    height: 'auto',
                    objectFit: 'contain',
                    display: 'block',
                  }}
                />
              </Box>
            </Grid>
          </Grid>

          {/* Dải 4 thẻ tổng quan dưới Hero (Under-Hero 4 Cards - Figma 2:5) */}
          <Box sx={{ mt: { xs: 4, md: 5 } }}>
            <Box
              sx={{
                bgcolor: '#F0EAFB',
                borderRadius: '24px',
                p: { xs: 2.5, sm: 3.5 },
                border: '1.5px solid #E3D5FF',
              }}
            >
              {/* Stepper link text */}
              <Typography
                sx={{
                  color: '#190568',
                  fontWeight: 800,
                  fontSize: '1.05rem',
                  mb: 2.5,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  pl: 0.5,
                }}
              >
                <span>Ôn tập</span>
                <span style={{ color: '#6500EF' }}>→</span>
                <span>Luyện tập</span>
                <span style={{ color: '#6500EF' }}>→</span>
                <span>Khám phá</span>
                <span style={{ color: '#6500EF' }}>→</span>
                <span>Kiểm tra</span>
              </Typography>

              <Grid container spacing={2.25}>
                {/* Card 1: Luyện tập tương tác */}
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Box
                    sx={{
                      bgcolor: '#F0EAFD',
                      borderRadius: '16px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #DCCCFF',
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
                          height: 72,
                          borderRadius: '9px',
                          overflow: 'hidden',
                          mb: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: '#EBF4FF',
                        }}
                      >
                        <Box
                          component="img"
                          src="/ui/card1-practice.png"
                          alt="Luyện tập tương tác"
                          sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </Box>
                      <Typography sx={{ fontWeight: 900, fontSize: '1.08rem', color: '#190568', mb: 0.5 }}>
                        Luyện tập tương tác
                      </Typography>
                      <Typography sx={{ fontSize: '0.88rem', color: '#190568', opacity: 0.85 }}>
                        Mỗi giờ, 100% điểm số!
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '14px',
                          bgcolor: '#AE80E8',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.9rem',
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
                      bgcolor: '#F0EAFD',
                      borderRadius: '16px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #DCCCFF',
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
                          height: 72,
                          borderRadius: '9px',
                          overflow: 'hidden',
                          mb: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: '#190568',
                        }}
                      >
                        <Box
                          component="img"
                          src="/ui/card2-exercises.png"
                          alt="Bài tập đa dạng"
                          sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </Box>
                      <Typography sx={{ fontWeight: 900, fontSize: '1.08rem', color: '#190568', mb: 0.5 }}>
                        Bài tập đa dạng
                      </Typography>
                      <Typography sx={{ fontSize: '0.88rem', color: '#190568', opacity: 0.85 }}>
                        Từ cơ bản đến nâng cao.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '14px',
                          bgcolor: '#AE80E8',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.9rem',
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
                      bgcolor: '#F0EAFD',
                      borderRadius: '16px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #DCCCFF',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Header inside Card 3 */}
                      <Typography sx={{ fontSize: '0.88rem', fontWeight: 700, color: '#190568', textAlign: 'center', mb: 1 }}>
                        Interactive minigames
                      </Typography>
                      {/* Image Preview: Equation */}
                      <Box
                        sx={{
                          height: 48,
                          borderRadius: '9px',
                          overflow: 'hidden',
                          mb: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: '#FAF8FC',
                          border: '1px solid #ECE3F8',
                        }}
                      >
                        <Box
                          component="img"
                          src="/ui/card3-minigames.png"
                          alt="Interactive minigames"
                          sx={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        />
                      </Box>
                      <Typography sx={{ fontWeight: 900, fontSize: '1.08rem', color: '#190568', mb: 0.5 }}>
                        Minigames thú vị
                      </Typography>
                      <Typography sx={{ fontSize: '0.88rem', color: '#190568', opacity: 0.85 }}>
                        Rèn luyện tư duy nhanh.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '14px',
                          bgcolor: '#AE80E8',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.9rem',
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
                      bgcolor: '#F0EAFD',
                      borderRadius: '16px',
                      p: 2,
                      boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
                      border: '1px solid #DCCCFF',
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'transform 180ms ease',
                      '&:hover': { transform: 'translateY(-2px)' },
                    }}
                  >
                    <Box>
                      {/* Header inside Card 4 */}
                      <Typography sx={{ fontSize: '0.88rem', fontWeight: 700, color: '#190568', textAlign: 'center', mb: 1 }}>
                        Socratic guidance
                      </Typography>
                      {/* Image Preview: Socratic guidance */}
                      <Box
                        sx={{
                          height: 48,
                          borderRadius: '9px',
                          overflow: 'hidden',
                          mb: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: '#FAF8FC',
                          border: '1px solid #ECE3F8',
                        }}
                      >
                        <Box
                          component="img"
                          src="/ui/card4-socratic.png"
                          alt="Socratic guidance"
                          sx={{ width: '100%', height: '100%', objectFit: 'contain' }}
                        />
                      </Box>
                      <Typography sx={{ fontWeight: 900, fontSize: '1.08rem', color: '#190568', mb: 0.5 }}>
                        Hỗ trợ từ AI
                      </Typography>
                      <Typography sx={{ fontSize: '0.88rem', color: '#190568', opacity: 0.85 }}>
                        Gợi ý, hướng dẫn và chấm điểm.
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1.5 }}>
                      <Box
                        sx={{
                          width: 28,
                          height: 28,
                          borderRadius: '14px',
                          bgcolor: '#AE80E8',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 900,
                          fontSize: '0.9rem',
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
      {/* 2. SECTION LỘ TRÌNH (Ảnh 2 & Figma 2:6)                                   */}
      {/* ========================================================================= */}
      <Box id="lo-trinh" sx={{ py: { xs: 7, md: 10 }, bgcolor: '#FFFFFF' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          
          {/* Header Section */}
          <Typography sx={{ color: '#9A50FF', fontWeight: 900, fontSize: '0.92rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 1 }}>
            LỘ TRÌNH
          </Typography>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-end', gap: 2, mb: 4.5 }}>
            <Box>
              <Typography
                variant="h2"
                sx={{
                  fontFamily: 'Nunito, sans-serif',
                  fontWeight: 900,
                  fontSize: { xs: '2.1rem', sm: '2.75rem' },
                  color: '#190568',
                  lineHeight: 1.25,
                  mb: 0.75,
                }}
              >
                Mỗi bước nhỏ, một khám phá lớn
              </Typography>
              <Typography sx={{ color: '#4C29A5', fontSize: '1.15rem' }}>
                Từ những con số đầu tiên đến tư duy toán học vững chắc
              </Typography>
            </Box>
            <Typography sx={{ color: '#6900FF', fontWeight: 700, fontSize: '0.95rem' }}>
              Dành cho học sinh tiểu học
            </Typography>
          </Box>

          {/* Grade Selector Capsule Bar (Figma 2:68) */}
          <Box
            sx={{
              display: 'inline-flex',
              bgcolor: '#EEE6FA',
              border: '1px solid #E7D9FF',
              borderRadius: '18px',
              p: 0.6,
              mb: 5,
              width: '100%',
              maxWidth: 760,
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
                    py: 1.1,
                    borderRadius: '14px',
                    fontWeight: 800,
                    fontSize: '1.02rem',
                    textTransform: 'none',
                    bgcolor: active ? '#8C4CD6' : 'transparent',
                    color: active ? '#FFFFFF' : '#260780',
                    boxShadow: active ? '0 4px 12px rgba(140, 76, 214, 0.25)' : 'none',
                    '&:hover': {
                      bgcolor: active ? '#8C4CD6' : 'rgba(140, 76, 214, 0.08)',
                    },
                  }}
                >
                  {grade.label}
                </Button>
              );
            })}
          </Box>

          {/* 3 Roadmap Cards (Figma 2:75, 2:84, 2:93) */}
          <Grid container spacing={3.5} sx={{ mb: 4.5 }}>
            {/* Card 01 */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 4,
                  border: '1.5px solid #DFD0FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.25 }}>
                    <Box
                      sx={{
                        width: 44,
                        height: 42,
                        borderRadius: '14px',
                        bgcolor: '#FFF0C9',
                        color: '#B66B00',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.15rem',
                        fontWeight: 900,
                      }}
                    >
                      01
                    </Box>
                    <Typography sx={{ color: '#B66B00', fontWeight: 900, fontSize: '0.85rem', letterSpacing: '0.04em' }}>
                      BẮT ĐẦU TỪ ĐÂY
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.55rem', color: '#190568', mb: 1.5 }}>
                    Làm quen con số
                  </Typography>
                  <Typography sx={{ color: '#55349F', fontSize: '1.05rem', lineHeight: 1.6 }}>
                    Đếm, so sánh và khám phá các số trong phạm vi 10.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3.5, borderTop: '1px solid #F8FAFC', mt: 3.5 }}>
                  <Typography sx={{ fontSize: '1.02rem', fontWeight: 700, color: '#5937A5' }}>
                    6 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 42,
                      height: 42,
                      borderRadius: '21px',
                      bgcolor: '#F0E6FF',
                      color: '#6300FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 900,
                      fontSize: '1.25rem',
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
                  p: 4,
                  border: '1.5px solid #DFD0FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.25 }}>
                    <Box
                      sx={{
                        width: 44,
                        height: 42,
                        borderRadius: '14px',
                        bgcolor: '#EEE2FF',
                        color: '#6500FF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.15rem',
                        fontWeight: 900,
                      }}
                    >
                      02
                    </Box>
                    <Typography sx={{ color: '#6500FF', fontWeight: 900, fontSize: '0.85rem', letterSpacing: '0.04em' }}>
                      TIẾN BƯỚC VỮNG VÀNG
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.55rem', color: '#190568', mb: 1.5 }}>
                    Cộng trừ thật vui
                  </Typography>
                  <Typography sx={{ color: '#55349F', fontSize: '1.05rem', lineHeight: 1.6 }}>
                    Học phép tính qua hình ảnh và những câu chuyện gần gũi.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3.5, borderTop: '1px solid #F8FAFC', mt: 3.5 }}>
                  <Typography sx={{ fontSize: '1.02rem', fontWeight: 700, color: '#5937A5' }}>
                    8 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 42,
                      height: 42,
                      borderRadius: '21px',
                      bgcolor: '#F0E6FF',
                      color: '#6300FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 900,
                      fontSize: '1.25rem',
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
                  p: 4,
                  border: '1.5px solid #DFD0FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.25 }}>
                    <Box
                      sx={{
                        width: 44,
                        height: 42,
                        borderRadius: '14px',
                        bgcolor: '#D8FCF1',
                        color: '#008D77',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.15rem',
                        fontWeight: 900,
                      }}
                    >
                      03
                    </Box>
                    <Typography sx={{ color: '#008D77', fontWeight: 900, fontSize: '0.85rem', letterSpacing: '0.04em' }}>
                      THỬ THÁCH LỚN
                    </Typography>
                  </Box>
                  <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.55rem', color: '#190568', mb: 1.5 }}>
                    Thế giới hình học
                  </Typography>
                  <Typography sx={{ color: '#55349F', fontSize: '1.05rem', lineHeight: 1.6 }}>
                    Nhận biết hình khối, vị trí và quy luật quanh em.
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 3.5, borderTop: '1px solid #F8FAFC', mt: 3.5 }}>
                  <Typography sx={{ fontSize: '1.02rem', fontWeight: 700, color: '#5937A5' }}>
                    5 bài học
                  </Typography>
                  <Box
                    sx={{
                      width: 42,
                      height: 42,
                      borderRadius: '21px',
                      bgcolor: '#F0E6FF',
                      color: '#6300FF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 900,
                      fontSize: '1.25rem',
                    }}
                  >
                    →
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Stepper capsule bar below (Figma 2:102) */}
          <Box
            sx={{
              bgcolor: '#F0E7FC',
              borderRadius: '22px',
              py: 2,
              px: { xs: 2.5, sm: 4 },
              textAlign: 'center',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'center',
              gap: { xs: 2, sm: 3.5 },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Typography sx={{ color: '#A16AFF', fontWeight: 900, fontSize: '1.05rem' }}>01</Typography>
              <Typography sx={{ color: '#190568', fontWeight: 800, fontSize: '1.05rem' }}>Ôn tập</Typography>
            </Box>
            <Typography sx={{ color: '#9C4AFF', fontWeight: 800, fontSize: '1.2rem' }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Typography sx={{ color: '#A16AFF', fontWeight: 900, fontSize: '1.05rem' }}>02</Typography>
              <Typography sx={{ color: '#190568', fontWeight: 800, fontSize: '1.05rem' }}>Luyện tập</Typography>
            </Box>
            <Typography sx={{ color: '#9C4AFF', fontWeight: 800, fontSize: '1.2rem' }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Typography sx={{ color: '#A16AFF', fontWeight: 900, fontSize: '1.05rem' }}>03</Typography>
              <Typography sx={{ color: '#190568', fontWeight: 800, fontSize: '1.05rem' }}>Khám phá</Typography>
            </Box>
            <Typography sx={{ color: '#9C4AFF', fontWeight: 800, fontSize: '1.2rem' }}>→</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
              <Typography sx={{ color: '#A16AFF', fontWeight: 900, fontSize: '1.05rem' }}>04</Typography>
              <Typography sx={{ color: '#190568', fontWeight: 800, fontSize: '1.05rem' }}>Kiểm tra</Typography>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 3. SECTION TÍNH NĂNG (Ảnh 3 & Figma 2:7)                                  */}
      {/* ========================================================================= */}
      <Box id="tinh-nang" sx={{ py: { xs: 7, md: 10 }, bgcolor: '#FAF8FE' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          
          {/* Header */}
          <Typography sx={{ color: '#9A50FF', fontWeight: 900, fontSize: '0.92rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 0.5 }}>
            TÍNH NĂNG
          </Typography>
          <Box sx={{ width: 80, height: 3, bgcolor: '#D9C2FF', borderRadius: '2px', mb: 2 }} />

          <Typography
            variant="h2"
            sx={{
              fontFamily: 'Nunito, sans-serif',
              fontWeight: 900,
              fontSize: { xs: '2.1rem', sm: '2.75rem' },
              color: '#190568',
              lineHeight: 1.25,
              mb: 1.25,
            }}
          >
            Bốn cách học vui, một hành trình tự tin
          </Typography>
          <Typography sx={{ color: '#4C29A5', fontSize: '1.15rem', mb: 5 }}>
            Luyện tập, khám phá và ôn lại giờ theo cách của riêng em.
          </Typography>

          {/* 2x2 Grid of Feature Cards */}
          <Grid container spacing={3.5}>
            
            {/* Feature 01: Luyện tập tương tác (Figma 2:118) */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 4,
                  border: '1.5px solid #E1D1FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box
                      sx={{
                        width: 38,
                        height: 38,
                        borderRadius: '12px',
                        bgcolor: '#FFF2CE',
                        color: '#BE7400',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.95rem',
                        fontWeight: 900,
                      }}
                    >
                      01
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.45rem', color: '#190568' }}>
                      Luyện tập tương tác
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#5737A2', fontSize: '1.05rem', lineHeight: 1.6, mb: 3.5 }}>
                    Chọn đáp án, nhận phản hồi và ôn lại kiến thức ngay lập tức qua trò chơi thú vị.
                  </Typography>

                  {/* Interactive box (Figma 2:146) */}
                  <Box sx={{ bgcolor: '#F7F1FC', borderRadius: '18px', p: 3, mb: 2.5 }}>
                    <Typography sx={{ color: '#190568', fontSize: '0.88rem', fontWeight: 800, mb: 1.5 }}>
                      Chọn đáp án đúng
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.85rem', color: '#190568' }}>
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
                                minWidth: 58,
                                height: 48,
                                borderRadius: '14px',
                                fontWeight: 900,
                                fontSize: '1.15rem',
                                bgcolor: active ? '#FFDA52' : '#FFFFFF',
                                color: '#190568',
                                border: active ? '1.5px solid #FFDA52' : '1.5px solid #E0D0FF',
                                boxShadow: active ? '0 2px 8px rgba(255, 218, 82, 0.3)' : 'none',
                                '&:hover': { bgcolor: active ? '#FFDA52' : '#F1F5F9' },
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
                    color: '#6400FF',
                    fontWeight: 800,
                    fontSize: '1.05rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1.5,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Luyện tập ngay →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 02: Bài tập đa dạng (Figma 2:125) */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 4,
                  border: '1.5px solid #E1D1FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box
                      sx={{
                        width: 38,
                        height: 38,
                        borderRadius: '12px',
                        bgcolor: '#F0E6FF',
                        color: '#6500FF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.95rem',
                        fontWeight: 900,
                      }}
                    >
                      02
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.45rem', color: '#190568' }}>
                      Bài tập đa dạng
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#5737A2', fontSize: '1.05rem', lineHeight: 1.6, mb: 3.5 }}>
                    Từ cơ bản đến nâng cao, cho từng cấp độ, ôn đúng kiến thức, tiến bộ từng bước nhỏ.
                  </Typography>

                  {/* Inner list box (Figma 2:155) */}
                  <Box sx={{ bgcolor: '#F3EBFD', borderRadius: '18px', p: 2.5, mb: 2.5, display: 'grid', gap: 1.5 }}>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.75, borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E0D0FF' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography sx={{ fontSize: '1.02rem', fontWeight: 900, color: '#6800FF' }}>
                          01
                        </Typography>
                        <Typography sx={{ fontSize: '1.02rem', fontWeight: 800, color: '#190568' }}>
                          Đếm số còn thiếu
                        </Typography>
                      </Box>
                      <Chip label="Cấp độ" size="small" sx={{ bgcolor: '#F1F5F9', color: '#6740B3', fontSize: '0.85rem', fontWeight: 800, height: 26 }} />
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.75, borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', border: '1px solid #E0D0FF' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography sx={{ fontSize: '1.02rem', fontWeight: 900, color: '#6800FF' }}>
                          02
                        </Typography>
                        <Typography sx={{ fontSize: '1.02rem', fontWeight: 800, color: '#190568' }}>
                          Giải toán có lời văn
                        </Typography>
                      </Box>
                      <Chip label="Vận dụng" size="small" sx={{ bgcolor: '#F1F5F9', color: '#6740B3', fontSize: '0.85rem', fontWeight: 800, height: 26 }} />
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6400FF',
                    fontWeight: 800,
                    fontSize: '1.05rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1.5,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Khám phá bài tập →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 03: Minigames thú vị! (Figma 2:132) */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 4,
                  border: '1.5px solid #E1D1FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box
                      sx={{
                        width: 38,
                        height: 38,
                        borderRadius: '12px',
                        bgcolor: '#D7FAF0',
                        color: '#006E78',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.95rem',
                        fontWeight: 900,
                      }}
                    >
                      03
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.45rem', color: '#190568' }}>
                      Minigames thú vị!
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#5737A2', fontSize: '1.05rem', lineHeight: 1.6, mb: 3.5 }}>
                    Biến phép tính thành trò chơi hấp dẫn. Rèn phản xạ, tư duy nhanh và bền hơn.
                  </Typography>

                  {/* Interactive game box (Figma 2:164) */}
                  <Box sx={{ bgcolor: '#F8F4FD', borderRadius: '18px', p: 3, mb: 2.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                      <Typography sx={{ color: '#008D43', fontSize: '0.92rem', fontWeight: 800 }}>
                        Thử thách trong tuần
                      </Typography>
                      <Chip label="0/24" size="small" sx={{ bgcolor: '#D5FFE2', color: '#009F37', fontWeight: 900, fontSize: '0.88rem', height: 26 }} />
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 900, fontSize: '1.85rem', color: '#190568' }}>
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
                                minWidth: 58,
                                height: 48,
                                borderRadius: '14px',
                                fontWeight: 900,
                                fontSize: '1.15rem',
                                bgcolor: active ? '#C6FAE4' : '#FFFFFF',
                                color: '#190568',
                                border: active ? '1.5px solid #B9F2D8' : '1.5px solid #E0D0FF',
                                boxShadow: active ? '0 2px 8px rgba(198, 250, 228, 0.4)' : 'none',
                                '&:hover': { bgcolor: active ? '#C6FAE4' : '#F1F5F9' },
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
                    color: '#6400FF',
                    fontWeight: 800,
                    fontSize: '1.05rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1.5,
                    '&:hover': { textDecoration: 'underline' },
                  }}
                >
                  Chơi thử minigame →
                </Typography>
              </Box>
            </Grid>

            {/* Feature 04: Hỗ trợ từ AI (Figma 2:139) */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                sx={{
                  bgcolor: '#FFFFFF',
                  borderRadius: '24px',
                  p: 4,
                  border: '1.5px solid #E1D1FF',
                  boxShadow: '0 2px 12px rgba(0,0,0,0.02)',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'transform 180ms ease',
                  '&:hover': { transform: 'translateY(-3px)' },
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                    <Box
                      sx={{
                        width: 38,
                        height: 38,
                        borderRadius: '12px',
                        bgcolor: '#F1E7FF',
                        color: '#6500FF',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.95rem',
                        fontWeight: 900,
                      }}
                    >
                      04
                    </Box>
                    <Typography sx={{ fontFamily: 'Nunito, sans-serif', fontWeight: 900, fontSize: '1.45rem', color: '#190568' }}>
                      Hỗ trợ từ AI
                    </Typography>
                  </Box>
                  <Typography sx={{ color: '#5737A2', fontSize: '1.05rem', lineHeight: 1.6, mb: 3.5 }}>
                    Chưa rõ hoặc cần hỗ trợ? Hãy hỏi AI, giúp bạn và giải mọi thắc mắc, từng bước một.
                  </Typography>

                  {/* AI Chat box (Figma 2:175) */}
                  <Box sx={{ bgcolor: '#F7F1FD', borderRadius: '18px', p: 2.5, mb: 2.5, display: 'grid', gap: 1.5 }}>
                    <Box sx={{ bgcolor: '#F0E6FC', py: 1.25, px: 2, borderRadius: '20px', textAlign: 'center' }}>
                      <Typography sx={{ fontSize: '1.05rem', fontWeight: 800, color: '#190568' }}>
                        Bài toán: 8 + 7 = ?
                      </Typography>
                    </Box>
                    <Box sx={{ bgcolor: '#FFFFFF', p: 1.75, borderRadius: '14px', border: '1px solid #DDCAFF' }}>
                      <Typography sx={{ fontSize: '0.98rem', color: '#8464BD' }}>
                        Em hãy trả lời: 8 + 7 bằng bao nhiêu?
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                <Typography
                  component={RouterLink}
                  to="/login"
                  sx={{
                    color: '#6400FF',
                    fontWeight: 800,
                    fontSize: '1.05rem',
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.75,
                    mt: 1.5,
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
      {/* 4. SECTION GIẢI ĐÁP CÙNG BA MẸ (FAQ - Figma 6:3)                          */}
      {/* ========================================================================= */}
      <Box id="giai-dap" sx={{ py: { xs: 7, md: 10 }, bgcolor: '#EFEAFB' }}>
        <Container maxWidth="md" sx={{ px: { xs: 2.5, sm: 4 } }}>
          
          <Box sx={{ textAlign: 'center', mb: 5.5 }}>
            <Typography sx={{ color: '#6C507F', fontWeight: 900, fontSize: '0.92rem', letterSpacing: '0.04em', textTransform: 'uppercase', mb: 1 }}>
              GIẢI ĐÁP CÙNG BA MẸ
            </Typography>
            <Typography
              variant="h2"
              sx={{
                fontFamily: 'Nunito, sans-serif',
                fontWeight: 900,
                fontSize: { xs: '2.1rem', sm: '2.75rem' },
                color: '#302936',
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
                borderRadius: '18px',
                p: { xs: 2.5, sm: 3.5 },
                border: '1.5px solid #E4DDEA',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
                transition: 'border-color 160ms ease',
                '&:hover': { borderColor: '#C4B5FD' },
              }}
              onClick={() => toggleFaq(1)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.05rem', sm: '1.18rem' }, color: '#302936' }}>
                  MathVisionKid phù hợp với học sinh lớp mấy?
                </Typography>
                <Typography sx={{ fontSize: '1.6rem', fontWeight: 700, color: '#6C507F', lineHeight: 1 }}>
                  {faqOpen[1] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[1]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#6B7280', fontSize: '1.02rem', lineHeight: 1.7 }}>
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
                borderRadius: '18px',
                p: { xs: 2.5, sm: 3.5 },
                border: '1.5px solid #E4DDEA',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
                transition: 'border-color 160ms ease',
                '&:hover': { borderColor: '#C4B5FD' },
              }}
              onClick={() => toggleFaq(2)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.05rem', sm: '1.18rem' }, color: '#302936' }}>
                  Con cần học bao lâu mỗi ngày?
                </Typography>
                <Typography sx={{ fontSize: '1.6rem', fontWeight: 700, color: '#6C507F', lineHeight: 1 }}>
                  {faqOpen[2] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[2]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#6B7280', fontSize: '1.02rem', lineHeight: 1.7 }}>
                    Chỉ cần 15 đến 20 phút mỗi ngày. Các bài tập được chia nhỏ thành các thử thách ngắn giúp bé hào hứng học mà không bị mỏi mệt.
                  </Typography>
                </Box>
              </Collapse>
            </Box>

            {/* FAQ 3 */}
            <Box
              sx={{
                bgcolor: '#FFFFFF',
                borderRadius: '18px',
                p: { xs: 2.5, sm: 3.5 },
                border: '1.5px solid #E4DDEA',
                boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
                cursor: 'pointer',
                transition: 'border-color 160ms ease',
                '&:hover': { borderColor: '#C4B5FD' },
              }}
              onClick={() => toggleFaq(3)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
                <Typography sx={{ fontWeight: 800, fontSize: { xs: '1.05rem', sm: '1.18rem' }, color: '#302936' }}>
                  AI sẽ giúp con học như thế nào?
                </Typography>
                <Typography sx={{ fontSize: '1.6rem', fontWeight: 700, color: '#6C507F', lineHeight: 1 }}>
                  {faqOpen[3] ? '−' : '+'}
                </Typography>
              </Box>
              <Collapse in={faqOpen[3]}>
                <Box sx={{ pt: 2, borderTop: '1px solid #F1F5F9', mt: 2 }}>
                  <Typography sx={{ color: '#6B7280', fontSize: '1.02rem', lineHeight: 1.7 }}>
                    AI của MathVisionKid đóng vai trò người gia sư kiên nhẫn: phân tích từng nét chữ đặt tính trên vở ô ly, chỉ ra điểm nhầm lẫn và đặt câu hỏi gợi mở để con tự tìm ra cách giải, tuyệt đối không đưa sẵn đáp số.
                  </Typography>
                </Box>
              </Collapse>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* ========================================================================= */}
      {/* 5. SECTION CTA BANNER (MỖI NGÀY MỘT CHÚT TỰ TIN - Figma 6:4)              */}
      {/* ========================================================================= */}
      <Box sx={{ py: { xs: 5, md: 8 }, bgcolor: '#F9F6FD' }}>
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          <Box
            sx={{
              bgcolor: '#EBE1FC',
              borderRadius: '26px',
              py: { xs: 5, md: 7 },
              px: { xs: 3, sm: 6 },
              textAlign: 'center',
              border: '1.5px solid #E3D7EE',
            }}
          >
            <Typography sx={{ color: '#6C507F', fontWeight: 900, fontSize: '0.85rem', letterSpacing: '0.06em', textTransform: 'uppercase', mb: 1.5 }}>
              MỖI NGÀY MỘT CHÚT TỰ TIN
            </Typography>

            <Typography
              variant="h2"
              sx={{
                fontFamily: 'Nunito, sans-serif',
                fontWeight: 900,
                fontSize: { xs: '2.1rem', sm: '2.75rem' },
                color: '#302936',
                lineHeight: 1.25,
                mb: 1.5,
              }}
            >
              Sẵn sàng cho chuyến phiêu lưu toán học?
            </Typography>

            <Typography
              sx={{
                color: '#71697A',
                fontSize: { xs: '1.05rem', md: '1.18rem' },
                maxWidth: 620,
                mx: 'auto',
                mb: 4.5,
              }}
            >
              Cùng MathVisionKid biến “con chưa biết” thành “con làm được rồi!”
            </Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 2.5 }}>
              <Button
                component={RouterLink}
                to="/login"
                sx={{
                  bgcolor: '#FFDA67',
                  color: '#302936',
                  fontWeight: 900,
                  fontSize: '1.08rem',
                  borderRadius: '25px',
                  px: 4.5,
                  py: 1.35,
                  textTransform: 'none',
                  boxShadow: '0 4px 14px rgba(255, 218, 103, 0.4)',
                  transition: 'all 180ms ease',
                  '&:hover': { bgcolor: '#F5CE38', transform: 'translateY(-2px)' },
                }}
              >
                Bắt đầu học ngay →
              </Button>
              <Button
                component="a"
                href="#lo-trinh"
                sx={{
                  bgcolor: '#FFFFFF',
                  color: '#302936',
                  fontWeight: 800,
                  fontSize: '1.08rem',
                  borderRadius: '25px',
                  px: 4.5,
                  py: 1.35,
                  textTransform: 'none',
                  border: '1.5px solid #E3D7EE',
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
      {/* 6. SECTION FOOTER (Figma 6:5)                                             */}
      {/* ========================================================================= */}
      <Box
        component="footer"
        sx={{
          pt: { xs: 6, md: 8 },
          pb: 4.5,
          bgcolor: '#EEE7F8',
          borderTop: '1px solid #DDD4E8',
        }}
      >
        <Container maxWidth="lg" sx={{ px: { xs: 2.5, sm: 4, md: 5 } }}>
          <Grid container spacing={{ xs: 4, md: 5 }} sx={{ mb: 5 }}>
            {/* Col 1: Brand */}
            <Grid size={{ xs: 12, md: 5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                <Box
                  component="img"
                  src="/ui/planet-logo.png"
                  alt="MathVisionKid"
                  sx={{
                    width: 36,
                    height: 27,
                    objectFit: 'contain',
                  }}
                />
                <Typography
                  sx={{
                    fontFamily: 'Nunito, sans-serif',
                    fontWeight: 900,
                    fontSize: '1.45rem',
                    color: '#6C507F',
                    letterSpacing: '-0.02em',
                  }}
                >
                  MathVisionKid
                </Typography>
              </Box>
              <Typography sx={{ color: '#71697A', fontSize: '0.95rem', lineHeight: 1.65, maxWidth: 340 }}>
                Nuôi dưỡng niềm vui học toán,<br />
                chắp cánh những khám phá nhỏ.
              </Typography>
            </Grid>

            {/* Col 2: Khám phá */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '1rem', color: '#302936', mb: 2 }}>
                Khám phá
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.25 }}>
                <Box component="a" href="#lo-trinh" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Lộ trình học
                </Box>
                <Box component="a" href="#tinh-nang" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Bài tập & trò chơi
                </Box>
              </Box>
            </Grid>

            {/* Col 3: Đồng hành */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '1rem', color: '#302936', mb: 2 }}>
                Đồng hành
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.25 }}>
                <Box component="a" href="#giai-dap" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Dành cho phụ huynh
                </Box>
                <Box component="a" href="#giai-dap" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Câu hỏi thường gặp
                </Box>
              </Box>
            </Grid>

            {/* Col 4: Thông tin */}
            <Grid size={{ xs: 6, sm: 4, md: 2.3 }}>
              <Typography sx={{ fontWeight: 800, fontSize: '1rem', color: '#302936', mb: 2 }}>
                Thông tin
              </Typography>
              <Box sx={{ display: 'grid', gap: 1.25 }}>
                <Box component="a" href="#" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Quyền riêng tư
                </Box>
                <Box component="a" href="#" sx={{ color: '#71697A', fontSize: '0.92rem', textDecoration: 'none', '&:hover': { color: '#6500EF' } }}>
                  Điều khoản
                </Box>
              </Box>
            </Grid>
          </Grid>

          {/* Bottom Line */}
          <Box
            sx={{
              pt: 3,
              borderTop: '1px solid #DDD4E8',
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 1.5,
              color: '#71697A',
              fontSize: '0.88rem',
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
