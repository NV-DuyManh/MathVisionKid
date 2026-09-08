import { useState, useEffect } from 'react';
import { Box, Typography, Button, Card, CardContent, Grid, IconButton, Tooltip, Select, MenuItem, FormControl, InputLabel, Alert } from '@mui/material';
import { CloudUpload, Close, PrivacyTip, CheckCircle, Refresh } from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import PrivacyEditorModal from './PrivacyEditorModal';
// import type { Class } from '../types';

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
  const [roster, setRoster] = useState<{id: string, name: string}[]>([]);
  const [editingFile, setEditingFile] = useState<FileState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    const fetchClass = async () => {
      try {
        const classes = await AppTeacherService.getClasses();
        // Just mock a roster based on first class's student count
        if (classes.length > 0) {
            const cls = classes[0]; // Or fetch actual assignment's class if we had an endpoint
            const students = Array.from({length: cls.studentCount}, (_, i) => ({
                id: `st_${i+1}`,
                name: `Học sinh ${i+1}`
            }));
            setRoster(students);
        }
      } catch(err) {
        console.error(err);
      }
    };
    fetchClass();
    
    // Cleanup URLs on unmount
    return () => {
      files.forEach(f => URL.revokeObjectURL(f.previewUrl));
    };
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        originalFile: file,
        sanitizedBlob: null,
        studentId: '',
        previewUrl: URL.createObjectURL(file)
      }));
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (idToRemove: string) => {
    setFiles(prev => {
      const f = prev.find(x => x.id === idToRemove);
      if (f) URL.revokeObjectURL(f.previewUrl);
      return prev.filter(x => x.id !== idToRemove);
    });
  };

  const handleReplaceFile = (idToReplace: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      setFiles(prev => prev.map(f => {
        if (f.id === idToReplace) {
          URL.revokeObjectURL(f.previewUrl);
          return {
            ...f,
            originalFile: file,
            sanitizedBlob: null, // Reset privacy state
            previewUrl: URL.createObjectURL(file)
          };
        }
        return f;
      }));
    }
  };

  const updateStudent = (id: string, studentId: string) => {
    setFiles(prev => prev.map(f => f.id === id ? { ...f, studentId } : f));
  };

  const handleSaveSanitized = (blob: Blob) => {
    if (editingFile) {
      setFiles(prev => prev.map(f => f.id === editingFile.id ? { 
        ...f, 
        sanitizedBlob: blob,
        previewUrl: URL.createObjectURL(blob) // update preview to sanitized version
      } : f));
    }
    setEditingFile(null);
  };

  const handleStartProcessing = async () => {
    setError(null);
    if (files.length < 10) {
      setError('Phải tải lên ít nhất 10 ảnh.');
      return;
    }
    if (files.length > 30) {
      setError('Chỉ được tải lên tối đa 30 ảnh.');
      return;
    }
    if (files.some(f => !f.studentId)) {
      setError('Vui lòng chọn học sinh cho tất cả các bài làm.');
      return;
    }
    if (files.some(f => !f.sanitizedBlob)) {
      setError('Vui lòng che thông tin (Privacy Gate) cho tất cả các bài làm.');
      return;
    }

    try {
      setUploading(true);
      const batch = await AppTeacherService.createBatch(assignmentId, files.length);
      
      const uploadFiles = files.map(f => new File([f.sanitizedBlob!], f.originalFile.name, { type: f.originalFile.type }));
      const mappings = files.map((f, i) => ({ fileIndex: i, studentId: f.studentId }));
      
      await AppTeacherService.uploadImages(batch.batchId || batch.id || '', uploadFiles, mappings);
      navigate(`/batches/${batch.batchId || batch.id}`);
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Có lỗi xảy ra khi tạo lượt chấm.');
      setUploading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', mt: 4 }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'text.primary' }}>Tải ảnh bài làm & Che thông tin</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Tải lên từ 10 đến 30 ảnh, che thông tin cá nhân và ghép cặp với học sinh.</Typography>
      
      {error && <Alert severity="error" sx={{ mb: 4 }}>{error}</Alert>}

      {files.length === 0 ? (
        <Card sx={{ borderStyle: 'dashed', borderWidth: 2, borderColor: 'primary.light', bgcolor: 'primary.50', mb: 4 }}>
          <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Button variant="contained" component="label" size="large">
              Chọn ảnh từ máy tính
              <input type="file" hidden multiple accept="image/*" onChange={handleFileSelect} />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" color="text.primary">
              Đã chọn {files.length}/30 ảnh
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" component="label">
                Thêm ảnh
                <input type="file" hidden multiple accept="image/*" onChange={handleFileSelect} />
              </Button>
              <Button variant="contained" size="large" onClick={handleStartProcessing} disabled={uploading}>
                {uploading ? 'Đang tải lên...' : 'Bắt đầu chấm'}
              </Button>
            </Box>
          </Box>
          
          <Grid container spacing={3}>
            {files.map((file) => (
              <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={file.id}>
                <Card variant="outlined" sx={{ position: 'relative' }}>
                  <Box sx={{ position: 'absolute', top: 4, right: 4, zIndex: 10, display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Thay thế ảnh">
                      <IconButton 
                        component="label"
                        size="small" 
                        sx={{ bgcolor: 'rgba(255,255,255,0.8)', '&:hover': { bgcolor: 'primary.main', color: 'white' } }}
                      >
                        <Refresh sx={{ fontSize: 16 }} />
                        <input type="file" hidden accept="image/*" onChange={(e) => handleReplaceFile(file.id, e)} />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Xóa ảnh">
                      <IconButton 
                        size="small" 
                        onClick={() => removeFile(file.id)}
                        sx={{ bgcolor: 'rgba(255,255,255,0.8)', '&:hover': { bgcolor: 'error.main', color: 'white' } }}
                      >
                        <Close sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  
                  <Box sx={{ position: 'relative', paddingTop: '75%', bgcolor: 'grey.200', overflow: 'hidden' }}>
                    <img 
                      src={file.previewUrl} 
                      alt="Preview" 
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'contain' }} 
                    />
                    {file.sanitizedBlob && (
                      <Box sx={{ position: 'absolute', bottom: 8, right: 8, bgcolor: 'success.main', color: 'white', px: 1, py: 0.5, borderRadius: 1, display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.75rem' }}>
                        <CheckCircle sx={{ fontSize: 14 }} /> Đã che
                      </Box>
                    )}
                  </Box>
                  
                  <CardContent sx={{ p: 2 }}>
                    <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                      <InputLabel>Học sinh</InputLabel>
                      <Select
                        value={file.studentId}
                        label="Học sinh"
                        onChange={(e) => updateStudent(file.id, e.target.value)}
                      >
                        {roster.map(st => (
                          <MenuItem key={st.id} value={st.id}>{st.name}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    
                    <Button 
                      fullWidth 
                      variant={file.sanitizedBlob ? "outlined" : "contained"} 
                      color={file.sanitizedBlob ? "primary" : "warning"}
                      startIcon={<PrivacyTip />}
                      onClick={() => setEditingFile(file)}
                    >
                      {file.sanitizedBlob ? "Sửa vùng che" : "Che thông tin (Bắt buộc)"}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
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
