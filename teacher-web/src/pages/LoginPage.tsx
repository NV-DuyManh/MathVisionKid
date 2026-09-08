import { Box, Button, Card, CardContent, Typography, TextField, Alert } from '@mui/material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('lan.teacher@mathvision.local');
  const [password, setPassword] = useState('MathVision123!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      await AppTeacherService.login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Đăng nhập thất bại. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

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

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <TextField fullWidth label="Email" variant="outlined" margin="normal" value={email} onChange={e => setEmail(e.target.value)} />
          <TextField fullWidth label="Mật khẩu" type="password" variant="outlined" margin="normal" value={password} onChange={e => setPassword(e.target.value)} />

          <Button 
            fullWidth 
            variant="contained" 
            size="large" 
            sx={{ mt: 3, mb: 2 }}
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
