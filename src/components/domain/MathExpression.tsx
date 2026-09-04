import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../constants/theme';
import { RecognizedExercise } from '../../types';

interface MathExpressionProps {
  exercise: RecognizedExercise;
  highlightIndex?: number;
}

export const MathExpression: React.FC<MathExpressionProps> = ({ exercise, highlightIndex }) => {
  const op1 = exercise.operands[0]?.value || '';
  const op2 = exercise.operands[1]?.value || '';
  const result = exercise.observedResult.map(t => t.value).join('');

  return (
    <View style={styles.container}>
      <Text style={styles.digit}>{op1}</Text>
      <View style={styles.row}>
        <Text style={styles.operator}>{exercise.operator}</Text>
        <Text style={styles.digit}>{op2}</Text>
      </View>
      <View style={styles.divider} />
      <Text style={[styles.digit, highlightIndex !== undefined && styles.errorDigit]}>{result}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'flex-end',
    padding: 24,
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  digit: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    letterSpacing: 8,
  },
  operator: {
    fontSize: 40,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginRight: 16,
  },
  divider: {
    height: 4,
    backgroundColor: COLORS.textPrimary,
    width: '100%',
    marginVertical: 12,
  },
  errorDigit: {
    color: COLORS.error,
  }
});
