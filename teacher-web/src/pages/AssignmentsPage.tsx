import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function AssignmentsPage() {
  const navigate = useNavigate();

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h5">Bài tập</Typography>
        <Button variant="contained" onClick={() => navigate('/assignments/create')}>
          + Tạo bài tập
        </Button>
      </Box>
      <Typography color="text.secondary">Danh sách bài tập sẽ hiển thị ở đây (chưa tích hợp Mock đầy đủ cho danh sách này).</Typography>
    </Box>
  );
}
