import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  Typography,
} from '@mui/material';
import Add from '@mui/icons-material/Add';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { PageHeader } from '../components/common/PageHeader';
import { RequestError } from '../components/common/RequestError';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { ClassFormDialog } from '../components/classes/ClassFormDialog';

export function ClassesPage() {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const [creating, setCreating] = useState(params.get('create') === 'true');
  const [saved, setSaved] = useState(false);
  const query = useQuery({
    queryKey: ['admin-classes', page, size],
    queryFn: () => adminService.getClasses({ page, size }),
  });

  return (
    <Box>
      <AdminTopbar title="Quản lý lớp học" subtitle="Tổ chức lớp học, phân công giáo viên và quản lý sĩ số" />
      <PageContent>
        <PageHeader
          title="Danh sách lớp học"
          description={
            query.data ? `${query.data.totalElements} lớp trong hệ thống` : 'Dữ liệu lớp học từ hệ thống quản lý'
          }
          actions={
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => {
                setSaved(false);
                setCreating(true);
              }}
              sx={{ borderRadius: 2.5, fontWeight: 700 }}
            >
              Tạo lớp học
            </Button>
          }
        />

        {saved && (
          <Alert severity="success" sx={{ mb: 2, borderRadius: 2.5 }} onClose={() => setSaved(false)}>
            Đã tạo lớp học thành công.
          </Alert>
        )}

        <RequestError
          error={query.error}
          retry={() => {
            void query.refetch();
          }}
        />

        {!query.error && (
          <Card sx={{ borderRadius: 3.5, overflow: 'hidden', border: '1px solid #E2E8F0' }}>
            <TableContainer>
              <Table aria-label="Danh sách lớp học" sx={{ minWidth: 700 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Lớp học</TableCell>
                    <TableCell>Khối</TableCell>
                    <TableCell>Năm học</TableCell>
                    <TableCell>Giáo viên phụ trách</TableCell>
                    <TableCell>Sĩ số</TableCell>
                    <TableCell align="right">Thao tác</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {query.isLoading ? (
                    <TableSkeleton rows={5} columns={6} />
                  ) : query.data?.content.length ? (
                    query.data.content.map((c) => (
                      <TableRow key={c.classId} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 800, color: '#0F172A' }}>
                            {c.name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#64748B' }}>
                            {new Date(c.createdAt).toLocaleDateString('vi-VN')}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ color: '#334155' }}>Khối {c.gradeLevel}</TableCell>
                        <TableCell sx={{ color: '#334155' }}>{c.academicYear || 'Chưa xác định'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                            {c.teacher?.displayName || 'Chưa phân công'}
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#64748B' }}>
                            {c.teacher?.email}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ fontWeight: 700, color: '#334155' }}>{c.studentCount} học sinh</TableCell>
                        <TableCell align="right">
                          <Button
                            component={Link}
                            to={`/classes/${c.classId}`}
                            variant="outlined"
                            size="small"
                            aria-label={`Xem chi tiết ${c.name}`}
                            sx={{
                              borderRadius: 2,
                              fontWeight: 700,
                              borderColor: '#CBD5E1',
                              color: '#0F172A',
                              '&:hover': { borderColor: '#94A3B8', bgcolor: '#F8FAFC' },
                            }}
                          >
                            Chi tiết
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <EmptyState
                          title="Chưa có lớp học"
                          description="Tạo lớp và chọn giáo viên để bắt đầu."
                          actionText="Tạo lớp học"
                          onAction={() => setCreating(true)}
                        />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              component="div"
              count={query.data?.totalElements || 0}
              page={page}
              rowsPerPage={size}
              rowsPerPageOptions={[10, 20, 50]}
              onPageChange={(_, p) => setPage(p)}
              onRowsPerPageChange={(e) => {
                setSize(Number(e.target.value));
                setPage(0);
              }}
            />
          </Card>
        )}

        {creating && (
          <ClassFormDialog
            onSaved={() => setSaved(true)}
            onClose={() => {
              setCreating(false);
              if (params.has('create')) {
                params.delete('create');
                setParams(params, { replace: true });
              }
            }}
          />
        )}
      </PageContent>
    </Box>
  );
}
