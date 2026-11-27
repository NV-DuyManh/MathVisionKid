import { useRouter } from 'expo-router';
import { AppButton } from '../../../components/ui/AppButton';
import type { FlowDomain } from '../state/recognitionDraftStore';

export type DraftImagePickerProps = { title?: string; mode?: FlowDomain; disabled?: boolean; showReason?: boolean; dialogTitle?: string };
export function DraftImagePicker({ title = 'Chọn lại ảnh', disabled }: DraftImagePickerProps) {
  const router = useRouter();
  return <AppButton title={title} disabled={disabled} onPress={() => router.push('/gallery')} />;
}
