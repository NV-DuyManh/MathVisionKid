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
  Paper,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload,
  Close,
  PrivacyTip,
  CheckCircle,
  Refresh,
  ArrowBack,
  WarningAmber,
  FactCheck,
} from '@mui/icons-material';
import { PageHeader } from '../components/common/PageHeader';
import { Link, useNavigate, useLocation, useOutletContext, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { newCreationRequestId } from '../services/api/newCreationRequestId';
import { AuthTokenStore } from '../services/api/AuthTokenStore';
import { useUploadDraftGuard } from '../hooks/useUploadDraftGuard';
import { useQuery } from '@tanstack/react-query';
import PrivacyEditorModal from './PrivacyEditorModal';

interface FileState {
  id: string;
  originalFile: File;
  sanitizedBlob: Blob | null;
  studentId: string;
  previewUrl: string;
  error?: string;
}

function getImageError(file: File) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    return 'Định dạng không hỗ trợ (chỉ nhận JPG, PNG, WebP)';
  }
  if (file.size > 10 * 1024 * 1024) return 'Dung lượng vượt quá 10 MB';
  if (file.size === 0) return 'Tệp rỗng không có nội dung';
}

export default function BatchCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const assignmentId = location.state?.assignmentId;

  const [params, setParams] = useSearchParams();
  const resumeId = params.get('batchId') || '';
  const resume = useQuery({
    queryKey: ['batch', resumeId], queryFn: () => AppTeacherService.getBatchStatus(resumeId),
    enabled: !!resumeId, refetchOnMount: 'always', refetchOnWindowFocus: false,
  });
  const canResume = resume.data?.status === 'CREATED' && (resume.data.totalCount ?? resume.data.totalImages ?? 0) === 0;
  const chosenId = resumeId ? resume.data?.assignmentId : params.get('assignmentId') || assignmentId;
  const [hasDraft, setHasDraft] = useState(false);
  const outlet = useOutletContext<{ setUploadDraftActive: (active: boolean) => void } | undefined>();
  const setUploadDraftActive = outlet?.setUploadDraftActive;
  useEffect(() => {
    setUploadDraftActive?.(hasDraft);
    return () => setUploadDraftActive?.(false);
  }, [hasDraft, setUploadDraftActive]);
  const { data: assignments = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['teacher-assignments'], queryFn: () => AppTeacherService.getAssignments(),
  });
  return <Box>
    <PageHeader title={resumeId ? 'Tiếp tục tải ảnh' : 'Tạo đợt chấm bài'} subtitle="Chọn bài tập rồi tải ảnh bài làm của học sinh." />
    {resumeId && (resume.isPending || resume.isFetching || resume.isPaused) &&
      <Typography role="status" sx={{ mb: 2 }}>Đang kiểm tra đợt chấm…</Typography>}
    {resumeId && resume.isError && <Alert severity="error" action={<Button onClick={() => void resume.refetch()}>Thử lại</Button>}>
      Chưa kiểm tra được đợt chấm. Vui lòng thử lại.
    </Alert>}
    {resumeId && !resume.isFetching && resume.isSuccess && (!canResume || !chosenId) &&
      <Alert severity="info" action={<Button component={Link} to={`/batches/${encodeURIComponent(resumeId)}`}>Xem đợt chấm</Button>}>
        Đợt này đã nhận ảnh hoặc không còn mở để tải ảnh.
      </Alert>}
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>Chưa tải được bài tập.</Alert>}
    <FormControl fullWidth sx={{ mb: 3 }} disabled={isLoading || hasDraft || !!resumeId}>
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
    {chosenId && (!resumeId || canResume || hasDraft) &&
      <BatchUpload key={JSON.stringify([location.search, assignmentId, chosenId])} assignmentId={chosenId} resumeBatchId={resumeId}
        checkingResume={Boolean(resumeId && (!canResume || !resume.isSuccess || resume.isFetching || resume.isPaused))}
        onDraftChange={setHasDraft} />}
  </Box>;
}

function BatchUpload({ assignmentId, resumeBatchId, checkingResume, onDraftChange }: {
  assignmentId: string; resumeBatchId: string; checkingResume: boolean; onDraftChange: (value: boolean) => void;
}) {
  const navigate = useNavigate();
  const { key: historyEntry } = useLocation();
  const [files, setFiles] = useState<FileState[]>([]);
  const [editingFile, setEditingFile] = useState<FileState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const submitLock = useRef(false);
  const filePicker = useRef<HTMLInputElement>(null);
  const mounted = useRef(false);
  const creationRequestId = useRef<string | undefined>(undefined);
  const [createdBatchId, setCreatedBatchId] = useState('');
  const [canRetryUpload, setCanRetryUpload] = useState(false);
  const { confirmation, allowNextNavigation } = useUploadDraftGuard(files.length > 0 || uploading, () => {
    mounted.current = false;
  });
  useEffect(() => { onDraftChange(files.length > 0 || uploading); }, [files.length, uploading, onDraftChange]);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
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
      const remainingSlots = 30 - files.length;
      if (remainingSlots <= 0) {
        setError('Đã đạt tối đa 30 ảnh cho một đợt chấm.');
        return;
      }
      const overflowCount = Math.max(0, selected.length - remainingSlots);
      const filesToAdd = selected.slice(0, remainingSlots);
      const newFiles: FileState[] = filesToAdd.map((file) => {
        const fileError = getImageError(file);
        return {
          id: Math.random().toString(36).substr(2, 9),
          originalFile: file,
          sanitizedBlob: null,
          studentId: '',
          previewUrl: fileError ? '' : URL.createObjectURL(file),
          error: fileError,
        };
      });
      const invalidCount = newFiles.filter((file) => file.error).length;
      setFiles((prev) => [...prev, ...newFiles]);
      if (overflowCount > 0 && invalidCount > 0) {
        setError(`Đã thêm ${filesToAdd.length} ảnh (${invalidCount} ảnh không hợp lệ). Bỏ qua ${overflowCount} ảnh do vượt quá giới hạn 30 ảnh cho một đợt chấm.`);
      } else if (overflowCount > 0) {
        setError(`Đã thêm ${filesToAdd.length} ảnh. Bỏ qua ${overflowCount} ảnh do vượt quá giới hạn 30 ảnh cho một đợt chấm.`);
      } else if (invalidCount > 0) {
        setError(`Có ${invalidCount} ảnh không hợp lệ. Vui lòng kiểm tra hoặc thay thế các ảnh báo lỗi.`);
      } else {
        setError(null);
      }
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
      e.target.value = '';
      const fileError = getImageError(file);
      const old = files.find(f => f.id === idToReplace);
      if (old && old.previewUrl) URL.revokeObjectURL(old.previewUrl);
      const previewUrl = fileError ? '' : URL.createObjectURL(file);
      setFiles((prev) =>
        prev.map((f) => {
          if (f.id === idToReplace) {
            return {
              ...f,
              originalFile: file,
              sanitizedBlob: null,
              previewUrl,
              error: fileError,
            };
          }
          return f;
        })
      );
      if (fileError) {
        setError('Ảnh thay thế không hợp lệ: ' + fileError);
      } else {
        setError(null);
      }
    }
  };

  const updateStudent = (id: string, studentId: string) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, studentId } : f)));
  };

  const nextFile = editingFile && files.slice(files.findIndex(file => file.id === editingFile.id) + 1)
    .find(file => !file.error && !file.sanitizedBlob);
  const handleSaveSanitized = (blob: Blob, advance = false) => {
    if (blob.size > 8 * 1024 * 1024) {
      setError(`Ảnh ${editingFile?.originalFile.name ?? ''} sau khi che vượt quá 8 MiB. Hãy thay bằng ảnh nhỏ hơn.`);
      setEditingFile(null);
      return;
    }
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
    setEditingFile(advance ? nextFile || null : null);
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
  const hasFileErrors = files.some((f) => Boolean(f.error));
  const isReadyToSubmit = isCountValid && isMappingValid && isPrivacyValid && !hasFileErrors
    && !rosterLoading && !rosterError && roster.length > 0 && (!createdBatchId || canRetryUpload) && !checkingResume;

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
    let storageKey: string | undefined;
    let batchId = resumeBatchId || (canRetryUpload ? createdBatchId : '');
    setCanRetryUpload(false);
    const finishCreation = () => {
      creationRequestId.current = undefined;
      if (storageKey) {
        try { sessionStorage.removeItem(storageKey); } catch { /* storage unavailable */ }
      }
    };
    try {
      setUploadProgress(null);
      setUploading(true);
      if (!batchId) {
        try {
          const sessionId = AuthTokenStore.getSessionId();
          if (sessionId) {
            storageKey = `teacher:batch-create:${sessionId}:${historyEntry}:${assignmentId}`;
            creationRequestId.current ??= sessionStorage.getItem(storageKey) ?? undefined;
          }
        } catch { /* in-memory retry */ }
        creationRequestId.current ??= newCreationRequestId();
        if (storageKey) {
          try { sessionStorage.setItem(storageKey, creationRequestId.current); } catch { /* in-memory retry */ }
        }
        const batch = await AppTeacherService.createBatch(assignmentId, files.length, creationRequestId.current);
        if (!mounted.current) return;
        batchId = batch.batchId || batch.id || '';
        if (batchId && (batch.status !== 'CREATED' || (batch.totalCount ?? batch.totalImages ?? 0) > 0)) {
          finishCreation();
          setCreatedBatchId(batchId);
          setError('Đợt chấm đã nhận ảnh hoặc đã đóng. Hãy kiểm tra đợt trước khi tạo đợt mới.');
          return;
        }
      }
      if (!batchId) throw new Error('Missing batch identifier');
      setCreatedBatchId(batchId);
      const uploadFiles = files.map(
        (f) => new File([f.sanitizedBlob!], f.originalFile.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg' })
      );
      const mappings = files.map((f, i) => ({ fileIndex: i, studentId: f.studentId }));

      await AppTeacherService.uploadImages(batchId, uploadFiles, mappings, (percent) => {
        if (mounted.current) setUploadProgress(percent);
      });
      if (!mounted.current) return;
      finishCreation();
      allowNextNavigation();
      navigate(`/batches/${batchId}`);
    } catch (err: any) {
      if (mounted.current) {
        const validationError = [400, 413, 415, 422].includes(err.response?.status);
        if (batchId && validationError) setCanRetryUpload(true);
        setError(batchId && !validationError
          ? 'Chưa xác nhận được kết quả tải ảnh. Hãy kiểm tra đợt chấm trước khi gửi lại.'
          : err.response?.data?.error?.message || (validationError ? 'Máy chủ từ chối dữ liệu ảnh. Hãy kiểm tra ảnh và thử lại.' : 'Chưa xác nhận được đợt chấm. Bạn có thể thử gửi lại.'));
      }
    } finally {
      submitLock.current = false;
      if (mounted.current) setUploading(false);
    }
  };

  return (
    <Box>
      {confirmation}
      <input ref={filePicker} type="file" hidden multiple accept="image/jpeg,image/png,image/webp" onChange={handleFileSelect} />
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
      {!rosterLoading && !rosterError && !roster.length && <Alert severity="info" sx={{ mb: 2 }}>Lớp chưa có học sinh. Hãy liên hệ quản trị viên để cập nhật danh sách trước khi gửi bài.</Alert>}

      {uploading && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3, borderRadius: 2, bgcolor: '#EFF6FF', borderColor: '#BFDBFE' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 700, color: '#1E40AF' }}>
              {uploadProgress === null ? 'Đang gửi ảnh bài làm…'
                : uploadProgress === 100 ? 'Đang chờ xác nhận tải ảnh…'
                  : `Đang tải ảnh bài làm (${uploadProgress}%)`}
            </Typography>
          </Box>
          <LinearProgress
            aria-label="Tiến độ gửi ảnh bài làm"
            variant={uploadProgress === null || uploadProgress === 100 ? 'indeterminate' : 'determinate'}
            value={uploadProgress ?? undefined}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Paper>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }} role="alert">
          {error}
          {createdBatchId && <Button onClick={() => navigate(`/batches/${createdBatchId}`)}>Kiểm tra đợt chấm</Button>}
        </Alert>
      )}

      {/* Upload Zone when empty */}
      {files.length === 0 ? (
        <Card component="section" variant="outlined" aria-labelledby="batch-add-images" sx={{ mb: 4 }}>
          <CardContent sx={{ display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 3fr) minmax(0, 2fr)' },
            alignItems: 'start', gap: 2.5, p: { xs: 2, md: 3 } }}>
            <Box>
              <Typography id="batch-add-images" component="h2" variant="h6" sx={{ mb: 0.75 }}>Chọn ảnh bài làm</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Mỗi đợt nhận từ 1 đến 30 ảnh. Chọn tệp JPG, PNG hoặc WebP, tối đa 10 MB mỗi ảnh.
              </Typography>
              <Button disabled={rosterLoading || rosterError || !roster.length} variant="contained" size="large"
                startIcon={<CloudUpload />} onClick={() => filePicker.current?.click()}>
                Chọn ảnh từ máy tính
              </Button>
            </Box>
            <Box sx={{ bgcolor: 'primary.light', borderRadius: '12px', p: 2 }}>
              <Typography component="h3" variant="subtitle2">Sau khi chọn ảnh</Typography>
              <Box component="ol" sx={{ mt: 1, mb: 0, pl: 2.5, color: 'text.secondary', '& li + li': { mt: 0.75 } }}>
                <li>Gán mỗi ảnh cho học sinh tương ứng.</li>
                <li>Kiểm tra và che thông tin riêng tư.</li>
                <li>Gửi các ảnh đã chuẩn bị để chấm bài.</li>
              </Box>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ mb: 4 }}>
          <Paper component="section" variant="outlined" aria-labelledby="batch-readiness" sx={{ p: { xs: 2, md: 2.5 }, mb: 2.5 }}>
            <Typography id="batch-readiness" component="h2" variant="h6">Kiểm tra trước khi gửi</Typography>
            <Typography role="status" color="text.secondary" variant="body2" sx={{ mt: 0.5, mb: 1.5 }}>
              {isReadyToSubmit ? 'Đợt ảnh đã sẵn sàng.' : 'Hoàn tất các mục còn thiếu để gửi ảnh.'}
            </Typography>
            <Box component="ul" sx={{
              display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', sm: 'repeat(3, minmax(0, 1fr))' },
              listStyle: 'none', p: 0, m: 0, borderBlock: '1px solid', borderColor: 'divider',
            }}>
              {[
                { label: 'Ảnh đã chọn', count: `${totalFiles}/30`, ready: isCountValid },
                { label: 'Đã gán học sinh', count: `${mappedCount}/${totalFiles}`, ready: isMappingValid },
                { label: 'Đã che thông tin', count: `${sanitizedCount}/${totalFiles}`, ready: isPrivacyValid },
              ].map(({ label, count, ready }) => (
                <Box component="li" key={label} sx={{
                  display: 'flex', alignItems: 'center', gap: 1, py: 1.25, px: { xs: 0, sm: 1 },
                  '& + &': { borderTop: { xs: '1px solid', sm: 0 }, borderInlineStart: { sm: '1px solid' }, borderColor: 'divider' },
                }}>
                  {ready ? <CheckCircle color="success" fontSize="small" aria-hidden="true" />
                    : <WarningAmber color="warning" fontSize="small" aria-hidden="true" />}
                  <Typography variant="body2" sx={{ flex: 1 }}>{label}</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 800, fontVariantNumeric: 'tabular-nums' }}>{count}</Typography>
                </Box>
              ))}
            </Box>
            {hasDuplicateStudent && (
              <Typography color="text.secondary" variant="body2" sx={{ mt: 1 }}>Có học sinh được gán nhiều ảnh.</Typography>
            )}
            <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'flex-end', gap: 1, mt: 2 }}>
              <Button variant="outlined" onClick={() => filePicker.current?.click()} disabled={totalFiles >= 30 || uploading}>
                Thêm ảnh
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleStartProcessing}
                disabled={!isReadyToSubmit || uploading}
                aria-busy={uploading}
                startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <FactCheck />}
              >
                {uploading ? 'Đang tải lên & bắt đầu chấm...' : 'Bắt đầu chấm bài bằng AI'}
              </Button>
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
                        src={file.previewUrl || undefined}
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
                      {file.error && (
                        <Alert severity="error" sx={{ mb: 1.5, py: 0.25, px: 1, fontSize: '0.75rem', fontWeight: 600 }}>
                          {file.error}
                        </Alert>
                      )}
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
                        disabled={uploading || Boolean(file.error)}
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
          key={editingFile.id}
          open={Boolean(editingFile)}
          onClose={() => setEditingFile(null)}
          file={editingFile.sanitizedBlob || editingFile.originalFile}
          imageLabel={`Ảnh ${files.findIndex(file => file.id === editingFile.id) + 1}/${files.length}: ${editingFile.originalFile.name}`}
          onSave={blob => handleSaveSanitized(blob)}
          onSaveAndNext={nextFile ? blob => handleSaveSanitized(blob, true) : undefined}
        />
      )}
    </Box>
  );
}
