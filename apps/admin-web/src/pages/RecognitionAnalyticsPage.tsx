import { Box, Card, CardContent, Grid, Typography } from '@mui/material';
import { Analytics, PhotoLibrary, FormatListNumbered, VerifiedOutlined } from '@mui/icons-material';
import { AdminTopbar } from '../components/layout/AdminTopbar';

const METRICS = [
  { title: 'Ảnh đã xử lý', icon: <PhotoLibrary /> },
  { title: 'Dòng được nhận dạng', icon: <FormatListNumbered /> },
  { title: 'Độ tin cậy nhận dạng', icon: <VerifiedOutlined /> },
];
export const RecognitionAnalyticsPage: React.FC = () => (
  <Box>
    <AdminTopbar title="Phân tích nhận dạng" subtitle="Theo dõi chất lượng đọc và nhận dạng bài làm" />
    <Box className="workspace-content" sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {METRICS.map(metric => <Grid size={{ xs: 12, md: 4 }} key={metric.title}>
          <Card><CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, color: 'primary.main', mb: 2 }}>{metric.icon}<Typography variant="subtitle2" component="p" color="text.secondary">{metric.title}</Typography></Box>
            <Typography variant="h4" component="p" aria-label="Chưa có dữ liệu">—</Typography>
            <Typography variant="caption" color="text.secondary">Chưa có dữ liệu thống kê</Typography>
          </CardContent></Card>
        </Grid>)}
      </Grid>
      <Card>
        <CardContent sx={{ py: { xs: 5, md: 8 }, textAlign: 'center' }}>
          <Box sx={{ display: 'inline-flex', p: 2.5, bgcolor: 'primary.light', borderRadius: '50%', color: 'primary.main', mb: 2 }}><Analytics sx={{ fontSize: 36 }} /></Box>
          <Typography variant="h5" component="h2" sx={{ mb: 1 }}>Chưa có thống kê nhận dạng</Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 540, mx: 'auto' }}>
            Trang này chưa kết nối nguồn thống kê nhận dạng thực tế. Biểu đồ và chỉ số sẽ được hiển thị khi có dữ liệu đã xác minh.
          </Typography>
          <Typography variant="body2" sx={{ mt: 2, color: 'primary.dark' }}>Không sử dụng số liệu mẫu để đánh giá chất lượng mô hình.</Typography>
        </CardContent>
      </Card>
    </Box>
  </Box>
);
