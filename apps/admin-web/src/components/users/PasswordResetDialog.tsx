import { useEffect, useState, useRef } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography } from '@mui/material';
import { adminService } from '../../services/api/adminService';
import { useAdminAction } from '../../hooks/useAdminAction';
import { RequestError } from '../common/RequestError';
import type { AdminUserResponse } from '../../types';
export function PasswordResetDialog({ user, onClose }: { user: AdminUserResponse; onClose: () => void }) {
  const action = useAdminAction();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState('');
  useEffect(() => {
    if (!secret) return;
    const timeout = window.setTimeout(() => { setSecret(null); closeRef.current(); }, 60000);
    return () => window.clearTimeout(timeout);
  }, [secret]);
  const close = () => { setSecret(null); onClose(); };
  const reset = () => { void action.run(async () => {
    const result = await adminService.resetPassword(user.userId);
    if (result.userId !== user.userId || result.email !== user.email || typeof result.temporaryPassword !== 'string' || !result.temporaryPassword) {
      throw Object.assign(new Error('Invalid password reset response'), { response: { status: 500 } });
    }
    return result.temporaryPassword;
  }, password => setSecret(password)); };
  return <Dialog open onClose={action.pending ? undefined : close} maxWidth="sm" fullWidth aria-labelledby="password-reset-title">
    <DialogTitle id="password-reset-title">{secret ? 'Mật khẩu tạm thời' : 'Xác nhận đặt lại mật khẩu'}</DialogTitle>
    <DialogContent><RequestError error={action.error} />
      <Typography variant="body2" sx={{ mb: 2, overflowWrap: 'anywhere' }}>Tài khoản: <strong>{user.email}</strong></Typography>
      {secret ? <>
        <Alert severity="warning" sx={{ mb: 2 }}>Chỉ hiển thị trong lần này và tự đóng sau 60 giây. Bàn giao qua kênh riêng, an toàn.</Alert>
        <Box sx={{ bgcolor: 'primary.light', p: 2.5, borderRadius: 2, overflowWrap: 'anywhere' }}><Typography component="p" sx={{ fontFamily: 'monospace', fontSize: 22, letterSpacing: 1 }}>{secret}</Typography></Box>
        {copied && <Typography role="status" variant="body2" sx={{ mt: 1 }}>{copied}</Typography>}
      </> : <Typography color="text.secondary">Mật khẩu hiện tại sẽ được thay thế và các phiên làm mới sẽ bị thu hồi. Bạn có muốn tạo mật khẩu tạm thời cho người dùng này?</Typography>}
    </DialogContent>
    <DialogActions sx={{ p: 3 }}>
      <Button onClick={close} disabled={action.pending}>{secret ? 'Đóng và xóa khỏi màn hình' : 'Hủy'}</Button>
      {secret ? <Button variant="contained" onClick={async () => {
        try { await navigator.clipboard.writeText(secret); setCopied('Đã sao chép. Bàn giao mật khẩu qua kênh riêng.'); }
        catch { setCopied('Không thể sao chép tự động. Hãy chọn và sao chép mật khẩu trên màn hình.'); }
      }}>Sao chép mật khẩu</Button> : <Button variant="contained" onClick={reset} disabled={action.pending}>{action.pending ? 'Đang đặt lại…' : 'Tạo mật khẩu tạm thời'}</Button>}
    </DialogActions>
  </Dialog>;
}
