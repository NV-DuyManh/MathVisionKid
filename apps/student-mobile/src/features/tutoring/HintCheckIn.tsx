import React, { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';
import { MathText } from '../../components/domain/MathText';

type Check = { question: string; correct: string; other: string; why: string };
type HintContext = { expression: string; reading?: boolean; hint?: string; stepTitle?: string; stepQuestion?: string; unit?: string };
const plain = (value: string) => value.normalize('NFD').toLowerCase().replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/[‐‑–—-]/g, ' ');

/** A check of the current hint, not a second grading path or a guessed new exercise. */
export function hintConcept({ expression, reading = false, hint = '', stepTitle = '', stepQuestion = '', unit = '' }: HintContext): Check | null {
  const help = plain(hint), context = plain(`${hint} ${stepTitle} ${stepQuestion} ${unit}`);
  const symbol = expression.match(/[\d)]\s*([+×*÷:−-])\s*(?=[(\d])/)?.[1];
  const division = /^\s*\(?[+−-]?\d+(?:[.,]\d+)?\)?\s*[/÷:]\s*\(?[+−-]?\d+(?:[.,]\d+)?\)?\s*(?:=\s*\?)?\s*$/.test(expression);
  if (division && /rut gon|chia (?:ca )?(?:tu|tu so) va (?:mau|mau so)|ca hai so.*chia/.test(help) && /chia|thuong|tu.*mau/.test(help)) return {
    question: `Khi rút gọn ${expression || 'phép chia này'}, em cần chia những số nào cho cùng một số khác 0?`,
    correct: 'Cả số bị chia và số chia', other: 'Chỉ số bị chia',
    why: 'Chia cả số bị chia và số chia cho cùng một số khác 0 thì thương không thay đổi.',
  };
  if (/doi|cung don vi/.test(help) && /dien tich/.test(context)) return {
    question: 'Trước khi so sánh hai diện tích, em cần làm gì?', correct: 'Đưa hai diện tích về cùng đơn vị',
    other: 'Giữ mỗi diện tích một đơn vị', why: 'Hai diện tích cần cùng đơn vị đo thì em mới so sánh hoặc chia chúng cho nhau.',
  };
  if (/gach|lat nen|lat kin/.test(context) && /dien tich/.test(help) && /chia/.test(help)) return {
    question: 'Để tìm số viên gạch, em lấy gì chia cho gì?', correct: 'Diện tích nền nhà chia diện tích một viên gạch',
    other: 'Diện tích một viên gạch chia diện tích nền nhà', why: 'Mỗi viên che một phần nền nhà. Chia diện tích nền cho diện tích một viên, cùng đơn vị, sẽ ra số viên.',
  };
  if (/dien tich/.test(context) && /chieu dai/.test(help) && /chieu rong/.test(help) && /nhan/.test(help)) return {
    question: 'Diện tích hình chữ nhật được tính thế nào?', correct: 'Chiều dài nhân chiều rộng, cùng đơn vị đo',
    other: 'Chiều dài cộng chiều rộng', why: 'Diện tích hình chữ nhật bằng chiều dài nhân chiều rộng. Hai chiều phải dùng cùng đơn vị đo.',
  };
  if (reading) {
    if (/can tim|de hoi|cau hoi/.test(help)) return {
      question: 'Phần gợi ý này giúp em xác định điều gì?', correct: 'Điều đề bài yêu cầu tìm', other: 'Đáp số để chép ngay',
      why: 'Xác định đúng điều cần tìm giúp em chọn cách giải. Bước này chưa yêu cầu tính đáp số.',
    };
    if (/du kien|da biet|cho biet/.test(help)) return {
      question: 'Khi tìm dữ kiện, em cần đối chiếu với đâu?', correct: 'Những thông tin đề bài đã cho', other: 'Một con số tự đoán',
      why: 'Dữ kiện phải lấy từ đúng đề bài, gồm số, đơn vị và mối liên hệ đã cho.',
    };
    return null;
  }
  if (symbol === '+' && /gop.*nhom|them.*nhom|ca hai nhom/.test(help)) return {
    question: 'Dấu + có nghĩa gì?', correct: 'Gộp các nhóm lại', other: 'Bớt một nhóm đi',
    why: 'Phép cộng gộp số lượng của các nhóm để tìm tất cả có bao nhiêu.',
  };
  if ((symbol === '−' || symbol === '-') && /bot|lay di|con lai/.test(help)) return {
    question: `Dấu ${symbol} có nghĩa gì?`, correct: 'Bớt một phần để tìm phần còn lại', other: 'Gộp thêm một nhóm vào',
    why: 'Phép trừ lấy số lượng ban đầu bớt đi phần đã cho, để tìm phần còn lại.',
  };
  if (/tu so/.test(help) && /cho biet|dem|so phan/.test(help)) return {
    question: 'Tử số cho biết điều gì?', correct: 'Số phần bằng nhau được lấy',
    other: 'Số hình có trong bài', why: 'Tử số đếm số phần được lấy. Mỗi phần có kích thước do mẫu số quy định.',
  };
  if (/mau so/.test(help) && /cho biet|chia.*phan|phan bang nhau/.test(help)) return {
    question: 'Mẫu số cho biết điều gì?', correct: 'Số phần bằng nhau của một hình nguyên',
    other: 'Số phần đã được chọn', why: 'Mẫu số cho biết hình nguyên được chia thành bao nhiêu phần bằng nhau.',
  };
  if (/quy dong|cung mau|khac mau/.test(help) && /phan so|mau/.test(context)) return {
    question: 'Trước khi cộng hoặc trừ hai phân số khác mẫu, em cần làm gì?', correct: 'Quy đồng để có cùng mẫu số',
    other: 'Cộng hoặc trừ cả tử và mẫu', why: 'Quy đồng giúp hai phân số cùng biểu diễn những phần có kích thước bằng nhau.',
  };
  // A slash alone can be a division (675000/900), not a numerator lesson.
  // If the hint has no recognised concept, do not add an unrelated quiz to it.
  if (hint.trim()) return null;
  // A leading sign belongs to a number; teach only an operation between operands.
  const names: Record<string, [string, string]> = {
    '+': ['Phép cộng', 'Phép trừ'], '×': ['Phép nhân', 'Phép chia'], '*': ['Phép nhân', 'Phép chia'],
    '÷': ['Phép chia', 'Phép nhân'], ':': ['Phép chia', 'Phép nhân'], '−': ['Phép trừ', 'Phép cộng'], '-': ['Phép trừ', 'Phép cộng'],
  };
  if (symbol && names[symbol]) return { question: `Dấu ${symbol} có nghĩa gì?`, correct: names[symbol][0], other: names[symbol][1], why: `Dấu ${symbol} chỉ ${names[symbol][0].toLowerCase()}.` };
  return null;
}

export function HintCheckIn(props: HintContext & { depth?: number; disabled?: boolean; onReady: () => void }) {
  // Remount only this small interaction when context changes; no stale choice from the previous hint.
  return <CheckIn key={JSON.stringify([props.expression, props.reading, props.hint, props.stepTitle, props.stepQuestion, props.unit])} {...props} />;
}

function CheckIn({ depth = 1, disabled = false, onReady, ...context }: HintContext & { depth?: number; disabled?: boolean; onReady: () => void }) {
  const check = hintConcept(context);
  const [choice, setChoice] = useState('');
  const [focused, setFocused] = useState<string | null>(null);
  const correct = !!check && choice === check.correct;
  return <View style={styles.card}>
    {check ? <><Text style={styles.title}>Kiểm tra cách hiểu</Text>
    <MathText style={styles.body}>{check.question}</MathText>
    {(depth % 2 === 0 ? [check.correct, check.other] : [check.other, check.correct]).map(label => {
      const selected = choice === label, right = selected && correct, wrong = selected && !correct;
      return <Pressable key={label} accessibilityRole="button"
      accessibilityLabel={label} aria-pressed={choice === label}
      accessibilityHint={right ? 'Em đã chọn đúng. Bấm Em đã hiểu để quay lại bước học.' : wrong ? 'Em đã chọn đáp án này, chưa đúng. Em có thể chọn lại.' : undefined}
      accessibilityState={Platform.OS === 'web' ? { disabled: disabled || correct } : { selected, disabled: disabled || correct }} disabled={disabled || correct}
      onPress={() => { if (!disabled && !correct) setChoice(label); }} onFocus={() => setFocused(label)} onBlur={() => setFocused(null)}
      style={({ pressed }) => [styles.choice, right && styles.rightChoice, wrong && styles.wrongChoice, focused === label && styles.focused, pressed && styles.pressed]}>
      <Ionicons name={right ? 'checkmark-circle' : wrong ? 'close-circle' : 'ellipse-outline'} size={22} color={right ? '#23734D' : wrong ? '#B23D39' : '#988AAE'} accessible={false} />
      <View style={styles.choiceCopy}><Text style={styles.body}>{label}</Text>{selected ? <Text style={[styles.state, right ? styles.rightText : styles.wrongText]}>{right ? 'Đã chọn · Đúng' : 'Đã chọn · Chưa đúng'}</Text> : null}</View>
    </Pressable>})}
    {choice ? <View accessibilityLiveRegion="polite" style={[styles.feedback, correct ? styles.rightChoice : styles.wrongChoice]}>
      <Text style={[styles.feedbackTitle, correct ? styles.rightText : styles.wrongText]}>{correct ? 'Đúng rồi!' : 'Chưa đúng, em thử chọn lại nhé'}</Text>
      <Text style={styles.detail}>{check.why}</Text>
    </View> : null}</> : <Text style={styles.detail}>Em xem lại gợi ý rồi thử tiếp bước đang làm nhé.</Text>}
    {(!check || correct) && <Pressable accessibilityRole="button" accessibilityLabel="Em đã hiểu, để em thử" disabled={disabled}
      accessibilityState={{ disabled }}
      onFocus={() => setFocused('ready')} onBlur={() => setFocused(null)} onPress={onReady}
      style={({ pressed }) => [styles.ready, focused === 'ready' && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.readyText}>Em đã hiểu, để em thử</Text><Ionicons name="arrow-forward" size={18} color="#FFF" accessible={false} />
    </Pressable>}
  </View>;
}

const styles = StyleSheet.create({
  card: { gap: 10, marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#D9CFF2' },
  title: { fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.primaryDark },
  body: { fontFamily: FONTS.semiBold, fontSize: 15, lineHeight: 23, color: COLORS.textPrimary },
  detail: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  choice: { minHeight: 52, padding: 12, gap: 10, flexDirection: 'row', alignItems: 'center', borderRadius: 14, borderWidth: 1, borderColor: '#D5CADF', backgroundColor: COLORS.surface },
  choiceCopy: { flex: 1, minWidth: 0, gap: 3 }, state: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 18 },
  rightChoice: { borderColor: '#75BC94', backgroundColor: '#EBF8F0' }, wrongChoice: { borderColor: '#DA9D97', backgroundColor: '#FFF2EF' },
  rightText: { color: '#23734D' }, wrongText: { color: '#A83C35' },
  feedback: { padding: 12, gap: 5, borderRadius: 14, borderWidth: 1 }, feedbackTitle: { fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 21 },
  ready: { minHeight: 48, padding: 12, gap: 8, borderRadius: 14, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.primaryDark },
  readyText: { fontFamily: FONTS.bold, fontSize: 15, lineHeight: 23, color: '#FFF', flexShrink: 1, textAlign: 'center' },
  focused: { borderStyle: 'dashed', borderWidth: 2, borderColor: COLORS.textPrimary }, pressed: { opacity: .75 },
});
