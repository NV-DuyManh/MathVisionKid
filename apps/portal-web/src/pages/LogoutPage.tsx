import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

export function LogoutPage() {
  const navigate = useNavigate();
  useEffect(() => {
    // logout clears local credentials synchronously. Server revocation can
    // finish in the background without keeping the user on an extra screen.
    void authService.logout();
    navigate('/', { replace: true });
  }, [navigate]);
  return null;
}
