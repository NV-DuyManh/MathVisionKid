import { useRef, useState } from 'react';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { AppTeacherService } from '../services/api/ServiceLocator';
import PrivacyEditorModal from './PrivacyEditorModal';

const MAX_IMAGE_BYTES = 8 * 1024 * 1024;

export function SubmissionRetake({ id, refresh }: { id: string; refresh: () => Promise<boolean> }) {
  const input = useRef<HTMLInputElement>(null);
  const [source, setSource] = useState<File | null>(null);
  const [redacted, setRedacted] = useState<Blob | null>(null);
  const [error, setError] = useState('');
  const [needsCheck, setNeedsCheck] = useState(false);
  const [checking, setChecking] = useState(false);

  const checkResult = async () => {
    setChecking(true);
    if (await refresh()) setNeedsCheck(false);
    setChecking(false);
  };

  const upload = useMutation({
    mutationFn: (image: Blob) => AppTeacherService.retakeSubmission(id, image),
    networkMode: 'always',
    retry: false,
    onSuccess: () => {
      setRedacted(null);
      void checkResult();
    },
    onError: (failure) => {
      const status = isAxiosError(failure) ? failure.response?.status : undefined;
      if (status === 401 || status === 403 || status === 404) {
        setRedacted(null);
        void checkResult();
      } else if (!status || status >= 500 || status === 408 || status === 409) {
        setNeedsCheck(true);
      } else {
        setError('Không gửi được ảnh. Hãy kiểm tra định dạng, dung lượng hoặc chọn lại ảnh.');
      }
    },
  });

  const busy = upload.isPending || checking;
  return <Stack spacing={2}>
    <Alert severity="warning">Chụp lại ảnh rõ toàn bộ bài làm, đủ sáng và không bị cắt mất phần tính toán. Bài này vẫn đang chờ xử lý.</Alert>
    {error && <Alert severity="error">{error}</Alert>}
    {upload.isSuccess ? (
      <Alert severity="success" action={<Button disabled={busy} onClick={() => void checkResult()}>Làm mới</Button>}>
        Đã gửi ảnh chụp lại.
      </Alert>
    ) : needsCheck ? (
      <Alert severity="warning" action={<Button disabled={busy} onClick={() => void checkResult()}>Kiểm tra lại</Button>}>
        Chưa xác nhận được ảnh đã gửi. Kiểm tra trạng thái trước khi gửi lại.
      </Alert>
    ) : (
      <Stack spacing={1} sx={{ alignItems: 'flex-start' }}>
        <Button variant="outlined" disabled={busy} onClick={() => input.current?.click()}>Chọn ảnh chụp lại</Button>
        <input ref={input} type="file" hidden aria-label="Chọn ảnh chụp lại" accept="image/jpeg,image/png,image/webp"
          onChange={(event) => {
            const selected = event.currentTarget.files?.[0];
            event.currentTarget.value = '';
            if (!selected) return;
            setRedacted(null);
            if (!['image/jpeg', 'image/png', 'image/webp'].includes(selected.type) || !selected.size || selected.size > MAX_IMAGE_BYTES) {
              setError('Chọn ảnh JPG, PNG hoặc WebP có dung lượng tối đa 8 MB.');
              return;
            }
            setError('');
            setSource(selected);
          }} />
        {redacted && <Typography role="status" variant="body2">Ảnh đã qua bước che thông tin và sẵn sàng gửi.</Typography>}
        <Button variant="contained" disabled={busy || !redacted} onClick={() => {
          if (!redacted || busy) return;
          setError('');
          upload.mutate(redacted);
        }}>{upload.isPending ? 'Đang gửi ảnh…' : 'Gửi ảnh chụp lại'}</Button>
      </Stack>
    )}
    <PrivacyEditorModal open={!!source} file={source} onClose={() => setSource(null)} onSave={(blob) => {
      setSource(null);
      if (blob.type !== 'image/jpeg' || !blob.size || blob.size > MAX_IMAGE_BYTES) {
        setError('Ảnh sau khi che phải là JPEG và có dung lượng tối đa 8 MB.');
        return;
      }
      setRedacted(blob);
    }} />
  </Stack>;
}
