import React, { useId, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import type { KeyDownEvent } from 'react-native';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { FractionShape, FractionShapeKind } from './FractionShape';

type SourceFraction = { numerator: number; denominator: number };
type Props = SourceFraction & { label?: string };

const SHAPES: { kind: FractionShapeKind; label: string }[] = [
  { kind: 'circle', label: 'Hình tròn' },
  { kind: 'square', label: 'Hình vuông' },
  { kind: 'bar', label: 'Thanh phân số' },
];

/** Read only literal source fractions; never calculate a result for the pupil. */
export function fractionsInProblem(text: string): SourceFraction[] {
  const fractions: SourceFraction[] = [];
  const pattern = /(?<![\p{L}\p{N}_/.,+\-−])(\d+)\s*\/\s*(\d+)(?![\p{L}\p{N}_/]|[.,]\d)/gu;
  for (const match of text.matchAll(pattern)) {
    const before = text.slice(0, match.index).trimEnd();
    const after = text.slice(match.index + match[0].length).trimStart();
    // Keep the existing signed-literal exclusion even when whitespace follows the sign.
    if (/[+\-−]$/u.test(before)) continue;
    // A slash chain is a date or another unsupported notation, not a fraction.
    if (before.endsWith('/') || after.startsWith('/')
      || /(?:ngày|date|dated)\s*[:=]?$/iu.test(before)) continue;
    const numerator = Number(match[1]);
    const denominator = Number(match[2]);
    if (!Number.isSafeInteger(numerator) || !Number.isSafeInteger(denominator) || denominator === 0) continue;
    if (fractions.some(value => value.numerator === numerator && value.denominator === denominator)) continue;
    fractions.push({ numerator, denominator });
    if (fractions.length === 2) break;
  }
  return fractions;
}

export function FractionExplorer({ numerator, denominator, label }: Props) {
  const supported = Number.isSafeInteger(numerator) && Number.isSafeInteger(denominator)
    && numerator >= 0 && denominator >= 1 && denominator <= 20 && numerator <= denominator * 3;
  if (!supported) return <View style={styles.card}>
    <Text style={styles.title}>Cùng nhìn phân số</Text>
    <Text style={styles.body}>Phân số này chưa có hình tương tác phù hợp. Em dùng cách biểu diễn khác cùng thầy cô nhé.</Text>
  </View>;
  // A new given fraction starts a fresh exploration, including after invalid input.
  return <FractionParts key={`${numerator}/${denominator}`} numerator={numerator} denominator={denominator} label={label} />;
}

function FractionParts({ numerator, denominator, label }: Props) {
  const [shape, setShape] = useState<FractionShapeKind>('circle');
  const [selected, setSelected] = useState<number[]>([]);
  const [feedback, setFeedback] = useState('');
  const [showExplanation, setShowExplanation] = useState(false);
  const explanationId = useId();
  const [focused, setFocused] = useState<number | FractionShapeKind | 'check' | 'reset' | 'explanation' | null>(null);
  const wholes = Math.max(1, Math.ceil(numerator / denominator));
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
    <Text style={styles.title}>Cùng nhìn phân số</Text>
    {label ? <Text style={styles.label}>{label}</Text> : null}
    <MathText style={styles.prompt}>{`Em chọn các phần để tạo ${numerator}/${denominator}.`}</MathText>
    <Text style={styles.body}>{denominator === 1
      ? `Mẫu số 1 cho biết mỗi hình nguyên là 1 phần. Tử số ${numerator} cho biết số hình nguyên cần chọn.`
      : `Mẫu số ${denominator} cho biết mỗi hình nguyên có ${denominator} phần bằng nhau. Tử số ${numerator} cho biết số phần cần chọn.`}</Text>
    <Text style={styles.body}>Chạm vào một phần của hình hoặc nút số bên dưới để chọn, bỏ chọn. Dấu ✓ cho biết phần đã chọn.</Text>
    <Pressable accessibilityRole="button" accessibilityLabel="Vì sao mỗi phần bằng nhau?" focusable
      aria-expanded={showExplanation} aria-controls={Platform.OS === 'web' ? explanationId : undefined}
      accessibilityState={{ expanded: showExplanation }} onPress={() => setShowExplanation(current => !current)}
      onFocus={() => setFocused('explanation')} onBlur={() => setFocused(null)}
      style={({ pressed }) => [styles.button, focused === 'explanation' && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.label}>{`${showExplanation ? '−' : '+'} Vì sao mỗi phần bằng nhau?`}</Text>
    </Pressable>
    {showExplanation ? <View nativeID={explanationId} style={styles.explanation}>
      <Text style={styles.body}>{denominator === 1
        ? 'Mẫu số 1 nghĩa là mỗi hình nguyên là 1 phần. Chọn một phần là chọn trọn một hình nguyên.'
        : `Chia đều một hình nguyên thành ${denominator} phần để mỗi phần có diện tích bằng nhau. Mỗi phần là một trong ${denominator} phần bằng nhau của hình nguyên.`}</Text>
      {wholes > 1 ? <Text style={styles.body}>Các hình nguyên bằng nhau, nên em đếm các phần được chọn ở tất cả các hình.</Text> : null}
      <Text style={styles.body}>{`Chọn hay bỏ chọn chỉ đổi số phần được chọn; cách chia mỗi hình nguyên không đổi nên mẫu số vẫn là ${denominator}.`}</Text>
    </View> : null}
    <Text style={styles.label}>Em muốn dùng hình nào?</Text>
    <View style={styles.actions}>
      {SHAPES.map(option => <Pressable key={option.kind} accessibilityRole="button" focusable
        accessibilityLabel={option.label} aria-pressed={shape === option.kind}
        accessibilityState={Platform.OS === 'web' ? undefined : { selected: shape === option.kind }}
        onPress={() => setShape(option.kind)} onFocus={() => setFocused(option.kind)} onBlur={() => setFocused(null)}
        style={({ pressed }) => [styles.button, shape === option.kind && styles.shapeSelected,
          focused === option.kind && styles.focused, pressed && styles.pressed]}>
        <Text style={styles.label}>{`${shape === option.kind ? '✓ ' : ''}${option.label}`}</Text>
      </Pressable>)}
    </View>
    <View style={styles.wholes}>
      {Array.from({ length: wholes }, (_, whole) => <View key={whole} style={styles.whole}>
        <Text style={styles.label}>{`Hình nguyên ${whole + 1} · ${denominator} phần bằng nhau`}</Text>
        <FractionShape shape={shape} denominator={denominator} whole={whole} selected={selected} onToggle={toggle} />
        <Text style={styles.body}>Chọn từng phần theo số:</Text>
        <View style={styles.pieces}>
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
              accessibilityHint="Chọn hoặc bỏ chọn phần này" aria-checked={checked} accessibilityState={{ checked }}
              onPress={() => toggle(index)} onFocus={() => setFocused(index)} onBlur={() => setFocused(null)}
              style={({ pressed }) => [styles.piece, checked && styles.selected,
                focused === index && styles.focused, pressed && styles.pressed]}>
              <Text accessible={false} style={[styles.pieceText, checked && styles.selectedText]}>{`${part + 1}${checked ? '✓' : ''}`}</Text>
            </Pressable>;
          })}
        </View>
      </View>)}
    </View>
    <View accessibilityLiveRegion="polite">
      <MathText style={styles.prompt}>{`Em đã chọn: ${selected.length}/${denominator}.`}</MathText>
    </View>
    <View style={styles.actions}>
      <Pressable accessibilityRole="button" accessibilityLabel="Kiểm tra phần em chọn" focusable
        onFocus={() => setFocused('check')} onBlur={() => setFocused(null)}
        onPress={checkSelection}
        style={({ pressed }) => [styles.button, styles.check, focused === 'check' && styles.focused, pressed && styles.pressed]}>
        <Text style={styles.checkText}>Kiểm tra phần em chọn</Text>
      </Pressable>
      <Pressable accessibilityRole="button" accessibilityLabel="Chọn lại từ đầu" focusable
        onFocus={() => setFocused('reset')} onBlur={() => setFocused(null)}
        onPress={() => { setSelected([]); setFeedback(''); }}
        style={({ pressed }) => [styles.button, focused === 'reset' && styles.focused, pressed && styles.pressed]}>
        <Text style={styles.label}>Chọn lại từ đầu</Text>
      </Pressable>
    </View>
    <Text accessibilityLiveRegion="polite" style={styles.body}>{feedback}</Text>
  </View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: COLORS.surface, borderWidth: 1, borderColor: '#EAE2F8', borderRadius: 23, padding: 16, gap: 14 },
  title: { color: COLORS.textPrimary, fontSize: 20, fontFamily: FONTS.extraBold },
  label: { color: COLORS.textPrimary, fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold },
  body: { color: COLORS.textSecondary, fontSize: 15, lineHeight: 23, fontFamily: FONTS.regular },
  prompt: { color: COLORS.textPrimary, fontSize: 18, lineHeight: 27, fontFamily: FONTS.bold },
  wholes: { gap: 12 },
  whole: { borderWidth: 1.5, borderColor: '#D8CBF1', backgroundColor: '#FAF8FE', borderRadius: 22, padding: 14, gap: 13 },
  explanation: { backgroundColor: COLORS.surfaceSubdued, borderRadius: 12, padding: 12, gap: 8 },
  pieces: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  piece: { minWidth: SIZES.minTouchTarget, minHeight: SIZES.minTouchTarget, maxWidth: '100%', paddingHorizontal: 6, paddingVertical: 8,
    borderWidth: 2, borderColor: COLORS.primaryDark,
    backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center', borderRadius: 13 },
  selected: { backgroundColor: COLORS.primaryDark },
  shapeSelected: { backgroundColor: COLORS.primaryLight },
  pieceText: { fontSize: 20, color: COLORS.primaryDark, fontFamily: FONTS.bold },
  selectedText: { color: COLORS.surface },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  pressed: { opacity: 0.7 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  button: { minHeight: SIZES.minTouchTarget, maxWidth: '100%', borderWidth: 2, borderColor: COLORS.primaryDark,
    borderRadius: 24, paddingVertical: 12, paddingHorizontal: 18, alignItems: 'center', justifyContent: 'center' },
  check: { backgroundColor: COLORS.primaryDark },
  checkText: { color: COLORS.surface, fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold, textAlign: 'center' },
});
