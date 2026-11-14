import { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Card, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../services/api/apiClient';
import { newCreationRequestId } from '../services/api/newCreationRequestId';
import { appConfig } from '../config/runtime';

const modes = { APPROVAL_REQUIRED: 'Chờ giáo viên duyệt', AUTO_JOIN: 'Vào lớp ngay' };
type Mode = keyof typeof modes;
type Invitation = { code: string; token: string };
type Request = { studentId: string; displayName: string; requestId: string };
type ClassDetails = { name: string; gradeLevel: number; joinMode: Mode };

export function CreateClassForm({ onCreated }: { onCreated: (id: string) => void }) {
  const [name, setName] = useState('');
  const [grade, setGrade] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const key = useRef<{ payload: string; id: string } | null>(null);
  return <Box component="form" onSubmit={async event => {
    event.preventDefault();
    if (busy || !name.trim()) return;
    const payload = JSON.stringify([name.trim(), grade]);
    if (key.current?.payload !== payload) key.current = { payload, id: newCreationRequestId() };
    setBusy(true); setError('');
    try {
      const { data } = await apiClient.post<{ classId: string }>('/teacher/classes', {
        name: name.trim(), gradeLevel: grade, requestId: key.current.id,
      });
      onCreated(data.classId);
    } catch { setError('Chưa tạo được lớp. Hãy thử lại.'); }
    finally { setBusy(false); }
  }}>
    <Stack spacing={2}>
      {error && <Alert severity="error">{error}</Alert>}
      <TextField autoFocus required label="Tên lớp" value={name} onChange={event => setName(event.target.value)} slotProps={{ htmlInput: { maxLength: 120 } }} />
      <TextField select label="Khối lớp" value={grade} onChange={event => setGrade(Number(event.target.value))}>
        {[1, 2, 3, 4, 5].map(value => <MenuItem key={value} value={value}>Khối {value}</MenuItem>)}
      </TextField>
      <Button variant="contained" type="submit" disabled={busy || !name.trim()}>{busy ? 'Đang tạo lớp…' : 'Tạo lớp'}</Button>
    </Stack>
  </Box>;
}

export function ClassroomSettings({ id, refresh }: { id: string; refresh: () => Promise<unknown> }) {
  const path = '/teacher/classes/' + encodeURIComponent(id);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [qr, setQr] = useState<{ link: string; source: string }>();
  const [editing, setEditing] = useState<ClassDetails | null>(null);
  const details = useQuery({ queryKey: ['foundation-details', id], queryFn: async () => (await apiClient.get<ClassDetails>(path)).data });
  const invitation = useQuery({ queryKey: ['foundation-invitation', id], queryFn: async () => {
    const response = await apiClient.get<Invitation>(path + '/invitation');
    return response.status === 204 ? null : response.data;
  } });
  const requests = useQuery({ queryKey: ['foundation-requests', id], queryFn: async () =>
    (await apiClient.get<Request[]>(path + '/join-requests')).data });
  const link = invitation.data ? appConfig.portalOrigin + '/login#classroom=' + invitation.data.token : '';
  useEffect(() => {
    if (!link) return;
    let active = true;
    void Promise.all([import('zxing-wasm/writer'), import('zxing-wasm/writer/zxing_writer.wasm?url')])
      .then(async ([writer, wasm]) => {
        writer.prepareZXingModule({ overrides: { locateFile: (file: string) => file.endsWith('.wasm') ? wasm.default : file } });
        const result = await writer.writeBarcode(link, { format: 'QRCode', scale: 4 });
        if (active && result.svg) setQr({ link, source: 'data:image/svg+xml,' + encodeURIComponent(result.svg) });
      }).catch(() => { if (active) setMessage('Chưa tạo được QR. Hãy dùng mã lớp hoặc link.'); });
    return () => { active = false; };
  }, [link]);

  const action = async (run: () => Promise<unknown>, notice: string) => {
    if (busy) return;
    setBusy(true); setError(''); setMessage('');
    try {
      await run();
      await Promise.all([details.refetch(), requests.refetch(), invitation.refetch(), refresh()]);
      setMessage(notice);
    } catch { setError('Thao tác chưa hoàn tất. Hãy tải lại lớp và thử lại.'); }
    finally { setBusy(false); }
  };

  return <Card variant="outlined" sx={{ p: { xs: 2, sm: 3 }, my: 2 }}>
    <Stack spacing={2}>
      <Typography component="h2" variant="h6">Mời học sinh</Typography>
      {(details.isError || invitation.isError || requests.isError || error) &&
        <Alert severity="error">{error || 'Chưa tải được cài đặt lớp.'}</Alert>}
      {message && <Typography role="status">{message}</Typography>}
      {details.data && <TextField select label="Cách học sinh vào lớp" disabled={busy}
        helperText="Đổi cách vào lớp không tự duyệt yêu cầu đang chờ."
        value={details.data.joinMode} onChange={event => void action(
          () => apiClient.patch(path, { joinMode: event.target.value }), 'Đã cập nhật cách vào lớp.')}>
        {Object.entries(modes).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
      </TextField>}
      {details.data && !editing && <Button onClick={() => setEditing(details.data ?? null)}>Sửa tên và khối lớp</Button>}
      {editing && <Stack spacing={1}>
        <TextField label="Tên lớp" slotProps={{ htmlInput: { maxLength: 120 } }} value={editing.name} onChange={event => setEditing({ ...editing, name: event.target.value })} />
        <TextField select label="Khối lớp" value={editing.gradeLevel} onChange={event => setEditing({ ...editing, gradeLevel: Number(event.target.value) })}>
          {[1, 2, 3, 4, 5].map(grade => <MenuItem key={grade} value={grade}>Khối {grade}</MenuItem>)}
        </TextField>
        <Button disabled={busy || !editing.name.trim()} onClick={() => void action(async () => {
          await apiClient.patch(path, { name: editing.name.trim(), gradeLevel: editing.gradeLevel }); setEditing(null);
        }, 'Đã lưu thông tin lớp.')}>Lưu thông tin lớp</Button>
        <Button onClick={() => setEditing(null)}>Hủy</Button>
      </Stack>}
      {invitation.isSuccess && <Box>
        {invitation.data && <>
          <Typography variant="h5" sx={{ fontVariantNumeric: 'tabular-nums' }}>Mã lớp {invitation.data.code}</Typography>
          {qr?.link === link && <Box component="img" src={qr.source} alt="QR tham gia lớp" width={156} height={156} sx={{ display: 'block', my: 1 }} />}
          <TextField label="Link tham gia lớp" fullWidth value={link} slotProps={{ input: { readOnly: true } }} sx={{ my: 1 }} />
        </>}
        <Stack direction="row" useFlexGap sx={{ flexWrap: 'wrap', gap: 1 }}>
          <Button variant="contained" disabled={busy} onClick={() => {
            if (invitation.data && !window.confirm('Đổi lời mời sẽ làm mã, link và QR cũ mất hiệu lực. Thành viên hiện tại vẫn ở trong lớp.')) return;
            void action(() => apiClient.post(path + '/invitation'), 'Đã cập nhật lời mời.');
          }}>{invitation.data ? 'Đổi mã và link' : 'Tạo lời mời'}</Button>
          {invitation.data && <>
            <Button disabled={busy} onClick={() => void (navigator.clipboard?.writeText(link) ?? Promise.reject()).then(
              () => setMessage('Đã sao chép link.'), () => setMessage('Hãy chọn và sao chép link trong ô bên trên.'))}>Sao chép link</Button>
            <Button disabled={busy} onClick={() => {
              if (!window.confirm('Tắt lời mời sẽ làm mã, link và QR mất hiệu lực. Thành viên và yêu cầu đang chờ vẫn được giữ.')) return;
              void action(() => apiClient.delete(path + '/invitation'), 'Đã tắt lời mời.');
            }}>Tắt lời mời</Button>
          </>}
        </Stack>
      </Box>}
      <Typography component="h2" variant="h6">Yêu cầu tham gia</Typography>
      {requests.isSuccess && (requests.data.length ? requests.data.map(request =>
        <Stack key={request.requestId} direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ alignItems: { sm: 'center' } }}>
          <Typography sx={{ flex: 1 }}>{request.displayName}</Typography>
          {[true, false].map(approve => <Button key={String(approve)} disabled={busy} onClick={() => void action(
            () => apiClient.put(path + '/join-requests/' + request.studentId, { requestId: request.requestId, approve }),
            approve ? 'Đã thêm học sinh.' : 'Đã từ chối yêu cầu.')}>{approve ? 'Đồng ý' : 'Từ chối'}</Button>)}
        </Stack>) : <Typography color="text.secondary">Chưa có yêu cầu đang chờ.</Typography>)}
    </Stack>
  </Card>;
}
