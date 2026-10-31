import { Box, Card, CardContent, Typography } from '@mui/material';
import InsightsOutlined from '@mui/icons-material/InsightsOutlined';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
export function RecognitionAnalyticsPage() {
  return <Box><AdminTopbar title="Theo dõi nhận diện" subtitle="Thống kê tổng hợp về quá trình nhận diện bài làm" /><PageContent>
    <Card><CardContent sx={{ py: { xs: 5, sm: 9 }, textAlign: 'center' }}>
      <Box sx={{ display: 'inline-flex', p: 2, borderRadius: 3, bgcolor: 'primary.light', color: 'primary.main', mb: 3 }}><InsightsOutlined sx={{ fontSize: 38 }} /></Box>
      <Typography variant="h5" component="h2" sx={{ mb: 1.5 }}>Chưa có nguồn thống kê tổng hợp</Typography>
      <Typography color="text.secondary" sx={{ maxWidth: 560, mx: 'auto' }}>Hệ thống hiện chưa cung cấp dữ liệu nhận diện tổng hợp cho quản trị viên. Các chỉ số sẽ xuất hiện khi có nguồn dữ liệu được xác minh.</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 3, maxWidth: 560, mx: 'auto' }}>Độ tin cậy của mô hình và độ chính xác là hai chỉ số khác nhau. Đánh giá độ chính xác cần kết quả đối chiếu với nhãn đã kiểm chứng.</Typography>
    </CardContent></Card>
  </PageContent></Box>;
}
