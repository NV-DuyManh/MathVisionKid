import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  InputAdornment,
  IconButton,
  Divider,
} from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      const message =
        e.response?.data?.error?.message ||
        e.message ||
        'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin đăng nhập.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDevQuickFill = () => {
    setEmail('admin.demo@mathvision.local');
    setPassword('MathVision123!');
    setError(null);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#F8FAFC',
        px: 2,
      }}
    >
      <Card sx={{ maxWidth: 420, width: '100%', p: 1, borderRadius: 3 }}>
        <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
          {/* Header */}
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3, textAlign: 'center' }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2.5,
                bgcolor: '#0F172A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF',
                mb: 1.5,
              }}
            >
              <AdminPanelSettingsIcon fontSize="medium" />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#0F172A' }}>
              Cổng Quản Trị Hệ Thống
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
              MathVision Kids — Admin Portal
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2.5, fontSize: '0.875rem' }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              label="Email quản trị viên"
              type="email"
              fullWidth
              size="small"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              sx={{ mb: 2 }}
            />

            <TextField
              label="Mật khẩu"
              type={showPassword ? 'text' : 'password'}
              fullWidth
              size="small"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              sx={{ mb: 3 }}
              slotProps={{
                input: {
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        size="small"
                        aria-label="Ẩn/hiện mật khẩu"
                      >
                        {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                      </IconButton>
                    </InputAdornment>
                  ),
                },
              }}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              disabled={loading}
              sx={{
                bgcolor: '#0F172A',
                py: 1.2,
                fontWeight: 600,
                fontSize: '0.95rem',
                '&:hover': { bgcolor: '#1E293B' },
              }}
            >
              {loading ? 'Đang xác thực...' : 'Đăng nhập Quản trị'}
            </Button>
          </form>

          {/* Dev Mode Helper */}
          <Divider sx={{ my: 3 }}>
            <Typography variant="caption" sx={{ color: '#94A3B8', px: 1 }}>
              TÀI KHOẢN MẪU DEV
            </Typography>
          </Divider>

          <Button
            variant="outlined"
            fullWidth
            size="small"
            onClick={handleDevQuickFill}
            startIcon={<FlashOnIcon sx={{ color: '#F59E0B' }} />}
            sx={{
              borderColor: '#CBD5E1',
              color: '#334155',
              fontSize: '0.8rem',
              py: 0.8,
              '&:hover': {
                borderColor: '#94A3B8',
                bgcolor: '#F1F5F9',
              },
            }}
          >
            Điền tài khoản Admin mẫu
          </Button>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#94A3B8', display: 'block' }}>
              Hệ thống không hỗ trợ đăng ký tự do. Tài khoản được cấp bởi Quản trị viên.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};
