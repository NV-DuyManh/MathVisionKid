import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  Table,
  TableBody,
  TableCell,
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
import { LedgerTable } from '../components/common/LedgerTable';
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
      <AdminTopbar title="Quản lý lớp học" />
      <PageContent>
        <PageHeader
          title="Danh sách lớp học"
          description={
            query.data ? `${query.data.totalElements.toLocaleString('vi-VN')} lớp trong hệ thống` : 'Xem lớp học, sĩ số và giáo viên phụ trách.'
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
          <Card aria-busy={query.isFetching}>
            <LedgerTable label="Vùng cuộn bảng lớp học">
              <Table aria-label="Danh sách lớp học" sx={{ minWidth: 700 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Lớp học</TableCell>
                    <TableCell>Khối</TableCell>
                    <TableCell>Năm học</TableCell>
                    <TableCell>Giáo viên phụ trách</TableCell>
                    <TableCell align="right">Sĩ số</TableCell>
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
                          <Typography variant="body2" sx={{ fontWeight: 800, color: 'text.primary', overflowWrap: 'anywhere' }}>
                            {c.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                            {new Date(c.createdAt).toLocaleDateString('vi-VN')}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ color: '#334155' }}>Khối {c.gradeLevel}</TableCell>
                        <TableCell sx={{ color: '#334155' }}>{c.academicYear || 'Chưa xác định'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 700, color: 'text.primary', overflowWrap: 'anywhere' }}>
                            {c.teacher?.displayName || 'Chưa phân công'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                            {c.teacher?.email}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, color: 'text.primary', whiteSpace: 'nowrap' }}>{c.studentCount.toLocaleString('vi-VN')}</TableCell>
                        <TableCell align="right">
                          <Button
                            component={Link}
                            to={`/classes/${c.classId}`}
                            variant="outlined"
                            size="small"
                            aria-label={`Xem chi tiết ${c.name}`}
                            sx={{
                              whiteSpace: 'nowrap',
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
            </LedgerTable>
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
