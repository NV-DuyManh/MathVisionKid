import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS } from '../constants/theme';
import { getSubmissionService } from '../services/api/SubmissionServiceFactory';
import { recognitionDraftStore, isHandwritingDomain, resolveFlowDomain } from '../features/recognition/state/recognitionDraftStore';
import { ensureFileUri } from '../features/recognition/image/imagePipeline';
import { RecognitionProgress } from '../features/recognition/components/RecognitionProgress';
import { StatusCard } from '../components/domain/StatusCard';
import { AppButton } from '../components/ui/AppButton';
import { resolveResultRoute } from '../utils/resultRouting';
import { pollSubmission } from '../utils/submissionPolling';

export default function ProcessingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uri?: string; originalUri?: string; retrySubmissionId?: string; submissionId?: string }>();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const controllerRef = useRef<AbortController | null>(null);
  const resumeId = useRef(params.submissionId || '');
  const draft = recognitionDraftStore.getDraft();
  const activeUri = draft?.uri || params.uri || '';

  useEffect(() => {
    const controller = new AbortController();
    controllerRef.current = controller;
    setError(null);
    setStep(0);
    const process = async () => {
      try {
        const currentDraft = recognitionDraftStore.getDraft();
        const mode = resolveFlowDomain(null, currentDraft?.mode);
        if (!resumeId.current && (isHandwritingDomain(mode) || mode !== 'ARITHMETIC')) {
          router.replace(mode === 'OCR_PILOT' ? '/recognition/line-crop' : '/recognition/multiline-review');
          return;
        }
        if (!activeUri && !resumeId.current) throw new Error('IMAGE_MISSING');
        const service = getSubmissionService();
        const retryId = currentDraft?.retrySubmissionId || params.retrySubmissionId;
        const initial = resumeId.current ? await service.getSubmission(resumeId.current, undefined, controller.signal)
          : retryId ? await service.retrySubmission(retryId, ensureFileUri(activeUri), controller.signal)
          : await service.uploadImage(ensureFileUri(activeUri), controller.signal);
        if (controller.signal.aborted) return;
        resumeId.current = initial.id;
        if (currentDraft?.mode === 'ARITHMETIC' && !params.submissionId) recognitionDraftStore.updateDraft({ arithmeticSubmissionId: initial.id });
        setStep(1);
        const scenarioHint = activeUri.includes('mock-earliest-error') ? 'mock-earliest-error' : activeUri.includes('mock-confirm') ? 'mock-confirm' : undefined;
        const result = await pollSubmission(initial, service, controller.signal, scenarioHint);
        if (controller.signal.aborted) return;
        router.replace(resolveResultRoute(result, currentDraft?.rawUri || params.originalUri) as any);
      } catch (failure: any) {
        if (controller.signal.aborted) return;
        setError(failure?.message === 'SUBMISSION_PENDING' ? 'Bài vẫn đang được xử lý. Em có thể xem lại kết quả hoặc quay về trang chủ.'
          : failure?.message === 'IMAGE_MISSING' ? 'Chưa tìm thấy ảnh bài làm. Em hãy chọn hoặc chụp lại ảnh nhé.'
          : 'Chưa thể nhận kết quả lúc này. Em hãy thử lại nhé.');
      }
    };
    void process();
    return () => controller.abort();
  }, [params.uri, params.originalUri, params.retrySubmissionId, params.submissionId, attempt, router]);

  const cancel = () => { controllerRef.current?.abort(); router.back(); };
  return <SafeAreaView style={styles.container}>
    {error ? <View style={styles.error}>
      <StatusCard status="warning" title="Chưa có kết quả" subtitle={error} />
      <AppButton title={resumeId.current ? 'Xem lại kết quả' : 'Thử gửi lại'} onPress={() => setAttempt(value => value + 1)} />
      <AppButton title="Về trang chủ" variant="secondary" onPress={() => { controllerRef.current?.abort(); router.replace('/(tabs)'); }} />
    </View> : <RecognitionProgress title={step === 0 ? 'Đang đọc bài toán' : 'Đang kiểm tra bài làm'}
      description={step === 0 ? 'Gửi và nhận dạng các chữ số trong ảnh.' : 'MathVision đang kiểm tra phép tính của em.'}
      imageUri={activeUri || undefined} onCancel={cancel} />}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background, justifyContent: 'center', alignItems: 'center', padding: 24 },
  error: { width: '100%', maxWidth: 500, gap: 16 },
});
