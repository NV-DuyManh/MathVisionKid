import React, { useState } from 'react';
import {
  Container,
  Paper,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  Divider,
} from '@mui/material';
import { Link as RouterLink, Navigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import QrCode2Icon from '@mui/icons-material/QrCode2';
import DnsIcon from '@mui/icons-material/Dns';
import SchoolIcon from '@mui/icons-material/School';
import PersonIcon from '@mui/icons-material/Person';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

export const DevRuntimePage: React.FC = () => {
  const showDevTools = import.meta.env.VITE_SHOW_DEV_TOOLS === 'true';
  const [copied, setCopied] = useState<string | null>(null);

  // Gate page: if dev flag is false/unset, redirect to home
  if (!showDevTools) {
    return <Navigate to="/" replace />;
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button
          component={RouterLink}
          to="/"
          startIcon={<ArrowBackIcon />}
          sx={{ color: '#64748B' }}
        >
          Quay lại Trang chủ
        </Button>
        <Chip
          icon={<DeveloperModeIcon />}
          label="DEVELOPER & TEST ENVIRONMENT"
          color="warning"
          variant="filled"
          sx={{ fontWeight: 700 }}
        />
      </Box>

      <Paper sx={{ p: { xs: 3, sm: 5 }, borderRadius: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 3,
              bgcolor: '#FEF3C7',
              color: '#D97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <DeveloperModeIcon sx={{ fontSize: 32 }} />
          </Box>
          <Box>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 800, color: '#0F172A' }}>
              Môi trường Phát triển & Kiểm thử (Dev Only)
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Trang kỹ thuật dành riêng cho nhà phát triển và kiểm thử viên — Không hiển thị trong giao diện sản phẩm.
            </Typography>
          </Box>
        </Box>

        <Alert severity="warning" sx={{ mb: 4, borderRadius: 2 }}>
          Trang này chỉ kích hoạt khi cờ <code>VITE_SHOW_DEV_TOOLS=true</code>. Học sinh và người dùng thực tế không bao giờ thấy trang này.
        </Alert>

        <Grid container spacing={3}>
          {/* Card 1: Student Metro / Expo LAN Tooling */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card sx={{ height: '100%', bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <QrCode2Icon sx={{ color: '#4F46E5', fontSize: 28 }} />
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    Student Mobile (Metro LAN)
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 2 }}>
                  Quy trình khởi chạy và kiểm thử ứng dụng học sinh di động trên thiết bị thật:
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 2.5 }}>
                  <Box sx={{ p: 1.5, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#4F46E5', display: 'block' }}>
                      LỆNH KHỞI CHẠY HỆ THỐNG:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#0F172A' }}>
                      RUN_MATHVISION.bat
                    </Typography>
                  </Box>
                  <Box sx={{ p: 1.5, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#4F46E5', display: 'block' }}>
                      CỬA SỔ TERMINAL EXPO QR:
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#334155' }}>
                      MathVision Kids - Student Mobile (Metro LAN)
                    </Typography>
                  </Box>
                  <Box sx={{ p: 1.5, bgcolor: '#FFFFFF', borderRadius: 2, border: '1px solid #E2E8F0' }}>
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#4F46E5', display: 'block' }}>
                      METRO BUNDLER PORT:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#0F172A' }}>
                      http://localhost:8081 (LAN host)
                    </Typography>
                  </Box>
                </Box>

                <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.85rem' }}>
                  • Kết nối điện thoại và laptop cùng Wi-Fi.<br />
                  • Mở Expo Go và quét mã QR thật từ cửa sổ console Metro.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Card 2: Backend Architecture & Ports */}
          <Grid size={{ xs: 12, sm: 6 }}>
            <Card sx={{ height: '100%', bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <DnsIcon sx={{ color: '#059669', fontSize: 28 }} />
                  <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    Kiến trúc Dịch vụ & Cổng
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#64748B', mb: 2 }}>
                  Danh sách cổng các dịch vụ cục bộ:
                </Typography>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>Unified Portal</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>5172</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>Teacher Web</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>5173</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>Admin Web</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>5174</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>Student Metro Bundler</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>8081</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>Spring Boot API</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>8080</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>FastAPI AI (Loopback)</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>8000 (127.0.0.1)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #E2E8F0' }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>PostgreSQL / Redis</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>5432 / 6379</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                    <Typography variant="body2" sx={{ color: '#334155' }}>MinIO API / Console</Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>9000 / 9001</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4 }} />

        {/* Demo Accounts for Developer Testing */}
        <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A', mb: 2 }}>
          Tài khoản Demo dành cho Kiểm thử
        </Typography>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 2, bgcolor: '#EEF2FF', border: '1px solid #C7D2FE', borderRadius: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <SchoolIcon sx={{ color: '#4F46E5', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#312E81' }}>
                  Học sinh
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#1E1B4B', mb: 0.5 }}>
                an.student@mathvision.local
              </Typography>
              <Typography variant="caption" sx={{ color: '#4338CA', display: 'block', mb: 1.5 }}>
                Mật khẩu: MathVision123!
              </Typography>
              <Button
                size="small"
                variant="outlined"
                startIcon={<ContentCopyIcon />}
                onClick={() => copyToClipboard('an.student@mathvision.local', 'student')}
                sx={{ bgcolor: '#FFFFFF' }}
              >
                {copied === 'student' ? 'Đã sao chép' : 'Sao chép Email'}
              </Button>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 2, bgcolor: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <PersonIcon sx={{ color: '#059669', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#064E3B' }}>
                  Giáo viên
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#022C22', mb: 0.5 }}>
                lan.teacher@mathvision.local
              </Typography>
              <Typography variant="caption" sx={{ color: '#047857', display: 'block', mb: 1.5 }}>
                Mật khẩu: MathVision123!
              </Typography>
              <Button
                size="small"
                variant="outlined"
                color="success"
                startIcon={<ContentCopyIcon />}
                onClick={() => copyToClipboard('lan.teacher@mathvision.local', 'teacher')}
                sx={{ bgcolor: '#FFFFFF' }}
              >
                {copied === 'teacher' ? 'Đã sao chép' : 'Sao chép Email'}
              </Button>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Paper sx={{ p: 2, bgcolor: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 2.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <AdminPanelSettingsIcon sx={{ color: '#D97706', fontSize: 20 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#78350F' }}>
                  Quản trị viên
                </Typography>
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#451A03', mb: 0.5 }}>
                admin@mathvision.local
              </Typography>
              <Typography variant="caption" sx={{ color: '#B45309', display: 'block', mb: 1.5 }}>
                Mật khẩu: MathVision123!
              </Typography>
              <Button
                size="small"
                variant="outlined"
                color="warning"
                startIcon={<ContentCopyIcon />}
                onClick={() => copyToClipboard('admin@mathvision.local', 'admin')}
                sx={{ bgcolor: '#FFFFFF' }}
              >
                {copied === 'admin' ? 'Đã sao chép' : 'Sao chép Email'}
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};
