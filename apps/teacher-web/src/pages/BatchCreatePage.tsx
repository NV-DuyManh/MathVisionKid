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
import { PageHeader } from '../components/common/PageHeader';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { useQuery } from '@tanstack/react-query';
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
  const assignmentId = location.state?.assignmentId;

  const [params, setParams] = useSearchParams();
  const chosenId = params.get('assignmentId') || assignmentId;
  const [hasDraft, setHasDraft] = useState(false);
  const { data: assignments = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['teacher-assignments'], queryFn: () => AppTeacherService.getAssignments(),
  });
  return <Box>
    <PageHeader title="Tạo đợt chấm bài" subtitle="Chọn bài tập rồi tải ảnh bài làm của học sinh." />
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>Chưa tải được bài tập.</Alert>}
    <FormControl fullWidth sx={{ mb: 3 }} disabled={isLoading || hasDraft}>
      <InputLabel id="batch-assignment-label">Bài tập cần chấm</InputLabel>
      <Select labelId="batch-assignment-label" label="Bài tập cần chấm" value={chosenId || ''}
        onChange={e => setParams({ assignmentId: e.target.value })}>
        {chosenId && !assignments.some(a => (a.assignmentId || a.id) === chosenId) &&
          <MenuItem value={chosenId}>Bài tập đã chọn</MenuItem>}
        {assignments.map(a => <MenuItem key={a.assignmentId || a.id} value={a.assignmentId || a.id}>{a.title}</MenuItem>)}
      </Select>
    </FormControl>
    {hasDraft && <Typography variant="body2" sx={{ mb: 2 }}>Xóa các ảnh đã chọn nếu muốn đổi bài tập.</Typography>}
    {!isLoading && !isError && assignments.length === 0 && !chosenId &&
      <Alert severity="info" action={<Button onClick={() => navigate('/assignments/create')}>Tạo bài tập</Button>}>Chưa có bài tập để chấm.</Alert>}
    {chosenId && <BatchUpload key={chosenId} assignmentId={chosenId} onDraftChange={setHasDraft} />}
  </Box>;
}

function BatchUpload({ assignmentId, onDraftChange }: { assignmentId: string; onDraftChange: (value: boolean) => void }) {
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileState[]>([]);
  const [editingFile, setEditingFile] = useState<FileState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const submitLock = useRef(false);
  const [createdBatchId, setCreatedBatchId] = useState('');
  useEffect(() => { onDraftChange(files.length > 0 || uploading); }, [files.length, uploading, onDraftChange]);
  const { data: roster = [], isLoading: rosterLoading, isError: rosterError, refetch } = useQuery({
    queryKey: ['assignment-roster', assignmentId],
    queryFn: () => AppTeacherService.getAssignmentRoster(assignmentId),
  });
  const filesRef = useRef(files);
  useEffect(() => { filesRef.current = files; }, [files]);
  useEffect(() => () => {
    filesRef.current.forEach(f => URL.revokeObjectURL(f.previewUrl));
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files);
      e.target.value = '';
      if (selected.some(file => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type))) {
        setError('Hãy chọn ảnh JPG, PNG hoặc WebP.');
        return;
      }
      if (selected.some(file => file.size > 10 * 1024 * 1024)) {
        setError('Mỗi ảnh tối đa 10 MB. Hãy chọn ảnh nhỏ hơn.'); return;
      }
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
    const removed = files.find(f => f.id === idToRemove);
    if (removed) URL.revokeObjectURL(removed.previewUrl);
    setFiles(prev => prev.filter(f => f.id !== idToRemove));
  };

  const handleReplaceFile = (idToReplace: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.size > 10 * 1024 * 1024) { setError('Mỗi ảnh tối đa 10 MB.'); e.target.value = ''; return; }
      e.target.value = '';
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        setError('Hãy chọn ảnh JPG, PNG hoặc WebP.'); return;
      }
      const old = files.find(f => f.id === idToReplace);
      if (old) URL.revokeObjectURL(old.previewUrl);
      const previewUrl = URL.createObjectURL(file);
      setFiles((prev) =>
        prev.map((f) => {
          if (f.id === idToReplace) {
            return {
              ...f,
              originalFile: file,
              sanitizedBlob: null,
              previewUrl,
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
    if (blob.size > 10 * 1024 * 1024) { setError('Ảnh sau khi che lớn hơn 10 MB. Hãy chọn ảnh nhỏ hơn.'); setEditingFile(null); return; }
    if (editingFile) {
      URL.revokeObjectURL(editingFile.previewUrl);
      const previewUrl = URL.createObjectURL(blob);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === editingFile.id
            ? {
                ...f,
                sanitizedBlob: blob,
                previewUrl,
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
  const isReadyToSubmit = isCountValid && isMappingValid && isPrivacyValid && !rosterLoading && !rosterError && roster.length > 0 && !createdBatchId;

  const handleStartProcessing = async () => {
    if (submitLock.current || !isReadyToSubmit) return;
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

    if (files.reduce((size, f) => size + (f.sanitizedBlob?.size || 0), 0) > 95 * 1024 * 1024) {
      setError('Tổng ảnh quá lớn. Hãy chia thành đợt nhỏ hơn 95 MB.'); return;
    }
    submitLock.current = true;
    try {
      setUploading(true);
      const batch = await AppTeacherService.createBatch(assignmentId, files.length);
      const batchId = batch.batchId || batch.id;
      if (!batchId) throw new Error('Missing batch identifier');
      setCreatedBatchId(batchId);
      const uploadFiles = files.map(
        (f) => new File([f.sanitizedBlob!], f.originalFile.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg' })
      );
      const mappings = files.map((f, i) => ({ fileIndex: i, studentId: f.studentId }));

      await AppTeacherService.uploadImages(batchId, uploadFiles, mappings);
      navigate(`/batches/${batchId}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Có lỗi xảy ra khi tạo lượt chấm.');
    } finally {
      submitLock.current = false;
      setUploading(false);
    }
  };

  return (
    <Box>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate('/batches')}
        sx={{ mb: 2 }}
      >
        Quay lại danh sách đợt chấm
      </Button>

      {rosterLoading && <Typography role="status" sx={{ mb: 2 }}>Đang tải danh sách học sinh…</Typography>}
      {rosterError && <Alert severity="error" sx={{ mb: 2 }} action={<Button onClick={() => void refetch()}>Thử lại</Button>}>Chưa tải được danh sách học sinh.</Alert>}
      {!rosterLoading && !rosterError && !roster.length && <Alert severity="info" sx={{ mb: 2 }}>Lớp chưa có học sinh. Hãy thêm học sinh trước khi gửi bài.</Alert>}

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {createdBatchId ? 'Đợt chấm đã được tạo nhưng chưa xác nhận được kết quả tải ảnh. Hãy kiểm tra đợt chấm trước khi gửi lại để tránh trùng bài.' : error}
          {createdBatchId && <Button onClick={() => navigate(`/batches/${createdBatchId}`)}>Kiểm tra đợt chấm</Button>}
        </Alert>
      )}

      {/* Upload Zone when empty */}
      {files.length === 0 ? (
        <Card
          sx={{
            borderStyle: 'dashed',
            borderWidth: 2,
            borderColor: '#CBD5E1',
            bgcolor: '#F8FAFC',
            borderRadius: 3,
            mb: 4,
          }}
        >
          <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <CloudUpload sx={{ fontSize: 64, color: '#2563EB', mb: 2 }} />
            <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#0F172A' }}>
              Tải lên từ 1 đến 30 ảnh bài làm học sinh
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center', maxWidth: 480 }}>
              Hỗ trợ JPG, PNG, WebP, mỗi ảnh tối đa 10 MB (tối đa 30 bài/đợt; đợt chấm hàng loạt thường gồm 10–30 bài). Ảnh chụp vuông góc, rõ nét để AI nhận diện tối ưu.
            </Typography>
            <Button disabled={rosterLoading || rosterError || !roster.length} variant="contained" component="label" size="large" sx={{ px: 4, py: 1.25, fontWeight: 700 }}>
              Chọn ảnh từ máy tính
              <input type="file" hidden multiple accept="image/jpeg,image/png,image/webp" onChange={handleFileSelect} />
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
                <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#211844', mb: 0.5 }}>
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
                  <input type="file" hidden multiple accept="image/jpeg,image/png,image/webp" onChange={handleFileSelect} />
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
                    fontWeight: 700,
                    bgcolor: isReadyToSubmit ? 'primary.main' : '#94A3B8',
                    '&:hover': { bgcolor: isReadyToSubmit ? 'primary.dark' : '#94A3B8' },
                  }}
                >
                  {uploading ? 'Đang tải lên & bắt đầu chấm...' : 'Bắt đầu chấm bài bằng AI'}
                </Button>
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Lock sx={{ fontSize: 16, color: '#64748B' }} />
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
                          disabled={uploading}
                          aria-label="Thay thế ảnh này"
                          component="label"
                          size="small"
                          sx={{
                            bgcolor: 'rgba(255,255,255,0.9)',
                            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                            '&:hover': { bgcolor: 'primary.main', color: 'white' },
                          }}
                        >
                          <Refresh sx={{ fontSize: 16 }} />
                          <input type="file" hidden accept="image/jpeg,image/png,image/webp" onChange={(e) => handleReplaceFile(file.id, e)} />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Xóa ảnh này">
                        <IconButton
                          disabled={uploading}
                          aria-label="Xóa ảnh này"
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
                    <Box sx={{ position: 'relative', paddingTop: '75%', bgcolor: '#211844', overflow: 'hidden' }}>
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
                          disabled={uploading}
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
                        disabled={uploading}
                        onClick={() => setEditingFile(file)}
                        sx={{ fontWeight: 600 }}
                      >
                        {file.sanitizedBlob ? 'Bổ sung vùng che' : 'Che thông tin cá nhân'}
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
          file={editingFile.sanitizedBlob || editingFile.originalFile}
          onSave={handleSaveSanitized}
        />
      )}
    </Box>
  );
}
