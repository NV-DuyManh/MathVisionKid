import { useState } from 'react';
import { Alert, Box, Button, Card, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Skeleton, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { MathType } from '../types';
import { AppTeacherService } from '../services/api/ServiceLocator';
import type { AssignmentWorkflow } from '../services/api/TeacherService';

type Draft = { assignmentId?: string; creationRequestId: string; title: string; prompt: string; instructions: string; mathType: MathType; maxScore: number };
const blankDraft = (): Draft => ({ creationRequestId: crypto.randomUUID(), title: '', prompt: '', instructions: '', mathType: MathType.VERTICAL_ADDITION, maxScore: 10 });

export function ClassAssignmentsPanel({ classId, studentCount }: { classId: string; studentCount: number }) {
  const queryClient = useQueryClient();
  const [editor, setEditor] = useState<Draft | null>(null);
  const [preview, setPreview] = useState<AssignmentWorkflow | null>(null);
  const [publish, setPublish] = useState<AssignmentWorkflow | null>(null);
  const [error, setError] = useState('');
  const { data = [], isPending, isError, refetch } = useQuery({
    queryKey: ['teacher-class-assignments', classId],
    queryFn: () => AppTeacherService.listClassAssignments(classId),
  });
  const refresh = async () => { await queryClient.invalidateQueries({ queryKey: ['teacher-class-assignments', classId] }); };
  const save = useMutation({
    mutationFn: (draft: Draft) => AppTeacherService.saveAssignmentDraft({ ...draft, classId,
      creationRequestId: draft.creationRequestId }),
    onSuccess: async () => { setEditor(null); setError(''); await refresh(); },
    onError: () => setError('Chưa lưu được bản nháp. Nội dung của em vẫn còn trên màn hình, hãy thử lại.'),
  });
  const dispatch = useMutation({
    mutationFn: (item: AssignmentWorkflow) => AppTeacherService.publishAssignment(item.assignmentId ?? item.id ?? ''),
    onSuccess: async () => { setPublish(null); setError(''); await refresh(); },
    onError: () => setError('Chưa giao được bài. Bài vẫn ở trạng thái bản nháp.'),
  });

  return <Box sx={{ display: 'grid', gap: 2 }}>
    {error && <Alert severity="error" role="alert">{error}</Alert>}
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1, flexWrap: 'wrap' }}>
      <Typography component="h2" variant="h6">Bài tập</Typography>
      <Button variant="contained" onClick={() => setEditor(blankDraft())}>Tạo bài tập</Button>
    </Box>
    {isError && <Alert severity="error" action={<Button onClick={() => void refetch()}>Thử lại</Button>}>Chưa tải được bài tập của lớp.</Alert>}
    {isPending && <Card variant="outlined" sx={{ p: 2 }} aria-busy="true"><Skeleton height={70} /><Skeleton height={70} /></Card>}
    {!isPending && !isError && data.length === 0 && <Card variant="outlined" sx={{ p: 3 }}>
      <Typography variant="h6">Lớp chưa có bài tập</Typography>
      <Typography color="text.secondary" sx={{ my: 1 }}>Tạo bài, xem trước nội dung rồi giao cho học sinh trong lớp.</Typography>
      <Button onClick={() => setEditor(blankDraft())}>Tạo bài tập đầu tiên</Button>
    </Card>}
    {data.map(item => <Card key={item.assignmentId ?? item.id} variant="outlined" sx={{ p: { xs: 2, sm: 2.5 }, display: 'grid', gap: 1 }}>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: 1 }}>
        <Typography component="h3" variant="subtitle1" sx={{ fontWeight: 700 }}>{item.title}</Typography>
        <Typography color="text.secondary">{item.status === 'PUBLISHED' ? `Đã giao · ${item.recipientCount} học sinh` : 'Bản nháp'}</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{item.prompt}</Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button onClick={() => setPreview(item)}>Xem trước</Button>
        {item.status === 'DRAFT' && <>
          <Button onClick={() => setEditor({ assignmentId: item.assignmentId ?? item.id, title: item.title,
            creationRequestId: crypto.randomUUID(), prompt: item.prompt, instructions: item.instructions ?? '', mathType: item.mathType, maxScore: item.maxScore ?? 10 })}>Sửa bản nháp</Button>
          <Button variant="contained" onClick={() => setPublish(item)}>Giao bài</Button>
        </>}
      </Box>
    </Card>)}

    <Dialog open={editor !== null} onClose={() => !save.isPending && setEditor(null)} fullWidth maxWidth="sm">
      <DialogTitle>{editor?.assignmentId ? 'Sửa bản nháp' : 'Tạo bài tập'}</DialogTitle>
      {editor && <DialogContent sx={{ display: 'grid', gap: 2, pt: '12px !important' }}>
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
      <DialogContent><Typography>Giao “{publish?.title}” cho lớp hiện có {studentCount} học sinh? Danh sách người nhận được chốt tại thời điểm giao bài.</Typography></DialogContent>
      <DialogActions><Button disabled={dispatch.isPending} onClick={() => setPublish(null)}>Quay lại</Button>
        <Button disabled={dispatch.isPending} variant="contained" onClick={() => { if (publish) dispatch.mutate(publish); }}>{dispatch.isPending ? 'Đang giao…' : 'Xác nhận giao'}</Button></DialogActions>
    </Dialog>
  </Box>;
}
