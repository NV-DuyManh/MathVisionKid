import React, { useEffect, useState } from 'react';
import { Container, Paper, Box, Typography, CircularProgress, Alert, Button } from '@mui/material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import PersonIcon from '@mui/icons-material/Person';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';
import { appConfig } from '../config/runtime';

export const TeacherEntryPage: React.FC = () => {
  const [status, setStatus] = useState<string>('Đang kiểm tra quyền truy cập...');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const controller = new AbortController();
    const handleEntry = async () => {
      if (!tokenStore.hasTokens()) {
        navigate('/login?role=TEACHER');
        return;
      }

      try {
        const user = await authService.getMe(controller.signal);
        if (controller.signal.aborted) return;
        const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';

        if (role !== 'TEACHER') {
          // If already logged in as Student or another role, clear session so user can login with Teacher credentials
          tokenStore.clearTokens();
          window.dispatchEvent(new Event('portal_auth_changed'));
          navigate('/login?role=TEACHER');
          return;
        }

        setStatus('Đang khởi tạo phiên làm việc bảo mật...');
        const ticket = await authService.requestSsoTicket('TEACHER', controller.signal);
        if (controller.signal.aborted) return;

        setStatus('Đang chuyển hướng đến không gian Giáo viên...');
        window.location.href = `${appConfig.teacherOrigin}/login#sso=${encodeURIComponent(ticket.code)}`;
      } catch {
        if (controller.signal.aborted) return;
        setError( 'Lỗi khi khởi tạo phiên làm việc Giáo viên.');
      }
    };

    void handleEntry();
    return () => controller.abort();
  }, [navigate]);

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 3, sm: 5 }, textAlign: 'center', borderRadius: 4 }}>
        <Box
          sx={{
            width: 60,
            height: 60,
            borderRadius: 3,
            bgcolor: '#ECFDF5',
            color: '#059669',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          <PersonIcon sx={{ fontSize: 32 }} />
        </Box>

        <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', mb: 2 }}>
          Không gian Giáo viên — MathVision Kids
        </Typography>

        {error ? (
          <Box>
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
              {error}
            </Alert>
            <Button component={RouterLink} to="/login" variant="contained">
              Đăng nhập lại
            </Button>
          </Box>
        ) : (
          <Box sx={{ py: 3 }}>
            <CircularProgress color="success" size={40} sx={{ mb: 2 }} />
            <Typography variant="body1" sx={{ color: '#475569', fontWeight: 500 }}>
              {status}
            </Typography>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default TeacherEntryPage;
