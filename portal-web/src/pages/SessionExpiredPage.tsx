import React from 'react';
import { Container, Paper, Box, Typography, Button, Alert } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LoginIcon from '@mui/icons-material/Login';

export const SessionExpiredPage: React.FC = () => {
  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 3, sm: 5 }, textAlign: 'center', borderRadius: 4 }}>
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            bgcolor: '#FEF3C7',
            color: '#D97706',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
          }}
        >
          <AccessTimeIcon sx={{ fontSize: 36 }} />
        </Box>

        <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A', mb: 1 }}>
          Phiên đăng nhập đã hết hạn
        </Typography>

        <Alert severity="info" sx={{ my: 3, textAlign: 'left', borderRadius: 2 }}>
          Phiên làm việc bảo mật của bạn đã hết hiệu lực. Vui lòng đăng nhập lại để tiếp tục sử dụng hệ thống MathVision Kids.
        </Alert>

        <Button
          component={RouterLink}
          to="/login"
          variant="contained"
          color="primary"
          size="large"
          startIcon={<LoginIcon />}
          sx={{ px: 4, py: 1.2 }}
        >
          Đăng nhập lại
        </Button>
      </Paper>
    </Container>
  );
};
