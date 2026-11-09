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
} from '@mui/material';
import { ArrowBack, CheckCircleOutlined } from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Class } from '../types';
import { MathType } from '../types';

export default function AssignmentCreatePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const requestedClass = params.get('classId');
  const submitLock = useRef(false);
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [title, setTitle] = useState('');
  const [mathType, setMathType] = useState<MathType>(MathType.VERTICAL_ADDITION);
  const [maxScore, setMaxScore] = useState<string>("10");
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
            const chosen = data.find(c => (c.id || c.classId) === requestedClass) || data[0];
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

  return (
    <Box sx={{ maxWidth: 640, mx: 'auto', mt: 2 }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/assignments')}
        sx={{ mb: 2 }}
      >
        Quay lại danh sách bài tập
      </Button>

      <Card sx={{ borderRadius: 2.5, border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          <Typography variant="h5" component="h1" sx={{ fontWeight: 800, mb: 0.5 }}>
            Tạo bài tập mới
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Thiết lập bài tập toán đặt tính (cộng hoặc trừ) dành cho học sinh tiểu học.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
              {error}
            </Alert>
          )}

          <Box component="form" noValidate>
            <TextField
              select
              fullWidth
              label="Lớp học áp dụng"
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
              disabled={loadingClasses || submitting}
              helperText="Chọn lớp học trong danh sách phụ trách"
              sx={{ mb: 3 }}
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
              placeholder="Ví dụ: Phép cộng có nhớ trong phạm vi 1000"
              disabled={submitting}
              helperText="Nên ghi rõ dạng bài để dễ nhận diện trong sổ điểm"
              sx={{ mb: 3 }}
            />

            <TextField
              fullWidth
              type="number"
              label="Thang điểm tối đa"
              value={maxScore}
              onChange={(e) => setMaxScore(e.target.value)}
              slotProps={{ htmlInput: { min: 1, max: 100, step: 1 } }}
              disabled={submitting}
              helperText="Thang điểm chuẩn dành cho bài tập (từ 1 đến 100 điểm, mặc định là 10)"
              sx={{ mb: 3 }}
            />

            <TextField
              select
              fullWidth
              label="Dạng phép tính (Phạm vi hỗ trợ MVP)"
              value={mathType}
              onChange={(e) => setMathType(e.target.value as MathType)}
              disabled={submitting}
              helperText="Hệ thống hiện tại hỗ trợ tối ưu phép toán đặt dọc 2 số hạng (1–6 chữ số)"
              sx={{ mb: 3.5 }}
            >
              <MenuItem value={MathType.VERTICAL_ADDITION}>
                Phép cộng đặt tính dọc (Vertical Addition)
              </MenuItem>
              <MenuItem value={MathType.VERTICAL_SUBTRACTION}>
                Phép trừ đặt tính dọc (Vertical Subtraction)
              </MenuItem>
            </TextField>

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
                  Lưu ý khi thu thập bài làm của học sinh
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#047857', display: 'block' }}>
                • Học sinh viết rõ nét, đặt tính thẳng cột dọc (hàng đơn vị, chục, trăm).
              </Typography>
              <Typography variant="caption" sx={{ color: '#047857', display: 'block' }}>
                • Chụp ảnh đủ sáng, góc chụp thẳng, mỗi ảnh tương ứng một bài làm.
              </Typography>
            </Box>

            <Divider sx={{ mb: 3 }} />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                color="inherit"
                onClick={() => navigate('/assignments')}
                disabled={submitting}
                sx={{ flex: 1 }}
              >
                Hủy
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleCreate}
                disabled={!selectedClass || !title.trim() || submitting}
                startIcon={submitting ? <CircularProgress size={20} color="inherit" /> : null}
                sx={{ flex: 2, py: 1.25 }}
              >
                {submitting ? 'Đang tạo bài tập...' : 'Tạo bài tập & Thu thập ảnh'}
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
