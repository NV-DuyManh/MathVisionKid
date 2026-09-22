import { Box, Typography, Card, CardContent, Grid, Divider, Chip } from '@mui/material';
import { Person, Security, InfoOutlined } from '@mui/icons-material';
import { useAuth } from '../components/layout/AuthContext';

export default function SettingsPage() {
  const { user } = useAuth();
  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.name || 'Giáo viên');

  return (
    <Box sx={{ maxWidth: 960, mx: 'auto' }}>
      <Box sx={{ mb: 3.5 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          Cài đặt & Thông tin tài khoản
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Thông tin giáo viên, quy chuẩn bảo mật dữ liệu và cấu hình hệ thống chấm bài.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ borderRadius: 2.5, height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Person sx={{ color: '#2563EB', fontSize: 24 }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Thông tin Giáo viên
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  Họ và tên
                </Typography>
                <Typography variant="body1" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  {displayName}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  Email công vụ
                </Typography>
                <Typography variant="body1" sx={{ color: '#0F172A' }}>
                  {user?.email || '—'}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  Vai trò hệ thống
                </Typography>
                <Chip
                  label="Giáo viên Tiểu học (TEACHER)"
                  size="small"
                  sx={{ bgcolor: '#EFF6FF', color: '#1D4ED8', fontWeight: 600, mt: 0.5 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Security & Privacy Standards Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ borderRadius: 2.5, height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Security sx={{ color: '#0D9488', fontSize: 24 }} />
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Tiêu chuẩn Quyền riêng tư
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.6 }}>
                • <strong>Che thông tin thủ công (Manual Masking):</strong> Tất cả ảnh chụp bài làm của học sinh được giáo viên che tên và con dấu trường học trước khi tải lên máy chủ OCR.
              </Typography>
              <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.6 }}>
                • <strong>Bảo vệ dữ liệu trẻ em:</strong> Hệ thống không lưu trữ danh tính nhạy cảm kết nối công khai với hình ảnh gốc.
              </Typography>
              <Typography variant="body2" sx={{ lineHeight: 1.6 }}>
                • <strong>Thẩm quyền con người:</strong> Đề xuất điểm từ mô hình trí tuệ nhân tạo chỉ mang tính chất tham vấn. Giáo viên toàn quyền phê duyệt hoặc điều chỉnh.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* System info */}
        <Grid size={{ xs: 12 }}>
          <Card sx={{ borderRadius: 2.5, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0' }}>
            <CardContent sx={{ p: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <InfoOutlined sx={{ color: '#64748B' }} />
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    MathVision Kids — Phiên bản Cổng Giáo Viên
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Phiên bản v1.0.0 (Bản phát hành chính thức cho trường học)
                  </Typography>
                </Box>
              </Box>
              <Chip label="Hệ thống hoạt động bình thường" size="small" sx={{ bgcolor: '#DCFCE7', color: '#15803D', fontWeight: 600 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
