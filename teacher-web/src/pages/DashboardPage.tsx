import { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, Chip, Button, List, ListItem, ListItemText, Paper } from '@mui/material';
import { AssignmentTurnedIn, PendingActions, FactCheck, ChevronRight } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { DashboardStats } from '../types';
import { useAuth } from '../components/layout/AuthContext';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    AppTeacherService.getDashboard().then(setStats);
  }, []);

  if (!stats) return <Typography>Đang tải...</Typography>;

  const displayName = user?.firstName ? `${user.lastName || ''} ${user.firstName}`.trim() : (user?.displayName || 'cô Lan');

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'text.primary' }}>Xin chào, {displayName}</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Tổng quan công việc hôm nay của bạn.</Typography>

      <Grid container spacing={3} sx={{ mb: 6 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          {/* Cần xem lại is primary attention area */}
          <Card sx={{ bgcolor: 'error.main', color: 'white', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PendingActions sx={{ mr: 1 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: '600' }}>Cần giáo viên xem lại</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: '700', my: 1 }}>{stats.reviewRequired} bài</Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                AI đã hoàn tất chấm sơ bộ. Đang chờ quyết định cuối cùng từ giáo viên.
              </Typography>
              <Button 
                variant="contained" 
                color="inherit" 
                sx={{ mt: 3, color: 'error.main', bgcolor: 'white', '&:hover': { bgcolor: 'grey.100' } }}
                onClick={() => navigate('/classes')} // Should navigate to review queue ideally
              >
                Xử lý ngay
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 6 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography color="text.secondary" variant="subtitle2">Tổng bài hôm nay</Typography>
                    <AssignmentTurnedIn color="primary" />
                  </Box>
                  <Typography variant="h4" color="text.primary" sx={{ fontWeight: '700' }}>{stats?.totalToday || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Typography color="text.secondary" variant="subtitle2">Đã xử lý tự động</Typography>
                    <FactCheck color="success" />
                  </Box>
                  <Typography variant="h3" color="primary.main" sx={{ fontWeight: '700' }}>{stats?.reviewRequired || 0}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      <Typography variant="h5" sx={{ mb: 3 }}>Lượt chấm gần đây</Typography>
      <Paper variant="outlined" sx={{ borderRadius: 2 }}>
        <List sx={{ p: 0 }}>
          {stats.recentBatches.length === 0 ? (
            <ListItem><Typography color="text.secondary">Chưa có lượt chấm nào.</Typography></ListItem>
          ) : stats.recentBatches.map((batch, index) => (
            <ListItem 
              key={batch.id}
              divider={index !== stats.recentBatches.length - 1}
              sx={{ py: 2, px: 3, '&:hover': { bgcolor: 'grey.50' }, cursor: 'pointer', transition: 'background-color 150ms' }}
              onClick={() => navigate(`/batches/${batch.id}`)}
            >
              <ListItemText
                primary={<Typography variant="subtitle1" sx={{ fontWeight: '600' }}>Toán {batch.className}</Typography>}
                secondary={batch.assignmentTitle}
              />
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Chip label={`${batch.totalImages} ảnh`} size="small" />
                <Chip label={`${batch.processedCount} OK`} size="small" color="success" variant="outlined" />
                {batch.reviewRequiredCount > 0 && (
                  <Chip label={`${batch.reviewRequiredCount} Cần xem`} size="small" color="error" />
                )}
                <ChevronRight color="action" sx={{ ml: 2 }} />
              </Box>
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
