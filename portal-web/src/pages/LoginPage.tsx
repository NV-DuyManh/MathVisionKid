import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import LoginIcon from '@mui/icons-material/Login';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';

  // Display session expired notice if redirected after expiry
  useEffect(() => {
    if (searchParams.get('expired') === 'true' || searchParams.get('session') === 'expired') {
      setError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      return;
    }

    if (tokenStore.hasTokens()) {
      authService.getMe().then((user) => {
        const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';
        if (role === 'STUDENT') {
          navigate('/student', { replace: true });
        } else if (role === 'TEACHER') {
          authService.requestSsoTicket('TEACHER').then((ticket) => {
            window.location.href = `http://localhost:5173/login#sso=${encodeURIComponent(ticket.code)}`;
          });
        } else if (role === 'ADMIN') {
          authService.requestSsoTicket('ADMIN').then((ticket) => {
            window.location.href = `http://localhost:5174/login#sso=${encodeURIComponent(ticket.code)}`;
          });
        }
      }).catch(() => {
        tokenStore.clearTokens();
      });
    }
  }, [searchParams, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const user = await authService.login(email.trim(), password);
      const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';

      switch (role) {
        case 'STUDENT':
          navigate('/student');
          break;
        case 'TEACHER': {
          const ticket = await authService.requestSsoTicket('TEACHER');
          window.location.href = `http://localhost:5173/login#sso=${encodeURIComponent(ticket.code)}`;
          break;
        }
        case 'ADMIN': {
          const ticket = await authService.requestSsoTicket('ADMIN');
          window.location.href = `http://localhost:5174/login#sso=${encodeURIComponent(ticket.code)}`;
          break;
        }
        default:
          tokenStore.clearTokens();
          setError('Tài khoản không có quyền truy cập hệ thống.');
          setLoading(false);
          break;
      }
    } catch (err: any) {
      setLoading(false);
      if (err.response?.status === 401 || err.response?.status === 400) {
        setError('Tài khoản hoặc mật khẩu chưa đúng.');
      } else {
        setError(err.response?.data?.message || err.message || 'Không thể kết nối đến máy chủ xác thực.');
      }
    }
  };

  const fillCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 3.5, sm: 5 }, borderRadius: 4, boxShadow: '0 10px 30px rgba(0, 0, 0, 0.06)' }}>
        <Box sx={{ textAlign: 'center', mb: 3.5 }}>
          <Box
            component="img"
            src="/logo.svg"
            alt="MathVision Kids"
            sx={{ width: 60, height: 60, mb: 1.5, borderRadius: 3 }}
          />
          <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 0.5 }}>
            Đăng nhập MathVision Kids
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Nhập tài khoản của bạn để tiếp tục
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleLogin} noValidate>
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email"
            name="email"
            autoComplete="email"
            autoFocus
            value={email}
            disabled={loading}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email@mathvision.local"
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="Mật khẩu"
            type={showPassword ? 'text' : 'password'}
            id="password"
            autoComplete="current-password"
            value={password}
            disabled={loading}
            onChange={(e) => setPassword(e.target.value)}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiển thị mật khẩu'}
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            size="large"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
            sx={{ mt: 3, mb: 1.5, py: 1.5, fontSize: '1.05rem', borderRadius: 2.5, fontWeight: 700 }}
          >
            {loading ? 'Đang xác thực...' : 'Đăng nhập'}
          </Button>
        </Box>

        {/* Developer Demo Tools — Rendered ONLY when VITE_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <Box sx={{ mt: 3 }}>
            <Accordion sx={{ bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '12px !important', '&:before': { display: 'none' } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DeveloperModeIcon sx={{ fontSize: 18, color: '#D97706' }} />
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Công cụ Developer Demo (Dev Only)
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1.5 }}>
                  Điền nhanh tài khoản kiểm thử cho môi trường phát triển:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  <Chip
                    label="Học sinh (minh.student)"
                    onClick={() => fillCredentials('minh.student@mathvision.local', 'Student@123')}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 600 }}
                  />
                  <Chip
                    label="Giáo viên (lan.teacher)"
                    onClick={() => fillCredentials('lan.teacher@mathvision.local', 'Teacher@123')}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 600 }}
                  />
                  <Chip
                    label="Quản trị (admin)"
                    onClick={() => fillCredentials('admin@mathvision.local', 'Admin@123')}
                    size="small"
                    color="secondary"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 600 }}
                  />
                </Box>
              </AccordionDetails>
            </Accordion>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default LoginPage;
