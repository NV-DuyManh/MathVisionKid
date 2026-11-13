import { Button, Alert } from '@mui/material';
import { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import apiClient from '../services/api/apiClient';
import { AuthTokenStore } from '../services/api/AuthTokenStore';
import { appConfig } from '../config/runtime';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const ssoStarted = useRef(false);
  const [ssoCode] = useState(() =>
    new window.URLSearchParams(window.location.hash.slice(1)).get('sso') || (window as Window & { mathVisionSsoTicket?: string }).mathVisionSsoTicket || searchParams.get('code'));
  // Handle SSO Ticket Exchange if redirected from Unified Portal (URL Fragment #sso= preferred)
  useEffect(() => {
    if (ssoStarted.current) return;
    if (!ssoCode) {
      window.location.replace(appConfig.portalOrigin);
      return;
    }

    // IMMEDIATELY scrub the URL (fragment or query) before any network operation
    ssoStarted.current = true;
    delete (window as Window & { mathVisionSsoTicket?: string }).mathVisionSsoTicket;
    window.history.replaceState(window.history.state, document.title, window.location.pathname);

    const exchangeTicket = async () => {
      try {
        setError(null);
        const res = await apiClient.post('/auth/sso/exchange', {
          code: ssoCode,
          targetApp: 'TEACHER',
        });
        const { accessToken, refreshToken } = res.data;
        if (!accessToken || !refreshToken) throw new Error('Incomplete Teacher SSO session');
        AuthTokenStore.setTokens(accessToken, refreshToken, true);
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        setError(
          err.response?.data?.message ||
          'Mã xác thực chuyển giao (SSO) không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại qua Portal.'
        );
      }
    };

    exchangeTicket();
  }, [ssoCode, navigate]);

  return (
    <main className="auth-page teacher-session-screen">
      {error ? (
        <div>
          <Alert severity="error">{error}</Alert>
          <Button component="a" href={`${appConfig.portalOrigin}/login?session=expired`}>
            Đăng nhập lại
          </Button>
        </div>
      ) : <p role="status">{ssoCode ? 'Đang mở không gian giáo viên…' : 'Đang chuyển đến trang đăng nhập…'}</p>}
    </main>
  );
}
