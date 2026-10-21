import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SIZES } from '../../constants/theme';
import { StudentResultShell } from '../../components/ui/StudentResultShell';
import { AppButton } from '../../components/ui/AppButton';
import { StatusCard } from '../../components/domain/StatusCard';
import { MathExpression } from '../../components/domain/MathExpression';
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
    const destination = result ? resolveResultRoute(result) : null;
    if (destination && destination.pathname !== '/results/correct') router.replace(destination as any);
  }, [result, router]);

  useEffect(() => {
    logFlowDomain('RESULT', 'ARITHMETIC');
  }, []);

  return (
    <StudentResultShell title="Kết quả bài làm" success={target?.pathname === '/results/correct'}>
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
      </StudentResultShell>
  );
}

const styles = StyleSheet.create({
  expressionContainer: {
    marginTop: SIZES.medium,
    marginBottom: SIZES.large,
    alignItems: 'center',
  },
  actions: {
    paddingBottom: SIZES.medium,
  },
});
