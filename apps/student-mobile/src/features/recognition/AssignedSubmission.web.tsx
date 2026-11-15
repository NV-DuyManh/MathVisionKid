import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import { isAxiosError } from 'axios';
import apiClient from '../../services/api/apiClient';
import { exportCropImage } from '../../utils/cropRotation.web';

type Status = {
  imageVersion: number;
  status: string;
  score: number | null;
  feedback: string | null;
  retakeReason: 'UNREADABLE' | 'WRONG_ASSIGNMENT' | null;
  retakeInstruction: string | null;
};
const edges = [
  ['top', 'trên'], ['right', 'phải'], ['bottom', 'dưới'], ['left', 'trái'],
] as const;
const emptyCrop = { top: 0, right: 0, bottom: 0, left: 0 };
const emptyMask = { x: 0, y: 0, w: 0, h: 0 };

function newUploadKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join('-');
}
const labels: Record<string, string> = {
  UPLOADING: 'Đang gửi ảnh',
  AWAITING_IMAGE: 'Chưa gửi',
  AWAITING_REVIEW: 'Cô/thầy đã nhận bài',
  RETAKE_REQUESTED: 'Cần chụp lại',
  GRADE_RELEASED: 'Cô/thầy đã trả bài',
};

export default function AssignedSubmission({ assignmentId, maxScore }: {
  assignmentId: string;
  maxScore: number;
}) {
  const [result, setResult] = useState<Status>();
  const [failed, setFailed] = useState(false);
  const [revision, setRevision] = useState(0);
  const [photo, setPhoto] = useState<{ file: File; key: string; version: number; preview: string; normalized: boolean; checked: boolean }>();
  const [confirmed, setConfirmed] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [crop, setCrop] = useState(emptyCrop);
  const [mask, setMask] = useState(emptyMask);
  const [editing, setEditing] = useState(false);
  const hasMask = mask.w > 0 && mask.h > 0;
  const hasMaskDraft = Object.values(mask).some(Boolean);
  const incompleteMask = hasMaskDraft && !hasMask;
  const hasEdits = Object.values(crop).some(Boolean) || hasMaskDraft;
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  const preview = photo?.preview;
  useEffect(() => {
    if (preview) return () => URL.revokeObjectURL(preview);
  }, [preview]);
  async function applyPrivacyEdits() {
    if (!photo || editing || sending || !hasEdits || incompleteMask) return;
    setEditing(true);
    setConfirmed(false);
    setUploadError('');
    try {
      const cropped = await exportCropImage(photo.preview, 0, {
        x: crop.left / 100, y: crop.top / 100,
        w: (100 - crop.left - crop.right) / 100, h: (100 - crop.top - crop.bottom) / 100,
      }, hasMask ? [{ x: mask.x / 100, y: mask.y / 100, w: mask.w / 100, h: mask.h / 100 }] : []);
      try {
        const blob = await (await fetch(cropped.uri)).blob();
        setPhoto({ ...photo, normalized: true, checked: false, file: new File([blob], 'bai-lam.jpg', { type: 'image/jpeg' }),
          key: newUploadKey(), preview: URL.createObjectURL(blob) });
        setCrop(emptyCrop);
        setMask(emptyMask);
      } finally { URL.revokeObjectURL(cropped.uri); }
    } catch {
      setUploadError('Chưa chỉnh được ảnh. Em thử chọn ảnh khác nhé.');
    } finally { setEditing(false); }
  }
  async function checkPrivacy() {
    if (!photo || hasEdits || editing || pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setEditing(true);
    setConfirmed(false);
    setUploadError('');
    try {
      let checkedPhoto = photo;
      if (!photo.normalized) {
        const image = await exportCropImage(photo.preview, 0, { x: 0, y: 0, w: 1, h: 1 });
        try {
          const blob = await (await fetch(image.uri)).blob();
          if (controller.signal.aborted) return;
          checkedPhoto = { ...photo, normalized: true, checked: false,
            file: new File([blob], 'bai-lam.jpg', { type: 'image/jpeg' }), preview: URL.createObjectURL(blob) };
          setPhoto(checkedPhoto);
        } finally { URL.revokeObjectURL(image.uri); }
      }
      const form = new FormData();
      form.append('image', checkedPhoto.file, 'bai-lam.jpg');
      await apiClient.post(`/student/assignments/${encodeURIComponent(assignmentId)}/submission/privacy-check`, form,
        { signal: controller.signal });
      if (!controller.signal.aborted) setPhoto({ ...checkedPhoto, checked: true });
    } catch (error) {
      if (controller.signal.aborted) return;
      const code = isAxiosError<{ error?: { code?: string } }>(error) ? error.response?.data?.error?.code : undefined;
      setUploadError(code === 'IMAGE_PRIVACY_REVIEW'
        ? 'Em hãy cắt hoặc che thông tin riêng tư rồi kiểm tra lại ảnh.'
        : 'Chưa kiểm tra được ảnh. Em hãy thử lại.');
    } finally {
      pending.current = null;
      if (!controller.signal.aborted) setEditing(false);
    }
  }
  async function send() {
    if (!photo?.checked || !result || !confirmed || hasEdits || editing || pending.current) return;
    const request = photo.version === result.imageVersion
      ? photo
      : { ...photo, version: result.imageVersion, key: newUploadKey() };
    const controller = new AbortController();
    pending.current = controller;
    setSending(true);
    setUploadError('');
    const form = new FormData();
    form.append('expectedImageVersion', String(request.version));
    form.append('privacyConfirmed', 'true');
    try {
      const finalImage = photo.normalized
        ? photo.file
        : await exportCropImage(photo.preview, 0, { x: 0, y: 0, w: 1, h: 1 }).then(async image => {
          try { return await (await fetch(image.uri)).blob(); }
          finally { URL.revokeObjectURL(image.uri); }
        });
      if (controller.signal.aborted) return;
      if (!photo.normalized) {
        setPhoto({ ...request, normalized: true, file: new File([finalImage], 'bai-lam.jpg', { type: 'image/jpeg' }),
          preview: URL.createObjectURL(finalImage) });
      } else if (request !== photo) {
        setPhoto(request);
      }
      form.append('image', finalImage, 'bai-lam');
      await apiClient.post(`/student/assignments/${encodeURIComponent(assignmentId)}/submission`, form, {
        headers: { 'Idempotency-Key': request.key }, signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      setPhoto(undefined);
      setConfirmed(false);
      setResult(undefined);
      setRevision(value => value + 1);
    } catch (error) {
      if (controller.signal.aborted) return;
      const response = isAxiosError<{ error?: { code?: string } }>(error) ? error.response : undefined;
      if (response?.data?.error?.code === 'IMAGE_PRIVACY_REVIEW') {
        setPhoto(current => current && { ...current, checked: false });
        setConfirmed(false);
        setUploadError('Em hãy cắt hoặc che thông tin riêng tư. Nếu ảnh chưa rõ, em có thể chụp lại.');
      } else if (response?.data?.error?.code === 'IMAGE_PRIVACY_UNAVAILABLE') {
        setUploadError('Chưa kiểm tra được ảnh. Em hãy thử gửi lại sau.');
      } else if (response?.status === 409) {
        if (response.data?.error?.code === 'UPLOAD_EXPIRED') {
          const key = newUploadKey();
          setPhoto(current => current && { ...current, key });
        }
        setConfirmed(false);
        setResult(undefined);
        setRevision(value => value + 1);
        setUploadError('Ảnh em đã chọn vẫn còn. Kiểm tra trạng thái bài rồi xác nhận lại nếu em muốn gửi ảnh này.');
      } else {
        setUploadError('Chưa gửi được ảnh. Em có thể thử lại hoặc tải lại bài để xem trạng thái.');
      }
    } finally {
      pending.current = null;
      if (!controller.signal.aborted) setSending(false);
    }
  }
  useEffect(() => {
    const controller = new AbortController();
    void apiClient.get<Status>(`/student/assignments/${encodeURIComponent(assignmentId)}/submission`, {
      signal: controller.signal,
    }).then(({ data }) => {
      if (!controller.signal.aborted) setResult(data);
    }).catch(() => {
      if (!controller.signal.aborted) setFailed(true);
    });
    return () => controller.abort();
  }, [assignmentId, revision]);

  useEffect(() => {
    if (result?.status !== 'UPLOADING' || failed) return;
    const timer = window.setTimeout(() => setRevision(value => value + 1), 5000);
    return () => window.clearTimeout(timer);
  }, [result, failed]);

  return <View style={{ gap: 8, padding: 16, borderRadius: 16, backgroundColor: '#fff' }}>
    {failed ? <>
      <Text accessibilityRole="alert">Chưa xem được bài đã gửi.</Text>
      <Pressable accessibilityRole="button" style={{ minHeight: 44 }} onPress={() => {
        setFailed(false);
        setResult(undefined);
        setRevision(value => value + 1);
      }}><Text>Thử lại</Text></Pressable>
    </> : result ? <>
      <Text accessibilityRole="header" style={{ fontSize: 18, fontWeight: '700' }}>
        {labels[result.status] ?? 'Bài làm của em'}
      </Text>
      {result.status === 'RETAKE_REQUESTED' && <>
        <Text>{result.retakeReason === 'WRONG_ASSIGNMENT' ? 'Ảnh chưa đúng đề bài.' : 'Ảnh chưa đọc rõ.'}</Text>
        <Text>{result.retakeInstruction}</Text>
      </>}
      {result.status === 'GRADE_RELEASED' && <>
        {result.score !== null && <Text style={{ fontSize: 22 }}>{result.score}/{maxScore} điểm</Text>}
        {!!result.feedback && <Text selectable>{result.feedback}</Text>}
      </>}
      {result.imageVersion > 0 && <SubmittedImage
        key={result.imageVersion} assignmentId={assignmentId} />}
      {result.status === 'UPLOADING' && <Text accessibilityRole="status">Đang kiểm tra ảnh đã gửi. Em có thể quay lại bài này sau.</Text>}
      {result.status !== 'GRADE_RELEASED' && (result.status !== 'UPLOADING' || photo) && <>
        <Text>Chụp rõ phần bài làm. Để tên, mặt và thông tin riêng tư ngoài khung ảnh.</Text>
        {(['Chụp ảnh', 'Chọn ảnh'] as const).map(label => <label key={label}>
          {label}
          <input type="file" accept="image/jpeg,image/png" capture={label === 'Chụp ảnh' ? 'environment' : undefined}
            disabled={sending || editing || result.status === 'UPLOADING'} onChange={event => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = '';
              if (!file) return;
              setConfirmed(false);
              setCrop(emptyCrop);
              setMask(emptyMask);
              setUploadError('');
              setPhoto({ file, key: newUploadKey(), version: result.imageVersion, normalized: false, checked: false,
                preview: URL.createObjectURL(file) });
            }} />
        </label>)}
        {photo && <>
          <img src={photo.preview} alt="Xem trước ảnh bài làm" style={{ maxWidth: '100%', maxHeight: 350, objectFit: 'contain' }} />
          <details>
            <summary>Cắt ảnh hoặc che thông tin</summary>
            <fieldset disabled={sending || editing}>
              <legend>Cắt mép ảnh</legend>
              {edges.map(([edge, name]) => <label key={edge} style={{ display: 'block' }}>
                Mép {name} ({crop[edge]}%) <input type="range" min={0} max={45} value={crop[edge]}
                  onChange={event => { setCrop({ ...crop, [edge]: Number(event.target.value) }); setConfirmed(false); }} />
              </label>)}
            </fieldset>
            <fieldset disabled={sending || editing}>
              <legend>Vùng che trên ảnh sau khi cắt</legend>
              {([['x', 'Từ trái'], ['y', 'Từ trên'], ['w', 'Chiều rộng'], ['h', 'Chiều cao']] as const)
                .map(([key, name]) => <label key={key} style={{ display: 'block' }}>
                  {name} ({mask[key]}%) <input type="range" min={0} max={key === 'x' || key === 'y' ? 99 : 100} value={mask[key]}
                    onChange={event => { setMask({ ...mask, [key]: Number(event.target.value) }); setConfirmed(false); }} />
                </label>)}
            </fieldset>
            {incompleteMask && <Text accessibilityRole="status">Chọn cả chiều rộng và chiều cao của vùng che.</Text>}
            {hasMaskDraft && <button type="button" disabled={sending || editing} onClick={() => setMask(emptyMask)}>
              Hủy vùng che đang chỉnh
            </button>}
          </details>
          <button type="button" disabled={sending || editing || !hasEdits || incompleteMask} onClick={() => void applyPrivacyEdits()}>
            {editing ? 'Đang chỉnh ảnh…' : 'Áp dụng'}
          </button>
          {!photo.checked && <button type="button" style={{ minHeight: 44 }} disabled={sending || editing || hasEdits}
            onClick={() => void checkPrivacy()}>{editing ? 'Đang kiểm tra ảnh…' : 'Kiểm tra ảnh'}</button>}
          {photo.checked && <Text accessibilityRole="status">Đã kiểm tra ảnh. Em hãy xem lại rồi xác nhận gửi.</Text>}
          <label><input type="checkbox" checked={confirmed} disabled={!photo.checked || sending || editing || hasEdits}
            onChange={event => setConfirmed(event.target.checked)} /> Em đã che hoặc bỏ thông tin riêng tư khỏi ảnh.</label>
          <button type="button" style={{ minHeight: 44 }} disabled={!photo.checked || !confirmed || sending || editing || hasEdits} onClick={() => void send()}>
            {sending ? 'Đang gửi ảnh…' : result.imageVersion ? 'Gửi ảnh mới' : 'Gửi bài làm'}
          </button>
        </>}
        {uploadError && <Text accessibilityRole="alert">{uploadError}</Text>}
      </>}
    </> : <ActivityIndicator accessibilityLabel="Đang tải trạng thái bài làm" />}
  </View>;
}

function SubmittedImage({ assignmentId }: { assignmentId: string }) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState<string>();
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    let objectUrl: string | undefined;
    void apiClient.get<Blob>(`/student/assignments/${encodeURIComponent(assignmentId)}/submission/image`, {
      responseType: 'blob', signal: controller.signal,
    }).then(({ data }) => {
      if (controller.signal.aborted) return;
      objectUrl = URL.createObjectURL(data);
      setUrl(objectUrl);
    }).catch(() => {
      if (!controller.signal.aborted) setFailed(true);
    });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [assignmentId, open]);

  return <>
    <button type="button" style={{ minHeight: 44 }} aria-expanded={open} onClick={() => {
      setUrl(undefined);
      setFailed(false);
      setOpen(!open);
    }}>{open ? 'Ẩn ảnh đã gửi' : 'Xem ảnh đã gửi'}</button>
    {open && (failed
      ? <Text accessibilityRole="alert">Chưa mở được ảnh. Em hãy đóng ảnh và thử lại.</Text>
      : url
        ? <img src={url} alt="Ảnh bài làm em đã gửi" onError={() => setFailed(true)}
            style={{ maxWidth: '100%', maxHeight: 350, objectFit: 'contain' }} />
        : <Text accessibilityRole="status">Đang mở ảnh…</Text>)}
  </>;
}
