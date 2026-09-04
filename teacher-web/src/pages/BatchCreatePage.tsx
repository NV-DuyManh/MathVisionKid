import { useState } from 'react';
import { Box, Typography, Button, Card, CardContent, Grid, IconButton, Tooltip } from '@mui/material';
import { CloudUpload, Close, AddPhotoAlternate } from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { MockTeacherService } from '../services/api/MockTeacherService';

export default function BatchCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const assignmentId = location.state?.assignmentId || 'a1';
  // Mock state: Array of fake file objects to represent thumbnails
  const [selectedFiles, setSelectedFiles] = useState<{id: number, name: string}[]>([]);

  const handleMockUploadSelect = () => {
    // Generate 30 mock files for demo
    const files = Array.from({ length: 30 }, (_, i) => ({ id: i, name: `bai_lam_${i+1}.jpg` }));
    setSelectedFiles(files);
  };

  const removeFile = (idToRemove: number) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== idToRemove));
  };

  const handleStartProcessing = async () => {
    if (selectedFiles.length === 0) return;
    const batch = await MockTeacherService.createBatch(assignmentId, selectedFiles.length);
    MockTeacherService.uploadImages(batch.id, []); 
    navigate(`/batches/${batch.id}`);
  };

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', mt: 4 }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'text.primary' }}>Tải ảnh bài làm</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Tải lên tối đa 30 ảnh cho mỗi đợt chấm.</Typography>
      
      {selectedFiles.length === 0 ? (
        <Card sx={{ borderStyle: 'dashed', borderWidth: 2, borderColor: 'primary.light', bgcolor: 'primary.50', mb: 4, transition: 'background-color 150ms', '&:hover': { bgcolor: 'primary.100' } }}>
          <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8, cursor: 'pointer' }} onClick={handleMockUploadSelect}>
            <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" color="primary.main">Kéo ảnh bài làm vào đây</Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>Hoặc click để chọn từ máy tính (Tạo 30 ảnh mẫu)</Typography>
          </CardContent>
        </Card>
      ) : (
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" color="text.primary">
              Đã chọn {selectedFiles.length} ảnh
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" color="error" onClick={() => setSelectedFiles([])}>Xóa tất cả</Button>
              <Button variant="contained" size="large" onClick={handleStartProcessing}>Bắt đầu chấm ({selectedFiles.length})</Button>
            </Box>
          </Box>
          
          <Card sx={{ p: 2, bgcolor: 'background.default', border: '1px solid', borderColor: 'divider' }}>
            <Grid container spacing={2}>
              {selectedFiles.map((file) => (
                <Grid size={{ xs: 4, sm: 3, md: 2, lg: 1.5 }} key={file.id}>
                  <Box sx={{ 
                    position: 'relative', 
                    paddingTop: '100%', // 1:1 aspect ratio
                    bgcolor: 'grey.200',
                    borderRadius: 1,
                    overflow: 'hidden',
                    border: '1px solid',
                    borderColor: 'grey.300',
                    '&:hover .remove-btn': { opacity: 1 }
                  }}>
                    <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                      <AddPhotoAlternate sx={{ color: 'grey.400' }} />
                      <Typography variant="caption" sx={{ color: 'grey.600', mt: 0.5, fontSize: '0.65rem', px: 1, textAlign: 'center', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', width: '100%' }}>
                        {file.name}
                      </Typography>
                    </Box>
                    <Tooltip title="Xóa ảnh">
                      <IconButton 
                        className="remove-btn"
                        aria-label={`Xóa ảnh ${file.name}`}
                        size="small" 
                        onClick={() => removeFile(file.id)}
                        sx={{ 
                          position: 'absolute', top: 2, right: 2, bgcolor: 'rgba(0,0,0,0.5)', color: 'white', opacity: 0, transition: 'opacity 150ms',
                          '&:hover': { bgcolor: 'error.main' },
                          width: 24, height: 24
                        }}
                      >
                        <Close sx={{ fontSize: 14 }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Card>
        </Box>
      )}
    </Box>
  );
}
