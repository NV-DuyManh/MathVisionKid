import React, { useState, useEffect } from 'react';
import { ActivityIndicator, ScrollView, Text, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, SIZES } from '../../constants/theme';
import { recognitionAnalyticsStore, exportTrialToJson, exportTrialToCsv, type TrialAnalytics } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildRecognitionMetrics } from '../../features/recognition/analytics/recognitionMetrics';
import { RecognitionSummary } from '../../features/recognition/components/RecognitionSummary';
import { shareRecognitionExport } from '../../features/recognition/analytics/shareExport';
import { RecognitionService } from '../../features/recognition/api/RecognitionService';

export default function RecognitionTrialAnalyticsScreen() {
  const { trialId: rawId } = useLocalSearchParams<{ trialId?: string | string[] }>();
  const trialId = Array.isArray(rawId) ? rawId[0] : rawId;
  const [trial, setTrial] = useState<TrialAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setTrial(null);
    async function load() {
      if (!trialId) return;
      await recognitionAnalyticsStore.init();
      let data = await recognitionAnalyticsStore.getCurrentTrialAnalytics(trialId);
      if (!data) {
        const result = await RecognitionService.getMultilineTrial(trialId);
        data = recognitionAnalyticsStore.computeTrialAnalytics(result, result.lines.length > 0 && result.lines.every(line => ['CORRECT', 'CORRECTED', 'SKIPPED'].includes(line.verdict)));
      }
      if (active) setTrial(data);
    }
    load().catch(() => { if (active) setTrial(null); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [trialId]);
  const metrics = buildRecognitionMetrics(recognitionAnalyticsStore.getSessions().filter(session => session.sessionId === trialId));
  return <SafeAreaView style={styles.container}>
    <AppHeader title="Chi tiết bài nhận dạng" showBack />
    {loading ? <ActivityIndicator style={styles.loading} color={COLORS.primary} accessibilityLabel="Đang tải kết quả" />
      : <ScrollView contentContainerStyle={styles.content}>
        {trial ? <>
          <RecognitionSummary metrics={metrics} />
          <Text style={styles.message}>{trial.totalLines} dòng chữ · {trial.status === 'COMPLETED' ? 'Đã lưu kết quả xác nhận' : 'Đang kiểm tra từng dòng'}</Text>
          {trial.lineMetrics.map((line, index) => <View style={styles.card} key={line.lineId || index}>
            <Text style={styles.title}>Dòng {index + 1}</Text>
            <Text style={styles.label}>Chữ nhận dạng ban đầu</Text><Text style={styles.text}>{line.ocrOutput || line.modelOutput || line.ocrText || '(Trống)'}</Text>
            {(line.aiCandidate || line.aiSuggestion) ? <><Text style={styles.label}>Gợi ý AI</Text><Text style={styles.text}>{line.aiCandidate || line.aiSuggestion}</Text></> : null}
            <Text style={styles.label}>Nội dung đã chọn</Text><Text style={styles.text}>{line.finalResult || line.finalText || line.text || '(Trống)'}</Text>
          </View>)}
          <AppButton title="Xuất kết quả JSON" variant="outlined" onPress={() => shareRecognitionExport(exportTrialToJson(trial), 'mathvision-recognition-result.json')} />
          <AppButton title="Xuất kết quả CSV" variant="outlined" onPress={() => shareRecognitionExport(exportTrialToCsv(trial), 'mathvision-recognition-result.csv')} />
        </> : <Text style={styles.message}>Chưa có kết quả cho bài này. Em hãy nhận dạng lại ảnh hoặc quay lại lịch sử.</Text>}
      </ScrollView>}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SIZES.medium, gap: SIZES.medium, width: '100%', maxWidth: 640, alignSelf: 'center' },
  card: { padding: SIZES.medium, gap: SIZES.small, backgroundColor: COLORS.surface, borderRadius: SIZES.cardRadius },
  title: { fontSize: 17, fontWeight: '700', color: COLORS.textPrimary },
  label: { fontSize: 14, fontWeight: '600', color: COLORS.textSecondary },
  text: { fontSize: 16, color: COLORS.textPrimary, lineHeight: 24 },
  message: { fontSize: 15, color: COLORS.textSecondary, lineHeight: 23 },
  loading: { margin: SIZES.xxlarge },
});
