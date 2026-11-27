import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import { RecoveryNotice } from '../../../components/ui/RecoveryNotice';
import { normalizeImageDraft } from '../image/imagePipeline';
import { recognitionDraftStore, resolveFlowDomain } from '../state/recognitionDraftStore';
import { imageDraftPersistence } from '../state/imageDraftPersistence';
import { COLORS } from '../../../constants/theme';
import type { DraftImagePickerProps } from './DraftImagePicker';

const messages = {
  none: 'Em có thể chọn ảnh khác để bắt đầu lại bước kiểm tra riêng tư.',
  missing: 'Chưa có ảnh đã xác nhận để khôi phục. Em chọn ảnh bài tập nhé.',
  expired: 'Ảnh đã hết thời gian lưu tạm. Em chọn lại ảnh để tiếp tục nhé.',
  corrupt: 'Ảnh lưu tạm không còn mở được. Em chọn lại ảnh nhé.',
  unavailable: 'Chưa mở được nơi lưu ảnh trên thiết bị. Em vẫn có thể chọn ảnh để tiếp tục.',
  unauthorized: 'Chưa xác minh được phiên học của em. Em đăng nhập lại trước khi chọn ảnh nhé.',
};
export function DraftImagePicker({ title = 'Chọn lại ảnh', mode, disabled, showReason, dialogTitle }: DraftImagePickerProps) {
  const input = useRef<HTMLInputElement>(null), active = useRef(true), locked = useRef(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(false);
  const recovery = useSyncExternalStore(imageDraftPersistence.subscribe, imageDraftPersistence.getSnapshot, imageDraftPersistence.getSnapshot);
  const identity = useRef('');
  const request = useRef(0);
  const router = useRouter();
  useFocusEffect(useCallback(() => {
    active.current = true; setBusy(false);
    return () => { active.current = false; request.current++; locked.current = false; };
  }, []));
  useEffect(() => {
    active.current = true;
    const element = input.current;
    const cancel = () => { locked.current = false; };
    element?.addEventListener('cancel', cancel);
    return () => { active.current = false; element?.removeEventListener('cancel', cancel); };
  }, []);
  const pick = () => {
    if (disabled || locked.current || !input.current) return;
    identity.current = imageDraftPersistence.identity();
    request.current++;
    locked.current = true; input.current.value = ''; input.current.click();
  };
  const selected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    if (!file) { locked.current = false; return; }
    const old = recognitionDraftStore.getDraft();
    const id = request.current;
    const original = URL.createObjectURL(file);
    setBusy(true); setError(false);
    try {
      const draft = await normalizeImageDraft(original, undefined, undefined, 'GALLERY');
      if (!active.current || id !== request.current || identity.current !== imageDraftPersistence.identity()) {
        imageDraftPersistence.releaseUrl(draft.uri); return;
      }
      draft.rawUri = draft.uri;
      draft.mode = resolveFlowDomain(mode, old?.mode || 'MATH_TUTOR');
      draft.lessonContext = old?.lessonContext;
      draft.retrySubmissionId = old?.retrySubmissionId;
      const sourcePath = window.location.pathname;
      const selectedDraft = recognitionDraftStore.setDraft(draft);
      await imageDraftPersistence.savePrivacy(selectedDraft);
      // Updating the draft can remount the crop screen before storage finishes.
      if (window.location.pathname !== sourcePath || identity.current !== imageDraftPersistence.identity()
          || recognitionDraftStore.getDraft()?.imageSessionId !== selectedDraft.imageSessionId) return;
      router.push('/privacy');
    } catch { if (active.current && id === request.current) setError(true); }
    finally { URL.revokeObjectURL(original); if (id === request.current) { locked.current = false; if (active.current) setBusy(false); } }
  };
  return <View style={[{ gap: 12 }, showReason && { backgroundColor: COLORS.surface, padding: 16, borderRadius: 16 }]}>
    {showReason && !dialogTitle ? <Text style={{ color: COLORS.textSecondary }}>{messages[recovery.issue]}</Text> : null}
    {error ? <Text role="alert" style={{ color: COLORS.error }}>Chưa mở được ảnh này. Ảnh trước vẫn được giữ; em thử ảnh JPG hoặc PNG nhé.</Text> : null}
    <input ref={input} type="file" accept="image/*" hidden aria-label="Chọn ảnh bài tập" onChange={event => void selected(event)} />
    {dialogTitle ? <RecoveryNotice dialog={!recovery.restoring} title={dialogTitle}
      message={showReason ? messages[recovery.issue] : undefined}
      actions={[{ label: busy ? 'Đang mở ảnh…' : title, disabled: disabled || busy, onPress: pick }]} />
      : <AppButton title={title} onPress={pick} disabled={disabled || busy} loading={busy} loadingTitle="Đang mở ảnh..." />}
  </View>;
}
