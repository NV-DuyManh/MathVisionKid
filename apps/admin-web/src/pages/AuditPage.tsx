import { useState } from 'react';
import { Box, Button, Card, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../services/api/adminService';
import { AdminTopbar } from '../components/layout/AdminTopbar';
import { PageContent } from '../components/common/PageContent';
import { RequestError } from '../components/common/RequestError';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { AuditEventChip, EVENT_LABELS } from '../components/common/AuditEventChip';
import { AuditMetadata } from '../components/common/AuditMetadata';
import type { AdminAuditEventResponse } from '../types';
export function AuditPage() {
  const [type, setType] = useState('');
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(10);
  const [selected, setSelected] = useState<AdminAuditEventResponse | null>(null);
  const query = useQuery({ queryKey: ['admin-audit', type, page, size], queryFn: () => adminService.getAudit({ eventType: type || undefined, page, size }) });
  return <Box><AdminTopbar title="Nhật ký hệ thống" subtitle="Theo dõi người thao tác và các thay đổi đã được ghi nhận" /><PageContent>
    <Box className="page-actions"><Box><Typography variant="h5" component="h2">Lịch sử hoạt động</Typography><Typography variant="body2" color="text.secondary">Thông tin phục vụ kiểm tra và đối chiếu vận hành.</Typography></Box><Button variant="outlined" disabled={query.isFetching} onClick={() => { void query.refetch(); }}>Làm mới nhật ký</Button></Box>
    <RequestError error={query.error} retry={() => { void query.refetch(); }} />
    <Card><Box className="filter-bar"><TextField select label="Loại sự kiện" size="small" value={type} sx={{ minWidth: 260 }} onChange={e => { setType(e.target.value); setPage(0); }}><MenuItem value="">Tất cả sự kiện</MenuItem>{Object.entries(EVENT_LABELS).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField></Box>
      {!query.error && <><TableContainer><Table aria-label="Nhật ký hệ thống" sx={{ minWidth: 730 }}><TableHead><TableRow><TableCell>Thời gian</TableCell><TableCell>Người thao tác</TableCell><TableCell>Sự kiện</TableCell><TableCell align="right">Chi tiết</TableCell></TableRow></TableHead><TableBody>
        {query.isLoading ? <TableSkeleton rows={5} columns={4} /> : query.data?.content.length ? query.data.content.map(event => <TableRow hover key={event.auditEventId}>
          <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(event.createdAt).toLocaleString('vi-VN')}</TableCell><TableCell>{event.actorEmail || 'Hệ thống'}</TableCell><TableCell><AuditEventChip type={event.eventType} /></TableCell><TableCell align="right"><Button size="small" aria-label={`Xem sự kiện ${event.auditEventId}`} onClick={() => setSelected(event)}>Xem chi tiết</Button></TableCell>
        </TableRow>) : <TableRow><TableCell colSpan={4} sx={{ textAlign: 'center', py: 6 }}>Chưa có sự kiện phù hợp với bộ lọc.</TableCell></TableRow>}
      </TableBody></Table></TableContainer><TablePagination component="div" count={query.data?.totalElements || 0} page={page} rowsPerPage={size} rowsPerPageOptions={[10, 20, 50]} onPageChange={(_, p) => setPage(p)} onRowsPerPageChange={e => { setSize(Number(e.target.value)); setPage(0); }} /></>}
    </Card>
    <Dialog open={!!selected} onClose={() => setSelected(null)} fullWidth maxWidth="sm" aria-labelledby="audit-title"><DialogTitle id="audit-title">Chi tiết sự kiện</DialogTitle>
      <DialogContent>{selected && <Box sx={{ display: 'grid', gap: 2 }}>
        <AuditEventChip type={selected.eventType} /><Typography variant="body2">{new Date(selected.createdAt).toLocaleString('vi-VN')}</Typography><Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{selected.actorEmail || 'Hệ thống'}</Typography><Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>Mã sự kiện: {selected.auditEventId}</Typography><AuditMetadata metadata={selected.metadata} />
      </Box>}</DialogContent><DialogActions sx={{ p: 3 }}><Button variant="contained" onClick={() => setSelected(null)}>Đóng</Button></DialogActions>
    </Dialog>
  </PageContent></Box>;
}
