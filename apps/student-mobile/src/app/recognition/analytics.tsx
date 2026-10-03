import React, { useState, useCallback } from 'react';
import { ActivityIndicator, FlatList, Text, View, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { FONTS, COLORS, SIZES } from '../../constants/theme';
import { recognitionAnalyticsStore } from '../../features/recognition/analytics/recognitionAnalyticsStore';
import { buildRecognitionMetrics, type RecognitionMetrics } from '../../features/recognition/analytics/recognitionMetrics';
import { RecognitionSummary } from '../../features/recognition/components/RecognitionSummary';
import { shareRecognitionExport } from '../../features/recognition/analytics/shareExport';

export default function RecognitionAnalyticsScreen() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<RecognitionMetrics>(() => buildRecognitionMetrics([]));
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setLoading(true);
    setFailed(false);
    recognitionAnalyticsStore.init().then(() => {
      if (active) setMetrics(recognitionAnalyticsStore.getMeasuredMetrics());
    }).catch(() => { if (active) setFailed(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []));
  return <SafeAreaView style={styles.container}>
    <AppHeader title="Lịch sử nhận dạng" showBack />
    {loading ? <ActivityIndicator style={styles.loading} color={COLORS.primary} accessibilityLabel="Đang tải lịch sử" />
      : <FlatList contentContainerStyle={styles.content} data={metrics.sessions}
        keyExtractor={session => session.sessionId}
        ListHeaderComponent={<>
          <RecognitionSummary metrics={metrics} />
          <AppButton title="Xuất lịch sử" variant="outlined" disabled={!metrics.hasLiveSessions}
            onPress={() => shareRecognitionExport(JSON.stringify({ metrics, sessions: metrics.sessions }, null, 2), 'mathvision-recognition-history.json')} />
        </>}
        ListEmptyComponent={<Text style={styles.message}>
          {failed ? 'Chưa thể tải lịch sử. Vui lòng mở lại trang này.' : 'Chưa có bài nhận dạng được lưu. Hãy chụp bài và xác nhận các dòng chữ.'}
        </Text>}
        renderItem={({ item, index }) => <View style={styles.card}>
          <Text style={styles.title}>Bài nhận dạng {index + 1}</Text>
          <Text style={styles.message}>{new Date(item.timestamp).toLocaleDateString('vi-VN')} · {item.totalLines} dòng chữ</Text>
          <AppButton title="Xem kết quả" variant="secondary" onPress={() => router.push({
            pathname: '/recognition/trial-analytics', params: { trialId: item.sessionId },
          })} />
        </View>} />}
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SIZES.medium, gap: SIZES.medium, width: '100%', maxWidth: 640, alignSelf: 'center' },
  card: { padding: SIZES.medium, gap: SIZES.small, backgroundColor: COLORS.surface, borderRadius: SIZES.cardRadius },
  title: { fontSize: 17, fontFamily: FONTS.bold, color: COLORS.textPrimary },
  message: { color: COLORS.textSecondary, fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23 },
  loading: { margin: SIZES.xxlarge },
});
