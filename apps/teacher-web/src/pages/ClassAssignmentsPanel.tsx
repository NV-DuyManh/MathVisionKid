import { useState } from 'react';
import { Alert, Box, Button, Card, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Skeleton, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { MathType } from '../types';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { AssignmentWorkflow } from '../services/api/TeacherService';
import apiClient from '../services/api/apiClient';
import AssignedReviewDialog from './AssignedReviewDialog';
import { newCreationRequestId } from '../services/api/newCreationRequestId';

type Recipient = { studentId: string; studentName: string; submissionId: string | null; status: string };
const recipientLabels: Record<string, string> = {
  AWAITING_IMAGE: 'Chưa gửi', UPLOADING: 'Đang gửi ảnh', AWAITING_REVIEW: 'Chờ chấm',
  RETAKE_REQUESTED: 'Cần chụp lại', GRADE_RELEASED: 'Đã trả bài',
};

type Draft = { assignmentId?: string; creationRequestId: string; title: string; prompt: string; instructions: string; mathType: MathType; maxScore: number };
const blankDraft = (): Draft => ({ creationRequestId: newCreationRequestId(), title: '', prompt: '', instructions: '', mathType: MathType.VERTICAL_ADDITION, maxScore: 10 });

export function ClassAssignmentsPanel({ classId, studentCount }: { classId: string; studentCount: number }) {
  const queryClient = useQueryClient();
  const [editor, setEditor] = useState<Draft | null>(null);
  const [preview, setPreview] = useState<AssignmentWorkflow | null>(null);
  const [publish, setPublish] = useState<AssignmentWorkflow | null>(null);
  const [queue, setQueue] = useState<AssignmentWorkflow | null>(null);
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [queueFilter, setQueueFilter] = useState('');
  const queueId = queue?.assignmentId ?? queue?.id;
  const queueKey = ['assigned-review-queue', queueId];
  const recipientQuery = useQuery({
    queryKey: queueKey,
    enabled: Boolean(queueId),
    gcTime: 0,
    queryFn: async ({ signal }) => (await apiClient.get<Recipient[]>(
      `/teacher/assigned-submissions/queue/${encodeURIComponent(queueId ?? '')}`, { signal }
    )).data,
  });
  const recipients = recipientQuery.isError ? [] : recipientQuery.data ?? [];
  const visibleRecipients = recipients.filter(recipient => !queueFilter || recipient.status === queueFilter);
  const nextReviewId = visibleRecipients.find(recipient => recipient.status === 'AWAITING_REVIEW'
    && recipient.submissionId && recipient.submissionId !== reviewId)?.submissionId;
  const { data = [], isPending, isError, refetch } = useQuery({
    queryKey: ['teacher-class-assignments', classId],
    queryFn: () => AppTeacherService.listClassAssignments(classId),
  });
  const refresh = async () => { await queryClient.invalidateQueries({ queryKey: ['teacher-class-assignments', classId] }); };
  const save = useMutation({
    mutationFn: (draft: Draft) => AppTeacherService.saveAssignmentDraft({ ...draft, classId,
      creationRequestId: draft.creationRequestId }),
    onSuccess: async () => { setEditor(null); await refresh(); },
  });
  const dispatch = useMutation({
    mutationFn: (item: AssignmentWorkflow) => AppTeacherService.publishAssignment(item.assignmentId ?? item.id ?? ''),
    onSuccess: async () => { setPublish(null); await refresh(); },
  });

  return <Box sx={{ display: 'grid', gap: 2 }}>
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, flexWrap: 'wrap' }}>
      <Typography component="h2" variant="h6">Bài tập</Typography>
      <Button variant="contained" onClick={() => { save.reset(); setEditor(blankDraft()); }}>Tạo bài tập</Button>
    </Box>
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>Chưa tải được bài tập của lớp.</Alert>}
    {isPending && <Card variant="outlined" sx={{ p: 2 }} aria-busy="true"><Skeleton height={70} /><Skeleton height={70} /></Card>}
    {!isPending && !isError && data.length === 0 && <Card variant="outlined" sx={{ p: 3 }}>
      <Typography variant="h6">Lớp chưa có bài tập</Typography>
      <Typography color="text.secondary" sx={{ my: 1 }}>Tạo bài, xem trước nội dung rồi giao cho học sinh trong lớp.</Typography>
      <Button onClick={() => { save.reset(); setEditor(blankDraft()); }}>Tạo bài tập đầu tiên</Button>
    </Card>}
    {data.map(item => <Card key={item.assignmentId ?? item.id} variant="outlined" sx={{ p: { xs: 2, sm: 2.5 }, display: 'grid', gap: 1 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: 1 }}>
        <Typography component="h3" variant="subtitle1" sx={{ fontWeight: 700 }}>{item.title}</Typography>
        <Typography color="text.secondary">{item.status === 'PUBLISHED' ? `Đã giao · ${item.recipientCount} học sinh` : 'Bản nháp'}</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{item.prompt}</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button onClick={() => setPreview(item)}>Xem trước</Button>
        {item.status === 'PUBLISHED' && <Button onClick={() => { setQueueFilter(''); setQueue(item); }}>Bài nộp của lớp</Button>}
        {item.status === 'PUBLISHED' && <Button component={Link}
          to={`/assignments/${encodeURIComponent(item.assignmentId ?? item.id ?? '')}/results`}>Kết quả</Button>}
        {item.status === 'DRAFT' && <>
          <Button onClick={() => { save.reset(); setEditor({ assignmentId: item.assignmentId ?? item.id, title: item.title,
            creationRequestId: newCreationRequestId(), prompt: item.prompt, instructions: item.instructions ?? '', mathType: item.mathType, maxScore: item.maxScore ?? 10 }); }}>Sửa bản nháp</Button>
          <Button variant="contained" onClick={() => { dispatch.reset(); setPublish(item); }}>Giao bài</Button>
        </>}
      </Box>
    </Card>)}

    <Dialog open={queue !== null && !reviewId} onClose={() => setQueue(null)} fullWidth maxWidth="sm">
      <DialogTitle>Bài nộp · {queue?.title}</DialogTitle>
      <DialogContent>
        {recipientQuery.isPending && <Skeleton aria-label="Đang tải bài nộp" height={48} />}
        {recipientQuery.isError && <Alert severity="error" action={<Button onClick={() => void recipientQuery.refetch()}>Thử lại</Button>}>
          Chưa tải được danh sách bài nộp.
        </Alert>}
        {!recipientQuery.isError && recipientQuery.isSuccess && <TextField select fullWidth margin="dense"
          label="Trạng thái bài nộp" value={queueFilter} onChange={event => setQueueFilter(event.target.value)}
          slotProps={{ inputLabel: { shrink: true }, select: { displayEmpty: true } }}>
          <MenuItem value="">Tất cả</MenuItem>
          {Object.entries(recipientLabels).map(([status, label]) => <MenuItem key={status} value={status}>{label}</MenuItem>)}
        </TextField>}
        {recipientQuery.isSuccess && !visibleRecipients.length && <Typography>Không có bài nộp phù hợp.</Typography>}
        {visibleRecipients.map(recipient => <Box key={recipient.studentId} sx={{ py: 1, borderBottom: 1, borderColor: 'divider' }}>
          <Typography>{recipient.studentName}</Typography>
          <Typography color="text.secondary">{recipientLabels[recipient.status] ?? 'Chưa xác định'}</Typography>
          {recipient.submissionId && !['AWAITING_IMAGE', 'UPLOADING'].includes(recipient.status) &&
            <Button onClick={() => setReviewId(recipient.submissionId)}>Mở bài làm</Button>}
        </Box>)}
      </DialogContent>
      <DialogActions><Button onClick={() => setQueue(null)}>Đóng</Button></DialogActions>
    </Dialog>
    {reviewId && <AssignedReviewDialog key={reviewId} id={reviewId} onClose={() => {
      setReviewId(null);
      void recipientQuery.refetch();
    }} onNext={nextReviewId ? () => setReviewId(nextReviewId) : undefined}
      onSaved={kind => {
        void queryClient.cancelQueries({ queryKey: queueKey, exact: true });
        queryClient.setQueryData<Recipient[]>(queueKey, previous => previous?.map(recipient =>
          recipient.submissionId === reviewId
            ? { ...recipient, status: kind === 'release-grade' ? 'GRADE_RELEASED' : 'RETAKE_REQUESTED' }
            : recipient));
        void recipientQuery.refetch();
      }} />}
    <Dialog open={editor !== null} onClose={() => !save.isPending && setEditor(null)} fullWidth maxWidth="sm">
      <DialogTitle>{editor?.assignmentId ? 'Sửa bản nháp' : 'Tạo bài tập'}</DialogTitle>
      {editor && <DialogContent sx={{ display: 'grid', gap: 2, pt: '12px !important' }}>
        {save.isError && <Alert severity="error">Chưa xác nhận được bản nháp đã lưu. Nội dung vẫn còn trong form. Hãy thử lại.</Alert>}
        <TextField autoFocus label="Tên bài tập" value={editor.title} onChange={e => setEditor({ ...editor, title: e.target.value })} slotProps={{ htmlInput: { maxLength: 255 } }} required />
        <TextField label="Đề toán" value={editor.prompt} onChange={e => setEditor({ ...editor, prompt: e.target.value })} slotProps={{ htmlInput: { maxLength: 10000 } }} multiline minRows={4} required />
        <TextField label="Hướng dẫn làm bài (không bắt buộc)" value={editor.instructions} onChange={e => setEditor({ ...editor, instructions: e.target.value })} slotProps={{ htmlInput: { maxLength: 3000 } }} multiline minRows={2} />
        <TextField select label="Loại phép tính" value={editor.mathType} onChange={e => setEditor({ ...editor, mathType: e.target.value as MathType })}>
          <MenuItem value={MathType.VERTICAL_ADDITION}>Phép cộng</MenuItem><MenuItem value={MathType.VERTICAL_SUBTRACTION}>Phép trừ</MenuItem>
        </TextField>
        <TextField type="number" label="Thang điểm" value={editor.maxScore} onChange={e => setEditor({ ...editor, maxScore: Number(e.target.value) })} slotProps={{ htmlInput: { min: 1, max: 100, step: 1 } }} required />
        <DialogActions sx={{ px: 0 }}>
          <Button disabled={save.isPending} onClick={() => setEditor(null)}>Hủy</Button>
          <Button disabled={save.isPending || !editor.title.trim() || !editor.prompt.trim() || !Number.isInteger(editor.maxScore) || editor.maxScore < 1 || editor.maxScore > 100}
          onClick={() => void save.mutate(editor)}>{save.isPending ? 'Đang lưu…' : 'Lưu bản nháp'}</Button>
          <Button disabled={save.isPending || !editor.title.trim() || !editor.prompt.trim()} variant="outlined" onClick={() => setPreview({ ...editor, assignmentId: editor.assignmentId ?? '', classId, status: 'DRAFT', recipientCount: 0, createdAt: new Date().toISOString() })}>Xem trước</Button>
        </DialogActions>
      </DialogContent>}
    </Dialog>
    <Dialog open={Boolean(preview)} onClose={() => setPreview(null)} fullWidth maxWidth="sm">
      <DialogTitle>{preview?.title || 'Xem trước bài tập'}</DialogTitle>
      <DialogContent><Typography sx={{ whiteSpace: 'pre-wrap', fontSize: 18 }}>{preview?.prompt}</Typography>
        {preview?.instructions && <Typography sx={{ mt: 2, whiteSpace: 'pre-wrap' }} color="text.secondary">{preview.instructions}</Typography>}
        <Typography sx={{ mt: 2 }} color="text.secondary">{preview?.maxScore} điểm · {preview?.status === 'PUBLISHED' ? `${preview.recipientCount} học sinh nhận bài` : 'Bản nháp, chưa gửi cho học sinh'}</Typography></DialogContent>
      <DialogActions><Button onClick={() => setPreview(null)}>Đóng</Button></DialogActions>
    </Dialog>
    <Dialog open={Boolean(publish)} onClose={() => !dispatch.isPending && setPublish(null)}>
      <DialogTitle>Xác nhận giao bài</DialogTitle>
      <DialogContent>
        <Typography>Giao “{publish?.title}” cho lớp hiện có {studentCount} học sinh? Chỉ học sinh có tài khoản hoạt động tại thời điểm giao mới nhận bài.</Typography>
        {dispatch.isError && <Alert severity="error" sx={{ mt: 2 }}>Chưa xác nhận được kết quả giao bài. Hãy bấm Xác nhận giao để thử lại.</Alert>}
      </DialogContent>
      <DialogActions><Button disabled={dispatch.isPending} onClick={() => setPublish(null)}>Quay lại</Button>
        <Button disabled={dispatch.isPending} variant="contained" onClick={() => { if (publish) dispatch.mutate(publish); }}>{dispatch.isPending ? 'Đang giao…' : 'Xác nhận giao'}</Button></DialogActions>
    </Dialog>
  </Box>;
}
