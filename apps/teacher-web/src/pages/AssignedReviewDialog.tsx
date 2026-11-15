import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, TextField, Typography } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import apiClient from '../services/api/apiClient';

type Detail = { studentName: string; prompt: string; status: string; maxScore: number; imageVersion: number };

export default function AssignedReviewDialog(props: {
  id: string; onClose: () => void; onSaved: () => void; onNext?: () => void;
}) {
  return <ReviewWorkspace key={props.id} {...props} />;
}

function ReviewWorkspace({ id, onClose, onSaved, onNext }: {
  id: string; onClose: () => void; onSaved: () => void; onNext?: () => void;
}) {
  const [saved, setSaved] = useState(false);
  const [refreshed, setRefreshed] = useState(false);
  const detail = useQuery({
    queryKey: ['assigned-review', id],
    gcTime: 0,
    queryFn: async ({ signal }) => (await apiClient.get<Detail>(`/teacher/assigned-submissions/${id}`, { signal })).data,
  });
  return <Dialog open onClose={onClose} fullWidth maxWidth="md">
    <DialogTitle>Bài làm của {detail.data?.studentName ?? 'học sinh'}</DialogTitle>
    <DialogContent>
      {saved && <Alert severity="success">Đã lưu phản hồi cho bài này.</Alert>}
      {refreshed && !saved && <Alert severity="info">Đã cập nhật bài nộp. Hãy xem ảnh và xác nhận lại trước khi chấm.</Alert>}
      {detail.isPending && <Typography role="status">Đang tải bài làm…</Typography>}
      {detail.isError && <Alert severity="error" action={<Button onClick={() => void detail.refetch()}>Thử lại</Button>}>Chưa mở được bài nộp.</Alert>}
      {!detail.isError && detail.data && <Review key={`${id}:${detail.data.imageVersion}:${detail.data.status}`} id={id} detail={detail.data}
        onSaved={() => { setSaved(true); void detail.refetch(); onSaved(); }}
        onRefresh={async () => {
          const result = await detail.refetch();
          if (!result.isError) setRefreshed(true);
          return !result.isError;
        }} />}
    </DialogContent>
    <DialogActions>
      {saved && onNext && <Button variant="contained" onClick={onNext}>Mở bài tiếp theo</Button>}
      <Button onClick={onClose}>Về danh sách</Button>
    </DialogActions>
  </Dialog>;
}

function Review({ id, detail, onSaved, onRefresh }: {
  id: string; detail: Detail; onSaved: () => void; onRefresh: () => Promise<boolean>;
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
  const [stale, setStale] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const active = useRef(true);
  const mutationRequest = useRef<AbortController | null>(null);
  useEffect(() => {
    active.current = true;
    return () => { active.current = false; mutationRequest.current?.abort(); };
  }, []);
  const clearAssessment = () => {
    setReadable(false); setMatchesAssignment(false); setScore(''); setFeedback('');
    setInstruction(''); setRequestId(crypto.randomUUID());
  };
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
      }).catch(error => {
        if (controller.signal.aborted) return;
        setPhotoError(true);
        if (isAxiosError(error) && error.response?.status === 409) {
          setStale(true);
          clearAssessment();
        }
      });
    }
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [id, detail.imageVersion, reload]);
  const action = useMutation({
    mutationFn: (kind: 'return-image' | 'release-grade') => {
      const controller = new AbortController();
      mutationRequest.current = controller;
      return apiClient.post(`/teacher/assigned-submissions/${id}/${kind}`,
        kind === 'return-image' ? { imageVersion: detail.imageVersion, reason, instruction } :
          { imageVersion: detail.imageVersion, requestId, readable, matchesAssignment, score: Number(score), feedback },
        { signal: controller.signal });
    },
    onSuccess: () => { if (active.current) onSaved(); },
    onError: error => {
      if (active.current && isAxiosError(error) && error.response?.status === 409) {
        setStale(true);
        clearAssessment();
      }
    },
  });
  const conflict = isAxiosError(action.error) && action.error.response?.status === 409;
  const refreshReview = async () => {
    if (refreshing) return;
    clearAssessment();
    setPhoto(''); setLoaded(false); setRefreshing(true);
    try {
      const success = await onRefresh();
      if (!active.current || !success) return;
      setPhotoError(false); setStale(false); action.reset(); setReload(value => value + 1);
    } finally { if (active.current) setRefreshing(false); }
  };
  const canReview = detail.status === 'AWAITING_REVIEW' && loaded && !photoError && !action.isPending && !stale && !refreshing;
  return <>
    <Typography sx={{ whiteSpace: 'pre-wrap', my: 2 }}>{detail.prompt}</Typography>
    {detail.imageVersion > 0 && <Typography>Phiên bản ảnh {detail.imageVersion}</Typography>}
    {photoError ? <Alert severity="error" action={<Button disabled={refreshing} onClick={() => void refreshReview()}>
      {stale ? 'Tải phiên bản mới' : 'Tải lại ảnh'}</Button>}>
      {stale ? 'Học sinh đã thay ảnh. Hãy tải phiên bản mới trước khi chấm.' : 'Chưa tải được ảnh bài làm.'}</Alert>
      : photo ? <><Button aria-pressed={zoom} onClick={() => setZoom(value => !value)}>{zoom ? 'Thu nhỏ ảnh' : 'Phóng to ảnh'}</Button>
        <div role="region" aria-label="Ảnh bài làm có thể cuộn" tabIndex={0} style={{ overflow: 'auto' }}><img src={photo} alt="Ảnh bài làm đã nộp"
          style={{ width: zoom ? '160%' : '100%' }} onLoad={() => setLoaded(true)} onError={() => setPhotoError(true)} /></div></>
      : detail.imageVersion > 0 && <Typography role="status">Đang tải ảnh…</Typography>}
    {refreshing && <Typography role="status">Đang tải phiên bản mới…</Typography>}
    {action.isError && <Alert severity="error" action={conflict && <Button disabled={refreshing} onClick={() => void refreshReview()}>Tải phiên bản mới</Button>}>
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
