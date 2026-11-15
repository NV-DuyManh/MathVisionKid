import { useEffect, useState } from 'react';
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, TextField, Typography } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import apiClient from '../services/api/apiClient';

type Detail = { studentName: string; prompt: string; status: string; maxScore: number; imageVersion: number };

export default function AssignedReviewDialog({ id, onClose, onSaved }: {
  id: string; onClose: () => void; onSaved: () => void;
}) {
  const detail = useQuery({
    queryKey: ['assigned-review', id],
    gcTime: 0,
    queryFn: async ({ signal }) => (await apiClient.get<Detail>(`/teacher/assigned-submissions/${id}`, { signal })).data,
  });
  return <Dialog open onClose={onClose} fullWidth maxWidth="md">
    <DialogTitle>Bài làm của {detail.data?.studentName ?? 'học sinh'}</DialogTitle>
    <DialogContent>
      {detail.isPending && <Typography role="status">Đang tải bài làm…</Typography>}
      {detail.isError && <Alert severity="error" action={<Button onClick={() => void detail.refetch()}>Thử lại</Button>}>Chưa mở được bài nộp.</Alert>}
      {!detail.isError && detail.data && <Review key={detail.data.imageVersion} id={id} detail={detail.data}
        onSaved={onSaved} onRefresh={async () => { await detail.refetch(); }} />}
    </DialogContent>
    <DialogActions><Button onClick={onClose}>Về danh sách</Button></DialogActions>
  </Dialog>;
}

function Review({ id, detail, onSaved, onRefresh }: {
  id: string; detail: Detail; onSaved: () => void; onRefresh: () => Promise<void>;
}) {
  const [photo, setPhoto] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [photoError, setPhotoError] = useState(false);
  const [reload, setReload] = useState(0);
  const [zoom, setZoom] = useState(false);
  const [readable, setReadable] = useState(false);
  const [matchesAssignment, setMatchesAssignment] = useState(false);
  const [score, setScore] = useState('');
  const [feedback, setFeedback] = useState('');
  const [reason, setReason] = useState('UNREADABLE');
  const [instruction, setInstruction] = useState('');
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());
  useEffect(() => {
    const controller = new AbortController();
    let url: string | undefined;
    if (detail.imageVersion > 0) {
      void apiClient.get<Blob>(`/teacher/assigned-submissions/${id}/image`, {
        signal: controller.signal, responseType: 'blob', params: { imageVersion: detail.imageVersion },
      }).then(({ data }) => {
        if (controller.signal.aborted) return;
        url = URL.createObjectURL(data);
        setPhoto(url);
      }).catch(() => { if (!controller.signal.aborted) setPhotoError(true); });
    }
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, detail.imageVersion, reload]);
  const action = useMutation({
    mutationFn: (kind: 'return-image' | 'release-grade') => apiClient.post(`/teacher/assigned-submissions/${id}/${kind}`,
      kind === 'return-image' ? { imageVersion: detail.imageVersion, reason, instruction } :
        { imageVersion: detail.imageVersion, requestId, readable, matchesAssignment, score: Number(score), feedback }),
    onSuccess: onSaved,
  });
  const conflict = isAxiosError(action.error) && action.error.response?.status === 409;
  const canReview = detail.status === 'AWAITING_REVIEW' && loaded && !photoError && !action.isPending && !conflict;
  return <>
    <Typography sx={{ whiteSpace: 'pre-wrap', my: 2 }}>{detail.prompt}</Typography>
    {detail.imageVersion > 0 && <Typography>Phiên bản ảnh {detail.imageVersion}</Typography>}
    {photoError ? <Alert severity="error" action={<Button onClick={() => {
      setPhoto(''); setLoaded(false); setPhotoError(false); setReload(value => value + 1);
    }}>Tải lại ảnh</Button>}>Chưa tải được ảnh bài làm.</Alert>
      : photo ? <><Button aria-pressed={zoom} onClick={() => setZoom(value => !value)}>{zoom ? 'Thu nhỏ ảnh' : 'Phóng to ảnh'}</Button>
        <div role="region" aria-label="Ảnh bài làm có thể cuộn" tabIndex={0} style={{ overflow: 'auto' }}><img src={photo} alt="Ảnh bài làm đã nộp"
          style={{ width: zoom ? '160%' : '100%' }} onLoad={() => setLoaded(true)} onError={() => setPhotoError(true)} /></div></>
      : detail.imageVersion > 0 && <Typography role="status">Đang tải ảnh…</Typography>}
    {action.isError && <Alert severity="error" action={conflict && <Button onClick={async () => {
      setReadable(false); setMatchesAssignment(false); setScore(''); setFeedback('');
      setInstruction(''); setRequestId(crypto.randomUUID());
      await onRefresh();
      action.reset();
    }}>Tải lại bài nộp</Button>}>
      {conflict ? 'Bài nộp đã thay đổi. Tải lại và kiểm tra ảnh trước khi chấm.' : 'Chưa lưu được phản hồi. Hãy thử lại.'}
    </Alert>}
    {detail.status === 'AWAITING_REVIEW' && <>
      <FormControlLabel control={<Checkbox checked={readable} onChange={(_, checked) => { setReadable(checked); setRequestId(crypto.randomUUID()); }} />} label="Ảnh đọc được" />
      <FormControlLabel control={<Checkbox checked={matchesAssignment} onChange={(_, checked) => { setMatchesAssignment(checked); setRequestId(crypto.randomUUID()); }} />} label="Bài làm đúng đề" />
      <TextField fullWidth margin="dense" label={`Điểm (0–${detail.maxScore})`} type="number" value={score}
        onChange={event => { setScore(event.target.value); setRequestId(crypto.randomUUID()); }} />
      <TextField fullWidth margin="dense" label="Nhận xét" multiline value={feedback}
        slotProps={{ htmlInput: { maxLength: 2000 } }} helperText={`${feedback.length}/2000 ký tự`}
        onChange={event => { setFeedback(event.target.value); setRequestId(crypto.randomUUID()); }} />
      <Button variant="contained" disabled={!canReview || !readable || !matchesAssignment || !/^\d+$/.test(score) || Number(score) > detail.maxScore}
        onClick={() => action.mutate('release-grade')}>Chấm và trả</Button>
      <TextField fullWidth margin="dense" select label="Lý do chụp lại" value={reason} onChange={event => setReason(event.target.value)}>
        <MenuItem value="UNREADABLE">Ảnh khó đọc</MenuItem><MenuItem value="WRONG_ASSIGNMENT">Bài làm sai đề</MenuItem>
      </TextField>
      <TextField fullWidth margin="dense" label="Hướng dẫn chụp lại" multiline value={instruction}
        slotProps={{ htmlInput: { maxLength: 500 } }} helperText={`${instruction.length}/500 ký tự`}
        onChange={event => setInstruction(event.target.value)} />
      <Button disabled={!canReview || !instruction.trim()} onClick={() => action.mutate('return-image')}>Yêu cầu chụp lại</Button>
    </>}
  </>;
}
