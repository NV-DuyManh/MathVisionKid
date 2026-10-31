import { useState } from 'react';
import { Autocomplete, Box, Button, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { adminService } from '../../services/api/adminService';
import { RequestError } from '../common/RequestError';
export function UserPicker({ role, value, onChange, exclude = [], disabled = false }: {
  role: 'STUDENT' | 'TEACHER'; value: string; onChange: (id: string) => void; exclude?: string[]; disabled?: boolean;
}) {
  const [search, setSearch] = useState('');
  const [input, setInput] = useState('');
  const [page, setPage] = useState(0);
  const label = role === 'TEACHER' ? 'Giáo viên phụ trách' : 'Học sinh';
  const query = useQuery({ queryKey: ['admin-picker', role, search, page], queryFn: () => adminService.getUsers({ role, active: true, query: search || undefined, page, size: 20 }) });
  const options = (query.data?.content || []).filter(user => !exclude.includes(user.userId));
  const selected = options.find(user => user.userId === value) || null;
  return <Box>
    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}><TextField fullWidth size="small" label={`Tìm ${label.toLowerCase()} theo tên / email`} value={input} onChange={e => setInput(e.target.value)} disabled={disabled} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); setSearch(input.trim()); setPage(0); onChange(''); } }} /><Button disabled={disabled || query.isFetching} onClick={() => { setSearch(input.trim()); setPage(0); onChange(''); }}>Tìm</Button></Box>
    <RequestError error={query.error} retry={() => { void query.refetch(); }} />
    <Autocomplete options={options} value={selected} loading={query.isFetching} disabled={disabled || !!query.error} filterOptions={values => values}
      getOptionLabel={user => `${user.displayName} (${user.email})`} isOptionEqualToValue={(a, b) => a.userId === b.userId}
      onChange={(_, user) => onChange(user?.userId || '')} noOptionsText="Không có tài khoản phù hợp trong trang này" loadingText="Đang tải…"
      renderInput={params => <TextField {...params} required label={`Chọn ${label.toLowerCase()}`} helperText="Chỉ hiển thị tài khoản đang hoạt động." />} />
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1, flexWrap: 'wrap' }}>
      <Button size="small" disabled={disabled || page === 0 || query.isFetching} onClick={() => { setPage(p => p - 1); onChange(''); }}>Trang trước</Button>
      <Typography variant="caption" color="text.secondary">Trang {page + 1} / {query.data?.totalPages || 1}</Typography>
      <Button size="small" disabled={disabled || !query.data || query.data.last || query.isFetching} onClick={() => { setPage(p => p + 1); onChange(''); }}>Trang sau</Button>
    </Box>
  </Box>;
}
