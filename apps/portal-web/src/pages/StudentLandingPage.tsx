import React, { useEffect } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const StudentLandingPage: React.FC = () => {
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    const session = tokenStore.getSessionId();
    const controller = new AbortController();
    authService.getMe(controller.signal).then(user => {
      if (!active || session !== tokenStore.getSessionId()) return;
      if (user.role.toUpperCase().replace('ROLE_', '') === 'STUDENT' && user.active !== false) {
        window.location.replace('/study/');
      } else {
        navigate('/access-denied', { replace: true });
      }
    }).catch(() => {
      if (active && session === tokenStore.getSessionId()) { tokenStore.clearTokens(); navigate('/session-expired', { replace: true }); }
    });
    return () => { active = false; controller.abort(); };
  }, [navigate]);
  return <Box sx={{ textAlign: 'center', py: 8 }}>
    <CircularProgress /><Typography sx={{ mt: 2 }}>Đang mở bài học của em…</Typography>
  </Box>;
};
