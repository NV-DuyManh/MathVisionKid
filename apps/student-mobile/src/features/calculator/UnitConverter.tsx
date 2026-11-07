import React, { useState } from 'react';
import { Keyboard, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { convertUnits, UNIT_GROUPS, type UnitGroup } from './convertUnits';

const DEFAULTS: Record<UnitGroup, [string, string]> = {
  length: ['m', 'cm'], area: ['m²', 'dm²'], mass: ['kg', 'g'], volume: ['l', 'ml'],
};

export function UnitConverter({ visible }: { visible: boolean }) {
  const [group, setGroup] = useState<UnitGroup>('length');
  const [amount, setAmount] = useState('');
  const [from, setFrom] = useState('m');
  const [to, setTo] = useState('cm');
  const [extra, setExtra] = useState<{ value: string; unit: string } | null>(null);
  const [selecting, setSelecting] = useState<'from' | 'to' | 'extra' | null>(null);
  const [answer, setAnswer] = useState<ReturnType<typeof convertUnits> | null>(null);
  const [error, setError] = useState('');
  const clearAnswer = () => { setAnswer(null); setError(''); };
  const chooseGroup = (next: UnitGroup) => {
    setGroup(next); setFrom(DEFAULTS[next][0]); setTo(DEFAULTS[next][1]); setExtra(null); setSelecting(null); clearAnswer();
  };
  const run = () => {
    Keyboard.dismiss(); setSelecting(null);
    try { setAnswer(convertUnits(group, [{ value: amount, unit: from }, ...(extra ? [extra] : [])], to)); setError(''); }
    catch (failure) { setAnswer(null); setError((failure as Error).message); }
  };
  const unitButton = (slot: 'from' | 'to' | 'extra', unit: string, label: string) => <Pressable
    accessibilityRole="button" accessibilityLabel={`${label}: ${unit}`} accessibilityState={{ expanded: selecting === slot }}
    onPress={() => { Keyboard.dismiss(); setSelecting(value => value === slot ? null : slot); }}
    style={({ pressed }) => [styles.unitButton, pressed && styles.pressed]}>
    <Text style={styles.unitText}>{unit}</Text><Ionicons name="chevron-down" size={18} color={COLORS.primaryDark} accessible={false} />
  </Pressable>;
  if (!visible) return null;
  return <View style={styles.content}>
    <View style={styles.groups}>
      {(Object.keys(UNIT_GROUPS) as UnitGroup[]).map(key => <Pressable key={key} accessibilityRole="button"
        accessibilityLabel={`Đổi ${UNIT_GROUPS[key].label.toLowerCase()}`} accessibilityState={{ selected: group === key }}
        onPress={() => chooseGroup(key)} style={({ pressed }) => [styles.group, group === key && styles.selected, pressed && styles.pressed]}>
        <Text style={[styles.label, group === key && styles.selectedText]}>{UNIT_GROUPS[key].label}</Text>
      </Pressable>)}
    </View>
    <View style={styles.form}>
      <Text style={styles.label}>Số đo cần đổi</Text>
      <View style={styles.row}>
        <TextInput accessibilityLabel="Số đo cần đổi" accessibilityHint="Có thể nhập 15,25 hoặc hỗn số 2 1/4."
          placeholder="Ví dụ: 15,25" value={amount} maxLength={32} onChangeText={value => { setAmount(value); clearAnswer(); }}
          onSubmitEditing={run} style={styles.input} />
        {unitButton('from', from, 'Đơn vị gốc')}
      </View>
      {extra ? <View style={styles.row}>
        <TextInput accessibilityLabel="Số đo thêm" placeholder="Ví dụ: 25" value={extra.value} maxLength={32}
          onChangeText={value => { setExtra({ ...extra, value }); clearAnswer(); }} onSubmitEditing={run} style={styles.input} />
        {unitButton('extra', extra.unit, 'Đơn vị thêm')}
        <Pressable accessibilityRole="button" accessibilityLabel="Bỏ số đo thêm" onPress={() => { setExtra(null); setSelecting(null); clearAnswer(); }} style={styles.iconButton}>
          <Ionicons name="close-circle-outline" size={24} color={COLORS.textSecondary} accessible={false} />
        </Pressable>
      </View> : <Pressable accessibilityRole="button" accessibilityLabel="Thêm số đo" onPress={() => { setExtra({ value: '', unit: to }); clearAnswer(); }} style={styles.add}>
        <Ionicons name="add-circle-outline" size={20} color={COLORS.primaryDark} accessible={false} />
        <Text style={styles.link}>Thêm số đo, ví dụ 15 m 25 cm</Text>
      </Pressable>}
      <View style={styles.row}>
        <Text style={[styles.label, styles.grow]}>Đổi sang</Text>
        {!extra ? <Pressable accessibilityRole="button" accessibilityLabel="Đảo hai đơn vị" onPress={() => {
          setFrom(to); setTo(from); setSelecting(null); clearAnswer();
        }} style={styles.iconButton}><Ionicons name="swap-vertical" size={22} color={COLORS.primaryDark} accessible={false} /></Pressable> : null}
        {unitButton('to', to, 'Đơn vị đích')}
      </View>
      {selecting ? <View style={styles.unitPicker} accessibilityLabel="Chọn đơn vị">
        {UNIT_GROUPS[group].units.map(([unit]) => <Pressable key={unit} accessibilityRole="button" accessibilityLabel={`Chọn ${unit}`}
          accessibilityState={{ selected: unit === (selecting === 'from' ? from : selecting === 'to' ? to : extra?.unit) }}
          onPress={() => {
            if (selecting === 'from') setFrom(unit);
            else if (selecting === 'to') setTo(unit);
            else if (extra) setExtra({ ...extra, unit });
            setSelecting(null); clearAnswer();
          }} style={({ pressed }) => [styles.unitOption, pressed && styles.pressed]}><Text style={styles.unitText}>{unit}</Text></Pressable>)}
      </View> : null}
      <Pressable accessibilityRole="button" accessibilityLabel="Đổi đơn vị ngay" onPress={run}
        style={({ pressed }) => [styles.convert, pressed && styles.pressed]}>
        <Ionicons name="swap-horizontal" size={21} color={COLORS.surface} accessible={false} /><Text style={styles.convertText}>Đổi đơn vị</Text>
      </Pressable>
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
    </View>
    {answer ? <View style={styles.result} accessibilityLiveRegion="polite">
      <Text style={styles.label}>Kết quả</Text><MathText style={styles.answer}>{answer.result}</MathText>
      <View style={styles.divider} />
      <Text style={styles.link}>Cách đổi</Text>
      {answer.steps.map((step, index) => <MathText key={index} style={styles.body}>{step}</MathText>)}
    </View> : <Text style={styles.hint}>Diện tích đổi theo mỗi bậc 100; thể tích theo mỗi bậc 1 000. Máy tính sẽ chỉ cách đổi theo đơn vị em chọn.</Text>}
  </View>;
}

const styles = StyleSheet.create({
  content: { gap: 12 }, groups: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  group: { minWidth: '45%', flexGrow: 1, minHeight: 48, paddingHorizontal: 8, justifyContent: 'center', alignItems: 'center', borderRadius: 14, borderWidth: 1, borderColor: COLORS.border },
  selected: { backgroundColor: COLORS.primaryLight, borderColor: COLORS.primaryDark }, selectedText: { color: COLORS.primaryDark },
  label: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.textPrimary },
  form: { backgroundColor: COLORS.background, borderRadius: 20, padding: 12, gap: 12 }, row: { flexDirection: 'row', alignItems: 'center', gap: 8 }, grow: { flex: 1 },
  input: { flex: 1, minWidth: 0, minHeight: 52, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 14, padding: 12, fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary },
  unitButton: { minWidth: 80, minHeight: 52, paddingHorizontal: 12, gap: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: COLORS.primaryLight },
  unitText: { fontFamily: FONTS.bold, fontSize: 17, color: COLORS.primaryDark }, iconButton: { minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center' },
  add: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 6 }, link: { flexShrink: 1, fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark },
  unitPicker: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, unitOption: { minWidth: 56, minHeight: 48, paddingHorizontal: 12, backgroundColor: COLORS.surface, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  convert: { minHeight: 52, borderRadius: 16, backgroundColor: COLORS.primaryDark, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  convertText: { fontFamily: FONTS.bold, fontSize: 16, color: COLORS.surface },
  result: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 20, padding: 16, gap: 12 },
  answer: { fontFamily: FONTS.extraBold, fontSize: 28, color: COLORS.primaryDark }, divider: { height: 1, backgroundColor: COLORS.border },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary }, hint: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: COLORS.textMuted },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: COLORS.errorText }, pressed: { opacity: .65 },
});
