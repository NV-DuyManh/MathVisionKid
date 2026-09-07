import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { HintCard } from '../../components/domain/HintCard';
import { MathExpression } from '../../components/domain/MathExpression';
import { SubmissionResult } from '../../types';

export default function ErrorHintScreen() {
  const router = useRouter();
  const { data } = useLocalSearchParams<{ data: string }>();
  
  let result: Partial<SubmissionResult> = {
    studentFeedback: {
      title: 'Hãy xem lại hàng chục',
      hint: 'Em nhớ kiểm tra số nhớ từ hàng đơn vị trước khi cộng các số ở hàng chục nhé.',
      revealAnswer: false,
    },
    recognizedExercise: {
      operator: '+',
      operands: [{ value: '458' }, { value: '276' }],
      observedResult: [{ value: '724' }],
    },
    validation: {
      decision: 'INVALID' as any,
      firstInvalidIndex: 1,
    }
  };

  try {
    if (data) result = JSON.parse(data);
  } catch {
    // handled
  }

  return (
    <View style={styles.container}>
      <AppHeader title="Kết quả" showBack />
      
      <View style={styles.content}>
        <Text style={styles.title}>{result.studentFeedback?.title}</Text>

        <View style={styles.expressionContainer}>
          {result.recognizedExercise && (
            <MathExpression 
              exercise={result.recognizedExercise} 
              highlightIndex={result.validation?.firstInvalidIndex} 
            />
          )}
        </View>

        <HintCard hint={result.studentFeedback?.hint || ''} />

        <View style={styles.spacer} />

        <AppButton 
          title="Em sửa lại" 
          onPress={() => router.replace('/(tabs)')} 
        />
        <View style={{ height: SIZES.medium }} />
        <AppButton 
          title="Chụp lại bài" 
          variant="secondary"
          onPress={() => router.replace('/camera')} 
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    padding: SIZES.medium,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: SIZES.large,
    textAlign: 'center',
  },
  expressionContainer: {
    alignItems: 'center',
    marginBottom: SIZES.xlarge,
  },
  spacer: {
    flex: 1,
  }
});
