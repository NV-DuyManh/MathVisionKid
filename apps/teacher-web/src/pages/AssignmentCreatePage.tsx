import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  MenuItem,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Divider,
  Grid,
  Chip,
  Paper,
  Stack,
} from '@mui/material';
import {
  ArrowBack,
  CheckCircleOutlined,
  AutoAwesome,
  AccessTime,
  FormatListNumbered,
  Preview,
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Class } from '../types';
import { MathType } from '../types';

interface PresetTemplate {
  id: string;
  badge: string;
  title: string;
  mathType: MathType;
  maxScore: string;
  gradeLevel: string;
  problems: string[];
  description: string;
}

const PRESET_TEMPLATES: PresetTemplate[] = [
  {
    id: 'fractions_compare',
    badge: 'Toán Lớp 4 • Đề kiểm tra',
    title: 'So sánh phân số cùng mẫu, khác mẫu và so sánh với 1',
    mathType: MathType.VERTICAL_ADDITION,
    maxScore: '10',
    gradeLevel: 'Lớp 4',
    problems: [
      'Câu 1: Điền dấu >, <, = : a) 2/3 ... 8/15  |  b) 9/8 ... 9/7  |  c) 7/6 ... 14/12',
      'Câu 2: Tìm số thích hợp: 4/9 < .../9 < 5/8',
      'Câu 3: Sắp xếp các phân số từ bé đến lớn: 2025/2024 ; 4/5 ; 23/22 ; 1000/1001 ; 6/5 ; 12/12',
    ],
    description: 'Bộ đề rèn kỹ năng quy đồng mẫu số, so sánh với 1 và sắp xếp thứ tự phân số.',
  },
  {
    id: 'vertical_addition_carry',
    badge: 'Toán Lớp 3 • Có nhớ',
    title: 'Phép cộng đặt tính dọc có nhớ trong phạm vi 1000',
    mathType: MathType.VERTICAL_ADDITION,
    maxScore: '10',
    gradeLevel: 'Lớp 3',
    problems: [
      'Câu 1: Đặt tính rồi tính: 458 + 276',
      'Câu 2: Đặt tính rồi tính: 689 + 145',
      'Câu 3: Đặt tính rồi tính: 327 + 498',
      'Câu 4: Tính nhẩm và điền kết quả: 500 + 400 = ...',
    ],
    description: 'Kiểm tra kỹ năng đặt tính thẳng hàng dọc và nhớ 1 sang hàng chục, hàng trăm.',
  },
  {
    id: 'vertical_subtraction_borrow',
    badge: 'Toán Lớp 3 • Có mượn',
    title: 'Phép trừ đặt tính dọc có mượn trong phạm vi 1000',
    mathType: MathType.VERTICAL_SUBTRACTION,
    maxScore: '10',
    gradeLevel: 'Lớp 3',
    problems: [
      'Câu 1: Đặt tính rồi tính: 724 - 458',
      'Câu 2: Đặt tính rồi tính: 500 - 238',
      'Câu 3: Đặt tính rồi tính: 813 - 475',
      'Câu 4: Tìm X biết: X + 238 = 500',
    ],
    description: 'Rèn luyện kỹ năng mượn số liên tiếp qua hàng chục và hàng trăm khi thực hiện phép trừ.',
  },
  {
    id: 'general_review',
    badge: 'Toán Lớp 2-3 • Tổng hợp',
    title: 'Ôn tập tổng hợp đặt tính và giải toán có lời văn',
    mathType: MathType.VERTICAL_ADDITION,
    maxScore: '10',
    gradeLevel: 'Lớp 3',
    problems: [
      'Câu 1: Đặt tính rồi tính: 356 + 248 và 671 - 294',
      'Câu 2: Tìm X biết: X - 145 = 328',
      'Câu 3: Một trường tiểu học có 458 bạn nam và 427 bạn nữ. Hỏi trường có tất cả bao nhiêu học sinh?',
    ],
    description: 'Bộ câu hỏi kiểm tra toàn diện cả kỹ năng tính toán lẫn tư duy toán đố.',
  },
];

export default function AssignmentCreatePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const requestedClass = params.get('classId');
  const submitLock = useRef(false);

  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [title, setTitle] = useState('');
  const [mathType, setMathType] = useState<MathType>(MathType.VERTICAL_ADDITION);
  const [maxScore, setMaxScore] = useState<string>('10');
  const [deadline, setDeadline] = useState('23:59 ngày mai');
  const [maxAttempts, setMaxAttempts] = useState('1');
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [activeProblems, setActiveProblems] = useState<string[]>([]);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    AppTeacherService.getClasses()
      .then((data) => {
        if (isMounted) {
          setClasses(data);
          if (data.length > 0) {
            const chosen = data.find((c) => (c.id || c.classId) === requestedClass) || data[0];
            setSelectedClass(chosen.id || chosen.classId || '');
          }
          setLoadingClasses(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setError('Chưa tải được lớp học. Hãy quay lại danh sách lớp rồi thử lại.');
          setLoadingClasses(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [requestedClass]);

  const handleSelectPreset = (preset: PresetTemplate) => {
    setSelectedPresetId(preset.id);
    setTitle(preset.title);
    setMathType(preset.mathType);
    setMaxScore(preset.maxScore);
    setActiveProblems(preset.problems);
  };

  const handleCreate = async () => {
    if (!selectedClass || !title.trim()) {
      setError('Vui lòng chọn lớp học và nhập tiêu đề bài tập.');
      return;
    }
    const trimmedScore = maxScore.trim();
    if (!trimmedScore) {
      setError('Vui lòng nhập thang điểm tối đa.');
      return;
    }
    if (!/^\d+$/.test(trimmedScore)) {
      setError('Thang điểm tối đa phải là số nguyên (không chứa số thập phân hoặc ký tự đặc biệt).');
      return;
    }
    const parsedScore = Number(trimmedScore);
    if (!Number.isSafeInteger(parsedScore) || parsedScore < 1 || parsedScore > 100) {
      setError('Thang điểm tối đa phải là số nguyên từ 1 đến 100.');
      return;
    }

    if (submitLock.current) return;
    submitLock.current = true;
    try {
      setSubmitting(true);
      setError(null);
      const assignment = await AppTeacherService.createAssignment(selectedClass, title.trim(), mathType, parsedScore);
      navigate(`/batches/create?assignmentId=${encodeURIComponent(assignment.assignmentId || assignment.id || '')}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Không thể tạo bài tập. Vui lòng thử lại.');
    } finally {
      submitLock.current = false;
      setSubmitting(false);
    }
  };

  const selectedClassObj = classes.find((c) => (c.id || c.classId) === selectedClass);

  return (
    <Box sx={{ maxWidth: 1120, mx: 'auto', mt: 2, pb: 6 }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/assignments')}
        sx={{ mb: 2, fontWeight: 600 }}
      >
        Quay lại danh sách bài tập
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
          Tạo bài tập mới cho học sinh
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Chọn bộ đề bài mẫu chuẩn sách giáo khoa hoặc tự thiết lập bài tập toán ô ly cho cả lớp.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {error}
        </Alert>
      )}

      {/* Section 1: AI & SGK Problem Presets */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AutoAwesome sx={{ color: '#059669', fontSize: 22 }} />
          <Typography variant="h6" sx={{ fontWeight: 800, color: '#065F46' }}>
            Ngân hàng đề bài mẫu (Tự động điền 1-click)
          </Typography>
        </Box>

        <Grid container spacing={2}>
          {PRESET_TEMPLATES.map((preset) => {
            const isSelected = selectedPresetId === preset.id;
            return (
              <Grid size={{ xs: 12, sm: 6, md: 3 }} key={preset.id}>
                <Paper
                  variant="outlined"
                  onClick={() => handleSelectPreset(preset)}
                  sx={{
                    p: 2,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    borderRadius: 2.5,
                    borderWidth: isSelected ? 2 : 1,
                    borderColor: isSelected ? '#059669' : '#E2E8F0',
                    bgcolor: isSelected ? '#ECFDF5' : '#FFFFFF',
                    transition: 'all 160ms ease-in-out',
                    '&:hover': {
                      borderColor: '#059669',
                      boxShadow: '0 4px 12px rgba(5,150,105,0.1)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  <Box>
                    <Chip
                      label={preset.badge}
                      size="small"
                      sx={{
                        bgcolor: isSelected ? '#059669' : '#F1F5F9',
                        color: isSelected ? '#FFFFFF' : '#475569',
                        fontWeight: 700,
                        fontSize: '0.7rem',
                        mb: 1.5,
                      }}
                    />
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A', mb: 1, lineHeight: 1.3 }}>
                      {preset.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5, lineHeight: 1.4 }}>
                      {preset.description}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', pt: 1, borderTop: '1px solid #E2E8F0' }}>
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#059669' }}>
                      {isSelected ? '✓ Đang chọn' : 'Chọn mẫu này'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Thang {preset.maxScore}đ
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      {/* Section 2: Form & Live Preview */}
      <Grid container spacing={3.5}>
        {/* Left Column: Assignment Configuration Form */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card sx={{ borderRadius: 2.5, border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
            <CardContent sx={{ p: { xs: 2.5, sm: 3.5 } }}>
              <Typography variant="h6" sx={{ fontWeight: 800, mb: 2.5, color: '#0F172A' }}>
                Thông tin bài tập
              </Typography>

              <Box component="form" noValidate>
                <TextField
                  select
                  fullWidth
                  label="Lớp học áp dụng"
                  value={selectedClass}
                  onChange={(e) => setSelectedClass(e.target.value)}
                  disabled={loadingClasses || submitting}
                  helperText="Chọn lớp học trong danh sách phụ trách giảng dạy"
                  sx={{ mb: 2.5 }}
                >
                  {classes.map((c) => (
                    <MenuItem key={c.id || c.classId} value={c.id || c.classId}>
                      {c.name.startsWith('Lớp ') ? c.name : `Lớp ${c.name}`} ({c.studentCount} học sinh)
                    </MenuItem>
                  ))}
                </TextField>

                <TextField
                  fullWidth
                  label="Tên bài tập"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: So sánh phân số hoặc Phép cộng có nhớ phạm vi 1000"
                  disabled={submitting}
                  helperText="Nên ghi rõ dạng bài để dễ nhận diện trong sổ điểm"
                  sx={{ mb: 2.5 }}
                />

                <Grid container spacing={2} sx={{ mb: 2.5 }}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Thang điểm tối đa"
                      value={maxScore}
                      onChange={(e) => setMaxScore(e.target.value)}
                      slotProps={{ htmlInput: { min: 1, max: 100, step: 1 } }}
                      disabled={submitting}
                      helperText="Thang điểm chuẩn (1–100đ, mặc định 10)"
                    />
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      select
                      fullWidth
                      label="Dạng phép tính chính"
                      value={mathType}
                      onChange={(e) => setMathType(e.target.value as MathType)}
                      disabled={submitting}
                      helperText="Hệ thống hỗ trợ đặt tính ô ly và phân số"
                    >
                      <MenuItem value={MathType.VERTICAL_ADDITION}>Phép cộng đặt tính dọc (Vertical Addition)</MenuItem>
                      <MenuItem value={MathType.VERTICAL_SUBTRACTION}>Phép trừ đặt tính dọc (Vertical Subtraction)</MenuItem>
                    </TextField>
                  </Grid>
                </Grid>

                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      select
                      fullWidth
                      label="Hạn chót nộp bài (Deadline)"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      disabled={submitting}
                      helperText="Thời gian đóng cổng nộp bài"
                    >
                      <MenuItem value="23:59 hôm nay">23:59 hôm nay</MenuItem>
                      <MenuItem value="23:59 ngày mai">23:59 ngày mai (Khuyên dùng)</MenuItem>
                      <MenuItem value="Sau 3 ngày">Sau 3 ngày</MenuItem>
                      <MenuItem value="Sau 1 tuần">Sau 1 tuần</MenuItem>
                      <MenuItem value="Không giới hạn">Không giới hạn</MenuItem>
                    </TextField>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <TextField
                      select
                      fullWidth
                      label="Số lần nộp tối đa"
                      value={maxAttempts}
                      onChange={(e) => setMaxAttempts(e.target.value)}
                      disabled={submitting}
                      helperText="Cho phép học sinh nộp lại bao nhiêu lần"
                    >
                      <MenuItem value="1">1 lần duy nhất</MenuItem>
                      <MenuItem value="2">Tối đa 2 lần</MenuItem>
                      <MenuItem value="unlimited">Không giới hạn (Luyện tập tự do)</MenuItem>
                    </TextField>
                  </Grid>
                </Grid>

                <Box
                  sx={{
                    p: 2,
                    bgcolor: '#ECFDF5',
                    borderRadius: 2,
                    border: '1px solid #A7F3D0',
                    mb: 3.5,
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <CheckCircleOutlined sx={{ fontSize: 18, color: '#059669' }} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#065F46' }}>
                      Lưu ý sư phạm khi thu thập bài làm của học sinh
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ color: '#047857', display: 'block' }}>
                    • Học sinh viết rõ nét vào vở ô ly, đặt tính thẳng hàng (hàng đơn vị, hàng chục, hàng trăm).
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#047857', display: 'block' }}>
                    • Chụp ảnh đủ sáng, góc chụp thẳng, mỗi ảnh tương ứng một trang bài làm hoàn chỉnh.
                  </Typography>
                </Box>

                <Divider sx={{ mb: 3 }} />

                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="outlined"
                    color="inherit"
                    onClick={() => navigate('/assignments')}
                    disabled={submitting}
                    sx={{ flex: 1, py: 1.25 }}
                  >
                    Hủy
                  </Button>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleCreate}
                    disabled={!selectedClass || !title.trim() || submitting}
                    startIcon={submitting ? <CircularProgress size={20} color="inherit" /> : null}
                    sx={{
                      flex: 2,
                      py: 1.25,
                      fontWeight: 700,
                      bgcolor: '#059669',
                      '&:hover': { bgcolor: '#047857' },
                    }}
                  >
                    {submitting ? 'Đang tạo bài tập...' : 'Tạo bài tập & Thu thập ảnh'}
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column: Live Student View Preview */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card
            variant="outlined"
            sx={{
              position: 'sticky',
              top: 24,
              borderRadius: 3,
              borderColor: '#CBD5E1',
              bgcolor: '#F8FAFC',
              boxShadow: '0 4px 16px rgba(15,23,42,0.06)',
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Preview sx={{ color: '#2563EB', fontSize: 20 }} />
                  <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#1E40AF', letterSpacing: '0.04em' }}>
                    XEM TRƯỚC (GIAO DIỆN HỌC SINH)
                  </Typography>
                </Box>
                <Chip label="Bản xem trước" size="small" sx={{ bgcolor: '#EFF6FF', color: '#1D4ED8', fontWeight: 600 }} />
              </Box>

              <Paper sx={{ p: 2.5, borderRadius: 2, bgcolor: '#FFFFFF', border: '1px solid #E2E8F0', mb: 2.5 }}>
                <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A', mb: 1 }}>
                  {title || 'Chưa nhập tiêu đề bài tập'}
                </Typography>

                <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 0.5 }}>
                  <Chip
                    label={selectedClassObj ? selectedClassObj.name : 'Chưa chọn lớp'}
                    size="small"
                    sx={{ bgcolor: '#ECFDF5', color: '#059669', fontWeight: 700 }}
                  />
                  <Chip
                    icon={<AccessTime sx={{ fontSize: 14 }} />}
                    label={`Hạn: ${deadline}`}
                    size="small"
                    variant="outlined"
                    sx={{ borderColor: '#CBD5E1', color: '#475569' }}
                  />
                  <Chip
                    label={`Thang ${maxScore || 10}đ`}
                    size="small"
                    variant="outlined"
                    sx={{ borderColor: '#CBD5E1', color: '#475569' }}
                  />
                </Stack>

                <Divider sx={{ my: 1.5 }} />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <FormatListNumbered sx={{ fontSize: 18, color: '#64748B' }} />
                  <Typography variant="caption" sx={{ fontWeight: 800, color: '#475569' }}>
                    DANH SÁCH BÀI TOÁN THỰC HÀNH:
                  </Typography>
                </Box>

                {activeProblems.length > 0 ? (
                  <Stack spacing={1}>
                    {activeProblems.map((p, idx) => (
                      <Box
                        key={idx}
                        sx={{
                          p: 1.25,
                          bgcolor: '#F8FAFC',
                          borderRadius: 1.5,
                          border: '1px solid #E2E8F0',
                          fontFamily: 'monospace',
                          fontSize: '0.82rem',
                          color: '#0F172A',
                          lineHeight: 1.4,
                        }}
                      >
                        {p}
                      </Box>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', py: 2 }}>
                    Chọn một mẫu đề từ Ngân hàng đề bài ở trên để xem danh sách câu hỏi chi tiết.
                  </Typography>
                )}
              </Paper>

              <Box sx={{ p: 2, bgcolor: '#FEF3C7', borderRadius: 2, border: '1px solid #FCD34D' }}>
                <Typography variant="caption" sx={{ color: '#92400E', fontWeight: 700, display: 'block', mb: 0.5 }}>
                  💡 Hướng dẫn học sinh nộp bài:
                </Typography>
                <Typography variant="caption" sx={{ color: '#78350F', display: 'block' }}>
                  Học sinh dùng điện thoại hoặc máy tính bảng tải ảnh vở ô ly lên hệ thống. AI MathVision Kids sẽ tự động nhận diện chữ viết tay và gửi về đợt chấm của thầy cô.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
