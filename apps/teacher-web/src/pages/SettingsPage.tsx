import { Box, Typography, Card, CardContent, Grid, Divider, Chip } from '@mui/material';
import { Person, Security, InfoOutlined } from '@mui/icons-material';
import { useAuth } from '../components/layout/AuthContext';
import { PageHeader } from '../components/common/PageHeader';

export default function SettingsPage() {
  const { user } = useAuth();
  const displayName = user?.firstName
    ? `${user.lastName || ''} ${user.firstName}`.trim()
    : (user?.displayName || user?.name || 'Giáo viên');

  return (
    <Box sx={{ maxWidth: 960, mx: 'auto' }}>
      <PageHeader
        title="Cài đặt & Thông tin tài khoản"
        subtitle="Thông tin giáo viên, quy chuẩn bảo mật dữ liệu và cấu hình hệ thống chấm bài."
      />

      <Grid container spacing={3}>
        {/* Profile Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ borderRadius: 2.5, height: '100%', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Person sx={{ color: '#059669', fontSize: 24 }} />
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
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
                  sx={{ bgcolor: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0', fontWeight: 600, mt: 0.5 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Security & Privacy Standards Card */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card sx={{ borderRadius: 2.5, height: '100%', border: '1px solid #E2E8F0', boxShadow: '0 1px 3px rgba(15,23,42,0.05)' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Security sx={{ color: '#059669', fontSize: 24 }} />
                <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  Tiêu chuẩn Quyền riêng tư
                </Typography>
              </Box>
              <Divider sx={{ mb: 2 }} />

              <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.6, color: '#334155' }}>
                • <strong>Che thông tin thủ công (Manual Masking):</strong> Tất cả ảnh chụp bài làm của học sinh được giáo viên che tên và con dấu trường học trước khi tải lên máy chủ OCR.
              </Typography>
              <Typography variant="body2" sx={{ mb: 1.5, lineHeight: 1.6, color: '#334155' }}>
                • <strong>Bảo vệ dữ liệu trẻ em:</strong> Hệ thống không lưu trữ danh tính nhạy cảm kết nối công khai với hình ảnh gốc.
              </Typography>
              <Typography variant="body2" sx={{ lineHeight: 1.6, color: '#334155' }}>
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
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    MathVision Kids — Phiên bản Cổng Giáo Viên
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Quản lý lớp học, giao bài và xem lại kết quả chấm bài.
                  </Typography>
                </Box>
              </Box>
              <Chip label="Không gian giáo viên" size="small" sx={{ bgcolor: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0', fontWeight: 600 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
