import { useEffect, useState } from 'react';
import { Text } from 'react-native';
import { workspaceOrigin } from '../config/workspaceOrigin.web';

export default function PortalLoginRedirect() {
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    // Dispatch after the commit; an obsolete/StrictMode setup must not navigate.
    queueMicrotask(() => {
      if (!active) return;
      try {
        const mounted = /^\/(?:study|learn)(?:\/|$)/.test(window.location.pathname);
        const origin = mounted ? window.location.origin : workspaceOrigin('PORTAL');
        const login = new URL('/login' + window.location.search, origin);
        if (login.href === window.location.href) { setUnavailable(true); return; }
        window.location.replace(login.href);
      } catch {
        setUnavailable(true);
      }
    });
    return () => { active = false; };
  }, []);

  return unavailable ? <Text accessibilityRole="alert">Chưa mở được trang đăng nhập. Em thử lại sau nhé.</Text> : null;
}
