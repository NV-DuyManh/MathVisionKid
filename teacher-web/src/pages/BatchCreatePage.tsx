import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Chip,
  Paper,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload,
  Close,
  PrivacyTip,
  CheckCircle,
  Refresh,
  ArrowBack,
  WarningAmber,
  Lock,
  FactCheck,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import PrivacyEditorModal from './PrivacyEditorModal';

interface FileState {
  id: string;
  originalFile: File;
  sanitizedBlob: Blob | null;
  studentId: string;
  previewUrl: string;
}

export default function BatchCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const assignmentId = location.state?.assignmentId || 'a1';

  const [files, setFiles] = useState<FileState[]>([]);
  const [roster, setRoster] = useState<{ id: string; name: string }[]>([]);
  const [editingFile, setEditingFile] = useState<FileState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const filesRef = useRef(files);
  useEffect(() => {
    filesRef.current = files;
  }, [files]);

  useEffect(() => {
    let isMounted = true;
    const fetchClass = async () => {
      try {
        const classes = await AppTeacherService.getClasses();
        if (classes.length > 0 && isMounted) {
          const cls = classes[0];
          const students = Array.from({ length: cls.studentCount }, (_, i) => ({
            id: `st_${i + 1}`,
            name: `Học sinh ${i + 1} (${cls.name})`,
          }));
          setRoster(students);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchClass();

    return () => {
      isMounted = false;
      // Clean up object URLs
      filesRef.current.forEach((f) => URL.revokeObjectURL(f.previewUrl));
    };
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      const remainingSlots = 30 - files.length;
      if (remainingSlots <= 0) {
        setError('Đã đạt tối đa 30 ảnh cho một đợt chấm.');
        return;
      }
      const filesToAdd = selected.slice(0, remainingSlots);
      const newFiles = filesToAdd.map((file) => ({
        id: Math.random().toString(36).substr(2, 9),
        originalFile: file,
        sanitizedBlob: null,
        studentId: '',
        previewUrl: URL.createObjectURL(file),
      }));
      setFiles((prev) => [...prev, ...newFiles]);
      setError(null);
    }
  };

  const removeFile = (idToRemove: string) => {
    setFiles((prev) => {
      const f = prev.find((x) => x.id === idToRemove);
      if (f) URL.revokeObjectURL(f.previewUrl);
      return prev.filter((x) => x.id !== idToRemove);
    });
  };

  const handleReplaceFile = (idToReplace: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setFiles((prev) =>
        prev.map((f) => {
          if (f.id === idToReplace) {
            URL.revokeObjectURL(f.previewUrl);
            return {
              ...f,
              originalFile: file,
              sanitizedBlob: null,
              previewUrl: URL.createObjectURL(file),
            };
          }
          return f;
        })
      );
    }
  };

  const updateStudent = (id: string, studentId: string) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, studentId } : f)));
  };

  const handleSaveSanitized = (blob: Blob) => {
    if (editingFile) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === editingFile.id
            ? {
                ...f,
                sanitizedBlob: blob,
                previewUrl: URL.createObjectURL(blob),
              }
            : f
        )
      );
    }
    setEditingFile(null);
  };

  // Duplicate mapping detection
  const studentMapCounts: Record<string, number> = {};
  files.forEach((f) => {
    if (f.studentId) {
      studentMapCounts[f.studentId] = (studentMapCounts[f.studentId] || 0) + 1;
    }
  });

  const totalFiles = files.length;
  const mappedCount = files.filter((f) => Boolean(f.studentId)).length;
  const sanitizedCount = files.filter((f) => Boolean(f.sanitizedBlob)).length;
  const hasDuplicateStudent = Object.values(studentMapCounts).some((count) => count > 1);

  const isCountValid = totalFiles >= 1 && totalFiles <= 30;
  const isMappingValid = mappedCount === totalFiles && totalFiles > 0;
  const isPrivacyValid = sanitizedCount === totalFiles && totalFiles > 0;
  const isReadyToSubmit = isCountValid && isMappingValid && isPrivacyValid;

  const handleStartProcessing = async () => {
    setError(null);
    if (totalFiles < 1) {
      setError('Vui lòng tải lên ít nhất 1 ảnh bài làm.');
      return;
    }
    if (totalFiles > 30) {
      setError('Mỗi đợt chấm hỗ trợ tối đa 30 bài làm.');
      return;
    }
    if (mappedCount < totalFiles) {
      setError('Còn bài làm chưa được gán với học sinh. Vui lòng kiểm tra lại danh sách.');
      return;
    }
    if (sanitizedCount < totalFiles) {
      setError('Bắt buộc che thông tin cá nhân (Privacy Gate) thủ công cho tất cả bài làm.');
      return;
    }

    try {
      setUploading(true);
      const batch = await AppTeacherService.createBatch(assignmentId, files.length);
      const uploadFiles = files.map(
        (f) => new File([f.sanitizedBlob!], f.originalFile.name, { type: f.originalFile.type })
      );
      const mappings = files.map((f, i) => ({ fileIndex: i, studentId: f.studentId }));

      await AppTeacherService.uploadImages(batch.batchId || batch.id || '', uploadFiles, mappings);
      navigate(`/batches/${batch.batchId || batch.id}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Có lỗi xảy ra khi tạo lượt chấm.');
      setUploading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/batches')}
        sx={{ mb: 2 }}
      >
        Quay lại danh sách đợt chấm
      </Button>

      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          Khởi tạo Đợt chấm bài (Batch Upload)
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tải lên từ 1 đến 30 ảnh bài làm (thông thường 10–30 bài), che thông tin cá nhân thủ công và ghép cặp minh bạch với học sinh.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {error}
        </Alert>
      )}

      {/* Upload Zone when empty */}
      {files.length === 0 ? (
        <Card
          sx={{
            borderStyle: 'dashed',
            borderWidth: 2,
            borderColor: '#93C5FD',
            bgcolor: '#EFF6FF',
            borderRadius: 3,
            mb: 4,
          }}
        >
          <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <CloudUpload sx={{ fontSize: 64, color: '#2563EB', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#1D4ED8' }}>
              Tải lên từ 1 đến 30 ảnh bài làm học sinh
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center', maxWidth: 480 }}>
              Hỗ trợ định dạng JPG, PNG (tối đa 30 bài/đợt; đợt chấm hàng loạt thường gồm 10–30 bài). Ảnh chụp vuông góc, rõ nét để AI nhận diện tối ưu.
            </Typography>
            <Button variant="contained" component="label" size="large" sx={{ px: 4 }}>
              Chọn ảnh từ máy tính
              <input type="file" hidden multiple accept="image/*" onChange={handleFileSelect} />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ mb: 4 }}>
          {/* READINESS SUMMARY PANEL */}
          <Paper
            variant="outlined"
            sx={{
              p: 2.5,
              mb: 3.5,
              borderRadius: 2.5,
              bgcolor: isReadyToSubmit ? '#F0FDF4' : '#FFFBEB',
              borderColor: isReadyToSubmit ? '#86EFAC' : '#FCD34D',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
                  Bảng kiểm tra sẵn sàng nộp bài (Readiness Checklist)
                </Typography>
                <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                  <Chip
                    label={`Ảnh: ${totalFiles}/30 (Quy chuẩn: 1–30 ảnh)`}
                    size="small"
                    color={isCountValid ? 'success' : 'error'}
                    variant={isCountValid ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 700 }}
                  />
                  <Chip
                    label={`Đã gán học sinh: ${mappedCount}/${totalFiles}`}
                    size="small"
                    color={isMappingValid ? 'success' : 'warning'}
                    variant={isMappingValid ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 700 }}
                  />
                  <Chip
                    label={`Đã che thông tin: ${sanitizedCount}/${totalFiles}`}
                    size="small"
                    color={isPrivacyValid ? 'success' : 'warning'}
                    variant={isPrivacyValid ? 'filled' : 'outlined'}
                    sx={{ fontWeight: 700 }}
                  />
                  {hasDuplicateStudent && (
                    <Chip
                      label="Lưu ý: Có học sinh nộp nhiều bài/ảnh"
                      size="small"
                      color="info"
                      variant="outlined"
                      sx={{ fontWeight: 700 }}
                    />
                  )}
                </Box>
              </Box>

              <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
                <Button variant="outlined" component="label" disabled={totalFiles >= 30 || uploading}>
                  Thêm ảnh
                  <input type="file" hidden multiple accept="image/*" onChange={handleFileSelect} />
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleStartProcessing}
                  disabled={!isReadyToSubmit || uploading}
                  startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <FactCheck />}
                  sx={{
                    px: 3,
                    py: 1.25,
                    bgcolor: isReadyToSubmit ? '#2563EB' : '#94A3B8',
                    '&:hover': { bgcolor: isReadyToSubmit ? '#1D4ED8' : '#94A3B8' },
                  }}
                >
                  {uploading ? 'Đang tải lên & bắt đầu chấm...' : 'Bắt đầu chấm bài bằng AI'}
                </Button>
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Lock sx={{ fontSize: 16, color: '#475569' }} />
              <Typography variant="caption" color="text.secondary">
                <strong>Cam kết quyền riêng tư:</strong> Toàn bộ họ tên và thông tin trường học được che thủ công trước khi gửi tới máy chủ xử lý OCR.
              </Typography>
            </Box>
          </Paper>

          {/* Grid of uploaded images */}
          <Grid container spacing={2.5}>
            {files.map((file, idx) => {
              const isDuplicate = file.studentId && studentMapCounts[file.studentId] > 1;
              const isMissingStudent = !file.studentId;
              const isMissingPrivacy = !file.sanitizedBlob;

              return (
                <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={file.id}>
                  <Card
                    variant="outlined"
                    sx={{
                      position: 'relative',
                      borderRadius: 2.5,
                      borderColor: isMissingStudent
                        ? '#F59E0B'
                        : isMissingPrivacy
                        ? '#94A3B8'
                        : isDuplicate
                        ? '#CBD5E1'
                        : '#E2E8F0',
                      borderWidth: isMissingStudent ? 2 : 1,
                    }}
                  >
                    {/* Index tag & action buttons */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        zIndex: 10,
                        bgcolor: 'rgba(15, 23, 42, 0.75)',
                        color: 'white',
                        px: 1,
                        py: 0.25,
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        fontWeight: 700,
                      }}
                    >
                      #{idx + 1}
                    </Box>

                    <Box sx={{ position: 'absolute', top: 6, right: 6, zIndex: 10, display: 'flex', gap: 0.5 }}>
                      <Tooltip title="Thay thế ảnh này">
                        <IconButton
                          component="label"
                          size="small"
                          sx={{
                            bgcolor: 'rgba(255,255,255,0.9)',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                            '&:hover': { bgcolor: '#2563EB', color: 'white' },
                          }}
                        >
                          <Refresh sx={{ fontSize: 16 }} />
                          <input type="file" hidden accept="image/*" onChange={(e) => handleReplaceFile(file.id, e)} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Xóa ảnh này">
                        <IconButton
                          size="small"
                          onClick={() => removeFile(file.id)}
                          sx={{
                            bgcolor: 'rgba(255,255,255,0.9)',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                            '&:hover': { bgcolor: '#DC2626', color: 'white' },
                          }}
                        >
                          <Close sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Tooltip>
                    </Box>

                    {/* Image Preview Area */}
                    <Box sx={{ position: 'relative', paddingTop: '75%', bgcolor: '#0F172A', overflow: 'hidden' }}>
                      <img
                        src={file.previewUrl}
                        alt={`Bài làm ${idx + 1}`}
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: '100%',
                          objectFit: 'contain',
                        }}
                      />
                      {file.sanitizedBlob ? (
                        <Box
                          sx={{
                            position: 'absolute',
                            bottom: 8,
                            right: 8,
                            bgcolor: '#15803D',
                            color: 'white',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 0.5,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        >
                          <CheckCircle sx={{ fontSize: 14 }} /> Đã che thông tin
                        </Box>
                      ) : (
                        <Box
                          sx={{
                            position: 'absolute',
                            bottom: 8,
                            right: 8,
                            bgcolor: '#B45309',
                            color: 'white',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 0.5,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        >
                          <WarningAmber sx={{ fontSize: 14 }} /> Chưa che
                        </Box>
                      )}
                    </Box>

                    {/* Card Content & Mapping Controls */}
                    <CardContent sx={{ p: 2 }}>
                      <FormControl fullWidth size="small" sx={{ mb: 1.5 }}>
                        <InputLabel id={`select-student-label-${file.id}`}>Học sinh thực hiện</InputLabel>
                        <Select
                          labelId={`select-student-label-${file.id}`}
                          value={file.studentId}
                          label="Học sinh thực hiện"
                          onChange={(e) => updateStudent(file.id, e.target.value)}
                        >
                          <MenuItem value="">
                            <em>-- Chưa chọn học sinh --</em>
                          </MenuItem>
                          {roster.map((st) => (
                            <MenuItem key={st.id} value={st.id}>
                              {st.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>

                      {isDuplicate && (
                        <Typography variant="caption" color="warning.main" sx={{ display: 'block', mb: 1, fontWeight: 600 }}>
                          Lưu ý: Học sinh này có nhiều hơn 1 bài làm trong đợt
                        </Typography>
                      )}

                      <Button
                        fullWidth
                        size="small"
                        variant={file.sanitizedBlob ? 'outlined' : 'contained'}
                        color={file.sanitizedBlob ? 'primary' : 'warning'}
                        startIcon={<PrivacyTip />}
                        onClick={() => setEditingFile(file)}
                        sx={{ fontWeight: 600 }}
                      >
                        {file.sanitizedBlob ? 'Chỉnh sửa vùng che' : 'Che thông tin cá nhân'}
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {editingFile && (
        <PrivacyEditorModal
          open={Boolean(editingFile)}
          onClose={() => setEditingFile(null)}
          file={editingFile.originalFile}
          onSave={handleSaveSanitized}
        />
      )}
    </Box>
  );
}
