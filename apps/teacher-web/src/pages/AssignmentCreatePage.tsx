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
import { ArrowBack } from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { newCreationRequestId } from '../services/api/newCreationRequestId';
import { useAuth } from '../components/layout/AuthContext';
import type { Class } from '../types';
import { MathType } from '../types';

export default function AssignmentCreatePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const requestedClass = params.get('classId');
  const { user } = useAuth();
  const storageKey = user?.userId ? `teacher:assignment-create:${user.userId}` : undefined;
  const submitLock = useRef(false);
  const pending = useRef(new Map<string, string>());
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [title, setTitle] = useState('');
  const [mathType, setMathType] = useState<MathType>(MathType.VERTICAL_ADDITION);
  const [maxScore, setMaxScore] = useState<string>("10");
  const [classLoad, setClassLoad] = useState<{ requestedClass: string | null; failed: boolean }>();
  const loadingClasses = !classLoad || classLoad.requestedClass !== requestedClass;
  const classLoadFailed = !loadingClasses && classLoad.failed;
  const unavailableClass = !loadingClasses && !classLoadFailed && requestedClass
    && !classes.some(c => (c.id || c.classId) === requestedClass);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    AppTeacherService.getClasses()
      .then((data) => {
        if (isMounted) {
          setClasses(data);
          const chosen = requestedClass ? data.find(c => (c.id || c.classId) === requestedClass) : data[0];
          setSelectedClass(chosen?.id || chosen?.classId || '');
          setClassLoad({ requestedClass, failed: false });
        }
      })
      .catch(() => {
        if (isMounted) {
          setClasses([]);
          setSelectedClass('');
          setClassLoad({ requestedClass, failed: true });
        }
      });

    return () => {
      isMounted = false;
    };
  }, [requestedClass]);

  const handleCreate = async () => {
    if (loadingClasses || classLoadFailed) return;
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
      const payload = JSON.stringify([selectedClass, title.trim(), mathType, parsedScore]);
      const key = `${storageKey ?? 'memory'}:${payload}`;
      let id = pending.current.get(key);
      if (storageKey) {
        try { id ??= window.sessionStorage.getItem(key) ?? undefined; } catch { /* in-memory retry */ }
      }
      id ??= newCreationRequestId();
      pending.current.set(key, id);
      if (storageKey) {
        try { window.sessionStorage.setItem(key, id); } catch { /* in-memory retry */ }
      }
      const assignment = await AppTeacherService.createAssignment(selectedClass, title.trim(), mathType, parsedScore, id);
      pending.current.delete(key);
      if (storageKey) {
        try { window.sessionStorage.removeItem(key); } catch { /* storage unavailable */ }
      }
      navigate(`/batches/create?assignmentId=${encodeURIComponent(assignment.assignmentId || assignment.id || '')}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Không thể tạo bài tập. Vui lòng thử lại.');
    } finally {
      submitLock.current = false;
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1040 }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/assignments')}
        sx={{ mb: 2 }}
      >
        Quay lại danh sách bài tập
      </Button>

      <Typography variant="h5" component="h1" sx={{ fontWeight: 800, mb: 0.5 }}>
        Tạo bài tập mới
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Chọn lớp, đặt tên bài tập và chọn cách chấm.
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: 'minmax(0, 2fr) minmax(0, 1fr)' },
        gap: 2, alignItems: 'start' }}>
        <Card variant="outlined">
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
                {error}
              </Alert>
            )}
            {classLoadFailed && (
              <Alert severity="error" sx={{ mb: 3 }}>
                Chưa tải được lớp học. Hãy quay lại danh sách lớp rồi thử lại.
              </Alert>
            )}
            {!loadingClasses && !classLoadFailed && classes.length === 0 && (
              <Alert severity="info" sx={{ mb: 3 }}>Cần có lớp được phân công trước khi tạo bài tập.</Alert>
            )}
            {unavailableClass && !selectedClass && (
              <Alert severity="warning" sx={{ mb: 3 }}>
                Lớp trong liên kết không còn khả dụng. Hãy chọn lớp phụ trách.
              </Alert>
            )}

            <Box component="form" aria-label="Thông tin bài tập" noValidate onSubmit={(event) => {
              event.preventDefault();
              void handleCreate();
            }}>
              <TextField
                select
                fullWidth
                label="Lớp học áp dụng"
                value={selectedClass}
                onChange={(e) => setSelectedClass(e.target.value)}
                disabled={loadingClasses || submitting}
                helperText={loadingClasses ? 'Đang tải lớp học…' : 'Chọn lớp học trong danh sách phụ trách'}
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
                label="Dạng phép tính"
                value={mathType}
                onChange={(e) => setMathType(e.target.value as MathType)}
                disabled={submitting}
                helperText="Đặt tính dọc với hai số hạng, mỗi số dài từ 1 đến 6 chữ số."
                sx={{ mb: 3 }}
              >
                <MenuItem value={MathType.VERTICAL_ADDITION}>
                  Phép cộng đặt tính dọc
                </MenuItem>
                <MenuItem value={MathType.VERTICAL_SUBTRACTION}>
                  Phép trừ đặt tính dọc
                </MenuItem>
              </TextField>

              <Divider sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'flex-end', gap: 1 }}>
                <Button
                  type="button"
                  variant="outlined"
                  color="inherit"
                  onClick={() => navigate('/assignments')}
                  disabled={submitting}
                >
                  Hủy
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  type="submit"
                  disabled={loadingClasses || !selectedClass || !title.trim() || submitting}
                  startIcon={submitting ? <CircularProgress size={20} color="inherit" /> : null}
                  aria-busy={submitting}
                  sx={{ py: 1.25 }}
                >
                  {submitting ? 'Đang tạo bài tập...' : 'Tạo bài tập & Thu thập ảnh'}
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
        <Card component="aside" variant="outlined" sx={{ bgcolor: 'primary.light', p: { xs: 2, sm: 3 } }}>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>Chuẩn bị ảnh bài làm</Typography>
          <Box component="ul" sx={{ m: 0, pl: 2.5, color: 'text.secondary', '& li + li': { mt: 1 } }}>
            <li>Nhắc học sinh viết rõ nét và đặt các chữ số thẳng cột.</li>
            <li>Chụp đủ sáng, giữ máy thẳng và lấy trọn một bài làm trong mỗi ảnh.</li>
          </Box>
        </Card>
      </Box>
    </Box>
  );
}
