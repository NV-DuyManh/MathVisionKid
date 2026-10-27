import { useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, TextField } from '@mui/material';
import { adminService } from '../../services/api/adminService';
import { useAdminAction } from '../../hooks/useAdminAction';
import { RequestError } from '../common/RequestError';
import type { AdminUserResponse } from '../../types';
export function UserFormDialog({ user, onClose, onSaved }: { user?: AdminUserResponse; onClose: () => void; onSaved?: () => void }) {
  const [name, setName] = useState(user?.displayName || '');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'STUDENT' | 'TEACHER'>('STUDENT');
  const [grade, setGrade] = useState(user?.gradeLevel || 3);
  const [password, setPassword] = useState('');
  const [invalid, setInvalid] = useState('');
  const action = useAdminAction();
  const student = user ? user.role === 'STUDENT' : role === 'STUDENT';
  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || (!user && (!email.trim() || password.length < 6))) { setInvalid('Nhập đầy đủ thông tin và mật khẩu ít nhất 6 ký tự.'); return; }
    const payload = { displayName: name.trim(), ...(student ? { gradeLevel: grade } : {}) };
    void action.run(() => user ? adminService.updateUser(user.userId, payload) : adminService.createUser({ ...payload, role, email: email.trim().toLowerCase(), initialPassword: password }), () => { setPassword(''); onSaved?.(); onClose(); });
  };
  const titleId = 'user-form-title';
  return <Dialog open onClose={action.pending ? undefined : onClose} maxWidth="sm" fullWidth aria-labelledby={titleId}>
    <DialogTitle id={titleId}>{user ? 'Chỉnh sửa hồ sơ' : 'Tạo người dùng'}</DialogTitle>
    <Box component="form" onSubmit={submit} aria-busy={action.pending}>
      <DialogContent><RequestError error={action.error} />{invalid && <Alert severity="error" sx={{ mb: 2 }}>{invalid}</Alert>}
        <Box sx={{ display: 'grid', gap: 2, pt: 1 }}>
          <TextField label="Họ và tên" autoFocus required fullWidth value={name} disabled={action.pending} onChange={e => setName(e.target.value)} />
          {!user && <>
            <TextField label="Email đăng nhập" type="email" required fullWidth value={email} disabled={action.pending} autoComplete="off" onChange={e => setEmail(e.target.value)} />
            <TextField select label="Vai trò" value={role} disabled={action.pending} onChange={e => setRole(e.target.value as typeof role)}><MenuItem value="STUDENT">Học sinh</MenuItem><MenuItem value="TEACHER">Giáo viên</MenuItem></TextField>
            <TextField label="Mật khẩu khởi tạo" type="password" required autoComplete="new-password" value={password} disabled={action.pending} onChange={e => setPassword(e.target.value)} slotProps={{ htmlInput: { minLength: 6 } }} helperText="Ít nhất 6 ký tự. Bàn giao cho người dùng qua kênh riêng." />
          </>}
          {student && <TextField select label="Khối lớp" value={grade} disabled={action.pending} onChange={e => setGrade(Number(e.target.value))}>{[1, 2, 3, 4, 5].map(n => <MenuItem value={n} key={n}>Khối {n}</MenuItem>)}</TextField>}
          {user && <TypographyNote />}
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 3 }}><Button onClick={onClose} disabled={action.pending}>Hủy</Button><Button type="submit" variant="contained" disabled={action.pending}>{action.pending ? 'Đang lưu…' : user ? 'Lưu thay đổi' : 'Tạo tài khoản'}</Button></DialogActions>
    </Box>
  </Dialog>;
}
function TypographyNote() { return <Alert severity="info">Email và vai trò được giữ cố định theo chính sách tài khoản.</Alert>; }
