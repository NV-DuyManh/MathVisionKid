import { useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, TextField } from '@mui/material';
import { adminService } from '../../services/api/adminService';
import { useAdminAction } from '../../hooks/useAdminAction';
import { RequestError } from '../common/RequestError';
import { UserPicker } from './UserPicker';
import type { AdminClassResponse } from '../../types';
export function ClassFormDialog({ classroom, onClose, onSaved }: { classroom?: AdminClassResponse; onClose: () => void; onSaved?: () => void }) {
  const [name, setName] = useState(classroom?.name || '');
  const [grade, setGrade] = useState(classroom?.gradeLevel || 3);
  const [year, setYear] = useState(classroom?.academicYear || '');
  const [teacherId, setTeacherId] = useState('');
  const [invalid, setInvalid] = useState('');
  const action = useAdminAction();
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || (!classroom && !teacherId)) { setInvalid('Nhập tên lớp và chọn giáo viên đang hoạt động.'); return; }
    const payload = { name: name.trim(), gradeLevel: grade, academicYear: year.trim() };
    void action.run(() => classroom ? adminService.updateClass(classroom.classId, payload) : adminService.createClass({ ...payload, teacherId }), () => { onSaved?.(); onClose(); });
  };
  return <Dialog open onClose={action.pending ? undefined : onClose} maxWidth="sm" fullWidth aria-labelledby="class-form-title"><DialogTitle id="class-form-title">{classroom ? 'Chỉnh sửa lớp học' : 'Tạo lớp học'}</DialogTitle>
    <Box component="form" onSubmit={submit} aria-busy={action.pending}><DialogContent>
      <RequestError error={action.error} />{invalid && <Alert severity="error" sx={{ mb: 2 }}>{invalid}</Alert>}
      <Box sx={{ display: 'grid', gap: 2.5, pt: 1 }}>
        <TextField required autoFocus label="Tên lớp học" value={name} disabled={action.pending} onChange={e => setName(e.target.value)} />
        <TextField select label="Khối lớp" value={grade} disabled={action.pending} onChange={e => setGrade(Number(e.target.value))}>{[1, 2, 3, 4, 5].map(n => <MenuItem key={n} value={n}>Khối {n}</MenuItem>)}</TextField>
        <TextField label="Năm học" value={year} disabled={action.pending} onChange={e => setYear(e.target.value)} helperText="Có thể để trống nếu chưa xác định." />
        {!classroom && <UserPicker role="TEACHER" value={teacherId} onChange={setTeacherId} disabled={action.pending} />}
      </Box>
    </DialogContent><DialogActions sx={{ p: 3 }}><Button disabled={action.pending} onClick={onClose}>Hủy</Button><Button type="submit" variant="contained" disabled={action.pending || (!classroom && !teacherId)}>{action.pending ? 'Đang lưu…' : classroom ? 'Lưu thay đổi' : 'Tạo lớp học'}</Button></DialogActions></Box>
  </Dialog>;
}
