import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../../constants/theme';
import type { RecognitionMetrics } from '../analytics/recognitionMetrics';
import { formatMetricPercent } from '../utils/metricFormat';

export function RecognitionSummary({ metrics }: { metrics: RecognitionMetrics }) {
  const rows = [
    ['Bài đã lưu', String(metrics.totalSessions)],
    ['Dòng chữ', String(metrics.totalLines)],
    ['Dòng đã đối chiếu với bản chuẩn', String(metrics.evaluatedLines)],
    ['Nhận dạng đúng cả dòng', formatMetricPercent(metrics.rawAccuracy)],
    ['Tỷ lệ sai ký tự', formatMetricPercent(metrics.cer)],
  ];
  return <View style={styles.card}>
    <Text style={styles.title} accessibilityRole="header">Kết quả nhận dạng</Text>
    {rows.map(([label, value]) => <View style={styles.row} key={label}>
      <Text style={styles.label}>{label}</Text><Text style={styles.value}>{value}</Text>
    </View>)}
    <Text style={styles.note}>
      {metrics.hasEvaluatedLines
        ? 'Tỷ lệ được tính trên các dòng có bản chuẩn độc lập để đối chiếu.'
        : 'Chưa có bản chuẩn để đo độ chính xác. Việc chọn gợi ý hoặc tự sửa chưa đủ để tính tỷ lệ này.'}
    </Text>
  </View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: COLORS.surface, padding: SIZES.medium, borderRadius: SIZES.cardRadius, gap: SIZES.small, marginBottom: SIZES.medium },
  title: { color: COLORS.textPrimary, fontSize: 18, fontWeight: '700' },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: SIZES.small, alignItems: 'baseline' },
  label: { flexGrow: 1, flexShrink: 1, color: COLORS.textSecondary, fontSize: 15 },
  value: { color: COLORS.primaryDark, fontWeight: '700', fontSize: 16 },
  note: { color: COLORS.textSecondary, fontSize: 14, lineHeight: 21 },
});
