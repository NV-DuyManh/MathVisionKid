import React, { useEffect, useState } from 'react';
import { Container, Paper, Box, Typography, CircularProgress, Alert, Button } from '@mui/material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import PersonIcon from '@mui/icons-material/Person';
import { authService } from '../services/authService';
import { tokenStore } from '../services/apiClient';

export const TeacherEntryPage: React.FC = () => {
  const [status, setStatus] = useState<string>('Đang kiểm tra quyền truy cập...');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleEntry = async () => {
      if (!tokenStore.hasTokens()) {
        navigate('/login');
        return;
      }

      try {
        const user = await authService.getMe();
        const role = user.role ? user.role.toUpperCase().replace('ROLE_', '') : '';

        if (role !== 'TEACHER') {
          navigate(`/access-denied?target=Giáo viên&current=${role}`);
          return;
        }

        setStatus('Đang khởi tạo phiên làm việc bảo mật...');
        const ticket = await authService.requestSsoTicket('TEACHER');

        setStatus('Đang chuyển hướng đến không gian Giáo viên...');
        window.location.href = `http://localhost:5173/login#sso=${encodeURIComponent(ticket.code)}`;
      } catch (err: any) {
        setError(err.response?.data?.message || err.message || 'Lỗi khi khởi tạo phiên làm việc Giáo viên.');
      }
    };

    handleEntry();
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
