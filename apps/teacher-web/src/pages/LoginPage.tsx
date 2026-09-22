import { Box, Button, Card, CardContent, Typography, TextField, Alert, InputAdornment, IconButton, CircularProgress, Divider } from '@mui/material';
import { Visibility, VisibilityOff, School } from '@mui/icons-material';
import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import apiClient from '../services/api/apiClient';
import { AuthTokenStore } from '../services/api/AuthTokenStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('lan.teacher@mathvision.local');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Handle SSO Ticket Exchange if redirected from Unified Portal (URL Fragment #sso= preferred)
  useEffect(() => {
    let ssoCode: string | null = null;
    const hash = window.location.hash;
    if (hash && hash.includes('sso=')) {
      const match = hash.match(/sso=([^&]*)/);
      if (match) {
        ssoCode = decodeURIComponent(match[1]);
      }
    }
    // Backward compatibility fallback to query param
    if (!ssoCode) {
      ssoCode = searchParams.get('code');
    }
    // Handle SSO Ticket Exchange if redirected from Unified Portal (URL Fragment #sso= preferred)
    if (!ssoCode) {
      const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
      const hasFallbackParam = searchParams.get('fallback') === 'true' || searchParams.get('direct') === 'true';
      const isAllowedFallback = showDevTools && hasFallbackParam;

      if (!isAllowedFallback) {
        window.location.href = 'http://localhost:5172/';
        return;
      }
      return;
    }

    // IMMEDIATELY scrub the URL (fragment or query) before any network operation
    window.history.replaceState({}, document.title, window.location.pathname);

    const exchangeTicket = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await apiClient.post('/auth/sso/exchange', {
          code: ssoCode,
          targetApp: 'TEACHER',
        });
        const { accessToken, refreshToken } = res.data;
        if (accessToken && refreshToken) {
          AuthTokenStore.setTokens(accessToken, refreshToken);
        }
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        setError(
          err.response?.data?.message ||
          'Mã xác thực chuyển giao (SSO) không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại qua Portal.'
        );
      } finally {
        setLoading(false);
      }
    };

    exchangeTicket();
  }, [searchParams, navigate]);

  const handleLogin = async (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!email || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await AppTeacherService.login(email, password);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Đăng nhập không thành công. Vui lòng kiểm tra lại email hoặc mật khẩu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#F8FAFC',
        p: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: 420,
          width: '100%',
          p: { xs: 2, sm: 3 },
          boxShadow: '0 4px 16px rgba(15, 23, 42, 0.08)',
          border: '1px solid #E2E8F0',
          borderRadius: 3,
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <Box
              sx={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                bgcolor: '#EFF6FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1.5px solid #BFDBFE',
              }}
            >
              <School sx={{ fontSize: 32, color: '#2563EB' }} />
            </Box>
          </Box>

          <Typography variant="h5" sx={{ fontWeight: 800, textAlign: 'center', color: '#2563EB', letterSpacing: '-0.02em', mb: 0.5 }}>
            MathVision<span style={{ color: '#0D9488' }}>Kids</span>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', fontWeight: 600, mb: 0.5 }}>
            CỔNG GIÁO VIÊN TIỂU HỌC
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mb: 3 }}>
            Đăng nhập để quản lý lớp, bài tập và duyệt bài chấm AI
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2.5, borderRadius: 2 }} role="alert">
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleLogin} noValidate>
            <TextField
              fullWidth
              id="email"
              label="Địa chỉ Email"
              variant="outlined"
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
              autoFocus
              slotProps={{
                htmlInput: { 'aria-label': 'Địa chỉ Email giáo viên' },
              }}
            />

            <TextField
              fullWidth
              id="password"
              label="Mật khẩu"
              type={showPassword ? 'text' : 'password'}
              variant="outlined"
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
              placeholder="Nhập mật khẩu của bạn"
              slotProps={{
                htmlInput: { 'aria-label': 'Mật khẩu' },
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
              size="large"
              sx={{
                mt: 3,
                mb: 1.5,
                py: 1.25,
                fontWeight: 700,
                fontSize: '0.95rem',
              }}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
            >
              {loading ? 'Đang đăng nhập...' : 'Đăng nhập vào hệ thống'}
            </Button>

            <Divider sx={{ my: 2 }}>
              <Typography variant="caption" sx={{ color: '#94A3B8', fontWeight: 600 }}>
                HOẶC ĐĂNG NHẬP CHÍNH THỨC
              </Typography>
            </Divider>

            <Button
              fullWidth
              variant="outlined"
              component="a"
              href="http://localhost:5172/login"
              sx={{
                py: 1.1,
                fontWeight: 600,
                fontSize: '0.9rem',
                borderColor: '#4F46E5',
                color: '#4F46E5',
                '&:hover': {
                  borderColor: '#4338CA',
                  bgcolor: '#EEF2FF',
                },
              }}
            >
              Đăng nhập qua MathVision Kids
            </Button>

            <Box sx={{ mt: 2.5, textAlign: 'center' }}>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                <a
                  href="http://localhost:5172"
                  style={{ color: '#64748B', textDecoration: 'none', fontWeight: 500 }}
                >
                  ← Về Trang chủ MathVision Kids
                </a>
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
