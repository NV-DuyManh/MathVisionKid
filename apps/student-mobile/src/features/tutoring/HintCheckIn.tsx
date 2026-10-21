import React, { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS, FONTS } from '../../constants/theme';

/** A small concept check, never a replacement for the server's lesson grading. */
function concept(expression: string, reading: boolean, depth: number) {
  if (reading) return {
    question: 'Ở bước hiểu đề, em cần làm gì?', correct: 'Tìm điều đã biết và điều cần tìm',
    other: 'Tính đáp số ngay', why: 'Đọc đúng dữ kiện và câu hỏi giúp em chọn cách giải phù hợp. Chưa cần tính ở bước này.',
  };
  if (/\d\s*\/\s*\d/.test(expression)) return depth > 1 ? {
    question: 'Tử số cho biết điều gì?', correct: 'Số phần bằng nhau được lấy',
    other: 'Số hình có trong bài', why: 'Tử số đếm số phần được lấy. Mỗi phần có kích thước do mẫu số quy định.',
  } : {
    question: 'Mẫu số cho biết điều gì?', correct: 'Số phần bằng nhau của một hình nguyên',
    other: 'Số phần đã được chọn', why: 'Mẫu số cho biết hình nguyên được chia thành bao nhiêu phần bằng nhau.',
  };
  // A leading sign belongs to a number; teach only an operation between operands.
  const symbol = expression.match(/[\d)]\s*([+×*÷:−-])\s*(?=[(\d])/)?.[1];
  const names: Record<string, [string, string]> = {
    '+': ['Phép cộng', 'Phép trừ'], '×': ['Phép nhân', 'Phép chia'], '*': ['Phép nhân', 'Phép chia'],
    '÷': ['Phép chia', 'Phép nhân'], ':': ['Phép chia', 'Phép nhân'], '−': ['Phép trừ', 'Phép cộng'], '-': ['Phép trừ', 'Phép cộng'],
  };
  if (symbol && names[symbol]) return { question: `Dấu ${symbol} có nghĩa gì?`, correct: names[symbol][0], other: names[symbol][1], why: `Dấu ${symbol} chỉ ${names[symbol][0].toLowerCase()}.` };
  return { question: 'Khi xem gợi ý, em nên làm gì tiếp?', correct: 'Thử làm từng ý nhỏ', other: 'Chép đáp số ngay', why: 'Thử làm từng ý giúp em hiểu cách giải.' };
}

export function HintCheckIn({ expression, reading = false, depth = 1, disabled = false, onReady }: {
  expression: string; reading?: boolean; depth?: number; disabled?: boolean; onReady: () => void;
}) {
  const check = concept(expression, reading, depth);
  const [choice, setChoice] = useState('');
  const [focused, setFocused] = useState<string | null>(null);
  const correct = choice === check.correct;
  return <View style={styles.card}>
    <Text style={styles.title}>Em thử chọn nhé</Text>
    <Text style={styles.body}>{check.question}</Text>
    {(depth % 2 === 0 ? [check.correct, check.other] : [check.other, check.correct]).map(label => <Pressable key={label} accessibilityRole="button"
      accessibilityLabel={label} aria-pressed={choice === label}
      accessibilityState={Platform.OS === 'web' ? { disabled } : { selected: choice === label, disabled }} disabled={disabled}
      onPress={() => setChoice(label)} onFocus={() => setFocused(label)} onBlur={() => setFocused(null)}
      style={({ pressed }) => [styles.choice, choice === label && styles.selected, focused === label && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.body}>{label}</Text>
    </Pressable>)}
    {choice ? <Text accessibilityLiveRegion="polite" style={styles.body}>
      {correct ? `Đúng rồi. ${check.why} Em thử làm bước này nhé.` : `Em chọn lại nhé. ${check.why}`}
    </Text> : null}
    {correct && <Pressable accessibilityRole="button" accessibilityLabel="Em đã hiểu, để em thử" disabled={disabled}
      accessibilityState={{ disabled }}
      onFocus={() => setFocused('ready')} onBlur={() => setFocused(null)} onPress={onReady}
      style={({ pressed }) => [styles.choice, focused === 'ready' && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.title}>Em đã hiểu, để em thử</Text>
    </Pressable>}
  </View>;
}

const styles = StyleSheet.create({
  card: { gap: 10, marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#D9CFF2' },
  title: { fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.primaryDark },
  body: { fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, color: COLORS.textPrimary },
  choice: { minHeight: 48, padding: 12, borderRadius: 14, borderWidth: 1, borderColor: '#BFB0DC', backgroundColor: COLORS.surface },
  selected: { borderColor: COLORS.primaryDark, borderWidth: 2, backgroundColor: '#EEE7FF' },
  focused: { borderStyle: 'dashed', borderWidth: 2, borderColor: COLORS.textPrimary }, pressed: { opacity: .75 },
});
