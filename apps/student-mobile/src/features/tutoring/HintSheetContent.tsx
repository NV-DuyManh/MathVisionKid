import React, { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { GivenFractionExplorer } from './FractionExplorer';
import type { HintVisual } from './hintVisualModel';

const robot = require('../../../assets/illustrations/web/robot-mascot.webp');

export function HintSheetContent({ hint, visual, children }: { hint: string; visual: HintVisual | null; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  const { width, fontScale } = useWindowDimensions();
  const compactIntro = width < 350 || fontScale > 1.3;
  const isFraction = visual?.kind === 'fractions';
  const toggleLabel = open
    ? isFraction ? 'Thu gọn hình phân số' : 'Thu gọn hình minh họa'
    : isFraction ? 'Nhìn phân số trong đề' : 'Xem hình minh họa';
  return <>
    <View style={[styles.intro, compactIntro && styles.compactIntro]}>
      <View style={styles.introCopy}><MathText style={styles.body}>{hint}</MathText></View>
      <Image source={robot} resizeMode="contain" style={[styles.mascot, compactIntro && styles.compactMascot]} accessible={false} aria-hidden />
    </View>
    {visual ? <>
      <Pressable accessibilityRole="button" accessibilityLabel={toggleLabel} accessibilityState={{ expanded: open }} aria-expanded={open}
        aria-controls="hint-visual-panel" onPress={() => setOpen(value => !value)}
        style={({ pressed }) => [styles.disclosure, pressed && styles.pressed]}>
        <View style={styles.disclosureIcon}><Ionicons name={isFraction ? 'pie-chart-outline' : 'apps-outline'} color={COLORS.primaryDark} size={20} accessible={false} aria-hidden /></View>
        <Text style={styles.disclosureText}>{toggleLabel}</Text>
        <Ionicons name={open ? 'chevron-up' : 'chevron-down'} color={COLORS.primaryDark} size={19} accessible={false} aria-hidden />
      </Pressable>
      <View nativeID="hint-visual-panel" style={open ? styles.panel : styles.hidden}>
        {open ? <VisualContent visual={visual} /> : null}
      </View>
    </> : null}
    {children}
  </>;
}

function VisualContent({ visual }: { visual: HintVisual }) {
  switch (visual.kind) {
    case 'fractions': return <FractionVisual visual={visual} />;
    case 'array': return <ArrayVisual rows={visual.rows} columns={visual.columns} />;
    case 'sharing': return <SharingVisual {...visual} />;
    case 'relation': return <RelationVisual initial={visual.initial} change={visual.change} mode={visual.mode} />;
  }
}

function FractionVisual({ visual }: { visual: Extract<HintVisual, { kind: 'fractions' }> }) {
  const [aligned, setAligned] = useState(false);
  const denominator = visual.commonDenominator;
  return <>
    <GivenFractionExplorer fractions={visual.values} />
    {denominator ? <>
      <VisualButton label={aligned ? 'Thu gọn cách quy đồng' : 'Xem hai phân số cùng mẫu'} expanded={aligned}
        onPress={() => setAligned(value => !value)} />
      {aligned ? <View style={styles.equivalence}>
        <Text style={styles.body}>{`Chia hai thanh cùng độ dài thành ${denominator} phần bằng nhau. Phần được tô giữ nguyên độ dài.`}</Text>
        {visual.values.map(({ numerator, denominator: original }) => {
          const selected = numerator * (denominator / original);
          return <View key={`${numerator}/${original}`} style={styles.equivalentRow}
            accessible accessibilityLabel={`${numerator} phần ${original} bằng ${selected} phần ${denominator}`}>
            <MathText style={styles.label}>{`${numerator}/${original} = ${selected}/${denominator}`}</MathText>
            <View style={styles.equalStrip} aria-hidden>
              {Array.from({ length: denominator }, (_, index) =>
                <View key={index} style={[styles.equalCell, index > 0 && styles.divider, index < selected && styles.filled]} />)}
            </View>
          </View>;
        })}
      </View> : null}
    </> : null}
  </>;
}

function ArrayVisual({ rows, columns }: { rows: number; columns: number }) {
  const [built, setBuilt] = useState(0);
  const [checked, setChecked] = useState(false);
  const change = (value: number) => { setBuilt(value); setChecked(false); };
  return <View style={styles.model}>
    <ModelHeading icon="grid-outline" title="Xếp thành các hàng" detail={`Tạo ${rows} hàng. Mỗi hàng có ${columns} chấm.`} />
    <View style={styles.dotBoard}>
      {built === 0 ? <Text style={styles.body}>Thêm một hàng để bắt đầu.</Text> : null}
      {Array.from({ length: built }, (_, row) => <View key={row} style={styles.dotRow} aria-hidden>
        <Dots count={columns} />
      </View>)}
    </View>
    <Text accessibilityLiveRegion="polite" style={styles.label}>{`Đã xếp ${built} trên ${rows} hàng`}</Text>
    <View style={styles.actions}>
      <VisualButton label="Thêm một hàng" primary disabled={built === rows} onPress={() => change(built + 1)} />
      <VisualButton label="Bỏ một hàng" disabled={!built} onPress={() => change(built - 1)} />
      <VisualButton label="Kiểm tra cách xếp" onPress={() => setChecked(true)} />
    </View>
    {checked ? <Feedback correct={built === rows}>{built === rows
      ? 'Đúng số hàng rồi. Em đếm hoặc tính số chấm của tất cả các hàng nhé.'
      : `Em cần xếp thêm ${rows - built} hàng để đủ số hàng trong phép tính.`}</Feedback> : null}
  </View>;
}

function SharingVisual({ amount, groups, allowsRemainder }: Extract<HintVisual, { kind: 'sharing' }>) {
  const [moves, setMoves] = useState<number[]>([]);
  const [checked, setChecked] = useState(false);
  const counts = Array<number>(groups).fill(0);
  moves.forEach(index => { counts[index] += 1; });
  const remaining = amount - moves.length;
  const equal = counts.every(count => count === counts[0]);
  const complete = equal && (allowsRemainder ? remaining < groups : remaining === 0);
  function distribute(index: number) {
    setMoves(current => current.length >= amount ? current : [...current, index]);
    setChecked(false);
  }
  return <View style={styles.model}>
    <ModelHeading icon="albums-outline" title="Chia đều vào các nhóm"
      detail={`Chia ${amount} chấm vào ${groups} nhóm. Chạm nhóm để thêm 1 chấm.`} />
    {remaining ? <View style={styles.pool} aria-hidden><Dots count={remaining} /></View> : null}
    <Text accessibilityLiveRegion="polite" style={styles.label}>{`Còn ${remaining} chấm chưa chia`}</Text>
    <View style={styles.actions}>
      {counts.map((count, index) => <Pressable key={index} accessibilityRole="button"
        accessibilityLabel={`Nhóm ${index + 1}, có ${count} chấm`} accessibilityHint="Thêm một chấm vào nhóm"
        disabled={!remaining} accessibilityState={{ disabled: remaining === 0 }} onPress={() => distribute(index)}
        style={({ pressed }) => [styles.group, pressed && styles.pressed]}>
        <Text style={styles.label}>{`Nhóm ${index + 1}`}</Text>
        {count ? <Dots count={count} /> : <Ionicons name="add" size={16} color={COLORS.primaryDark} accessible={false} aria-hidden />}
      </Pressable>)}
    </View>
    <View style={styles.actions}>
      <VisualButton label="Kiểm tra cách chia" primary onPress={() => setChecked(true)} />
      <VisualButton label="Bỏ lượt cuối" disabled={!moves.length} onPress={() => { setMoves(current => current.slice(0, -1)); setChecked(false); }} />
      <VisualButton label="Chia lại" onPress={() => { setMoves([]); setChecked(false); }} />
    </View>
    {checked ? <Feedback correct={complete}>{complete
      ? allowsRemainder ? 'Các nhóm bằng nhau. Không đủ chấm để chia thêm một lượt.' : 'Các nhóm có cùng số chấm. Em tự đếm số chấm của một nhóm nhé.'
      : remaining >= groups || (remaining && !allowsRemainder) ? 'Vẫn còn chấm chưa chia. Em tiếp tục chia vào các nhóm nhé.'
        : 'Số chấm giữa các nhóm chưa bằng nhau. Em thử bỏ lượt cuối hoặc chia lại nhé.'}</Feedback> : null}
  </View>;
}

function RelationVisual({ initial, change, mode }: { initial: number; change: number; mode: 'add' | 'remove' }) {
  const adding = mode === 'add';
  return <View style={styles.model}>
    <Text accessibilityRole="header" style={styles.title}>Nhìn mối quan hệ</Text>
    <View style={styles.diagram}>
      <View style={[styles.block, styles.wholeBlock]}>
        <Text style={styles.label}>{adding ? 'Tất cả' : 'Ban đầu'}</Text>
        <Text style={styles.title}>{adding ? '?' : initial}</Text>
      </View>
      <View style={styles.diagramLine} aria-hidden />
      <View style={styles.relationPair}>
        <View style={[styles.block, styles.baseBlock]}>
          <Text style={styles.label}>{adding ? 'Ban đầu' : 'Còn lại'}</Text>
          <Text style={styles.title}>{adding ? initial : '?'}</Text>
        </View>
        <View style={[styles.block, styles.changeBlock]}>
          <Text style={styles.label}>{adding ? 'Thêm vào' : 'Bớt đi'}</Text>
          <Text style={styles.title}>{change}</Text>
        </View>
      </View>
    </View>
    <Text style={styles.body}>{adding ? 'Gộp phần ban đầu và phần thêm vào để tìm tất cả.'
      : 'Phần còn lại và phần bớt đi ghép thành lượng ban đầu.'}</Text>
  </View>;
}

function ModelHeading({ icon, title, detail }: { icon: React.ComponentProps<typeof Ionicons>['name']; title: string; detail: string }) {
  return <View style={styles.modelHeading}>
    <View style={styles.modelIcon}><Ionicons name={icon} size={20} color={COLORS.primaryDark} accessible={false} aria-hidden /></View>
    <View style={styles.introCopy}>
      <Text accessibilityRole="header" style={styles.title}>{title}</Text>
      <Text style={styles.body}>{detail}</Text>
    </View>
  </View>;
}

function Dots({ count }: { count: number }) {
  return <View style={styles.dots} aria-hidden>
    {Array.from({ length: count }, (_, index) => <View key={index} style={styles.dot} />)}
  </View>;
}

function Feedback({ correct, children }: { correct: boolean; children: string }) {
  return <Text accessibilityLiveRegion="polite" style={[styles.feedback, correct ? styles.correct : styles.retry]}>{children}</Text>;
}

function VisualButton({ label, primary, disabled, expanded, onPress }: {
  label: string; primary?: boolean; disabled?: boolean; expanded?: boolean; onPress: () => void;
}) {
  const [focused, setFocused] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled, expanded }}
    aria-expanded={expanded} disabled={disabled} onPress={onPress} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    style={({ pressed }) => [styles.button, primary && styles.primary, disabled && styles.disabled,
      focused && styles.focused, pressed && styles.pressed]}>
    <Text style={[styles.label, primary && styles.primaryText]}>{label}</Text>
  </Pressable>;
}

const styles = StyleSheet.create({
  intro: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 4 },
  compactIntro: { flexWrap: 'wrap' },
  introCopy: { flex: 1, minWidth: 0 },
  mascot: { width: 72, height: 80 },
  compactMascot: { width: 54, height: 60 },
  body: { color: COLORS.textSecondary, fontSize: 15, lineHeight: 23, fontFamily: FONTS.regular },
  title: { color: COLORS.textPrimary, fontSize: 19, lineHeight: 26, fontFamily: FONTS.extraBold },
  label: { color: COLORS.textPrimary, fontSize: 14, lineHeight: 20, fontFamily: FONTS.bold },
  disclosure: { backgroundColor: '#EEE5FF', padding: 10, paddingHorizontal: 13, borderRadius: 18,
    minHeight: SIZES.minTouchTarget, flexDirection: 'row', alignItems: 'center', gap: 10, borderWidth: 1, borderColor: '#DAC9FA' },
  disclosureIcon: { backgroundColor: COLORS.surface, borderRadius: 10, padding: 7 },
  disclosureText: { flex: 1, fontSize: 15, lineHeight: 22, color: COLORS.primaryDark, fontFamily: FONTS.extraBold },
  pressed: { opacity: .72 },
  hidden: { display: 'none' },
  panel: { borderWidth: 1, borderColor: '#E5D9FA', padding: 12, borderRadius: 20, backgroundColor: COLORS.surface, gap: 12 },
  model: { gap: 8 },
  modelHeading: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: COLORS.surfaceSubdued, padding: 8, borderRadius: 12 },
  modelIcon: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surface },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  button: { minHeight: SIZES.minTouchTarget, alignItems: 'center', justifyContent: 'center',
    backgroundColor: COLORS.surface, borderWidth: 2, borderColor: COLORS.border, borderRadius: 13, padding: 9 },
  primary: { backgroundColor: COLORS.primaryDark, borderColor: COLORS.primaryDark },
  primaryText: { color: COLORS.surface },
  disabled: { opacity: .5 },
  focused: { borderStyle: 'dashed', borderColor: COLORS.textPrimary },
  equivalence: { padding: 10, gap: 9, borderRadius: 14, backgroundColor: COLORS.surfaceSubdued },
  equivalentRow: { gap: 4 },
  equalStrip: { flexDirection: 'row', height: 25, borderWidth: 1, borderColor: COLORS.primaryDark, borderRadius: 5, overflow: 'hidden' },
  equalCell: { flex: 1, backgroundColor: COLORS.surface, borderLeftWidth: 1, borderLeftColor: 'transparent' },
  divider: { borderLeftColor: COLORS.primaryDark },
  filled: { backgroundColor: '#BCA5F8' },
  dotBoard: { gap: 8, borderRadius: 12, backgroundColor: '#F8F4FE', padding: 8 },
  dotRow: { minHeight: 28, padding: 4, justifyContent: 'center', alignItems: 'center' },
  pool: { minHeight: 32, padding: 8, borderRadius: 12, backgroundColor: '#F8F4FE' },
  dots: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, minWidth: 12 },
  dot: { backgroundColor: COLORS.primaryDark, width: 13, height: 13, borderRadius: 7 },
  group: { minHeight: SIZES.minTouchTarget, flexGrow: 1, flexBasis: '30%', borderWidth: 1,
    borderColor: '#DAC9FA', borderRadius: 11, backgroundColor: '#FAF7FF', padding: 6, gap: 4 },
  diagram: { gap: 4 },
  block: { padding: 7, alignItems: 'center', borderRadius: 10, borderWidth: 1, borderColor: '#DAC9FA', flex: 1, gap: 2 },
  wholeBlock: { backgroundColor: COLORS.surfaceSubdued },
  baseBlock: { backgroundColor: '#E7F5F0' },
  changeBlock: { backgroundColor: '#FFF2D9' },
  diagramLine: { backgroundColor: '#7963AB', height: 10, width: 2, alignSelf: 'center' },
  relationPair: { flexDirection: 'row', gap: 5 },
  feedback: { color: COLORS.textPrimary, fontSize: 14, lineHeight: 20, fontFamily: FONTS.bold, borderRadius: 10, padding: 8 },
  correct: { backgroundColor: COLORS.successLight },
  retry: { backgroundColor: COLORS.warningLight },
});
