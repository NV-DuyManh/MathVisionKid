import { useState } from 'react';
import { Box, Button, Card, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Table, TableBody, TableCell, TableHead, TablePagination, TableRow, TextField, Typography } from '@mui/material';
import RefreshOutlined from '@mui/icons-material/RefreshOutlined';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { RequestError } from '../components/common/RequestError';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { AuditEventChip, EVENT_LABELS } from '../components/common/AuditEventChip';
import { AuditMetadata } from '../components/common/AuditMetadata';
import { PageHeader } from '../components/common/PageHeader';
import { LedgerTable } from '../components/common/LedgerTable';
import { EmptyState } from '../components/common/EmptyState';
import type { AdminAuditEventResponse } from '../types';

export function AuditPage() {
  const [type, setType] = useState('');
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const [selected, setSelected] = useState<AdminAuditEventResponse | null>(null);
  const query = useQuery({
    queryKey: ['admin-audit', type, page, size],
    queryFn: () => adminService.getAudit({ eventType: type || undefined, page, size }),
  });
  const refresh = () => { void query.refetch(); };

  return (
    <Box>
      <AdminTopbar title="Nhật ký hệ thống" />
      <PageContent>
        <PageHeader
          title="Lịch sử hoạt động"
          description="Tra cứu sự kiện, thời điểm và người thao tác."
          actions={
            <Button variant="outlined" startIcon={<RefreshOutlined />} disabled={query.isFetching} onClick={refresh}>
              Làm mới nhật ký
            </Button>
          }
        />
        <RequestError error={query.error} retry={refresh} />
        <Card aria-busy={query.isFetching}>
          <Box className="filter-bar">
            <TextField select label="Loại sự kiện" size="small" value={type} sx={{ width: 290, maxWidth: '100%' }}
              onChange={event => { setType(event.target.value); setPage(0); }}>
              <MenuItem value="">Tất cả sự kiện</MenuItem>
              {Object.entries(EVENT_LABELS).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </TextField>
          </Box>
          {!query.error && (
            <>
              <LedgerTable label="Vùng cuộn bảng nhật ký">
                <Table aria-label="Nhật ký hệ thống" sx={{ minWidth: 680 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Thời gian</TableCell>
                      <TableCell>Người thao tác</TableCell>
                      <TableCell>Sự kiện</TableCell>
                      <TableCell align="right">Chi tiết</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {query.isLoading ? <TableSkeleton rows={5} columns={4} /> : query.data?.content.length ? query.data.content.map(event => (
                      <TableRow hover key={event.auditEventId}>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          <time dateTime={event.createdAt}>{new Date(event.createdAt).toLocaleString('vi-VN')}</time>
                        </TableCell>
                        <TableCell sx={{ maxWidth: 240, overflowWrap: 'anywhere' }}>{event.actorEmail || 'Hệ thống'}</TableCell>
                        <TableCell><AuditEventChip type={event.eventType} /></TableCell>
                        <TableCell align="right">
                          <Button size="small" variant="outlined" aria-label={`Xem sự kiện ${event.auditEventId}`}
                            onClick={() => setSelected(event)} sx={{ whiteSpace: 'nowrap' }}>Xem chi tiết</Button>
                        </TableCell>
                      </TableRow>
                    )) : (
                      <TableRow>
                        <TableCell colSpan={4}>
                          <EmptyState title="Chưa có sự kiện phù hợp" description="Chọn loại sự kiện khác hoặc làm mới nhật ký." />
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </LedgerTable>
              <TablePagination
                component="div" count={query.data?.totalElements || 0} page={page} rowsPerPage={size} rowsPerPageOptions={[10, 20, 50]}
                onPageChange={(_, value) => setPage(value)}
                onRowsPerPageChange={event => { setSize(Number(event.target.value)); setPage(0); }}
              />
            </>
          )}
        </Card>
        <Dialog open={!!selected} onClose={() => setSelected(null)} fullWidth maxWidth="sm" aria-labelledby="audit-title">
          <DialogTitle id="audit-title">Chi tiết sự kiện</DialogTitle>
          <DialogContent>
            {selected && (
              <>
                <AuditEventChip type={selected.eventType} />
                <Box component="dl" sx={{ mx: 0, mt: 2, mb: 2, display: 'grid', gap: 1 }}>
                  {[
                    ['Thời gian', new Date(selected.createdAt).toLocaleString('vi-VN')],
                    ['Người thao tác', selected.actorEmail || 'Hệ thống'],
                    ['Mã sự kiện', selected.auditEventId],
                  ].map(([label, value]) => (
                    <Box key={label} sx={{ pt: 1, borderTop: 1, borderColor: 'divider' }}>
                      <Typography component="dt" variant="body2" color="text.secondary">{label}</Typography>
                      <Typography component="dd" variant="body2" sx={{ m: 0, fontWeight: 700, color: 'text.primary', overflowWrap: 'anywhere' }}>{value}</Typography>
                    </Box>
                  ))}
                </Box>
                <AuditMetadata metadata={selected.metadata} />
              </>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}><Button autoFocus variant="contained" onClick={() => setSelected(null)}>Đóng</Button></DialogActions>
        </Dialog>
      </PageContent>
    </Box>
  );
}
