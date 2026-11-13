import { Box, Card, CardContent, Typography } from '@mui/material';
import InsightsOutlined from '@mui/icons-material/InsightsOutlined';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';

export function RecognitionAnalyticsPage() {
  return (
    <Box>
      <AdminTopbar title="Theo dõi nhận diện" />
      <PageContent>
        <PageHeader
          title="Theo dõi nhận diện AI"
          description="Số liệu tổng hợp về nhận diện nét chữ trên bài làm."
        />
        <Card component="section" aria-labelledby="recognition-data-heading">
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, px: { xs: 2, sm: 3 }, py: 1.5, bgcolor: 'var(--admin-paper)', borderBottom: 1, borderColor: 'var(--admin-paper-line)' }}>
            <InsightsOutlined color="primary" />
            <Typography component="h2" id="recognition-data-heading" variant="h4">Dữ liệu nhận diện</Typography>
          </Box>
          <CardContent sx={{ p: { xs: 2, sm: 3 }, '&:last-child': { pb: { xs: 2, sm: 3 } } }}>
            <Typography component="h3" variant="h5" sx={{ mb: 0.75 }}>Chưa có nguồn thống kê tổng hợp</Typography>
            <Typography color="text.secondary" sx={{ maxWidth: '65ch' }}>
              Các chỉ số sẽ xuất hiện khi hệ thống có nguồn dữ liệu được xác minh. Độ tin cậy là mức chắc chắn do mô hình báo. Độ chính xác được đo bằng cách đối chiếu kết quả với nhãn đã kiểm chứng.
            </Typography>
          </CardContent>
        </Card>
      </PageContent>
    </Box>
  );
}
