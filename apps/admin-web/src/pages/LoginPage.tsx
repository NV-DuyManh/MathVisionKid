import React, { useState, useEffect, useRef } from 'react';
import { Box, Card, CardContent, Typography, TextField, Button, Alert, InputAdornment, IconButton, CircularProgress } from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import AdminPanelSettingsOutlined from '@mui/icons-material/AdminPanelSettingsOutlined';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { appConfig } from '../config/runtime';
import { errorMessage } from '../components/common/RequestError';
export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const started = useRef(false);
  const submitLock = useRef(false);
  const { login, loginWithSsoTicket, isAuthenticated, sessionError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const requested = (location.state as { from?: { pathname?: string } })?.from?.pathname;
  const from = requested && /^\/(dashboard|users|classes|audit|recognition)(\/|$)/.test(requested) ? requested : '/dashboard';
  useEffect(() => {
    if (started.current) return;
    const params = new URLSearchParams(window.location.hash.slice(1));
    const code = params.get('sso');
    if (!code) { if (isAuthenticated) navigate(from, { replace: true }); return; }
    started.current = true;
    window.history.replaceState({}, document.title, window.location.pathname);
    setBusy(true);
    void loginWithSsoTicket(code).then(() => navigate(from, { replace: true })).catch(cause => {
      setError(cause?.response ? 'Mã chuyển tiếp không hợp lệ, đã dùng hoặc đã hết hạn. Vui lòng đăng nhập lại qua Portal.' : errorMessage(cause));
    }).finally(() => setBusy(false));
  }, [loginWithSsoTicket, navigate, from, isAuthenticated]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitLock.current || busy) return;
    submitLock.current = true; setBusy(true); setError('');
    try { await login(email, password); navigate(from, { replace: true }); }
    catch (cause: any) {
      if (cause?.code === 'ROLE_FORBIDDEN') navigate('/403', { replace: true });
      else setError(cause?.response?.status === 401 ? 'Email hoặc mật khẩu chưa đúng.' : errorMessage(cause));
    } finally { setPassword(''); setBusy(false); submitLock.current = false; }
  };
  return <Box sx={{ minHeight: '100dvh', display: 'grid', placeItems: 'center', p: 2, bgcolor: '#F8FAFC' }}>
    <Card sx={{ width: '100%', maxWidth: 460, borderRadius: 3, border: '1px solid #E2E8F0', boxShadow: '0 4px 20px -2px rgba(15,23,42,0.06)' }}><CardContent sx={{ p: { xs: 3, sm: 5 } }}>
      <Box sx={{ color: 'primary.main', mb: 2 }}><AdminPanelSettingsOutlined sx={{ fontSize: 36 }} /></Box>
      <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: 2, fontWeight: 700 }}>MATHVISION KIDS / ADMIN</Typography>
      <Typography component="h1" variant="h5" sx={{ mt: 0.5, mb: 0.5, fontWeight: 800, color: '#0F172A' }}>Không gian quản trị</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Quản lý vận hành, tài khoản và giám sát toàn hệ thống.</Typography>
      {(error || sessionError) && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error || sessionError}</Alert>}
      <Box component="form" onSubmit={submit} sx={{ display: 'grid', gap: 2 }} aria-busy={busy}>
        <TextField label="Email quản trị" type="email" required autoComplete="username" value={email} disabled={busy} onChange={e => setEmail(e.target.value)} fullWidth />
        <TextField label="Mật khẩu" type={visible ? 'text' : 'password'} required autoComplete="current-password" value={password} disabled={busy} onChange={e => setPassword(e.target.value)} fullWidth
          slotProps={{ input: { endAdornment: <InputAdornment position="end"><IconButton aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} onClick={() => setVisible(!visible)} edge="end">{visible ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment> } }} />
        <Button type="submit" variant="contained" disabled={busy} startIcon={busy ? <CircularProgress size={18} color="inherit" /> : undefined} sx={{ py: 1.25, fontWeight: 700 }}>{busy ? 'Đang xác thực…' : 'Đăng nhập quản trị'}</Button>
        <Button component="a" href={`${appConfig.portalOrigin}/admin`} variant="outlined" sx={{ py: 1.1, fontWeight: 600 }}>Tiếp tục qua cổng MathVision Kids</Button>
      </Box>
    </CardContent></Card>
  </Box>;
}
