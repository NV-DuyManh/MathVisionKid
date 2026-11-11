import { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Paper,
  Divider,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  Alert,
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { AppTeacherService } from '../services/api/ServiceLocator';
import { CheckCircle, ArrowBack, ArrowForward, AutoAwesome, FilterList, Search } from '@mui/icons-material';
import { StatusChip } from '../components/common/StatusChip';
import { PageHeader } from '../components/common/PageHeader';

export default function ReviewQueuePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('DEFAULT');

  const { data: queue, isLoading, isError } = useQuery({
    queryKey: ['reviewQueue', id],
    queryFn: () => AppTeacherService.getReviewQueue(id!),
    enabled: !!id,
  });

  const filteredQueue = useMemo(() => {
    if (!queue) return [];
    const query = searchQuery.trim().toLocaleLowerCase('vi');
    const list = queue.filter((sub) =>
      (statusFilter === 'ALL' || sub.status === statusFilter)
      && (!query || sub.studentName?.toLocaleLowerCase('vi').includes(query)),
    );

    if (sortBy === 'CONFIDENCE_ASC') {
      list.sort((a, b) => (a.recognitionConfidence ?? 101) - (b.recognitionConfidence ?? 101));
    } else if (sortBy === 'SCORE_ASC') {
      list.sort((a, b) => (a.suggestedScore ?? Number.MAX_SAFE_INTEGER) - (b.suggestedScore ?? Number.MAX_SAFE_INTEGER));
    } else if (sortBy === 'SCORE_DESC') {
      list.sort((a, b) => (b.suggestedScore ?? -1) - (a.suggestedScore ?? -1));
    }
    return list;
  }, [queue, statusFilter, searchQuery, sortBy]);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Đang tải danh sách bài làm cần xem lại...
        </Typography>
      </Box>
    );
  }

  if (isError || !queue) {
    return (
      <Box sx={{ textAlign: 'center', mt: 6, p: 4 }}>
        <Typography color="error" variant="h6" component="h1" sx={{ mb: 2 }}>
          Đã xảy ra lỗi khi tải hàng đợi duyệt.
        </Typography>
        <Button variant="outlined" onClick={() => navigate(`/batches/${id}`)}>
          Quay lại đợt chấm
        </Button>
      </Box>
    );
  }

  // Meaningful completion state per Section 34
  if (queue.length === 0) {
    return (
      <Box sx={{ maxWidth: 680, mx: 'auto', textAlign: 'center', mt: 8 }}>
        <Paper
          variant="outlined"
          sx={{
            p: 5,
            bgcolor: '#F0FDF4',
            borderColor: '#86EFAC',
            borderRadius: 3,
          }}
        >
          <CheckCircle sx={{ fontSize: 56, color: '#16A34A', mb: 1.5 }} />
          <Typography variant="h5" component="h1" sx={{ fontWeight: 800, color: '#15803D', mb: 1 }}>
            Đã xử lý hết các bài cần giáo viên xem lại.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 440, mx: 'auto', mb: 3 }}>
            Tất cả các bài làm trong đợt này đã được giáo viên xem xét hoặc đã có đầy đủ đề xuất từ hệ thống.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button variant="outlined" onClick={() => navigate(`/batches/${id}`)}>
              Xem chi tiết đợt chấm
            </Button>
            <Button variant="contained" onClick={() => navigate('/dashboard')}>
              Về trang tổng quan
            </Button>
          </Box>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <Button
        variant="text"
        startIcon={<ArrowBack />}
        onClick={() => navigate(`/batches/${id}`)}
        sx={{ mb: 2 }}
      >
        Quay lại chi tiết đợt chấm
      </Button>

      <PageHeader
        title="Hàng đợi Thẩm định & Duyệt bài"
        subtitle={`Có ${queue.length} bài làm cần giáo viên thẩm định và quyết định điểm số chính thức.`}
      />

      {/* Filter and Sorting Toolbar (SCRUM-111) */}
      <Paper
        variant="outlined"
        sx={{
          p: 2.5,
          mb: 3,
          borderRadius: 2.5,
          bgcolor: '#FFFFFF',
          borderColor: '#E2E8F0',
        }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            label="Tên học sinh"
            placeholder="Tìm theo tên học sinh..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            slotProps={{
              input: {
                startAdornment: <Search sx={{ fontSize: 18, color: '#94A3B8', mr: 1 }} />,
              },
            }}
            sx={{ minWidth: 220, flex: { xs: '1 1 100%', sm: '1 1 auto' } }}
          />

          <FormControl size="small" sx={{ minWidth: 170 }}>
            <InputLabel id="filter-status-label">Trạng thái</InputLabel>
            <Select
              labelId="filter-status-label"
              value={statusFilter}
              label="Trạng thái"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="ALL">Tất cả trạng thái</MenuItem>
              <MenuItem value="REVIEW_REQUIRED">Cần giáo viên duyệt</MenuItem>
              <MenuItem value="PROPOSED_GRADE">Có điểm đề xuất</MenuItem>
              <MenuItem value="FEEDBACK_READY">Có phản hồi</MenuItem>
              <MenuItem value="NEEDS_CONFIRMATION">Cần xác nhận nét chữ</MenuItem>
              <MenuItem value="NEEDS_RETAKE">Cần chụp lại</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 190 }}>
            <InputLabel id="sort-by-label">Sắp xếp theo</InputLabel>
            <Select
              labelId="sort-by-label"
              value={sortBy}
              label="Sắp xếp theo"
              onChange={(e) => setSortBy(e.target.value)}
            >
              <MenuItem value="DEFAULT">Thứ tự mặc định</MenuItem>
              <MenuItem value="CONFIDENCE_ASC">Độ tin cậy: Thấp → Cao</MenuItem>
              <MenuItem value="SCORE_ASC">Điểm đề xuất: Thấp → Cao</MenuItem>
              <MenuItem value="SCORE_DESC">Điểm đề xuất: Cao → Thấp</MenuItem>
            </Select>
          </FormControl>

          {(statusFilter !== 'ALL' || searchQuery.trim() !== '' || sortBy !== 'DEFAULT') && (
            <Button
              variant="text"
              size="small"
              onClick={() => {
                setStatusFilter('ALL');
                setSearchQuery('');
                setSortBy('DEFAULT');
              }}
              sx={{ textTransform: 'none', color: '#64748B' }}
            >
              Đặt lại bộ lọc
            </Button>
          )}

          <Box sx={{ ml: 'auto' }}>
            <Chip
              icon={<FilterList sx={{ fontSize: 16 }} />}
              label={`Hiển thị ${filteredQueue.length} / ${queue.length} bài`}
              size="small"
              color={filteredQueue.length > 0 ? 'primary' : 'default'}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          </Box>
        </Box>
      </Paper>

      {filteredQueue.length === 0 ? (
        <Alert severity="info" sx={{ borderRadius: 2, my: 4 }}>
          Không tìm thấy bài làm nào phù hợp với bộ lọc hiện tại. Vui lòng thử đổi từ khóa tìm kiếm hoặc trạng thái.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredQueue.map((sub, idx) => {
            const subId = sub.id || sub.submissionId || '';
            const recConf = sub.recognitionConfidence !== undefined ? `${Math.round(sub.recognitionConfidence)}%` : 'Chưa có';
            const diagConf = sub.diagnosisConfidence !== undefined ? `${Math.round(sub.diagnosisConfidence)}%` : 'Chưa có';
            const suggested = sub.suggestedScore;
            const scale = (typeof sub.maxScore === 'number' && Number.isFinite(sub.maxScore) && sub.maxScore > 0)
              ? sub.maxScore
              : 10;

            return (
              <Grid size={{ xs: 12, md: 6, lg: 4 }} key={subId}>
                <Card
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                    borderRadius: 2.5,
                    border: '1.5px solid #FCA5A5',
                    boxShadow: '0 1px 3px rgba(15,23,42,0.05)',
                    transition: 'box-shadow 150ms ease, transform 150ms ease',
                    '&:hover': {
                      boxShadow: '0 6px 16px rgba(220, 38, 38, 0.1)',
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2.5 }}>
                    {/* Top Bar: Student Name + StatusChip */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                          {sub.studentName || `Học sinh #${idx + 1}`}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Thứ tự trong hàng đợi: #{idx + 1}/{filteredQueue.length}
                        </Typography>
                      </Box>
                      <StatusChip status={sub.status} />
                    </Box>

                    {/* Review reason callout */}
                    <Box
                      sx={{
                        bgcolor: '#FEF2F2',
                        p: 1.75,
                        borderRadius: 2,
                        mb: 2,
                        border: '1px solid #FECACA',
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 700, color: '#991B1B', display: 'block' }}>
                        Lý do cần giáo viên xem xét:
                      </Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#7F1D1D', mt: 0.25 }}>
                        {sub.evidence?.rule || 'Cần xác nhận nét chữ hoặc bước đặt tính'}
                      </Typography>
                    </Box>

                    {/* Advisory Score and Confidence Metrics */}
                    <Box sx={{ bgcolor: '#F8FAFC', p: 1.75, borderRadius: 2, border: '1px solid #E2E8F0', mb: 2.5, flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <AutoAwesome sx={{ fontSize: 16, color: '#2563EB' }} />
                          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                            AI đề xuất (chưa chính thức):
                          </Typography>
                        </Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#2563EB' }}>
                          {suggested !== undefined ? `${suggested} / ${scale} điểm` : 'Chưa chấm'}
                        </Typography>
                      </Box>

                      <Divider sx={{ my: 1 }} />

                      <Grid container spacing={1}>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            Độ tin cậy nhận diện:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                            {recConf}
                          </Typography>
                        </Grid>
                        <Grid size={{ xs: 6 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            Độ tin cậy chẩn đoán:
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                            {diagConf}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>

                    {/* Primary Action */}
                    <Button
                      variant="contained"
                      fullWidth
                      size="medium"
                      endIcon={<ArrowForward />}
                      onClick={() => navigate(`/submissions/${encodeURIComponent(subId)}?from=review`)}
                      sx={{
                        py: 1.1,
                        fontWeight: 700,
                      }}
                    >
                      Duyệt bài này
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}
