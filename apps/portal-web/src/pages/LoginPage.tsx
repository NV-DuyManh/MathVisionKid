import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  TextField,
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
import { useNavigate, useSearchParams } from 'react-router-dom';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';
import { appConfig, googleConfigured, showDevTools } from '../config/runtime';

import './studentAuth.css';

const studyIcons = {
  planet: 62659,
  'shapes-outline': 62831,
  'person-outline': 62636,
  'lock-closed-outline': 62408,
  'eye-outline': 62186,
  'eye-off-outline': 62184,
  'arrow-forward': 61747,
  'shield-checkmark-outline': 62841,
} as const;

const authIntro = {
  login: {
    title: 'Mỗi bài toán,',
    highlight: 'một khám phá.',
    description: 'Cùng MathVisionKid học Toán qua luyện tập, trò chơi và khám phá AI.',
  },
  register: {
    title: 'Học Toán vui,',
    highlight: 'giỏi từng ngày.',
    description: 'Tạo tài khoản để luyện tập theo lớp và lưu kết quả của em.',
  },
  'request-reset': {
    title: 'Quên mật khẩu?',
    highlight: 'Lấy lại nhé!',
    description: 'Nhập email đã đăng ký để nhận mã xác nhận.',
  },
  'confirm-reset': {
    title: 'Mật khẩu mới,',
    highlight: 'học tiếp thôi!',
    description: 'Dùng mã 6 chữ số trong email để đặt lại mật khẩu.',
  },
  'social-student-setup': {
    title: 'Em học lớp mấy?',
    highlight: 'Chọn lớp nhé!',
    description: 'Chọn lớp hiện tại để xem các bài Toán phù hợp.',
  },
};

function StudyIcon({ name, size, color }: { name: keyof typeof studyIcons; size: number; color?: string }) {
  return <span className="student-auth-icon" style={{ fontSize: size, color }} aria-hidden="true">{String.fromCodePoint(studyIcons[name])}</span>;
}

export const LoginPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const resetFromAccount = searchParams.get('reset') === 'password';
  const [email, setEmail] = useState('');
  const [accountResetEmail, setAccountResetEmail] = useState('');
  const [checkingResetAccount, setCheckingResetAccount] = useState(() => resetFromAccount && tokenStore.hasTokens());
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmRegisterPassword, setConfirmRegisterPassword] = useState('');
  const [gender, setGender] = useState<'' | 'MALE' | 'FEMALE' | 'OTHER'>('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [gradeLevel, setGradeLevel] = useState('1');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [authView, setAuthView] = useState<keyof typeof authIntro>(() => resetFromAccount ? 'request-reset' : 'login');
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
  const requestedRole = searchParams.get('role') === 'TEACHER' ? 'TEACHER' : undefined;

  // Display session expired notice if redirected after expiry
  useEffect(() => {
    const controller = new AbortController();
    sessionCheck.current = controller;
    if (resetFromAccount) {
      if (tokenStore.hasTokens()) {
        authService.getMe(controller.signal).then(user => {
          if (controller.signal.aborted || !user.active || user.role !== 'STUDENT') return;
          setAccountResetEmail(user.email);
          setEmail(user.email);
        }).catch(() => {}).finally(() => {
          if (!controller.signal.aborted) setCheckingResetAccount(false);
        });
      }
      return () => controller.abort();
    }
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
  }, [searchParams, navigate, resetFromAccount]);

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
        const user = await authService.loginWithGoogle(credential, requestedRole);
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
    if (!gender) {
      setError('Vui lòng chọn giới tính.');
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
        role: requestedRole ?? 'STUDENT',
        gender,
        phoneNumber: phoneNumber.trim(),
        ...(!requestedRole ? { gradeLevel: Number(gradeLevel) } : {}),
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
    if (checkingResetAccount) return;
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
      if (accountResetEmail) tokenStore.clearTokens();
      if (resetFromAccount) {
        setAccountResetEmail('');
        navigate('/login', { replace: true });
      }
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

  const intro = authIntro[authView];

  return (
    <main className="student-auth">
      <div className="student-auth-layout">
        <section className="student-auth-hero" aria-label="Cùng em khám phá Toán học">
          <div className="student-auth-brand">
            <StudyIcon name="planet" size={25} color="#FFE07C" />
            <span>MathVisionKid</span>
          </div>
          <div className="student-auth-hero-content">
            <div className="student-auth-intro">
              <p className="student-auth-slogan">{intro.title}<br /><span>{intro.highlight}</span></p>
              <p className="student-auth-description">{intro.description}</p>
            </div>
            <div className="student-auth-illustration" aria-hidden="true">
              <span className="student-auth-math"><b>8 + 5 = 13</b><StudyIcon name="shapes-outline" size={30} color="#D7F6FF" /></span>
              <div className="student-auth-art">
                <img src="/ui/robot-mascot.webp" alt="" />
              </div>
            </div>
          </div>
        </section>
        <div className="student-auth-main">
          <Box className="student-auth-card" sx={{
          '& .MuiOutlinedInput-root': { backgroundColor: '#F2EDF9', borderRadius: '17px', minHeight: 46 },
          '& .MuiOutlinedInput-input': { paddingBlock: '11px', fontSize: 15, color: '#211759' },
          '& .MuiOutlinedInput-input::placeholder': { color: '#64748B', opacity: 1 },
          '& .MuiOutlinedInput-root:focus-within': { boxShadow: '0 0 0 3px #7449df33' },
          '& .MuiOutlinedInput-notchedOutline': { borderColor: '#E4DCFF' },
          '& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#713CF7' },
          '& .MuiFormLabel-root.Mui-focused': { color: '#4D33D1' },
          '& .MuiFormLabel-asterisk': { display: 'none' },
          '& .MuiButton-text': { color: '#4D33D1' },
          '& .MuiButton-contained': {
            background: 'linear-gradient(105deg, #6034DF, #883EE9)', color: '#fff',
            borderRadius: '24px', minHeight: 48, fontWeight: 800, boxShadow: 'none', textTransform: 'none',
          },
          '& .MuiButton-contained.Mui-disabled': { background: '#E4DCFF', color: '#625A86' },
          }}>
        <div className="student-auth-heading">
          <h1>{authView === 'login' ? 'Đăng nhập' : authView === 'register' ? 'Tạo tài khoản' : authView === 'social-student-setup' ? 'Chọn lớp của em' : resetFromAccount ? 'Đổi mật khẩu MathVisionKid' : 'Khôi phục mật khẩu'}</h1>
          {authView === 'login' && <p>Đăng nhập để tiếp tục khám phá kiến thức cùng MathVisionKid.</p>}
          {authView === 'social-student-setup' && <p>Chọn khối lớp hiện tại để hoàn tất tài khoản học sinh.</p>}
        </div>

        {error && (
          <Alert id="auth-error" severity="error" role="alert" sx={{ mb: 2, borderRadius: 2 }}>
            {error}
          </Alert>
        )}
        {success && <Alert severity="success" role="status" sx={{ mb: 3, borderRadius: 2 }}>{success}</Alert>}

        {authView === 'login' && <Box component="form" onSubmit={handleLogin} noValidate aria-busy={loading} aria-describedby={error ? 'auth-error' : undefined}>
          <label className="student-auth-control-label" htmlFor="email">Email</label>
          <TextField
            required
            fullWidth
            id="email"
            placeholder="Nhập email của em"
            name="email"
            type="email"
            autoComplete="username"
            slotProps={{
              htmlInput: { autoCapitalize: 'none', spellCheck: false },
              input: { startAdornment: <InputAdornment position="start"><StudyIcon name="person-outline" size={18} color="#66568C" /></InputAdornment> },
            }}
            value={email}
            disabled={loading}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Box component="label" className="student-auth-control-label" htmlFor="password" sx={{ mt: 1.25 }}>Mật khẩu</Box>
          <TextField
            required
            fullWidth
            name="password"
            placeholder="Nhập mật khẩu của em"
            type={showPassword ? 'text' : 'password'}
            id="password"
            autoComplete="current-password"
            value={password}
            disabled={loading}
            onChange={(e) => setPassword(e.target.value)}
            slotProps={{
              input: {
                startAdornment: <InputAdornment position="start"><StudyIcon name="lock-closed-outline" size={18} color="#66568C" /></InputAdornment>,
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
                      <StudyIcon name={showPassword ? "eye-off-outline" : "eye-outline"} size={22} color="#66568C" />
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1, mb: 1.25 }}>
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
            endIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : <StudyIcon name="arrow-forward" size={18} />}
            sx={{ height: 48, minHeight: 48, px: 2, py: 0, fontSize: '1rem', fontWeight: 800 }}
          >
            {loading ? 'Đang xác thực...' : 'Đăng nhập'}
          </Button>
          <Typography variant="body2" sx={{ mt: 0.75, mb: 1, textAlign: 'center', color: '#475569' }}>
            Chưa có tài khoản?{' '}
            <Button
              data-cy="open-register"
              type="button"
              disabled={loading}
              onClick={() => { setAuthView('register'); setError(null); setSuccess(null); }}
              sx={{ textTransform: 'none', minWidth: 44, minHeight: 44, fontWeight: 800 }}
            >
              Đăng ký ngay
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
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: requestedRole ? "1fr" : "repeat(2, minmax(0, 1fr))" }, gap: { xs: 0, sm: 1.5 } }}>
          <TextField
            data-cy="register-phone"
            margin="normal" required fullWidth
            id="register-phone" label="Số điện thoại" name="tel" type="tel" autoComplete="tel"
            value={phoneNumber} disabled={loading} onChange={(event) => setPhoneNumber(event.target.value)}
          />
          {!requestedRole && <TextField
            data-cy="register-grade"
            margin="normal" required fullWidth select
            id="register-grade" label="Khối lớp" name="gradeLevel"
            slotProps={{ select: { native: true } }}
            value={gradeLevel} disabled={loading} onChange={(event) => setGradeLevel(event.target.value)}
          >
            {[1, 2, 3, 4, 5].map((grade) => <option key={grade} value={String(grade)}>Lớp {grade}</option>)}
          </TextField>}
          </Box>
          <TextField
            data-cy="register-gender"
            margin="normal" required fullWidth select
            id="register-gender" label="Giới tính" name="gender"
            slotProps={{ select: { native: true }, inputLabel: { shrink: true } }}
            value={gender} disabled={loading} onChange={(event) => setGender(event.target.value as typeof gender)}
          >
            <option value="" disabled hidden>Chọn giới tính</option>
            <option value="MALE">Nam</option>
            <option value="FEMALE">Nữ</option>
            <option value="OTHER">Khác</option>
          </TextField>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: { xs: 0, sm: 1.5 } }}>
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
          </Box>
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
            value={email} disabled={loading || checkingResetAccount} onChange={(event) => setEmail(event.target.value)}
            slotProps={{ htmlInput: { readOnly: Boolean(accountResetEmail) } }}
          />
          <Button data-cy="send-reset-code" type="submit" fullWidth variant="contained" size="large" disabled={loading || checkingResetAccount} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang gửi mã…' : 'Gửi mã xác nhận'}
          </Button>
          <Button data-cy="back-to-login" type="button" fullWidth disabled={loading} onClick={() => {
            if (resetFromAccount && tokenStore.hasTokens()) window.location.assign('/study/account');
            else {
              if (resetFromAccount) navigate('/login', { replace: true });
              setAuthView('login'); setError(null); setSuccess(null);
            }
          }} sx={{ mt: 1, textTransform: 'none' }}>
            {resetFromAccount && tokenStore.hasTokens() ? 'Quay lại hồ sơ' : 'Quay lại đăng nhập'}
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
            {accountResetEmail ? 'Gửi lại mã' : 'Gửi mã đến email khác'}
          </Button>
        </Box>}

        {authView === 'social-student-setup' && <Box component="form" onSubmit={handleSocialStudentSetup} noValidate>
          <TextField
            margin="normal" required fullWidth select id="google-student-grade" label="Khối lớp"
            slotProps={{ select: { native: true } }}
            value={socialSetupGrade} disabled={loading}
            onChange={(event) => setSocialSetupGrade(event.target.value)}
          >
            {[1, 2, 3, 4, 5].map((grade) => <option key={grade} value={String(grade)}>Lớp {grade}</option>)}
          </TextField>
          <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} aria-busy={loading} startIcon={loading ? <CircularProgress size={20} color="inherit" aria-hidden /> : undefined} sx={{ mt: 2, py: 1.4 }}>
            {loading ? 'Đang mở trang học sinh…' : 'Tiếp tục vào trang học sinh'}
          </Button>
          <Button type="button" fullWidth disabled={loading} onClick={() => { setSocialSetupCredential(''); setAuthView('login'); setError(null); setSuccess(null); }} sx={{ mt: 1, textTransform: 'none' }}>
            Quay lại đăng nhập
          </Button>
        </Box>}

        {authView === 'login' && googleConfigured && <Box sx={{ mb: 1.5 }}>
          <Divider sx={{ mb: 2.5, color: 'text.secondary', fontSize: '0.875rem' }}>Hoặc</Divider>
          <Box sx={{ display: 'grid', justifyItems: 'center', gap: 1.25, minWidth: 0 }}>
            {googleConfigured && <Button type="button" variant="outlined" fullWidth disabled={loading} onClick={() => void handleGoogleLogin()}
              startIcon={<img src="/ui/google-g.png" alt="" width={18} height={18} style={{ objectFit: 'contain' }} />}
              sx={{ maxWidth: 400, minHeight: 44, textTransform: 'none', bgcolor: '#fff' }}>
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
        <div className="student-auth-note">
          <StudyIcon name="shield-checkmark-outline" size={20} />
          <span>Thông tin của em được bảo vệ tại MathVisionKid.</span>
        </div>
          </Box>
        </div>
      </div>
    </main>
  );
};

export default LoginPage;
