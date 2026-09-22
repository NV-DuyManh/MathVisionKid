import React, { useState } from 'react';
import {
  Box,
  Card,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import type { AdminAuditEventResponse } from '../types';

const EVENT_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  ADMIN_USER_CREATED: { label: 'TẠO NGƯỜI DÙNG', color: '#16A34A' },
  ADMIN_USER_UPDATED: { label: 'CẬP NHẬT HỒ SƠ', color: '#2563EB' },
  ADMIN_USER_DISABLED: { label: 'VÔ HIỆU HÓA', color: '#DC2626' },
  ADMIN_USER_ENABLED: { label: 'KÍCH HOẠT LẠI', color: '#059669' },
  ADMIN_USER_PASSWORD_RESET: { label: 'ĐẶT LẠI MẬT KHẨU', color: '#D97706' },
  ADMIN_CLASS_CREATED: { label: 'TẠO LỚP HỌC', color: '#9333EA' },
  ADMIN_CLASS_UPDATED: { label: 'CẬP NHẬT LỚP', color: '#4F46E5' },
  ADMIN_CLASS_TEACHER_ASSIGNED: { label: 'GÁN GIÁO VIÊN', color: '#0284C7' },
  ADMIN_STUDENT_ADDED_TO_CLASS: { label: 'THÊM HỌC SINH', color: '#0D9488' },
  ADMIN_STUDENT_REMOVED_FROM_CLASS: { label: 'XÓA HỌC SINH', color: '#E11D48' },
};

export const AuditPage: React.FC = () => {
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [page, setPage] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(10);
  const [selectedEvent, setSelectedEvent] = useState<AdminAuditEventResponse | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['admin-audit', eventTypeFilter, page, pageSize],
    queryFn: () =>
      adminService.getAudit({
        eventType: eventTypeFilter === 'ALL' ? undefined : eventTypeFilter,
        page,
        size: pageSize,
      }),
  });

  return (
    <Box>
      <AdminTopbar title="Nhật ký Hệ thống" subtitle="Lịch sử thao tác quản trị tài khoản và danh sách lớp học" />

      <Box sx={{ p: { xs: 2, md: 4 } }}>
        {/* Filter Row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HistoryIcon sx={{ color: '#0F172A' }} />
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
              Nhật ký kiểm toán (Audit Trail)
            </Typography>
          </Box>

          <FormControl size="small" sx={{ minWidth: 260 }}>
            <InputLabel>Lọc theo loại hành động</InputLabel>
            <Select
              value={eventTypeFilter}
              label="Lọc theo loại hành động"
              onChange={(e) => {
                setEventTypeFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="ALL">Tất cả hành động</MenuItem>
              <MenuItem value="ADMIN_USER_CREATED">Tạo người dùng mới</MenuItem>
              <MenuItem value="ADMIN_USER_UPDATED">Cập nhật thông tin người dùng</MenuItem>
              <MenuItem value="ADMIN_USER_DISABLED">Vô hiệu hóa tài khoản</MenuItem>
              <MenuItem value="ADMIN_USER_ENABLED">Kích hoạt lại tài khoản</MenuItem>
              <MenuItem value="ADMIN_USER_PASSWORD_RESET">Đặt lại mật khẩu</MenuItem>
              <MenuItem value="ADMIN_CLASS_CREATED">Tạo lớp học</MenuItem>
              <MenuItem value="ADMIN_CLASS_UPDATED">Cập nhật lớp học</MenuItem>
              <MenuItem value="ADMIN_CLASS_TEACHER_ASSIGNED">Phân công giáo viên</MenuItem>
              <MenuItem value="ADMIN_STUDENT_ADDED_TO_CLASS">Thêm học sinh vào lớp</MenuItem>
              <MenuItem value="ADMIN_STUDENT_REMOVED_FROM_CLASS">Xóa học sinh khỏi lớp</MenuItem>
            </Select>
          </FormControl>
        </Box>

        {/* Audit Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Thời gian</TableCell>
                  <TableCell>Người thực hiện</TableCell>
                  <TableCell>Loại hành động</TableCell>
                  <TableCell>Dữ liệu thao tác (Metadata)</TableCell>
                  <TableCell align="right">Chi tiết</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading ? (
                  <TableSkeleton rows={pageSize} columns={5} />
                ) : data?.content && data.content.length > 0 ? (
                  data.content.map((ev) => {
                    const info = EVENT_TYPE_LABELS[ev.eventType] || {
                      label: ev.eventType,
                      color: '#475569',
                    };

                    return (
                      <TableRow key={ev.auditEventId} hover>
                        <TableCell sx={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                          {new Date(ev.createdAt).toLocaleString('vi-VN')}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 600, color: '#0F172A' }}>
                          {ev.actorEmail || 'Hệ thống'}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={info.label}
                            size="small"
                            sx={{
                              fontWeight: 600,
                              fontSize: '0.7rem',
                              bgcolor: `${info.color}15`,
                              color: info.color,
                              border: `1px solid ${info.color}40`,
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ color: '#475569', maxWidth: 320, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {ev.metadata ? JSON.stringify(ev.metadata) : '—'}
                        </TableCell>
                        <TableCell align="right">
                          <Button
                            size="small"
                            startIcon={<InfoOutlinedIcon fontSize="small" />}
                            onClick={() => setSelectedEvent(ev)}
                            sx={{ color: '#2563EB', fontWeight: 600 }}
                          >
                            Xem
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <EmptyState
                        title="Không có bản ghi nhật ký nào"
                        description="Chưa có hành động quản trị nào phù hợp với bộ lọc được chọn."
                      />
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={data?.totalElements ?? 0}
            page={page}
            onPageChange={(_, newPage) => setPage(newPage)}
            rowsPerPage={pageSize}
            onRowsPerPageChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setPage(0);
            }}
            rowsPerPageOptions={[5, 10, 20, 50]}
            labelRowsPerPage="Số hàng mỗi trang:"
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} trên ${count}`}
          />
        </Card>
      </Box>

      {/* Metadata Detail Dialog */}
      <Dialog
        open={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 700, color: '#0F172A' }}>
          Chi tiết bản ghi kiểm toán
        </DialogTitle>
        <DialogContent>
          {selectedEvent && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Mã bản ghi
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A', wordBreak: 'break-all' }}>
                  {selectedEvent.auditEventId}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Thời gian ghi nhận
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A' }}>
                  {new Date(selectedEvent.createdAt).toLocaleString('vi-VN')}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Quản trị viên thực hiện
                </Typography>
                <Typography variant="body2" sx={{ color: '#0F172A', fontWeight: 500 }}>
                  {selectedEvent.actorEmail} (ID: {selectedEvent.actorUserId})
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Loại hành động
                </Typography>
                <Typography variant="body2" sx={{ color: '#2563EB', fontWeight: 600 }}>
                  {selectedEvent.eventType}
                </Typography>
              </Box>

              <Box>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                  Dữ liệu thao tác (Metadata JSON)
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    p: 2,
                    bgcolor: '#F1F5F9',
                    borderRadius: 1.5,
                    fontSize: '0.8rem',
                    fontFamily: 'monospace',
                    overflow: 'auto',
                    maxHeight: 200,
                    border: '1px solid #E2E8F0',
                  }}
                >
                  {JSON.stringify(selectedEvent.metadata, null, 2)}
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            variant="contained"
            onClick={() => setSelectedEvent(null)}
            sx={{ bgcolor: '#0F172A', '&:hover': { bgcolor: '#1E293B' } }}
          >
            Đóng
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
