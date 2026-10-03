import React, { useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { MathExpression } from '../../components/domain/MathExpression';
import { SubmissionResult } from '../../types';
import { logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { useArithmeticResult } from '../../hooks/useArithmeticResult';
import { resolveResultRoute } from '../../utils/resultRouting';
import { RecognitionProgress } from '../../features/recognition/components/RecognitionProgress';

export default function CorrectScreen() {
  const router = useRouter();
  const { data, submissionId } = useLocalSearchParams<{ data?: string; submissionId?: string }>();
  const { result, loading } = useArithmeticResult(data, submissionId);
  const target = result ? resolveResultRoute(result) : null;

  useEffect(() => {
    if (target && target.pathname !== '/results/correct') router.replace(target as any);
  }, [result, router]);

  useEffect(() => {
    logFlowDomain('RESULT', 'ARITHMETIC');
  }, []);

  return (
    <View style={styles.container}>
      <AppHeader title="Kết quả bài làm" showBack />

      <ScrollView contentContainerStyle={styles.content}>
        {loading ? <RecognitionProgress title="Đang mở kết quả" description="Lấy lại kết quả bài làm của em." onCancel={() => router.back()} /> : target?.pathname === '/results/correct' && result ? <>
        <StatusCard
          status="success"
          title={result.studentFeedback?.title || 'Làm tốt lắm! 🎉'}
          subtitle={
            result.studentFeedback?.hint ||
            'MathVision chưa tìm thấy lỗi trong bài em vừa kiểm tra.'
          }
        />

        <View style={styles.expressionContainer}>
          {result.recognizedExercise && (
            <MathExpression exercise={result.recognizedExercise} />
          )}
        </View>
        </> : <StatusCard status="warning" title="Chưa có kết quả" subtitle="Chưa lấy được kết quả bài làm. Em hãy mở lại bài hoặc chụp ảnh mới nhé." />}

        <View style={styles.spacer} />

        <View style={styles.actions}>
          <AppButton
            title="Kiểm tra bài toán khác"
            onPress={() => router.replace({ pathname: '/camera', params: { mode: 'ARITHMETIC' } })}
            variant="primary"
          />
          <View style={{ height: SIZES.small }} />
          <AppButton
            title="Về trang chủ"
            variant="secondary"
            onPress={() => router.replace('/(tabs)')}
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
  expressionContainer: {
    marginTop: SIZES.medium,
    marginBottom: SIZES.large,
    alignItems: 'center',
  },
  spacer: {
    flex: 1,
    minHeight: SIZES.large,
  },
  actions: {
    paddingBottom: SIZES.medium,
  },
});
