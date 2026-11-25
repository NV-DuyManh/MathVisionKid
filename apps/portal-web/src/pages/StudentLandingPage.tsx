import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';
import { isAxiosError } from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const StudentLandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [attempt, setAttempt] = useState(0);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    if (!tokenStore.hasTokens()) {
      navigate('/login', { replace: true });
      return;
    }
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
    }).catch(error => {
      if (!active || session !== tokenStore.getSessionId()) return;
      const status = isAxiosError(error) ? error.response?.status : undefined;
      if (status === 401) {
        tokenStore.clearTokens();
        navigate('/session-expired', { replace: true });
      } else if (status === 403) {
        navigate('/access-denied', { replace: true });
      } else {
        setUnavailable(true);
      }
    });
    return () => { active = false; controller.abort(); };
  }, [attempt, navigate]);
  if (unavailable) return <Box sx={{ width: '100%', maxWidth: 520, mx: 'auto', py: 8, px: 2 }}>
    <Typography component="h1" variant="h5" sx={{ mb: 2 }}>Chưa mở được bài học</Typography>
    <Alert severity="warning">Em kiểm tra kết nối rồi thử lại nhé.</Alert>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
      <Button variant="contained" onClick={() => {
        setUnavailable(false);
        setAttempt(value => value + 1);
      }}>Thử lại</Button>
      <Button component={Link} to="/">Về trang chủ</Button>
    </Box>
  </Box>;
  return <Box role="status" sx={{ textAlign: 'center', py: 8, px: 2 }}>
    <CircularProgress aria-hidden="true" /><Typography sx={{ mt: 2 }}>Đang mở bài học của em…</Typography>
  </Box>;
};
