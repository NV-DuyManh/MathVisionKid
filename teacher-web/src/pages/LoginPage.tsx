import { Box, Button, Card, CardContent, Typography, TextField } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default' }}>
      <Card sx={{ maxWidth: 400, width: '100%', p: 2 }}>
        <CardContent>
          <Typography variant="h5" color="primary" sx={{ fontWeight: 800, textAlign: 'center', mb: 1 }}>
            MathVision<span style={{ color: '#14B8A6' }}>Kids</span>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 4 }}>
            Cổng quản lý dành cho Giáo viên
          </Typography>

          <TextField fullWidth label="Email" variant="outlined" margin="normal" defaultValue="teacher@mathvision.vn" />
          <TextField fullWidth label="Mật khẩu" type="password" variant="outlined" margin="normal" defaultValue="password" />

          <Button 
            fullWidth 
            variant="contained" 
            size="large" 
            sx={{ mt: 3, mb: 2 }}
            onClick={() => navigate('/dashboard')}
          >
            Đăng nhập
          </Button>

          <Button 
            fullWidth 
            variant="outlined" 
            color="secondary"
            onClick={() => navigate('/dashboard')}
          >
            Demo giáo viên
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
