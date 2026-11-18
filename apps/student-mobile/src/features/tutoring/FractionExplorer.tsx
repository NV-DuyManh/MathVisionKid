import React, { useId, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { KeyDownEvent } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { FractionShape, FractionShapeKind } from './FractionShape';
import type { SourceFraction } from './hintVisualModel';

export { fractionsInProblem } from './hintVisualModel';
const SHAPES: { kind: FractionShapeKind; label: string; shortLabel: string }[] = [
  { kind: 'bar', label: 'Thanh phân số', shortLabel: 'Thanh' },
  { kind: 'circle', label: 'Hình tròn', shortLabel: 'Tròn' },
  { kind: 'square', label: 'Hình vuông', shortLabel: 'Vuông' },
];

export function GivenFractionExplorer({ fractions }: { fractions: SourceFraction[] }) {
  const [index, setIndex] = useState(0);
  const [focused, setFocused] = useState<number | null>(null);
  const fraction = fractions[index];
  if (!fraction) return null;
  return <View testID="given-fraction-visuals" style={styles.source}>
    {fractions.length > 1 ? <View style={styles.sourceOptions}>
      <Text style={styles.label}>Chọn phân số trong đề</Text>
      <View style={styles.actions}>
        {fractions.map(({ numerator, denominator }, i) => <Pressable key={`${numerator}/${denominator}`}
          accessibilityRole="button" accessibilityLabel={`Xem phân số ${numerator} phần ${denominator}`}
          aria-pressed={index === i} accessibilityState={{ selected: index === i }} focusable
          onPress={() => setIndex(i)} onFocus={() => setFocused(i)} onBlur={() => setFocused(null)}
          style={({ pressed }) => [styles.sourceOption, index === i && styles.shapeSelected,
            focused === i && styles.focused, pressed && styles.pressed]}>
          <MathText style={styles.sourceNumber}>{`${numerator}/${denominator}`}</MathText>
          {index === i ? <Ionicons name="checkmark-circle" size={16} color={COLORS.primaryDark} accessible={false} aria-hidden /> : null}
        </Pressable>)}
      </View>
    </View> : null}
    <FractionExplorer {...fraction} />
  </View>;
}

export function FractionExplorer({ numerator, denominator }: SourceFraction) {
  const supported = Number.isSafeInteger(numerator) && Number.isSafeInteger(denominator)
    && numerator >= 0 && denominator >= 1 && denominator <= 20 && numerator <= denominator * 3;
  if (!supported) return <View style={styles.card}>
    <Text style={styles.body}>Phân số này chưa có hình tương tác phù hợp. Em dùng cách biểu diễn khác cùng thầy cô nhé.</Text>
  </View>;
  // A new given fraction starts a fresh exploration, including after invalid input.
  return <FractionParts key={`${numerator}/${denominator}`} numerator={numerator} denominator={denominator} />;
}

function FractionParts({ numerator, denominator }: SourceFraction) {
  const [shape, setShape] = useState<FractionShapeKind>('bar');
  const [selected, setSelected] = useState<number[]>([]);
  const [feedback, setFeedback] = useState('');
  const [showExplanation, setShowExplanation] = useState(false);
  const explanationId = useId();
  const [focused, setFocused] = useState<number | FractionShapeKind | 'check' | 'reset' | 'explanation' | null>(null);
  const { width, fontScale } = useWindowDimensions();
  const wholes = Math.max(1, Math.ceil(numerator / denominator));
  const directBar = shape === 'bar' && denominator <= (fontScale > 1.35 || width < 320 ? 3 : width < 390 ? 4 : 5);
  const toggle = (index: number) => {
    setSelected(current => current.includes(index) ? current.filter(value => value !== index) : [...current, index]);
    setFeedback('');
  };
  const checkSelection = () => {
    const count = selected.length;
    const reason = denominator === 1
      ? 'Mẫu số vẫn là 1 vì mỗi phần là trọn một hình nguyên.'
      : `Mẫu số vẫn là ${denominator} vì mỗi hình nguyên vẫn chia thành ${denominator} phần bằng nhau.`;
    if (count === numerator) {
      const match = count === 0
        ? 'Em chưa chọn phần nào, đúng với tử số 0.'
        : `Em đã chọn ${count} phần, đúng với tử số ${numerator}.`;
      setFeedback(`Đúng rồi, số phần em chọn biểu diễn phân số đã cho. ${match} ${reason}`);
    } else {
      const action = count < numerator
        ? `Em chọn thêm ${numerator - count} phần nhé.`
        : `Em bỏ chọn ${count - numerator} phần nhé.`;
      setFeedback(`Số phần em chọn chưa khớp với phân số đã cho. Em đã chọn ${count} phần và cần ${numerator} phần theo tử số. ${action} ${reason}`);
    }
  };

  return <View style={styles.card}>
    <View style={styles.target}>
      <View style={styles.fractionBadge}>
        <MathText style={styles.fractionNumber}>{`${numerator}/${denominator}`}</MathText>
      </View>
      <View style={styles.targetCopy}>
        <Text style={styles.title}>{numerator === 0 ? 'Để trống các phần' : `Tô màu ${numerator} phần`}</Text>
        <Text style={styles.body}>{denominator === 1
          ? 'Mỗi hình nguyên là 1 phần.'
          : `Mỗi hình chia thành ${denominator} phần bằng nhau.`}</Text>
      </View>
    </View>
    <View style={styles.stage}>
      <View style={styles.diagramHeader}>
        <Text style={styles.label}>Chạm vào phần muốn tô</Text>
        <View accessibilityLiveRegion="polite">
          <MathText style={styles.counter}>{`Em đã chọn: ${selected.length}/${denominator}.`}</MathText>
        </View>
      </View>
      {Array.from({ length: wholes }, (_, whole) => <View key={whole} style={styles.whole}>
        {wholes > 1 ? <Text style={styles.body}>{`Hình ${whole + 1}`}</Text> : null}
        {directBar ? null : <FractionShape shape={shape} denominator={denominator} whole={whole} selected={selected} onToggle={toggle} />}
        <View style={directBar ? styles.bar : styles.pieces}>
          {Array.from({ length: denominator }, (_, part) => {
            const index = whole * denominator + part;
            const checked = selected.includes(index);
            // React Native Web handles Enter for Pressable; checkbox Space needs its own handler.
            const webKeys = Platform.OS === 'web' ? { onKeyDown: (event: React.KeyboardEvent | KeyDownEvent) => {
              const keyboard = 'key' in event ? event : event.nativeEvent;
              if (keyboard.key === ' ' || keyboard.key === 'Spacebar') {
                event.preventDefault();
                if (!keyboard.repeat) toggle(index);
              }
            } } : {};
            return <Pressable key={part} {...webKeys} accessibilityRole="checkbox" focusable
              accessibilityLabel={`Phần ${part + 1} trong ${denominator} phần bằng nhau của hình nguyên ${whole + 1}`}
              accessibilityHint="Tô màu hoặc bỏ màu phần này" aria-checked={checked} accessibilityState={{ checked }}
              onPress={() => toggle(index)} onFocus={() => setFocused(index)} onBlur={() => setFocused(null)}
              style={({ pressed }) => [styles.piece, directBar && styles.segment,
                directBar && part > 0 && styles.separator, checked && styles.selected,
                focused === index && styles.focused, pressed && styles.pressed]}>
              <Text accessible={false} style={[styles.pieceText, checked && styles.selectedText]}>{checked ? '✓' : part + 1}</Text>
            </Pressable>;
          })}
        </View>
      </View>)}
      <View style={styles.actions}>
        <Pressable accessibilityRole="button" accessibilityLabel="Kiểm tra phần em chọn" focusable
          onFocus={() => setFocused('check')} onBlur={() => setFocused(null)} onPress={checkSelection}
          style={({ pressed }) => [styles.button, styles.check, focused === 'check' && styles.focused, pressed && styles.pressed]}>
          <Text style={styles.checkText}>Kiểm tra</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Chọn lại từ đầu" focusable
          onFocus={() => setFocused('reset')} onBlur={() => setFocused(null)}
          onPress={() => { setSelected([]); setFeedback(''); }}
          style={({ pressed }) => [styles.button, focused === 'reset' && styles.focused, pressed && styles.pressed]}>
          <Text style={styles.label}>Tô lại</Text>
        </Pressable>
      </View>
      {feedback ? <Text accessibilityLiveRegion="polite" style={[styles.feedback, selected.length === numerator ? styles.correct : styles.retry]}>
        {feedback}
      </Text> : null}
    </View>
    <View style={styles.shapeOptions}>
      <Text style={styles.body}>Đổi hình</Text>
      <View style={styles.actions}>
        {SHAPES.map(option => <Pressable key={option.kind} accessibilityRole="button" focusable
          accessibilityLabel={option.label} aria-pressed={shape === option.kind}
          accessibilityState={Platform.OS === 'web' ? undefined : { selected: shape === option.kind }}
          onPress={() => setShape(option.kind)} onFocus={() => setFocused(option.kind)} onBlur={() => setFocused(null)}
          style={({ pressed }) => [styles.button, styles.shapeButton, shape === option.kind && styles.shapeSelected,
            focused === option.kind && styles.focused, pressed && styles.pressed]}>
          <Text style={styles.label}>{`${shape === option.kind ? '✓ ' : ''}${option.shortLabel}`}</Text>
        </Pressable>)}
      </View>
    </View>
    <Pressable accessibilityRole="button" accessibilityLabel="Vì sao mỗi phần bằng nhau?" focusable
      aria-expanded={showExplanation} aria-controls={Platform.OS === 'web' ? explanationId : undefined}
      accessibilityState={{ expanded: showExplanation }} onPress={() => setShowExplanation(current => !current)}
      onFocus={() => setFocused('explanation')} onBlur={() => setFocused(null)}
      style={({ pressed }) => [styles.button, styles.learn, focused === 'explanation' && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.learnText}>Vì sao mỗi phần bằng nhau?</Text>
      <Ionicons name={showExplanation ? 'chevron-up' : 'chevron-down'} size={16} color={COLORS.primaryDark} accessible={false} aria-hidden />
    </Pressable>
    {showExplanation ? <View nativeID={explanationId} style={styles.explanation}>
      <Text style={styles.body}>{denominator === 1
        ? 'Mẫu số 1 nghĩa là mỗi hình nguyên là 1 phần. Chọn một phần là chọn trọn một hình nguyên.'
        : `Chia đều một hình nguyên thành ${denominator} phần. Mỗi phần có diện tích bằng nhau.`}</Text>
      {wholes > 1 ? <Text style={styles.body}>Các hình nguyên bằng nhau, nên em đếm các phần được chọn ở tất cả các hình.</Text> : null}
      <Text style={styles.body}>{`Chọn hay bỏ chọn chỉ đổi số phần được chọn; mỗi hình vẫn có ${denominator} phần nên mẫu số không đổi.`}</Text>
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  source: { gap: 14 },
  sourceOptions: { gap: 6 },
  sourceOption: { minHeight: SIZES.minTouchTarget, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 16, gap: 6, borderWidth: 2, borderColor: COLORS.border, borderRadius: 14, backgroundColor: COLORS.surface },
  sourceNumber: { color: COLORS.primaryDark, fontSize: 16, fontFamily: FONTS.extraBold },
  card: { gap: 10 },
  target: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 12, borderRadius: 18,
    padding: 12, backgroundColor: COLORS.surfaceSubdued },
  fractionBadge: { minWidth: 64, minHeight: 62, borderRadius: 13, paddingHorizontal: 10, paddingVertical: 5,
    alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surface },
  fractionNumber: { color: COLORS.primaryDark, fontSize: 27, fontFamily: FONTS.extraBold },
  targetCopy: { flex: 1, minWidth: 124, gap: 3 },
  title: { color: COLORS.textPrimary, fontSize: 20, lineHeight: 26, fontFamily: FONTS.extraBold },
  label: { color: COLORS.textPrimary, fontSize: 14, lineHeight: 20, fontFamily: FONTS.bold },
  body: { color: COLORS.textSecondary, fontSize: 14, lineHeight: 20, fontFamily: FONTS.regular },
  stage: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 18, backgroundColor: '#FAF8FE', padding: 12, gap: 10 },
  diagramHeader: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 6 },
  counter: { fontSize: 14, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  whole: { gap: 6 },
  bar: { flexDirection: 'row', borderWidth: 2, borderColor: COLORS.primaryDark, borderRadius: 13, overflow: 'hidden' },
  pieces: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 5 },
  piece: { minWidth: SIZES.minTouchTarget, minHeight: SIZES.minTouchTarget, maxWidth: '100%', paddingHorizontal: 6, paddingVertical: 8,
    borderWidth: 2, borderColor: '#D5C7F2', backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center', borderRadius: 10 },
  segment: { flex: 1, minHeight: 62, borderWidth: 2, borderColor: 'transparent', borderRadius: 0, backgroundColor: COLORS.surface },
  separator: { borderLeftColor: '#B9A5EB' },
  selected: { backgroundColor: COLORS.primaryDark },
  shapeSelected: { backgroundColor: COLORS.surfaceSubdued, borderColor: COLORS.primaryDark },
  pieceText: { fontSize: 19, color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  selectedText: { color: COLORS.surface },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  pressed: { opacity: 0.72 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 6 },
  button: { minHeight: SIZES.minTouchTarget, maxWidth: '100%', borderWidth: 2, borderColor: COLORS.border,
    backgroundColor: COLORS.surface, borderRadius: 13, paddingVertical: 8, paddingHorizontal: 12, alignItems: 'center', justifyContent: 'center' },
  check: { flexGrow: 1, backgroundColor: COLORS.primaryDark, borderColor: COLORS.primaryDark },
  checkText: { color: COLORS.surface, fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold, textAlign: 'center' },
  shapeOptions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 6 },
  shapeButton: { paddingHorizontal: 10 },
  learn: { justifyContent: 'space-between', flexDirection: 'row', gap: 6, borderColor: 'transparent' },
  learnText: { color: COLORS.primaryDark, fontSize: 14, lineHeight: 20, fontFamily: FONTS.bold, flexShrink: 1 },
  explanation: { backgroundColor: COLORS.surfaceSubdued, borderRadius: 12, padding: 10, gap: 5 },
  feedback: { color: COLORS.textPrimary, fontSize: 13, lineHeight: 19, fontFamily: FONTS.bold, borderRadius: 10, padding: 8 },
  correct: { backgroundColor: COLORS.successLight },
  retry: { backgroundColor: COLORS.warningLight },
});
