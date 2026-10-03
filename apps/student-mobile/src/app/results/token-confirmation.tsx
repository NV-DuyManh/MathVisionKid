import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, ScrollView, Text, Alert, Image, Pressable } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { FONTS, COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { TokenConfirmationCard } from '../../components/domain/TokenConfirmationCard';
import { getSubmissionService } from '../../services/api/SubmissionServiceFactory';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
import { SubmissionResult } from '../../types';
import { getUncertainTokens, resolveResultRoute } from '../../utils/resultRouting';

export default function TokenConfirmationScreen() {
  const router = useRouter();
  const { id, submissionId } = useLocalSearchParams<{ id?: string; submissionId?: string }>();
  const currentId = submissionId || id;
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [reload, setReload] = useState(0);
  const controller = useRef<AbortController | null>(null);
  const draft = recognitionDraftStore.getDraft();
  const tokens = result ? getUncertainTokens(result) : [];
  const selected = tokens.find(token => token.tokenId === selectedId) || tokens[0];
  const matchingDraft = draft?.mode === 'ARITHMETIC' && draft.arithmeticSubmissionId === currentId ? draft : null;
  const box = selected?.boundingBox;
  const validBox = box?.length === 4 && box.every(number => Number.isFinite(number) && number >= 0 && number <= 1) && box[2] > 0 && box[3] > 0 && box[0] + box[2] <= 1.001 && box[1] + box[3] <= 1.001;

  useEffect(() => {
    const request = new AbortController();
    controller.current = request;
    setLoading(true);
    setFailed(false);
    setResult(null);
    if (!currentId || currentId.startsWith('trial_')) { setLoading(false); setFailed(true); return () => request.abort(); }
    getSubmissionService().getSubmission(currentId, undefined, request.signal).then(current => {
      if (request.signal.aborted) return;
      const target = resolveResultRoute(current);
      if (target.pathname !== '/results/token-confirmation') router.replace(target as any);
      else { setResult(current); setSelectedId(null); }
    }).catch(() => { if (!request.signal.aborted) setFailed(true); })
      .finally(() => { if (!request.signal.aborted) setLoading(false); });
    return () => { request.abort(); controller.current?.abort(); };
  }, [currentId, reload, router]);

  const cancel = () => { controller.current?.abort(); router.back(); };
  const handleConfirm = async (newClass: string) => {
    if (loading || !currentId || !result?.jobId || !selected?.tokenId || !/^[0-9+-]$/.test(newClass)) return;
    const request = new AbortController();
    controller.current?.abort(); controller.current = request;
    setLoading(true);
    try {
      const updated = await getSubmissionService().confirmToken(currentId, { jobId: result.jobId, tokenId: selected.tokenId, newClass }, request.signal);
      if (request.signal.aborted) return;
      const target = resolveResultRoute(updated);
      if (target.pathname === '/results/token-confirmation') { setResult(updated); setSelectedId(null); }
      else router.replace(target as any);
    } catch (error: any) {
      if (request.signal.aborted) return;
      if (error?.response?.status === 409) {
        Alert.alert('Bài đã có kết quả mới', 'Em hãy mở lại các ký hiệu cần xác nhận nhé.', [{ text: 'Mở lại', onPress: () => setReload(value => value + 1) }]);
      } else Alert.alert('Chưa thể xác nhận', 'Chưa cập nhật được ký hiệu này. Em hãy thử lại nhé.');
    } finally { if (!request.signal.aborted) setLoading(false); }
  };

  return <View style={styles.container}>
    <AppHeader title="Xác nhận ký hiệu" showBack />
    {loading ? <RecognitionProgress title={result ? 'Đang kiểm tra lại bài' : 'Đang mở bài làm'} description={result ? 'Cập nhật ký hiệu em vừa xác nhận.' : 'Tìm các ký hiệu cần em xem lại.'} imageUri={matchingDraft?.uri} onCancel={cancel} />
      : <ScrollView contentContainerStyle={styles.content}>
        {selected && result?.jobId ? <>
          {matchingDraft && matchingDraft.width > 0 && matchingDraft.height > 0 && <View style={[styles.photoFrame, { aspectRatio: matchingDraft.width / matchingDraft.height, maxWidth: 320 * matchingDraft.width / matchingDraft.height }]}>
            <Image source={{ uri: matchingDraft.uri }} style={StyleSheet.absoluteFill} resizeMode="contain" accessibilityLabel="Ảnh bài làm đã gửi" />
            {validBox && box && <View pointerEvents="none" style={[styles.highlight, { left: `${box[0] * 100}%`, top: `${box[1] * 100}%`, width: `${box[2] * 100}%`, height: `${box[3] * 100}%` }]} />}
          </View>}
          <Text style={styles.context}>Chọn ký hiệu chưa rõ trong bài của em:</Text>
          <View style={styles.tokens}>{tokens.map((token, index) => <Pressable key={token.tokenId} accessibilityRole="button"
            accessibilityLabel={`Ký hiệu ${index + 1}: ${token.value}`} accessibilityState={{ selected: selected.tokenId === token.tokenId }}
            onPress={() => setSelectedId(token.tokenId!)} style={[styles.token, token.tokenId === selected.tokenId && styles.selectedToken]}>
            <Text style={styles.tokenText}>{token.value}</Text>
            <Text style={styles.position}>{token.row != null ? `Dòng ${token.row + 1}` : `Vị trí ${index + 1}`}{token.column != null && token.column < 99 ? ` · cột ${token.column + 1} từ phải` : ''}</Text>
          </Pressable>)}</View>
          <TokenConfirmationCard key={selected.tokenId} initialToken={selected.value} onConfirm={handleConfirm} />
        </> : <>
          <StatusCard status="warning" title="Chưa có ký hiệu để xác nhận" subtitle={failed ? 'Chưa lấy được bài làm. Em hãy thử mở lại nhé.' : 'Bài làm chưa đủ dữ liệu để xác nhận ký hiệu. Em hãy chụp lại ảnh rõ hơn nhé.'} />
          <AppButton title="Mở lại bài làm" onPress={() => setReload(value => value + 1)} />
          <AppButton title="Về trang chủ" variant="secondary" onPress={() => router.replace('/(tabs)')} />
        </>}
      </ScrollView>}
  </View>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SIZES.large, gap: 16, flexGrow: 1, maxWidth: 500, width: '100%', alignSelf: 'center' },
  photoFrame: { width: '100%', alignSelf: 'center', backgroundColor: COLORS.surface, borderRadius: 20, overflow: 'hidden' },
  highlight: { position: 'absolute', borderWidth: 2, borderColor: COLORS.primary, backgroundColor: 'rgba(120,83,226,0.18)' },
  context: { fontFamily: FONTS.semiBold, fontSize: 16, color: COLORS.textPrimary },
  tokens: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  token: { minHeight: 60, padding: 10, borderRadius: 12, borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.surface },
  selectedToken: { borderColor: COLORS.primary, backgroundColor: COLORS.surfaceSubdued },
  tokenText: { fontFamily: FONTS.bold, fontSize: 22, color: COLORS.primaryDark, textAlign: 'center' },
  position: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary },
});
