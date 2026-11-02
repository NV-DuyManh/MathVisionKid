import { Box, Card } from '@mui/material';
import InsightsOutlined from '@mui/icons-material/InsightsOutlined';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';
import { EmptyState } from '../components/common/EmptyState';

export function RecognitionAnalyticsPage() {
  return (
    <Box>
      <AdminTopbar title="Theo dõi nhận diện" subtitle="Thống kê tổng hợp về quá trình nhận diện bài làm" />
      <PageContent>
        <PageHeader
          title="Theo dõi nhận diện AI"
          description="Báo cáo chuyên sâu về hiệu năng và phân tích mô hình bóc tách nét chữ ô ly."
        />
        <Card sx={{ borderRadius: 3.5, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <EmptyState
            title="Chưa có nguồn thống kê tổng hợp"
            description="Hệ thống hiện chưa cung cấp dữ liệu nhận diện tổng hợp cho quản trị viên. Các chỉ số sẽ xuất hiện khi có nguồn dữ liệu được xác minh. Độ tin cậy của mô hình và độ chính xác là hai chỉ số khác nhau, cần kết quả đối chiếu với nhãn đã kiểm chứng."
            icon={<InsightsOutlined sx={{ fontSize: 42, color: '#2563EB' }} />}
          />
        </Card>
      </PageContent>
    </Box>
  );
}

export default RecognitionAnalyticsPage;
