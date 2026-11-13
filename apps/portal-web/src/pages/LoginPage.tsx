import React, { useState, useEffect, useRef } from 'react';
import {
  Paper,
  Box,
  Typography,
  TextField,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Chip,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';
import ArrowBack from '@mui/icons-material/ArrowBack';
import LoginIcon from '@mui/icons-material/Login';
import GoogleIcon from '@mui/icons-material/Google';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';
import { appConfig, googleConfigured, showDevTools } from '../config/runtime';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmRegisterPassword, setConfirmRegisterPassword] = useState('');
  const [role, setRole] = useState<'STUDENT' | 'TEACHER'>('STUDENT');
  const [gender, setGender] = useState<'MALE' | 'FEMALE' | 'OTHER' | 'PREFER_NOT_TO_SAY'>('PREFER_NOT_TO_SAY');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [gradeLevel, setGradeLevel] = useState('1');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [authView, setAuthView] = useState<'login' | 'register' | 'request-reset' | 'confirm-reset' | 'social-student-setup'>('login');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [socialSetupCredential, setSocialSetupCredential] = useState('');
  const [socialSetupGrade, setSocialSetupGrade] = useState('1');
  const sessionCheck = useRef<AbortController | null>(null);
  const submitLock = useRef(false);
  const beginSubmission = () => {
    if (submitLock.current) return false;
    submitLock.current = true;
    sessionCheck.current?.abort();
    return true;
  };

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const socialRequestedRole = searchParams.get('role') === 'TEACHER' ? 'TEACHER' : undefined;

  // Display session expired notice if redirected after expiry
  useEffect(() => {
    const controller = new AbortController();
    sessionCheck.current = controller;
    if (searchParams.get('connection') === 'failed') {
      setError('Chưa kết nối được máy chủ. Vui lòng kiểm tra kết nối và đăng nhập lại.');
      return () => controller.abort();
    }
    if (searchParams.get('expired') === 'true' || searchParams.get('session') === 'expired') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      return () => controller.abort();
    }

    if (tokenStore.hasTokens()) {
      authService.getMe(controller.signal).then(async (user) => {
        if (controller.signal.aborted) return;
        const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';
        if (role === 'STUDENT') {
          window.location.replace('/study/');
        } else if (role === 'TEACHER') {
          const ticket = await authService.requestSsoTicket('TEACHER', controller.signal);
          if (!controller.signal.aborted) {
            window.location.href = `${appConfig.teacherOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
          }
        } else if (role === 'ADMIN') {
          const ticket = await authService.requestSsoTicket('ADMIN', controller.signal);
          if (!controller.signal.aborted) {
            window.location.href = `${appConfig.adminOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
          }
        }
      }).catch(() => {
        if (!controller.signal.aborted) tokenStore.clearTokens();
      });
    }
    return () => controller.abort();
  }, [searchParams, navigate]);

  const handleGoogleLogin = async () => {
    if (!beginSubmission()) return;
    const name = 'Google';
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const { getGoogleCredential } = await import('../services/socialAuth');
      const credential = await getGoogleCredential();
      try {
        const user = await authService.loginWithGoogle(credential, socialRequestedRole);
        if (user.role === 'STUDENT') window.location.replace('/study/');
        else if (user.role === 'TEACHER' || user.role === 'ADMIN') {
          const origin = user.role === 'TEACHER' ? appConfig.teacherOrigin : appConfig.adminOrigin;
          const ticket = await authService.requestSsoTicket(user.role);
          window.location.href = origin + '/login#sso=' + encodeURIComponent(ticket.code);
        } else {
          tokenStore.clearTokens();
          setError('Tài khoản không có quyền truy cập hệ thống.');
        }
      } catch (err: any) {
        const code = err.response?.data?.error?.code;
        if (code === name.toUpperCase() + '_STUDENT_GRADE_REQUIRED') {
          setSocialSetupCredential(credential);
          setAuthView('social-student-setup');
          setSuccess(name + ' đã được xác minh. Chọn lớp để hoàn tất tạo tài khoản học sinh.');
        } else if (code === 'GOOGLE_ACCOUNT_CONFLICT') {
          setError('Email này đã có tài khoản. Hãy đăng nhập bằng phương thức đã đăng ký.');
        } else if (err.response?.status === 403) {
          setError('Tài khoản này đang bị khóa hoặc không có quyền truy cập.');
        } else {
          setError('Chưa đăng nhập được bằng ' + name + '. Vui lòng thử lại.');
        }
      }
    } catch (err: any) {
      if (err.code === 'auth/account-exists-with-different-credential') {
        setError('Email này đã liên kết với phương thức đăng nhập khác. Hãy dùng phương thức đó.');
      } else if (err.code === 'auth/popup-blocked') {
        setError('Trình duyệt đã chặn cửa sổ ' + name + '. Hãy cho phép cửa sổ bật lên rồi thử lại.');
      } else if (err.code === 'auth/network-request-failed') {
        setError('Chưa kết nối được dịch vụ đăng nhập. Hãy kiểm tra mạng rồi thử lại.');
      } else if (err.code !== 'auth/popup-closed-by-user' && err.code !== 'auth/cancelled-popup-request') {
        setError('Chưa mở được ' + name + '. Hãy dùng email hoặc thử lại sau.');
      }
    } finally {
      submitLock.current = false;
      setLoading(false);
    }
  };

  const handleSocialStudentSetup = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!socialSetupCredential) {
      setError('Phiên xác minh đã hết. Hãy đăng nhập lại.');
      setAuthView('login');
      return;
    }
    if (!beginSubmission()) return;
    setLoading(true);
    setError(null);
    try {
      const user = await authService.loginWithGoogle(socialSetupCredential, 'STUDENT', Number(socialSetupGrade));
      setSocialSetupCredential('');
      if (user.role.toUpperCase().replace('ROLE_', '') === 'STUDENT') window.location.replace('/study/');
      else {
        tokenStore.clearTokens();
        setError('Tài khoản này không thuộc cổng học sinh.');
      }
    } catch {
      setError('Chưa tạo được tài khoản học sinh. Hãy thử đăng nhập lại.');
    } finally {
      submitLock.current = false;
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitLock.current) return;
    if (!email.trim() || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }

    if (!beginSubmission()) return;
    setLoading(true);
    setError(null);

    try {
      const user = await authService.login(email.trim(), password);
      const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';

      switch (role) {
        case 'STUDENT':
          window.location.replace('/study/');
          break;
        case 'TEACHER': {
          const ticket = await authService.requestSsoTicket('TEACHER');
          window.location.href = `${appConfig.teacherOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
          break;
        }
        case 'ADMIN': {
          const ticket = await authService.requestSsoTicket('ADMIN');
          window.location.href = `${appConfig.adminOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
          break;
        }
        default:
          submitLock.current = false;
          tokenStore.clearTokens();
          setError('Tài khoản không có quyền truy cập hệ thống.');
          setLoading(false);
          break;
      }
    } catch (err: any) {
      submitLock.current = false;
      setPassword('');
      setLoading(false);
      if (err.response?.status === 401 || err.response?.status === 400) {
        setError('Tài khoản hoặc mật khẩu chưa đúng.');
      } else if (err.response?.status === 403) {
        setError('Tài khoản chưa được phép truy cập. Vui lòng liên hệ người quản lý tài khoản.');
      } else if (err.response?.status === 429) {
        setError('Bạn đã thử nhiều lần liên tiếp. Vui lòng chờ một chút rồi thử lại.');
      } else if (!err.response) {
        setError('Chưa kết nối được máy chủ. Vui lòng kiểm tra mạng rồi thử lại.');
      } else {
        setError('Máy chủ đang gặp sự cố. Vui lòng thử lại sau.');
      }
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedEmail = email.trim();
    if (!displayName.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError('Vui lòng nhập họ tên và email hợp lệ.');
      return;
    }
    if (registerPassword.length < 8 || registerPassword.length > 72) {
      setError('Mật khẩu phải có từ 8 đến 72 ký tự.');
      return;
    }
    if (registerPassword !== confirmRegisterPassword) {
      setError('Mật khẩu xác nhận không khớp.');
      return;
    }
    if (!/^[+0-9() .-]{7,32}$/.test(phoneNumber.trim())) {
      setError('Vui lòng nhập số điện thoại hợp lệ.');
      return;
    }

    if (!beginSubmission()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await authService.register({
        email: normalizedEmail,
        displayName: displayName.trim(),
        password: registerPassword,
        role,
        gender,
        phoneNumber: phoneNumber.trim(),
        ...(role === 'STUDENT' ? { gradeLevel: Number(gradeLevel) } : {}),
      });
      setAuthView('login');
      setPassword('');
      setRegisterPassword('');
      setConfirmRegisterPassword('');
      setSuccess('Đăng ký thành công. Hãy đăng nhập bằng email và mật khẩu vừa tạo.');
    } catch (err: any) {
      setError(err.response?.status === 409
        ? 'Email này đã được đăng ký. Hãy đăng nhập hoặc dùng chức năng quên mật khẩu.'
        : err.response?.status === 400
          ? 'Thông tin đăng ký chưa hợp lệ. Hãy kiểm tra lại các mục đã nhập.'
          : 'Chưa tạo được tài khoản. Hãy kiểm tra kết nối rồi thử lại.');
    } finally {
      submitLock.current = false;
      setLoading(false);
    }
  };

  const handleRequestPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Nhập email đã đăng ký để nhận mã xác nhận.');
      return;
    }
    if (!beginSubmission()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await authService.requestPasswordReset(email.trim());
      setAuthView('confirm-reset');
      setSuccess('Nếu email đã đăng ký, mã xác nhận sẽ được gửi đến hộp thư đó.');
    } catch (err: any) {
      const errorCode = err.response?.data?.error?.code;
      setError(errorCode === 'EMAIL_DELIVERY_FAILED'
        ? 'Chưa gửi được email xác nhận. Hãy thử lại sau hoặc liên hệ người hỗ trợ.'
        : err.response?.status === 503
          ? 'Dịch vụ gửi email tạm thời chưa sẵn sàng. Hãy thử lại sau.'
          : 'Chưa gửi được mã xác nhận. Hãy kiểm tra kết nối rồi thử lại.');
    } finally {
      submitLock.current = false;
      setLoading(false);
    }
  };

  const handleConfirmPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(resetCode)) {
      setError('Mã xác nhận phải gồm 6 chữ số.');
      return;
    }
    if (newPassword.length < 8 || newPassword.length > 72) {
      setError('Mật khẩu mới phải có từ 8 đến 72 ký tự.');
      return;
    }
    if (!beginSubmission()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await authService.confirmPasswordReset(email.trim(), resetCode, newPassword);
      setAuthView('login');
      setPassword('');
      setResetCode('');
      setNewPassword('');
      setSuccess('Đổi mật khẩu thành công. Hãy đăng nhập bằng mật khẩu mới.');
    } catch (err: any) {
      setError(err.response?.status === 400
        ? 'Mã không đúng hoặc đã hết hạn. Kiểm tra email rồi thử lại.'
        : 'Chưa đổi được mật khẩu. Hãy thử lại sau.');
    } finally {
      submitLock.current = false;
      setLoading(false);
    }
  };

  const fillCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <Box component="main" sx={{ minHeight: '100dvh', bgcolor: '#F3F6FC', p: { xs: 1.5, sm: 3, md: 5 }, display: 'grid', placeItems: 'center' }}>
        <Paper
          elevation={0}
          sx={{
            width: '100%', maxWidth: 940, display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 2fr) minmax(0, 3fr)' },
            borderRadius: { xs: 3, md: 5 }, border: '1px solid #E2E8F0', boxShadow: '0 20px 64px -32px #26427555',
            overflow: 'hidden',
          }}
        >
        <Box sx={{ bgcolor: '#E9F1FF', p: { xs: 2, sm: 3, md: 4 }, display: 'flex', flexDirection: { xs: 'row', md: 'column' }, alignItems: { xs: 'center', md: 'stretch' }, justifyContent: 'space-between', flexWrap: 'wrap', gap: { xs: 0.5, md: 3 } }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
            <Box component="img" src="/logo.svg" alt="" width={32} height={32} />
            <Typography sx={{ fontWeight: 900, color: '#143368' }}>MathVision Kids</Typography>
          </Box>
          <Box component="img" src="/ui/mathvision-star.png" alt="" sx={{ display: { xs: 'none', md: 'block' }, width: '100%', maxWidth: 240, alignSelf: 'center' }} />
          <Button component={RouterLink} to="/" startIcon={<ArrowBack />} sx={{ alignSelf: { md: 'flex-start' }, minHeight: 44, minWidth: 0, textTransform: 'none', px: 1 }}>
            Trang chủ
          </Button>
        </Box>
        <Box sx={{ minWidth: 0, p: { xs: 2.25, sm: 4, md: 5 } }}>
        <Box sx={{ mb: 2.5 }}>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 900, mb: 0.75, fontSize: { xs: '1.65rem', sm: '2rem' }, lineHeight: 1.2 }}>
            {authView === 'login' ? 'Đăng nhập' : authView === 'register' ? 'Tạo tài khoản' : authView === 'social-student-setup' ? 'Chọn lớp của em' : 'Khôi phục mật khẩu'}
          </Typography>
          {authView === 'login' && <Typography color="text.secondary">Dùng tài khoản Học sinh, Giáo viên hoặc Quản trị của bạn.</Typography>}
          {authView === 'social-student-setup' && <Typography color="text.secondary">Chọn khối lớp hiện tại để hoàn tất tài khoản học sinh.</Typography>}
        </Box>

        {error && (
          <Alert id="auth-error" severity="error" role="alert" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}
        {success && <Alert severity="success" role="status" sx={{ mb: 3, borderRadius: 2 }}>{success}</Alert>}

        {authView === 'login' && <Box component="form" onSubmit={handleLogin} aria-busy={loading} aria-describedby={error ? 'auth-error' : undefined}>
          <TextField
            required
            fullWidth
            id="email"
            label="Email"
            name="email"
            type="email"
            autoComplete="username"
            slotProps={{ htmlInput: { autoCapitalize: 'none', spellCheck: false } }}
            value={email}
            disabled={loading}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            sx={{ mt: 2 }}
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
                      type="button"
                      disabled={loading}
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      sx={{ width: 44, height: 44 }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', my: 0.5 }}>
            <Button data-cy="forgot-password" type="button" disabled={loading} onClick={() => { setAuthView('request-reset'); setError(null); setSuccess(null); }} sx={{ textTransform: 'none', minHeight: 44 }}>
              Quên mật khẩu?
            </Button>
          </Box>
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            size="large"
            disabled={loading}
            aria-busy={loading}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
            sx={{ minHeight: 48, fontSize: '1rem', borderRadius: 2.5, fontWeight: 800 }}
          >
            {loading ? 'Đang xác thực...' : 'Đăng nhập'}
          </Button>
          <Typography variant="body2" sx={{ mt: 0.75, textAlign: 'center', color: '#475569' }}>
            Chưa có tài khoản?{' '}
            <Button
              data-cy="open-register"
              type="button"
              disabled={loading}
              onClick={() => { setAuthView('register'); setError(null); setSuccess(null); }}
              sx={{ textTransform: 'none', minWidth: 44, minHeight: 44, fontWeight: 800 }}
            >
              Đăng ký
            </Button>
          </Typography>
        </Box>}

        {authView === 'register' && <Box component="form" onSubmit={handleRegister} noValidate>
          <TextField
            data-cy="register-name"
            margin="normal" required fullWidth autoFocus
            id="register-name" label="Họ và tên" name="name" autoComplete="name"
            value={displayName} disabled={loading} onChange={(event) => setDisplayName(event.target.value)}
          />
          <TextField
            data-cy="register-email"
            margin="normal" required fullWidth
            id="register-email" label="Email đăng nhập" name="email" type="email" autoComplete="email"
            value={email} disabled={loading} onChange={(event) => setEmail(event.target.value)}
          />
          <TextField
            data-cy="register-password"
            margin="normal" required fullWidth
            id="register-password" label="Mật khẩu" name="new-password" type="password" autoComplete="new-password"
            slotProps={{ htmlInput: { minLength: 8, maxLength: 72 } }}
            helperText="Từ 8 đến 72 ký tự"
            value={registerPassword} disabled={loading} onChange={(event) => setRegisterPassword(event.target.value)}
          />
          <TextField
            data-cy="register-confirm-password"
            margin="normal" required fullWidth
            id="register-confirm-password" label="Nhập lại mật khẩu" name="confirm-password" type="password" autoComplete="new-password"
            value={confirmRegisterPassword} disabled={loading} onChange={(event) => setConfirmRegisterPassword(event.target.value)}
          />
          <TextField
            data-cy="register-role"
            margin="normal" required fullWidth select
            id="register-role" label="Vai trò" name="role"
            value={role} disabled={loading} onChange={(event) => setRole(event.target.value as 'STUDENT' | 'TEACHER')}
          >
            <MenuItem value="STUDENT">Học sinh</MenuItem>
            <MenuItem value="TEACHER">Giáo viên</MenuItem>
          </TextField>
          {role === 'STUDENT' && <TextField
            data-cy="register-grade"
            margin="normal" required fullWidth select
            id="register-grade" label="Khối lớp" name="gradeLevel"
            value={gradeLevel} disabled={loading} onChange={(event) => setGradeLevel(event.target.value)}
          >
            {[1, 2, 3, 4, 5].map((grade) => <MenuItem key={grade} value={String(grade)}>Lớp {grade}</MenuItem>)}
          </TextField>}
          <TextField
            data-cy="register-gender"
            margin="normal" required fullWidth select
            id="register-gender" label="Giới tính" name="gender"
            value={gender} disabled={loading} onChange={(event) => setGender(event.target.value as typeof gender)}
          >
            <MenuItem value="MALE">Nam</MenuItem>
            <MenuItem value="FEMALE">Nữ</MenuItem>
            <MenuItem value="OTHER">Khác</MenuItem>
            <MenuItem value="PREFER_NOT_TO_SAY">Không muốn tiết lộ</MenuItem>
          </TextField>
          <TextField
            data-cy="register-phone"
            margin="normal" required fullWidth
            id="register-phone" label="Số điện thoại" name="tel" type="tel" autoComplete="tel"
            value={phoneNumber} disabled={loading} onChange={(event) => setPhoneNumber(event.target.value)}
          />
          <Button data-cy="submit-register" type="submit" fullWidth variant="contained" size="large" disabled={loading} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang tạo tài khoản…' : 'Tạo tài khoản'}
          </Button>
          <Button data-cy="back-to-login-from-register" type="button" fullWidth disabled={loading} onClick={() => { setAuthView('login'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Đã có tài khoản? Đăng nhập
          </Button>
        </Box>}

        {authView === 'request-reset' && <Box component="form" onSubmit={handleRequestPasswordReset} noValidate>
          <TextField
            data-cy="reset-email"
            margin="normal" required fullWidth autoFocus
            id="reset-email" label="Email đã đăng ký" name="email" type="email" autoComplete="email"
            value={email} disabled={loading} onChange={(event) => setEmail(event.target.value)}
          />
          <Button data-cy="send-reset-code" type="submit" fullWidth variant="contained" size="large" disabled={loading} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang gửi mã…' : 'Gửi mã xác nhận'}
          </Button>
          <Button data-cy="back-to-login" type="button" fullWidth disabled={loading} onClick={() => { setAuthView('login'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Quay lại đăng nhập
          </Button>
        </Box>}

        {authView === 'confirm-reset' && <Box component="form" onSubmit={handleConfirmPasswordReset} noValidate>
          <Typography variant="body2" sx={{ mt: 1, color: '#475569' }}>Nhập mã 6 chữ số đã gửi đến {email} và chọn mật khẩu mới.</Typography>
          <TextField
            data-cy="reset-code"
            margin="normal" required fullWidth autoFocus
            id="reset-code" label="Mã xác nhận 6 chữ số" name="code" type="text"
            autoComplete="one-time-code" slotProps={{ htmlInput: { inputMode: 'numeric', pattern: '[0-9]*', maxLength: 6 } }}
            value={resetCode} disabled={loading} onChange={(event) => setResetCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
          />
          <TextField
            data-cy="new-password"
            margin="normal" required fullWidth
            id="new-password" label="Mật khẩu mới" name="newPassword" type="password" autoComplete="new-password"
            slotProps={{ htmlInput: { minLength: 8 } }} value={newPassword} disabled={loading}
            onChange={(event) => setNewPassword(event.target.value)} helperText="Ít nhất 8 ký tự"
          />
          <Button data-cy="confirm-password-reset" type="submit" fullWidth variant="contained" size="large" disabled={loading} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang đổi mật khẩu…' : 'Xác nhận và đổi mật khẩu'}
          </Button>
          <Button type="button" fullWidth disabled={loading} onClick={() => { setAuthView('request-reset'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Gửi mã đến email khác
          </Button>
        </Box>}

        {authView === 'social-student-setup' && <Box component="form" onSubmit={handleSocialStudentSetup} noValidate>
          <TextField
            margin="normal" required fullWidth select id="google-student-grade" label="Khối lớp"
            value={socialSetupGrade} disabled={loading}
            onChange={(event) => setSocialSetupGrade(event.target.value)}
          >
            {[1, 2, 3, 4, 5].map((grade) => <MenuItem key={grade} value={String(grade)}>Lớp {grade}</MenuItem>)}
          </TextField>
          <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang mở trang học sinh…' : 'Tiếp tục vào trang học sinh'}
          </Button>
          <Button type="button" fullWidth disabled={loading} onClick={() => { setSocialSetupCredential(''); setAuthView('login'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Quay lại đăng nhập
          </Button>
        </Box>}

        {authView === 'login' && googleConfigured && <Box sx={{ mt: 2 }}>
          <Divider sx={{ mb: 2, color: 'text.secondary', fontSize: '0.875rem' }}>Hoặc</Divider>
          <Box sx={{ display: 'grid', justifyItems: 'center', gap: 1.25, minWidth: 0 }}>
            {googleConfigured && <Button type="button" variant="outlined" fullWidth disabled={loading} onClick={() => void handleGoogleLogin()}
              startIcon={<GoogleIcon aria-hidden="true" />} sx={{ maxWidth: 400, minHeight: 44, textTransform: 'none' }}>
              Tiếp tục với Google
            </Button>}

          </Box>
        </Box>}

        {/* Developer Demo Tools — Rendered ONLY when VITE_SHOW_DEV_TOOLS=true */}
        {showDevTools && (
          <Box sx={{ mt: 3 }}>
            <Accordion sx={{ bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '12px !important', '&:before': { display: 'none' } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DeveloperModeIcon sx={{ fontSize: 18, color: '#D97706' }} />
                  <Typography variant="caption" sx={{ fontWeight: 800, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Kiểm thử nhanh (Dev Demo)
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1.5 }}>
                  Chọn vai trò để điền nhanh thông tin thử nghiệm:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  <Chip
                    label="Tài khoản Học sinh mẫu"
                    onClick={() => fillCredentials('minh.student@mathvision.local', '123')}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 700 }}
                  />
                  <Chip
                    label="Tài khoản Giáo viên mẫu"
                    onClick={() => fillCredentials('lan.teacher@mathvision.local', '123')}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 700 }}
                  />
                  <Chip
                    label="Tài khoản Quản trị mẫu"
                    onClick={() => fillCredentials('admin.demo@mathvision.local', '123')}
                    size="small"
                    color="secondary"
                    variant="outlined"
                    sx={{ cursor: 'pointer', fontWeight: 700 }}
                  />
                </Box>
              </AccordionDetails>
            </Accordion>
          </Box>
        )}
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginPage;
