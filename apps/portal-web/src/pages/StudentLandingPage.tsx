import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Chip,
  Card,
  TextField,
  Dialog,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import MicIcon from '@mui/icons-material/Mic';
import SparklesIcon from '@mui/icons-material/AutoAwesome';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { authService, type UserProfile } from '../services/authService';
import { tokenStore } from '../services/apiClient';

interface PracticeProblem {
  grade: number;
  num1: number;
  num2: number;
  op: '+' | '-';
  result: number;
  carryText?: string;
}

const GRADE_PROBLEMS: Record<number, PracticeProblem[]> = {
  1: [
    { grade: 1, num1: 23, num2: 15, op: '+', result: 38 },
    { grade: 1, num1: 45, num2: 21, op: '+', result: 66 },
    { grade: 1, num1: 56, num2: 24, op: '+', result: 80, carryText: '6 + 4 = 10, viết 0 nhớ 1 sang hàng chục nhé!' },
  ],
  2: [
    { grade: 2, num1: 48, num2: 27, op: '+', result: 75, carryText: '8 + 7 = 15, viết 5 nhớ 1 sang hàng chục nhé!' },
    { grade: 2, num1: 83, num2: 36, op: '-', result: 47, carryText: '3 không trừ được 6, mượn 1 chục là 13 - 6 = 7 nhé!' },
    { grade: 2, num1: 54, num2: 39, op: '+', result: 93, carryText: '4 + 9 = 13, viết 3 nhớ 1 sang hàng chục nhé!' },
  ],
  3: [
    { grade: 3, num1: 245, num2: 178, op: '+', result: 423, carryText: '5 + 8 = 13 nhớ 1; 4 + 7 = 11 thêm 1 là 12 nhớ 1!' },
    { grade: 3, num1: 356, num2: 289, op: '+', result: 645, carryText: '6 + 9 = 15 nhớ 1; 5 + 8 = 13 thêm 1 là 14 nhớ 1!' },
    { grade: 3, num1: 524, num2: 187, op: '-', result: 337, carryText: 'Nhớ trả 1 vào hàng chục khi trừ có mượn nhé!' },
  ],
  4: [
    { grade: 4, num1: 1425, num2: 2839, op: '+', result: 4264, carryText: 'Đặt tính thẳng cột từ hàng đơn vị đến hàng nghìn!' },
    { grade: 4, num1: 4520, num2: 1785, op: '-', result: 2735, carryText: 'Trừ từng hàng từ phải sang trái, nhớ mượn chuẩn xác!' },
  ],
  5: [
    { grade: 5, num1: 3450, num2: 5870, op: '+', result: 9320, carryText: 'Cộng nhẩm nhanh các số tròn chục và nhớ hàng nghìn!' },
    { grade: 5, num1: 7240, num2: 3890, op: '-', result: 3350, carryText: 'Kiểm tra lại kết quả bằng phép tính cộng ngược lại!' },
  ],
};

export const StudentLandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [selectedGrade, setSelectedGrade] = useState<number>(3);
  const [problemIndex, setProblemIndex] = useState<number>(0);
  const [kidAnswer, setKidAnswer] = useState<string>('');
  const [feedback, setFeedback] = useState<{ status: 'idle' | 'correct' | 'hint'; message: string }>({
    status: 'idle',
    message: '',
  });
  const [stars, setStars] = useState<number>(12);
  const [companionDialog, setCompanionDialog] = useState<{ open: boolean; title: string; message: string } | null>(null);

  useEffect(() => {
    let active = true;
    if (tokenStore.hasTokens()) {
      authService
        .getMe()
        .then((profile) => {
          if (!active) return;
          const role = (profile.role || '').toUpperCase().replace('ROLE_', '');
          if (role !== 'STUDENT') {
            navigate('/access-denied', { replace: true });
          } else {
            setUser(profile);
            if (profile.gradeLevel && profile.gradeLevel >= 1 && profile.gradeLevel <= 5) {
              setSelectedGrade(profile.gradeLevel);
            }
          }
        })
        .catch(() => {
          if (active) {
            tokenStore.clearTokens();
            navigate('/login', { replace: true });
          }
        });
    } else {
      navigate('/login', { replace: true });
    }
    return () => {
      active = false;
    };
  }, [navigate]);

  const currentProblems = GRADE_PROBLEMS[selectedGrade] || GRADE_PROBLEMS[3];
  const problem = currentProblems[problemIndex % currentProblems.length];

  const handleCheckAnswer = () => {
    const val = parseInt(kidAnswer.trim(), 10);
    if (isNaN(val)) {
      setFeedback({ status: 'hint', message: 'Em hãy điền số kết quả vào ô nhé! ⭐' });
      return;
    }

    if (val === problem.result) {
      setFeedback({
        status: 'correct',
        message: 'Hoan hô! Em giải đúng rồi! Bạn Ngôi sao tặng em 1 ngôi sao vàng! ⭐⭐⭐',
      });
      setStars((prev) => prev + 1);
    } else {
      setFeedback({
        status: 'hint',
        message: problem.carryText || 'Bé hãy thử tính lại từng cột từ phải sang trái nhé, nhớ cộng số nhớ nữa nha!',
      });
    }
  };

  const handleNextProblem = () => {
    setKidAnswer('');
    setFeedback({ status: 'idle', message: '' });
    setProblemIndex((prev) => (prev + 1) % currentProblems.length);
  };

  const [listening, setListening] = useState(false);

  const handlePhotoSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCompanionDialog({
        open: true,
        title: 'Đã nhận ảnh bài làm! 🌟',
        message: `Bạn Ngôi sao đã nhận được ảnh "${file.name}"! AI đang rà soát nét chữ ô ly và đối chiếu từng bước tính toán. Em cũng có thể tự luyện thêm các phép tính ở bảng bên dưới nhé!`,
      });
    }
  };

  const handleVoiceStart = () => {
    setListening(true);
    setCompanionDialog({
      open: true,
      title: 'Đang lắng nghe câu hỏi... 🎙️',
      message: 'Em hãy nói to và rõ ràng phép tính cần gợi ý nhé. Ví dụ: "Bạn Ngôi sao ơi, phép tính 245 cộng 178 cộng hàng chục thế nào?"',
    });
    setTimeout(() => setListening(false), 3000);
  };

  const studentName = user?.displayName || 'bạn nhỏ';

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', bgcolor: '#F8FAFC', pb: 8 }}>
      {/* Student Welcome Stage */}
      <Box
        className="hero-mesh"
        sx={{
          pt: { xs: 3, sm: 5 },
          pb: { xs: 5, sm: 6 },
          borderBottom: '1px solid #E2E8F0',
          position: 'relative',
        }}
      >
        <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 2 }}>
            <Button
              component={RouterLink}
              to="/"
              startIcon={<ArrowBackIcon />}
              sx={{ fontWeight: 800, color: '#475569', borderRadius: 2 }}
            >
              Trang chủ
            </Button>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: '#FFFBEB',
                border: '1.5px solid #FDE68A',
                borderRadius: 3,
                px: 2,
                py: 0.75,
                boxShadow: '0 2px 8px rgba(245, 158, 11, 0.15)',
              }}
            >
              <EmojiEventsIcon sx={{ color: '#F59E0B', fontSize: 24 }} />
              <Typography variant="body1" sx={{ fontWeight: 900, color: '#B45309' }}>
                {stars} Ngôi sao tích lũy
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={4} sx={{ alignItems: 'center' }}>
            <Grid size={{ xs: 12, md: 8 }}>
              {/* Mascot Companion Greeting */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box
                  component="img"
                  src="/ui/mathvision-star.png"
                  alt="Mascot Star"
                  className="star-companion-float"
                  sx={{ width: 64, height: 64, objectFit: 'contain' }}
                />
                <Box className="speech-bubble">
                  <Typography variant="body1" sx={{ fontWeight: 800, color: '#0F172A', fontSize: '1rem' }}>
                    Chào <strong>{studentName}</strong>! Hôm nay em muốn chụp bài hay cùng luyện toán ô ly với bạn Ngôi sao? ⭐
                  </Typography>
                </Box>
              </Box>

              <Typography variant="h3" component="h1" sx={{ fontWeight: 900, color: '#0F172A', fontSize: { xs: '1.8rem', sm: '2.4rem' }, mb: 1 }}>
                Bàn học toán của em 🚀
              </Typography>
              <Typography variant="body1" sx={{ color: '#475569', fontSize: '1.05rem', maxWidth: 620 }}>
                Chụp bài tập trên trang vở ô ly để cùng bạn Ngôi sao khám phá từng bước giải, hoặc tự mình luyện tập để tích lũy thật nhiều sao thưởng!
              </Typography>
            </Grid>

            {/* Grade Switcher for Kid */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Box sx={{ p: 2.5, bgcolor: '#FFFFFF', borderRadius: 3.5, border: '1px solid #E2E8F0', boxShadow: '0 4px 14px rgba(15, 23, 42, 0.04)' }}>
                <Typography variant="caption" sx={{ fontWeight: 800, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', mb: 1.5 }}>
                  Chọn khối lớp của em
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {[1, 2, 3, 4, 5].map((g) => (
                    <Button
                      key={g}
                      variant={selectedGrade === g ? 'contained' : 'outlined'}
                      onClick={() => {
                        setSelectedGrade(g);
                        setProblemIndex(0);
                        setKidAnswer('');
                        setFeedback({ status: 'idle', message: '' });
                      }}
                      sx={{
                        flex: 1,
                        minWidth: 54,
                        minHeight: 42,
                        borderRadius: 2.5,
                        fontWeight: 900,
                        fontSize: '0.95rem',
                        bgcolor: selectedGrade === g ? '#2563EB' : '#FFFFFF',
                        borderColor: selectedGrade === g ? '#2563EB' : '#CBD5E1',
                        color: selectedGrade === g ? '#FFFFFF' : '#334155',
                      }}
                    >
                      Lớp {g}
                    </Button>
                  ))}
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Main Student Actions */}
      <Container maxWidth="xl" sx={{ px: { xs: 2.5, sm: 4, md: 6 }, mt: 5 }}>
        <Grid container spacing={3} sx={{ mb: 6 }}>
          {/* Action 1: Camera Primary Featured Target */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card
              sx={{
                p: 3.5,
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '2px solid #2563EB',
                boxShadow: '0 8px 24px -4px rgba(37, 99, 235, 0.16)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '100%',
                position: 'relative',
                transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                '&:hover': { transform: 'translateY(-3px)', boxShadow: '0 12px 30px -4px rgba(37, 99, 235, 0.24)' },
              }}
            >
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ width: 56, height: 56, borderRadius: 3, bgcolor: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#2563EB' }}>
                    <CameraAltIcon sx={{ fontSize: 32 }} />
                  </Box>
                  <Chip
                    label="Đề xuất cho bé ⭐"
                    size="small"
                    sx={{
                      height: 24,
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      bgcolor: '#EFF6FF',
                      color: '#2563EB',
                      border: '1px solid #BFDBFE',
                      borderRadius: 1.5,
                    }}
                  />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 900, mb: 1, color: '#0F172A' }}>
                  Chụp bài tập ô ly 📸
                </Typography>
                <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, mb: 3 }}>
                  Đặt điện thoại ngay ngắn, chụp trang vở bài làm để bạn Ngôi sao hướng dẫn từng bước tính toán.
                </Typography>
              </Box>
              <Button
                component="label"
                variant="contained"
                size="large"
                color="primary"
                sx={{
                  py: 1.4,
                  fontSize: '1rem',
                  fontWeight: 900,
                  borderRadius: 2.5,
                  boxShadow: '0 4px 14px rgba(37, 99, 235, 0.35)',
                  cursor: 'pointer',
                }}
              >
                Mở máy ảnh ngay
                <input
                  type="file"
                  hidden
                  accept="image/*"
                  capture="environment"
                  onChange={handlePhotoSelected}
                />
              </Button>
            </Card>
          </Grid>

          {/* Action 2: Upload Photo */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card
              sx={{
                p: 3.5,
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '1.5px solid #E2E8F0',
                boxShadow: '0 4px 16px rgba(15, 23, 42, 0.04)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '100%',
                transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                '&:hover': { transform: 'translateY(-3px)', borderColor: '#CBD5E1', boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.08)' },
              }}
            >
              <Box>
                <Box sx={{ width: 56, height: 56, borderRadius: 3, bgcolor: '#FFFBEB', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2, color: '#F59E0B' }}>
                  <UploadFileIcon sx={{ fontSize: 32 }} />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 900, color: '#0F172A', mb: 1 }}>
                  Tải ảnh từ máy 🖼️
                </Typography>
                <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, mb: 3 }}>
                  Chọn bức ảnh trang vở đã chụp sẵn trong thư viện ảnh của máy tính bảng hoặc điện thoại.
                </Typography>
              </Box>
              <Button
                component="label"
                variant="outlined"
                size="large"
                sx={{
                  borderColor: '#CBD5E1',
                  color: '#334155',
                  bgcolor: '#FFFFFF',
                  fontWeight: 900,
                  borderRadius: 2.5,
                  py: 1.4,
                  fontSize: '0.95rem',
                  cursor: 'pointer',
                  '&:hover': { bgcolor: '#FFFBEB', borderColor: '#F59E0B', color: '#B45309' },
                }}
              >
                Chọn ảnh bài làm
                <input
                  type="file"
                  hidden
                  accept="image/*"
                  onChange={handlePhotoSelected}
                />
              </Button>
            </Card>
          </Grid>

          {/* Action 3: Voice Prompt */}
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <Card
              sx={{
                p: 3.5,
                borderRadius: 4,
                bgcolor: '#FFFFFF',
                border: '1.5px solid #E2E8F0',
                boxShadow: '0 4px 16px rgba(15, 23, 42, 0.04)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '100%',
                transition: 'all 200ms cubic-bezier(0.16, 1, 0.3, 1)',
                '&:hover': { transform: 'translateY(-3px)', borderColor: '#CBD5E1', boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.08)' },
              }}
            >
              <Box>
                <Box sx={{ width: 56, height: 56, borderRadius: 3, bgcolor: '#ECFDF5', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2, color: '#10B981' }}>
                  <MicIcon sx={{ fontSize: 32 }} />
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 900, color: '#0F172A', mb: 1 }}>
                  Hỏi bằng giọng nói 🎙️
                </Typography>
                <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6, mb: 3 }}>
                  Em có thể nói câu hỏi hoặc phép tính khó, bạn Ngôi sao sẽ lắng nghe và gợi ý cho em.
                </Typography>
              </Box>
              <Button
                variant="outlined"
                size="large"
                onClick={handleVoiceStart}
                sx={{
                  borderColor: listening ? '#10B981' : '#CBD5E1',
                  color: listening ? '#047857' : '#334155',
                  bgcolor: listening ? '#ECFDF5' : '#FFFFFF',
                  fontWeight: 900,
                  borderRadius: 2.5,
                  py: 1.4,
                  fontSize: '0.95rem',
                  '&:hover': { bgcolor: '#ECFDF5', borderColor: '#10B981', color: '#047857' },
                }}
              >
                {listening ? 'Đang lắng nghe... 🎙️' : 'Bắt đầu nói'}
              </Button>
            </Card>
          </Grid>
        </Grid>

        {/* ========================================================================= */}
        {/* INTERACTIVE WORKBOOK ARENA: "BÀN LUYỆN TẬP SỐ HỌC Ô LY" */}
        {/* ========================================================================= */}
        <Box sx={{ mb: 6 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Chip
                label={`LUYỆN TẬP TOÁN LỚP ${selectedGrade}`}
                size="small"
                sx={{ bgcolor: '#EFF6FF', color: '#2563EB', fontWeight: 900, mb: 1, borderRadius: 1.5 }}
              />
              <Typography variant="h4" sx={{ fontWeight: 900, color: '#0F172A' }}>
                Bàn luyện tập số học ô ly ⭐
              </Typography>
              <Typography variant="body2" sx={{ color: '#475569', mt: 0.5 }}>
                Bé tự làm bài trên trang vở ô ly điện tử và kiểm tra từng bước tính cùng Ngôi sao.
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleNextProblem}
              sx={{ borderRadius: 2.5, fontWeight: 800, color: '#334155', borderColor: '#CBD5E1' }}
            >
              Đổi phép tính khác
            </Button>
          </Box>

          <Grid container spacing={4} sx={{ alignItems: 'stretch' }}>
            {/* O Ly Grid Workbook Sheet */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Box
                className="oly-grid-paper"
                sx={{
                  p: { xs: 3, sm: 4 },
                  pl: { xs: 6, sm: 7 },
                  borderRadius: 4,
                  border: '1.5px solid #CBD5E1',
                  bgcolor: '#FFFFFF',
                  boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.06)',
                  minHeight: 280,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}
              >
                <Box sx={{ maxWidth: 260, mx: 'auto', py: 2 }}>
                  {/* First Addend */}
                  <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: '36px 1fr',
                    textAlign: 'right',
                    fontSize: '2.5rem',
                    fontWeight: 900,
                    fontFamily: '"Nunito", "Plus Jakarta Sans", sans-serif',
                    fontVariantNumeric: 'tabular-nums',
                    color: '#0F172A',
                    letterSpacing: '0.15em',
                  }}>
                    <Box />
                    <Box>{problem.num1}</Box>
                  </Box>

                  {/* Operator & Second Addend */}
                  <Box sx={{
                    display: 'grid',
                    gridTemplateColumns: '36px 1fr',
                    textAlign: 'right',
                    fontSize: '2.5rem',
                    fontWeight: 900,
                    fontFamily: '"Nunito", "Plus Jakarta Sans", sans-serif',
                    fontVariantNumeric: 'tabular-nums',
                    color: '#0F172A',
                    letterSpacing: '0.15em',
                  }}>
                    <Box sx={{ color: '#2563EB', textAlign: 'left' }}>{problem.op}</Box>
                    <Box>{problem.num2}</Box>
                  </Box>

                  {/* Horizontal Bar */}
                  <Box sx={{ height: 3.5, bgcolor: '#0F172A', my: 1, borderRadius: 1 }} />

                  {/* Result Input Field */}
                  <Box sx={{ pt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                    <TextField
                      value={kidAnswer}
                      onChange={(e) => setKidAnswer(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleCheckAnswer();
                        }
                      }}
                      placeholder="Đáp số"
                      type="number"
                      autoFocus
                      aria-label="Nhập kết quả đáp số"
                      slotProps={{
                        htmlInput: {
                          'aria-label': 'Nhập kết quả đáp số',
                          inputMode: 'numeric',
                          style: {
                            textAlign: 'right',
                            fontSize: '1.8rem',
                            fontWeight: 900,
                            letterSpacing: '0.1em',
                            padding: '8px 14px',
                            color: '#0F172A',
                            fontFamily: '"Nunito", "Plus Jakarta Sans", sans-serif',
                            fontVariantNumeric: 'tabular-nums',
                          },
                        },
                      }}
                      sx={{
                        width: 170,
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2.5,
                          bgcolor: '#FFFFFF',
                          borderColor: '#2563EB',
                          boxShadow: '0 2px 8px rgba(37, 99, 235, 0.12)',
                          '&:hover': {
                            borderColor: '#1D4ED8',
                          },
                        },
                      }}
                    />
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Socratic Assistant Companion Feedback */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card
                sx={{
                  p: { xs: 3, sm: 4 },
                  borderRadius: 4,
                  border: '1.5px solid #E2E8F0',
                  bgcolor: '#FFFFFF',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  boxShadow: '0 8px 24px -4px rgba(15, 23, 42, 0.04)',
                }}
              >
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.5 }}>
                    <Box
                      component="img"
                      src="/ui/mathvision-star.png"
                      alt="Star mascot"
                      className="star-companion-float"
                      sx={{ width: 44, height: 44, objectFit: 'contain' }}
                    />
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 900, color: '#0F172A' }}>
                        Bạn Ngôi sao đồng hành
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        Trợ lý Socratic luôn sẵn sàng cổ vũ em
                      </Typography>
                    </Box>
                  </Box>

                  {/* Feedback or Prompt Message with Screen Reader Announcement */}
                  <Box aria-live="polite" id="socratic-feedback-region">
                    {feedback.status === 'correct' ? (
                      <Box sx={{ p: 2.5, borderRadius: 3, bgcolor: '#ECFDF5', border: '1.5px solid #A7F3D0', mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#047857', mb: 0.5 }}>
                          <CheckCircleIcon />
                          <Typography variant="subtitle1" sx={{ fontWeight: 900 }}>
                            Chính xác tuyệt vời!
                          </Typography>
                        </Box>
                        <Typography variant="body2" sx={{ color: '#065F46', lineHeight: 1.6 }}>
                          {feedback.message}
                        </Typography>
                      </Box>
                    ) : feedback.status === 'hint' ? (
                      <Box sx={{ p: 2.5, borderRadius: 3, bgcolor: '#FFFBEB', border: '1.5px solid #FDE68A', mb: 3 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 900, color: '#B45309', mb: 0.5 }}>
                          💡 Gợi ý nhỏ cho bé:
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#92400E', lineHeight: 1.6 }}>
                          {feedback.message}
                        </Typography>
                      </Box>
                    ) : (
                      <Box sx={{ p: 2.5, borderRadius: 3, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', mb: 3 }}>
                        <Typography variant="body2" sx={{ color: '#475569', lineHeight: 1.6 }}>
                          Bé hãy nhẩm tính từng hàng từ phải sang trái (đơn vị rồi đến hàng chục), sau đó điền kết quả vào ô trên trang vở nhé!
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    size="large"
                    color="primary"
                    startIcon={<SparklesIcon />}
                    onClick={handleCheckAnswer}
                    sx={{
                      flex: 1,
                      minHeight: 48,
                      borderRadius: 3,
                      fontWeight: 900,
                      fontSize: '1rem',
                      boxShadow: '0 6px 18px rgba(37, 99, 235, 0.35)',
                    }}
                  >
                    Kiểm tra cùng Ngôi sao ⭐
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={handleNextProblem}
                    sx={{
                      borderRadius: 3,
                      fontWeight: 800,
                      px: 3,
                      borderColor: '#CBD5E1',
                      color: '#475569',
                    }}
                  >
                    Bài tiếp theo ➔
                  </Button>
                </Box>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* ========================================================================= */}
        {/* STUDENT PROGRESS & BADGES: "GÓC THÀNH TÍCH CỦA EM" */}
        {/* ========================================================================= */}
        <Box sx={{ p: { xs: 3, sm: 4 }, bgcolor: '#FFFFFF', borderRadius: 4, border: '1.5px solid #E2E8F0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 2 }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 900, color: '#0F172A' }}>
                Huy hiệu & Thành tích của em 🏆
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
                Mỗi bài tập hoàn thành là một bước tiến bộ vững chắc của bé.
              </Typography>
            </Box>
            <Chip
              label="Học sinh chăm chỉ"
              size="small"
              sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 800, border: '1px solid #A7F3D0' }}
            />
          </Box>

          <Grid container spacing={2.5}>
            {[
              {
                title: 'Chiến binh Ô ly',
                desc: 'Đã hoàn thành 10 bài toán đặt tính chuẩn hàng',
                icon: '✏️',
                bg: '#EFF6FF',
                border: '#BFDBFE',
              },
              {
                title: 'Bậc thầy Số nhớ',
                desc: 'Nhớ số chuẩn xác không sai cột hàng chục',
                icon: '🎯',
                bg: '#ECFDF5',
                border: '#A7F3D0',
              },
              {
                title: 'Ngôi sao Tự giác',
                desc: 'Tự suy luận tìm ra lời giải mà không cần giải hộ',
                icon: '⭐',
                bg: '#FFFBEB',
                border: '#FDE68A',
              },
              {
                title: 'Nhà thám hiểm Toán học',
                desc: 'Khám phá tất cả các dạng phép tính Lớp 3',
                icon: '🚀',
                bg: '#FFF1F2',
                border: '#FECDD3',
              },
            ].map((badge) => (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={badge.title}>
                <Box
                  sx={{
                    p: 2.5,
                    borderRadius: 3,
                    bgcolor: badge.bg,
                    border: `1.5px solid ${badge.border}`,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Typography sx={{ fontSize: '2rem', mb: 1 }}>{badge.icon}</Typography>
                    <Typography variant="subtitle1" sx={{ fontWeight: 900, color: '#0F172A', mb: 0.5 }}>
                      {badge.title}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#475569', lineHeight: 1.5, display: 'block' }}>
                      {badge.desc}
                    </Typography>
                  </Box>
                  <Chip
                    label="Đã mở khóa"
                    size="small"
                    sx={{ width: 'fit-content', mt: 2, height: 20, fontSize: '0.68rem', fontWeight: 800, bgcolor: '#FFFFFF', color: '#0F172A' }}
                  />
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>
      {/* Kid-Friendly Companion Mascot Dialog */}
      <Dialog
        open={Boolean(companionDialog?.open)}
        onClose={() => setCompanionDialog(null)}
        maxWidth="xs"
        fullWidth
        aria-labelledby="companion-dialog-title"
        aria-describedby="companion-dialog-description"
        slotProps={{
          paper: {
            sx: {
              borderRadius: 4,
              p: 2,
              textAlign: 'center',
              boxShadow: '0 20px 48px -8px rgba(15, 23, 42, 0.16)',
            },
          },
        }}
      >
        <DialogContent sx={{ pt: 2, pb: 1 }}>
          <Box
            component="img"
            src="/ui/mathvision-star.png"
            alt="Ngôi sao MathVision"
            className="star-companion-float"
            sx={{ width: 80, height: 80, mx: 'auto', mb: 2, objectFit: 'contain' }}
          />
          <Typography id="companion-dialog-title" variant="h5" sx={{ fontWeight: 900, color: '#0F172A', mb: 1 }}>
            {companionDialog?.title}
          </Typography>
          <Typography id="companion-dialog-description" variant="body1" sx={{ color: '#475569', lineHeight: 1.6, fontSize: '0.98rem' }}>
            {companionDialog?.message}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 2 }}>
          <Button
            variant="contained"
            onClick={() => setCompanionDialog(null)}
            sx={{
              borderRadius: 3,
              px: 4,
              py: 1.2,
              fontWeight: 900,
              bgcolor: '#2563EB',
              fontSize: '1rem',
              '&:hover': { bgcolor: '#1D4ED8' },
            }}
          >
            Em đã hiểu rồi ⭐
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentLandingPage;
