import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { FONTS, COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { HintCard } from '../../components/domain/HintCard';
import { MathExpression } from '../../components/domain/MathExpression';
import { logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { useArithmeticResult } from '../../hooks/useArithmeticResult';
import { resolveResultRoute } from '../../utils/resultRouting';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';
import { StatusCard } from '../../components/domain/StatusCard';

export default function ErrorHintScreen() {
  const router = useRouter();
  const { data, submissionId } = useLocalSearchParams<{ data?: string; submissionId?: string }>();
  const { result, loading } = useArithmeticResult(data, submissionId);
  const target = result ? resolveResultRoute(result) : null;
  useEffect(() => {
    const destination = result ? resolveResultRoute(result) : null;
    if (destination && destination.pathname !== '/results/error-hint') router.replace(destination as any);
  }, [result, router]);

  useEffect(() => {
    logFlowDomain('RESULT', 'ARITHMETIC');
  }, []);

  return (
    <View style={styles.container}>
      <AppHeader title="Gợi ý bài làm" showBack />

      <ScrollView contentContainerStyle={styles.content}>
        {loading ? <RecognitionProgress title="Đang mở gợi ý" description="Lấy lại kết quả bài làm của em." onCancel={() => router.back()} /> : target?.pathname === '/results/error-hint' && result ? <>
        <Text style={styles.feedbackTitle}>{result.studentFeedback?.title}</Text>
        <Text style={styles.feedbackSubtitle}>
          MathVision đã phát hiện một bước tính cần em xem lại:
        </Text>

        <View style={styles.expressionContainer}>
          {result.recognizedExercise && (
            <MathExpression
              exercise={result.recognizedExercise}
              highlightIndex={result.evidence?.items?.find(item => item.evidenceId === result.studentFeedback?.focusEvidenceId)?.columnIndex ?? result.validation?.firstInvalidIndex}
            />
          )}
        </View>

        {result.studentFeedback?.hint ? (
          <HintCard hint={result.studentFeedback.hint} />
        ) : null}
        </> : <StatusCard status="warning" title="Chưa có kết quả" subtitle="Chưa lấy được kết quả bài làm. Em hãy mở lại bài hoặc chụp ảnh mới nhé." />}

        <View style={styles.spacer} />

        <View style={styles.actions}>
          <AppButton
            title="Em sẽ sửa lại"
            onPress={() => router.replace('/(tabs)')}
            variant="primary"
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Chụp lại bài đã sửa"
            variant="secondary"
            onPress={() => router.replace({ pathname: '/camera', params: { mode: 'ARITHMETIC' } })}
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.large,
    flexGrow: 1,
    maxWidth: 500,
    width: '100%',
    alignSelf: 'center',
  },
  feedbackTitle: {
    fontSize: 22,
    fontFamily: FONTS.extraBold,
    color: COLORS.primaryDark,
    marginBottom: 4,
    textAlign: 'center',
  },
  feedbackSubtitle: {
    fontFamily: FONTS.regular,
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SIZES.large,
  },
  expressionContainer: {
    alignItems: 'center',
    marginBottom: SIZES.large,
  },
  spacer: {
    flex: 1,
    minHeight: SIZES.large,
  },
  actions: {
    paddingBottom: SIZES.medium,
  },
});
