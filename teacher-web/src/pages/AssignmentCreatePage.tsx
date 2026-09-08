import { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, MenuItem, Card, CardContent } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { Class } from '../types';
import { MathType } from '../types';

export default function AssignmentCreatePage() {
  const navigate = useNavigate();
  const [classes, setClasses] = useState<Class[]>([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [title, setTitle] = useState('');
  const [mathType, setMathType] = useState<MathType>(MathType.VERTICAL_ADDITION);

  useEffect(() => {
    AppTeacherService.getClasses().then(setClasses);
  }, []);

  const handleCreate = async () => {
    if (!selectedClass || !title) return;
    const assignment = await AppTeacherService.createAssignment(selectedClass, title, mathType);
    navigate('/batches/create', { state: { assignmentId: assignment.assignmentId || assignment.id } });
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Card>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" sx={{ mb: 4 }}>Tạo bài tập mới</Typography>
          
          <TextField 
            select 
            fullWidth 
            label="Lớp học" 
            value={selectedClass} 
            onChange={e => setSelectedClass(e.target.value)}
            sx={{ mb: 3 }}
          >
            {classes.map(c => (
              <MenuItem key={c.id} value={c.id}>Lớp {c.name}</MenuItem>
            ))}
          </TextField>

          <TextField 
            fullWidth 
            label="Tên bài tập" 
            value={title} 
            onChange={e => setTitle(e.target.value)}
            placeholder="VD: Phép cộng có nhớ"
            sx={{ mb: 3 }}
          />

          <TextField 
            select 
            fullWidth 
            label="Loại toán" 
            value={mathType} 
            onChange={e => setMathType(e.target.value as MathType)}
            sx={{ mb: 4 }}
          >
            <MenuItem value={MathType.VERTICAL_ADDITION}>Phép cộng đặt tính</MenuItem>
            <MenuItem value={MathType.VERTICAL_SUBTRACTION}>Phép trừ đặt tính</MenuItem>
          </TextField>

          <Button 
            variant="contained" 
            size="large" 
            fullWidth 
            onClick={handleCreate}
            disabled={!selectedClass || !title}
          >
            Tạo bài tập và chuyển sang Lượt chấm
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
