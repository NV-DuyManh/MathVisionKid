import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import LoginIcon from '@mui/icons-material/Login';
import FacebookIcon from '@mui/icons-material/Facebook';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';
import { appConfig, googleClientId, showDevTools } from '../config/runtime';

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
  const [socialSetupProvider, setSocialSetupProvider] = useState<'google' | 'facebook'>('google');
  const [socialSetupGrade, setSocialSetupGrade] = useState('1');
  const sessionCheck = useRef<AbortController | null>(null);
  const googleButton = useRef<HTMLDivElement | null>(null);

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const googleRequestedRole = searchParams.get('role') === 'TEACHER' ? 'TEACHER' : undefined;
  const facebookConfigured = Boolean(import.meta.env.VITE_FIREBASE_API_KEY && import.meta.env.VITE_FIREBASE_AUTH_DOMAIN
    && import.meta.env.VITE_FIREBASE_PROJECT_ID && import.meta.env.VITE_FIREBASE_APP_ID);

  // Display session expired notice if redirected after expiry
  useEffect(() => {
    const controller = new AbortController();
    sessionCheck.current = controller;
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
          navigate('/student', { replace: true });
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

  useEffect(() => {
    if (authView !== 'login' || !googleClientId || !googleButton.current) return undefined;

    let cancelled = false;
    const renderGoogleButton = () => {
      if (cancelled || !googleButton.current || !window.google?.accounts.id) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async ({ credential }) => {
          setLoading(true);
          setError(null);
          try {
            const user = await authService.loginWithGoogle(credential, googleRequestedRole);
            const role = user.role.toUpperCase().replace('ROLE_', '');
            if (role === 'STUDENT') {
              navigate('/student');
            } else if (role === 'TEACHER' || role === 'ADMIN') {
              const target = role === 'TEACHER' ? 'TEACHER' : 'ADMIN';
              const origin = role === 'TEACHER' ? appConfig.teacherOrigin : appConfig.adminOrigin;
              const ticket = await authService.requestSsoTicket(target);
              window.location.href = `${origin}/login#sso=${encodeURIComponent(ticket.code)}`;
            } else {
              tokenStore.clearTokens();
              setError('Tài khoản không có quyền truy cập hệ thống.');
            }
          } catch (err: any) {
            tokenStore.clearTokens();
            if (err.response?.data?.error?.code === 'GOOGLE_STUDENT_GRADE_REQUIRED') {
              setSocialSetupCredential(credential);
              setSocialSetupProvider('google');
              setAuthView('social-student-setup');
              setSuccess('Google đã được xác minh. Chọn lớp để hoàn tất tạo tài khoản học sinh.');
            } else if (err.response?.status === 403) {
              setError('Tài khoản Google này đang bị khóa hoặc không có quyền truy cập cổng đã chọn.');
            } else if (err.response?.status === 401) {
              setError('Không xác minh được tài khoản Google. Hãy thử lại.');
            } else {
              setError('Đăng nhập Google hiện chưa khả dụng. Hãy thử lại sau.');
            }
          } finally {
            setLoading(false);
          }
        },
      });
      const buttonWidth = Math.min(400, Math.max(220, googleButton.current.clientWidth || 360));
      window.google.accounts.id.renderButton(googleButton.current, {
        type: 'standard', theme: 'outline', size: 'large', text: 'continue_with', shape: 'pill', width: buttonWidth, locale: 'vi',
      });
    };

    const existingScript = document.querySelector<HTMLScriptElement>('script[src="https://accounts.google.com/gsi/client"]');
    if (window.google?.accounts.id) {
      renderGoogleButton();
    } else if (existingScript) {
      existingScript.addEventListener('load', renderGoogleButton);
    } else {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.addEventListener('load', renderGoogleButton);
      document.head.appendChild(script);
    }

    return () => {
      cancelled = true;
      existingScript?.removeEventListener('load', renderGoogleButton);
    };
  }, [authView, googleClientId, googleRequestedRole, navigate]);

  const handleFacebookLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const { getFacebookCredential } = await import('../services/facebookAuth');
      const credential = await getFacebookCredential();
      try {
        const user = await authService.loginWithFacebook(credential, googleRequestedRole);
        const role = user.role.toUpperCase().replace('ROLE_', '');
        if (role === 'STUDENT') navigate('/student');
        else if (role === 'TEACHER' || role === 'ADMIN') {
          const target = role === 'TEACHER' ? 'TEACHER' : 'ADMIN';
          const origin = role === 'TEACHER' ? appConfig.teacherOrigin : appConfig.adminOrigin;
          const ticket = await authService.requestSsoTicket(target);
          window.location.href = `${origin}/login#sso=${encodeURIComponent(ticket.code)}`;
        } else {
          tokenStore.clearTokens();
          setError('Tài khoản không có quyền truy cập hệ thống.');
        }
      } catch (err: any) {
        tokenStore.clearTokens();
        if (import.meta.env.DEV) {
          console.warn('[Facebook login] Backend rejected Firebase credential:', err.response?.status, err.response?.data?.error?.code);
        }
        if (err.response?.data?.error?.code === 'FACEBOOK_STUDENT_GRADE_REQUIRED') {
          setSocialSetupCredential(credential);
          setSocialSetupProvider('facebook');
          setAuthView('social-student-setup');
          setSuccess('Facebook đã được xác minh. Chọn lớp để hoàn tất tài khoản học sinh.');
        } else if (err.response?.data?.error?.code === 'FACEBOOK_ACCOUNT_LINK_REQUIRED') {
          setError('Email này đã có tài khoản. Hãy đăng nhập bằng phương thức đã đăng ký.');
        } else if (err.response?.data?.error?.code === 'FACEBOOK_EMAIL_REQUIRED') {
          setError('Tài khoản Facebook cần có email để đăng nhập.');
        } else if (err.response?.status === 403) {
          setError('Tài khoản Facebook này đang bị khóa.');
        } else {
          setError('Chưa đăng nhập được bằng Facebook. Vui lòng thử lại.');
        }
      }
    } catch (err: any) {
      if (import.meta.env.DEV) console.warn('[Facebook login] Firebase Auth error:', err.code || 'unknown');
      if (err.code === 'auth/account-exists-with-different-credential') {
        setError('Email này đã liên kết với phương thức đăng nhập khác. Hãy dùng phương thức đó.');
      } else if (err.code === 'auth/popup-blocked') {
        setError('Trình duyệt đã chặn cửa sổ Facebook. Hãy cho phép cửa sổ bật lên rồi thử lại.');
      } else if (err.code === 'auth/unauthorized-domain') {
        setError('Tên miền hiện tại chưa được thêm vào Firebase Authentication → Settings → Authorized domains.');
      } else if (err.code === 'auth/operation-not-allowed') {
        setError('Facebook Login chưa được bật trong Firebase Authentication.');
      } else if (err.code === 'auth/invalid-api-key') {
        setError('Cấu hình Firebase Web chưa đúng. Hãy kiểm tra API key của ứng dụng Web.');
      } else if (err.code === 'auth/network-request-failed') {
        setError('Không kết nối được Firebase. Hãy kiểm tra mạng rồi thử lại.');
      } else if (err.code !== 'auth/popup-closed-by-user' && err.code !== 'auth/cancelled-popup-request') {
        setError('Facebook chưa mở được. Hãy kiểm tra cấu hình Facebook Login trong Meta và Firebase rồi thử lại.');
      }
    } finally {
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
    setLoading(true);
    setError(null);
    try {
      const user = socialSetupProvider === 'google'
        ? await authService.loginWithGoogle(socialSetupCredential, 'STUDENT', Number(socialSetupGrade))
        : await authService.loginWithFacebook(socialSetupCredential, 'STUDENT', Number(socialSetupGrade));
      setSocialSetupCredential('');
      if (user.role.toUpperCase().replace('ROLE_', '') === 'STUDENT') navigate('/student');
      else {
        tokenStore.clearTokens();
        setError('Tài khoản này không thuộc cổng học sinh.');
      }
    } catch {
      tokenStore.clearTokens();
      setError('Chưa tạo được tài khoản học sinh. Hãy thử đăng nhập lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }

    sessionCheck.current?.abort();
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
          window.location.href = `${appConfig.teacherOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
          break;
        }
        case 'ADMIN': {
          const ticket = await authService.requestSsoTicket('ADMIN');
          window.location.href = `${appConfig.adminOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
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
      } else if (err.response?.status === 403) {
        setError('Tài khoản chưa được phép truy cập. Vui lòng liên hệ giáo viên.');
      } else if (err.response?.status === 429) {
        setError('Em đã thử nhiều lần liên tiếp. Chờ một chút rồi đăng nhập lại nhé.');
      } else if (!err.response) {
        setError('Chưa kết nối được máy chủ. Em thử đăng nhập lại sau một chút nhé.');
      } else {
        setError('Máy chủ đang gặp sự cố. Em thử lại sau một chút nhé.');
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
      setLoading(false);
    }
  };

  const handleRequestPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Nhập email đã đăng ký để nhận mã xác nhận.');
      return;
    }
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
        ? 'Gmail từ chối đăng nhập SMTP. Quản trị viên cần cập nhật App Password đúng tài khoản gửi trong cấu hình rồi khởi động lại dịch vụ.'
        : err.response?.status === 503
          ? 'Dịch vụ gửi email chưa được cấu hình đầy đủ. Hãy kiểm tra cấu hình SMTP rồi khởi động lại dịch vụ.'
          : 'Chưa gửi được mã xác nhận. Hãy kiểm tra kết nối rồi thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmPasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(resetCode)) {
      setError('Mã xác nhận phải gồm 6 chữ số.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Mật khẩu mới phải có ít nhất 8 ký tự.');
      return;
    }
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
      setLoading(false);
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
            {authView === 'login' ? 'Đăng nhập MathVision Kids' : authView === 'register' ? 'Tạo tài khoản' : authView === 'social-student-setup' ? 'Chọn lớp của em' : 'Khôi phục mật khẩu'}
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            {authView === 'register' ? 'Điền thông tin để bắt đầu sử dụng MathVision Kids' : authView === 'social-student-setup' ? 'Chọn khối lớp hiện tại để hoàn tất tài khoản học sinh.' : 'Nhập tài khoản của bạn để tiếp tục'}
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" role="alert" sx={{ mb: 3, borderRadius: 2 }}>
            {error}
          </Alert>
        )}
        {success && <Alert severity="success" role="status" sx={{ mb: 3, borderRadius: 2 }}>{success}</Alert>}

        {authView === 'login' && <Box component="form" onSubmit={handleLogin} noValidate>
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
            placeholder="Nhập email của bạn"
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
          <Button
            data-cy="forgot-password"
            type="button"
            fullWidth
            disabled={loading}
            onClick={() => { setAuthView('request-reset'); setError(null); setSuccess(null); }}
            sx={{ textTransform: 'none' }}
          >
            Quên mật khẩu?
          </Button>
          <Typography variant="body2" sx={{ mt: 1.5, textAlign: 'center', color: '#64748B' }}>
            Chưa có tài khoản?{' '}
            <Button
              data-cy="open-register"
              type="button"
              disabled={loading}
              onClick={() => { setAuthView('register'); setError(null); setSuccess(null); }}
              sx={{ textTransform: 'none', minWidth: 0, p: 0.5, fontWeight: 700 }}
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
          <Button data-cy="submit-register" type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 2, py: 1.4 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Tạo tài khoản'}
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
          <Button data-cy="send-reset-code" type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 2, py: 1.4 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Gửi mã xác nhận'}
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
          <Button data-cy="confirm-password-reset" type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 2, py: 1.4 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Xác nhận và đổi mật khẩu'}
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
          <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 2, py: 1.4 }}>
            {loading ? <CircularProgress size={22} color="inherit" /> : 'Tiếp tục vào trang học sinh'}
          </Button>
          <Button type="button" fullWidth disabled={loading} onClick={() => { setSocialSetupCredential(''); setAuthView('login'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Quay lại đăng nhập
          </Button>
        </Box>}

        {authView === 'login' && (
          <Paper
            component="section"
            aria-labelledby="social-login-title"
            variant="outlined"
            sx={{
              mt: 3,
              p: { xs: 2, sm: 2.5 },
              borderRadius: 3.5,
              borderColor: '#E5E3FF',
              background: 'linear-gradient(145deg, #F7F6FF 0%, #FFFFFF 78%)',
              boxShadow: '0 8px 24px rgba(79, 70, 229, 0.06)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 2 }}>
              <Box sx={{ width: 42, height: 42, flexShrink: 0, display: 'grid', placeItems: 'center', borderRadius: 2.5, bgcolor: '#ECEBFF', color: '#5145CD' }}>
                <AutoAwesomeIcon aria-hidden="true" sx={{ fontSize: 23 }} />
              </Box>
              <Box>
                <Typography id="social-login-title" variant="subtitle1" sx={{ color: '#171A3A', fontWeight: 800, lineHeight: 1.25 }}>
                  Vào học nhanh hơn
                </Typography>
                <Typography variant="body2" sx={{ color: '#65708A', mt: 0.35 }}>
                  Chọn tài khoản Google hoặc Facebook của em
                </Typography>
              </Box>
            </Box>

            <Box role="group" aria-label="Đăng nhập bằng tài khoản Google hoặc Facebook" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.25 }}>
              {googleClientId ? (
                <Box
                  ref={googleButton}
                  sx={{ width: '100%', maxWidth: 400, minHeight: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: loading ? 0.6 : 1, pointerEvents: loading ? 'none' : 'auto', '& iframe': { maxWidth: '100%' } }}
                />
              ) : (
                <Button
                  type="button" variant="outlined" disabled fullWidth
                  aria-label="Đăng nhập với Google chưa khả dụng"
                  sx={{ maxWidth: 400, minHeight: 48, borderRadius: 999, textTransform: 'none', fontWeight: 700 }}
                >
                  <Box component="span" aria-hidden="true" sx={{ mr: 1, fontWeight: 800, fontSize: 18, color: '#4285F4' }}>G</Box>
                  Google đang được thiết lập
                </Button>
              )}
              <Button
                type="button" variant="outlined" fullWidth disabled={loading || !facebookConfigured}
                onClick={handleFacebookLogin}
                aria-label={facebookConfigured ? 'Đăng nhập bằng Facebook' : 'Đăng nhập bằng Facebook chưa khả dụng'}
                startIcon={<FacebookIcon aria-hidden="true" sx={{ color: '#1877F2', fontSize: 23 }} />}
                sx={{ maxWidth: 400, minHeight: 48, borderRadius: 999, borderColor: '#D7DCEC', bgcolor: '#FFFFFF', color: '#202744', fontSize: 15, fontWeight: 700, textTransform: 'none', '&:hover': { borderColor: '#1877F2', bgcolor: '#F3F8FF' }, '&.Mui-disabled': { borderColor: '#E2E8F0', bgcolor: '#F8FAFC', color: '#94A3B8' } }}
              >
                Tiếp tục với Facebook
              </Button>
            </Box>

            <Typography variant="caption" sx={{ display: 'block', mt: 1.75, textAlign: 'center', color: '#76819A', lineHeight: 1.45 }}>
              Tiến độ học tập sẽ được lưu trong tài khoản của em.
            </Typography>
          </Paper>
        )}

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
