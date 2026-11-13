import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { appConfig } from '../config/runtime';

export function LoginPage() {
  const { loginWithSsoTicket } = useAuth();
  const navigate = useNavigate();
  const started = useRef(false);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const handoff = window as Window & { mathVisionSsoTicket?: string };
    const code = handoff.mathVisionSsoTicket ?? new URLSearchParams(window.location.hash.slice(1)).get('sso');
    delete handoff.mathVisionSsoTicket;
    if (!code) { window.location.replace(`${appConfig.portalOrigin}/login`); return; }
    window.history.replaceState(window.history.state, '', window.location.pathname);
    void loginWithSsoTicket(code).then(() => navigate('/dashboard', { replace: true })).catch(() => setFailed(true));
  }, [loginWithSsoTicket, navigate]);

  return <main className="admin-auth">
    {failed ? <div><p role="alert">Chưa mở được phiên quản trị. Vui lòng đăng nhập lại.</p>
      <a href={`${appConfig.portalOrigin}/login?session=expired`}>Quay lại trang đăng nhập</a></div>
      : <p role="status">Đang mở trang quản trị…</p>}
  </main>;
}
