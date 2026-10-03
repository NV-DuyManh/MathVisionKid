import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { FONTS, COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { RecognizedExercise } from '../../types';

interface MathExpressionProps {
  exercise: RecognizedExercise;
  highlightIndex?: number;
}

export const MathExpression: React.FC<MathExpressionProps> = ({ exercise, highlightIndex }) => {
  const parsed = exercise.expression?.match(/^\s*(\d+)\s*([+-])\s*(\d+)\s*=\s*(\d+)\s*$/);
  const value = (token: { value: string } | string | undefined) => typeof token === 'string' ? token : token?.value || '';
  const op1 = value(exercise.operands?.[0]) || parsed?.[1] || '';
  const op2 = value(exercise.operands?.[1]) || parsed?.[3] || '';
  const operator = exercise.operator || parsed?.[2] || '';
  const resultText = typeof exercise.observedResult === 'string' ? exercise.observedResult : exercise.observedResult?.map(value).join('') || parsed?.[4] || '';
  const resultDigits = resultText.split('');
  if (!op1 || !op2 || !operator || !resultText) return exercise.expression ? <Text style={styles.expression}>{exercise.expression}</Text> : null;

  return (
    <View
      style={[styles.container, SHADOWS.small]}
      accessible
      accessibilityLabel={`Phép tính: ${op1} ${operator} ${op2} bằng ${resultDigits.join('')}`}
    >
      <Text style={styles.digitRow}>{op1}</Text>
      
      <View style={styles.operatorRow}>
        <Text style={styles.operator}>{operator}</Text>
        <Text style={styles.digitRow}>{op2}</Text>
      </View>
      
      <View style={styles.divider} />
      
      <View style={styles.resultRow}>
        {resultDigits.map((digit, idx) => {
          // Validator columns start with units at the right edge.
          const isError = highlightIndex !== undefined && resultDigits.length - 1 - idx === highlightIndex;
          return (
            <View key={idx} style={[styles.digitBox, isError && styles.errorDigitBox]}>
              <Text style={[styles.digit, isError && styles.errorDigitText]}>
                {digit}
              </Text>
              {isError && <View style={styles.errorIndicator} />}
            </View>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  expression: { fontFamily: FONTS.bold, fontSize: 24, color: COLORS.textPrimary, textAlign: 'center' },
  container: {
    alignItems: 'flex-end',
    paddingVertical: SIZES.large,
    paddingHorizontal: SIZES.xxlarge,
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.cardRadius,
    borderWidth: 1,
    borderColor: COLORS.border,
    minWidth: 200,
  },
  operatorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  digitRow: {
    fontSize: 44,
    fontFamily: FONTS.bold,
    color: COLORS.textPrimary,
    letterSpacing: 6,
    fontVariant: ['tabular-nums'],
  },
  operator: {
    fontSize: 36,
    fontFamily: FONTS.bold,
    color: COLORS.primaryDark,
    marginRight: 16,
  },
  divider: {
    height: 3,
    backgroundColor: COLORS.textPrimary,
    width: '100%',
    marginVertical: SIZES.small,
    borderRadius: 2,
  },
  resultRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  digitBox: {
    alignItems: 'center',
    paddingHorizontal: 2,
    position: 'relative',
  },
  errorDigitBox: {
    backgroundColor: '#FEE2E2',
    borderRadius: 8,
    paddingHorizontal: 6,
    borderWidth: 1.5,
    borderColor: '#FCA5A5',
  },
  digit: {
    fontSize: 44,
    fontFamily: FONTS.extraBold,
    color: COLORS.textPrimary,
    fontVariant: ['tabular-nums'],
  },
  errorDigitText: {
    color: COLORS.error,
  },
  errorIndicator: {
    width: '100%',
    height: 3,
    backgroundColor: COLORS.error,
    borderRadius: 2,
    marginTop: 2,
  },
});
