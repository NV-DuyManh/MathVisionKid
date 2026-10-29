import React, { useEffect, useRef, useState } from 'react';

type GoogleCredential = { credential: string };
type GoogleIdentity = {
  accounts: {
    id: {
      initialize: (options: { client_id: string; callback: (response: GoogleCredential) => void }) => void;
      renderButton: (element: HTMLElement, options: { theme: 'outline'; size: 'large'; text: 'continue_with'; shape: 'rectangular'; width: number; locale: string }) => void;
    };
  };
};
type GoogleWindow = Window & { google?: GoogleIdentity };

let googleIdentityPromise: Promise<GoogleIdentity> | undefined;

function loadGoogleIdentity(): Promise<GoogleIdentity> {
  const googleWindow = window as GoogleWindow;
  if (googleWindow.google) return Promise.resolve(googleWindow.google);
  if (googleIdentityPromise) return googleIdentityPromise;

  googleIdentityPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => googleWindow.google ? resolve(googleWindow.google) : reject(new Error('Google Identity Services did not initialize.'));
    script.onerror = () => reject(new Error('Google Identity Services could not load.'));
    document.head.appendChild(script);
  });
  return googleIdentityPromise;
}

export default function GoogleWebButton({ clientId, disabled, onCredential }: {
  clientId: string;
  disabled: boolean;
  onCredential: (credential: string) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const onCredentialRef = useRef(onCredential);
  const [unavailable, setUnavailable] = useState(false);
  onCredentialRef.current = onCredential;

  useEffect(() => {
    let active = true;
    void loadGoogleIdentity().then((google) => {
      if (!active || !host.current) return;
      google.accounts.id.initialize({ client_id: clientId, callback: ({ credential }) => onCredentialRef.current(credential) });
      google.accounts.id.renderButton(host.current, {
        theme: 'outline', size: 'large', text: 'continue_with', shape: 'rectangular', width: 280, locale: 'vi',
      });
    }).catch(() => { if (active) setUnavailable(true); });
    return () => { active = false; };
  }, [clientId]);

  return unavailable
    ? <p role="alert">Không tải được chức năng đăng nhập Google. Hãy tải lại trang rồi thử lại.</p>
    : <div ref={host} aria-label="Đăng nhập bằng Google" aria-busy={disabled} style={{ opacity: disabled ? 0.6 : 1, pointerEvents: disabled ? 'none' : 'auto', minHeight: 44 }} />;
}
