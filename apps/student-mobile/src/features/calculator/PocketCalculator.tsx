import React, { useRef, useState } from 'react';
import { Keyboard, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import type { ScrollViewInstance, TextInputInstance } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { MathText } from '../../components/domain/MathText';
import { calculateExpression } from './calculate';
import { UnitConverter } from './UnitConverter';

const KEYS = [['C', '⌫', '%', '÷'], ['7', '8', '9', '×'], ['4', '5', '6', '−'], ['1', '2', '3', '+'], ['a/b', '0', ',', '=']];
const LABELS: Record<string, string> = {
  C: 'Xóa phép tính', '⌫': 'Xóa chữ số cuối', '%': 'Phần trăm', '÷': 'Chia', '×': 'Nhân', '−': 'Trừ', '+': 'Cộng',
  'a/b': 'Nhập phân số', ',': 'Dấu phẩy thập phân', '=': 'Tính kết quả', '(': 'Mở ngoặc', ')': 'Đóng ngoặc', '±': 'Đổi dấu số',
};
type Result = ReturnType<typeof calculateExpression>;

/** One popup over its parent screen. No access to OCR, lesson answers or APIs. */
export function PocketCalculator({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const [expression, setExpression] = useState('');
  const [mode, setMode] = useState<'calculate' | 'convert'>('calculate');
  const [mixed, setMixed] = useState<{ whole: string; numerator: string; denominator: string } | null>(null);
  const [output, setOutput] = useState<Result | null>(null);
  const [error, setError] = useState('');
  const [panel, setPanel] = useState<'steps' | 'history' | null>(null);
  const [extras, setExtras] = useState(false);
  const [remainder, setRemainder] = useState(false);
  const [history, setHistory] = useState<Result[]>([]);
  const input = useRef<TextInputInstance>(null);
  const scroll = useRef<ScrollViewInstance>(null);
  const update = (value: string) => {
    setExpression(value.slice(0, 120)); setOutput(null); setError(''); setPanel(null); setRemainder(false);
  };
  const run = () => {
    try {
      const result = calculateExpression(expression);
      setOutput(result); setError(''); setRemainder(false); setPanel(result.steps.length ? 'steps' : null);
      setHistory(items => [result, ...items].slice(0, 10));
    } catch (failure) { setOutput(null); setPanel(null); setRemainder(false); setError((failure as Error).message); }
  };
  const pressKey = (key: string) => {
    if (key === '=') { run(); return; }
    if (key === 'C') { update(''); return; }
    if (key === '⌫') { update(expression.slice(0, -1)); return; }
    if (key === '±') {
      const negative = expression.match(/\(-([\d,.]+)\)$/);
      if (negative) { update(expression.slice(0, -negative[0].length) + negative[1]); return; }
      const match = expression.match(/(\d+(?:[,.]\d*)?)$/);
      if (match) update(expression.slice(0, -match[0].length) + `(-${match[0]})`);
      else update(expression + '(-');
      return;
    }
    const operator = ['+', '−', '×', '÷'].includes(key);
    // Keep the exact prior expression, even when its result exceeds literal input limits.
    let current = output && (operator || key === '%') ? `(${output.expression})` : output ? '' : expression;
    if (key === ',') {
      if (/\d+[,.]\d*$/.test(current)) return;
      if (!/\d$/.test(current)) current += '0';
    }
    if (operator && /[+−×÷]$/.test(current)) current = current.slice(0, -1);
    update(current + (key === 'a/b' ? '/' : key));
  };
  const keyButton = (key: string) => <Pressable key={key} accessibilityRole="button"
    accessibilityLabel={LABELS[key] || `Nhập ${key}`} onPress={() => pressKey(key)}
    style={({ pressed }) => [styles.key, ['÷', '×', '−', '+', '%', 'a/b'].includes(key) && styles.operator,
      key === '=' && styles.equals, pressed && styles.pressed]}>
    {key === 'a/b' ? <View accessible={false} style={styles.fractionKey}><Text style={styles.fractionLetter}>a</Text><View style={styles.bar} /><Text style={styles.fractionLetter}>b</Text></View>
      : key === '⌫' ? <Ionicons name="backspace-outline" size={25} color={COLORS.textPrimary} accessible={false} />
        : <Text style={[styles.keyText, key === '=' && styles.white]}>{key}</Text>}
  </Pressable>;
  const activeResult = remainder && output?.remainder ? output.remainder : output;
  const insertMixed = () => {
    if (!mixed) return;
    try {
      if (![mixed.whole, mixed.numerator, mixed.denominator].every(value => /^\d{1,6}$/.test(value)))
        throw new Error('Em điền đủ phần nguyên, tử số và mẫu số nhé.');
      const value = `${mixed.whole} ${mixed.numerator}/${mixed.denominator}`;
      calculateExpression(value);
      const prefix = output ? '' : expression;
      if (prefix && !/[+−×÷(]$/.test(prefix)) throw new Error('Em chọn dấu phép tính trước khi thêm hỗn số nhé.');
      if ((prefix + value).length > 120) throw new Error('Phép tính đã dài. Em tính kết quả trước nhé.');
      update(prefix + value); setMixed(null); Keyboard.dismiss();
    } catch (failure) { setError((failure as Error).message); }
  };
  return <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}
    onShow={() => { if (mode === 'calculate') input.current?.focus(); }} statusBarTranslucent>
    <SafeAreaView style={styles.overlay} edges={['top', 'bottom', 'left', 'right']}>
      <Pressable accessibilityRole="button" accessibilityLabel="Đóng máy tính bên ngoài" onPress={onClose} style={StyleSheet.absoluteFill} />
      <View style={styles.popup} accessibilityViewIsModal testID="calculator-popup">
        <View style={styles.header}>
          <Ionicons name="calculator-outline" size={22} color={COLORS.primaryDark} accessible={false} />
          <Text style={styles.title} accessibilityRole="header">Máy tính bỏ túi</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Đóng máy tính" onPress={onClose} style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}>
            <Ionicons name="close" size={24} color={COLORS.textPrimary} accessible={false} />
          </Pressable>
        </View>
        <ScrollView ref={scroll} keyboardShouldPersistTaps="handled" automaticallyAdjustKeyboardInsets contentContainerStyle={styles.content}>
          <View style={styles.modes}>
            {(['calculate', 'convert'] as const).map(key => <Pressable key={key} accessibilityRole="button"
              accessibilityLabel={key === 'calculate' ? 'Tính toán' : 'Đổi đơn vị'} accessibilityState={{ selected: mode === key }}
              onPress={() => { Keyboard.dismiss(); setMode(key); scroll.current?.scrollTo({ y: 0, animated: false }); }}
              style={({ pressed }) => [styles.mode, mode === key && styles.modeSelected, pressed && styles.pressed]}>
              <Ionicons name={key === 'calculate' ? 'calculator-outline' : 'swap-horizontal'} size={18} color={COLORS.primaryDark} accessible={false} />
              <Text style={styles.toolText}>{key === 'calculate' ? 'Tính toán' : 'Đổi đơn vị'}</Text>
            </Pressable>)}
          </View>
          <UnitConverter visible={mode === 'convert'} />
          {mode === 'calculate' ? <>
          <View style={styles.display}>
            <TextInput ref={input} accessibilityLabel="Phép tính" accessibilityHint="Nhập bằng bàn phím bên dưới. Phím phân số nối tử số với mẫu số."
              value={expression} placeholder="0" maxLength={120} showSoftInputOnFocus={false} multiline
              onChangeText={update} onSubmitEditing={run} style={[styles.expressionInput, expression.includes('/') && styles.fractionInput]} />
            {expression.includes('/') ? <View style={styles.result}><MathText style={styles.fractionPreview}>{expression}</MathText></View> : null}
            {output ? <View style={styles.result} accessibilityLiveRegion="polite"><MathText style={styles.answer}>{activeResult!.result}</MathText></View>
              : <Text style={styles.caption}>Chọn số và phép tính, rồi chạm =</Text>}
            {output?.mixedResult && !remainder ? <MathText style={styles.caption}>{`Hỗn số: ${output.mixedResult}`}</MathText> : null}
            {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          </View>
          <View style={styles.toolbar}>
            <Pressable accessibilityRole="button" accessibilityLabel="Lịch sử phép tính" accessibilityState={{ expanded: panel === 'history' }}
              onPress={() => setPanel(value => value === 'history' ? null : 'history')} style={({ pressed }) => [styles.tool, pressed && styles.pressed]}>
              <Ionicons name="time-outline" size={20} color={COLORS.primaryDark} accessible={false} /><Text style={styles.toolText}>Lịch sử</Text>
            </Pressable>
            {activeResult?.steps.length ? <Pressable accessibilityRole="button" accessibilityLabel="Xem cách tính" accessibilityState={{ expanded: panel === 'steps' }}
              onPress={() => setPanel(value => value === 'steps' ? null : 'steps')} style={({ pressed }) => [styles.tool, pressed && styles.pressed]}>
              <Ionicons name="bulb-outline" size={20} color={COLORS.primaryDark} accessible={false} /><Text style={styles.toolText}>Cách tính</Text>
            </Pressable> : null}
            <Pressable accessibilityRole="button" accessibilityLabel="Thêm chức năng" accessibilityState={{ expanded: extras }}
              onPress={() => setExtras(value => !value)} style={({ pressed }) => [styles.tool, pressed && styles.pressed]}>
              <Ionicons name={extras ? 'chevron-up' : 'chevron-down'} size={20} color={COLORS.primaryDark} accessible={false} /><Text style={styles.toolText}>Thêm</Text>
            </Pressable>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Nhập hỗn số" accessibilityState={{ expanded: !!mixed }}
            onPress={() => { setMixed(value => value ? null : { whole: '', numerator: '', denominator: '' }); setError(''); }}
            style={({ pressed }) => [styles.mixedToggle, pressed && styles.pressed]}>
            <Text style={styles.mixedSymbol}>2 ½</Text><Text style={styles.toolText}>Nhập hỗn số</Text>
            <Ionicons name={mixed ? 'chevron-up' : 'add-circle-outline'} size={20} color={COLORS.primaryDark} accessible={false} />
          </Pressable>
          {mixed ? <View style={styles.mixedForm}>
            <View style={styles.row}>
              {(['whole', 'numerator', 'denominator'] as const).map((part, index) => <View key={part} style={styles.mixedField}>
                <Text style={styles.toolText}>{['Phần nguyên', 'Tử số', 'Mẫu số'][index]}</Text>
                <TextInput accessibilityLabel={['Phần nguyên hỗn số', 'Tử số hỗn số', 'Mẫu số hỗn số'][index]}
                  value={mixed[part]} placeholder={['2', '1', '4'][index]} maxLength={6} keyboardType="number-pad"
                  onChangeText={value => { setMixed({ ...mixed, [part]: value }); setError(''); }} style={styles.mixedInput} />
              </View>)}
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Thêm hỗn số vào phép tính" onPress={insertMixed}
              style={({ pressed }) => [styles.mixedInsert, pressed && styles.pressed]}><Text style={[styles.toolText, styles.white]}>Thêm vào phép tính</Text></Pressable>
          </View> : null}
          {extras ? <View style={styles.row}>{['(', ')', '±'].map(keyButton)}</View> : null}
          {output?.remainder ? <Pressable accessibilityRole="button" accessibilityLabel="Xem thương và số dư" accessibilityState={{ selected: remainder }}
            onPress={() => { setRemainder(value => !value); setPanel('steps'); }} style={({ pressed }) => [styles.remainder, pressed && styles.pressed]}>
            <Text style={styles.toolText}>{remainder ? 'Xem kết quả đầy đủ' : 'Xem thương và số dư'}</Text>
          </Pressable> : null}
          {panel ? <ScrollView nestedScrollEnabled style={styles.detailsScroll} contentContainerStyle={styles.details}
            accessibilityLabel={panel === 'steps' ? 'Cách tính từng bước' : 'Lịch sử phép tính gần đây'}>
            {panel === 'steps' && activeResult ? activeResult.steps.map((step, index) => <View key={index} style={styles.step}>
              <Text style={styles.toolText}>Bước {index + 1}</Text><MathText style={styles.body}>{step}</MathText>
            </View>) : <>
              <View style={styles.historyHeader}><Text style={styles.toolText}>10 phép tính gần nhất</Text>
                <Pressable accessibilityRole="button" accessibilityLabel="Xóa lịch sử máy tính" onPress={() => setHistory([])} style={styles.iconButton}>
                  <Ionicons name="trash-outline" size={22} color={COLORS.primaryDark} accessible={false} />
                </Pressable>
              </View>
              {!history.length ? <Text style={styles.caption}>Chưa có phép tính. Lịch sử được giữ trên màn hình này.</Text> : history.map((entry, index) =>
                <Pressable key={index} accessibilityRole="button" accessibilityLabel={`Sửa phép tính ${entry.expression}`} style={({ pressed }) => [styles.historyItem, pressed && styles.pressed]}
                  onPress={() => { setExpression(entry.expression); setOutput(entry); setError(''); setRemainder(false); setPanel(entry.steps.length ? 'steps' : null); scroll.current?.scrollTo({ y: 0, animated: false }); }}>
                  <MathText style={styles.body}>{`${entry.expression} = ${entry.result}`}</MathText>
                </Pressable>)}
            </>}
          </ScrollView> : null}
          <View style={styles.keypad}>{KEYS.map((row, index) => <View key={index} style={styles.row}>{row.map(keyButton)}</View>)}</View>
          </> : null}
        </ScrollView>
      </View>
    </SafeAreaView>
  </Modal>;
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(15, 23, 42, 0.48)', justifyContent: 'center', alignItems: 'center', padding: 16 },
  popup: { width: '100%', maxWidth: 400, maxHeight: '94%', flexShrink: 1, borderRadius: 28, backgroundColor: COLORS.surface, overflow: 'hidden', ...SHADOWS.large },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingLeft: 16, paddingRight: 8, borderBottomWidth: 1, borderColor: COLORS.border },
  title: { flex: 1, fontFamily: FONTS.extraBold, fontSize: 17, color: COLORS.textPrimary },
  iconButton: { minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 16 },
  content: { padding: 12, gap: 8 }, display: { minHeight: 120, backgroundColor: COLORS.background, borderRadius: 20, padding: 12, gap: 8 },
  modes: { flexDirection: 'row', backgroundColor: COLORS.background, padding: 4, borderRadius: 16, gap: 4 },
  mode: { flex: 1, minHeight: 48, flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center', borderRadius: 12, paddingHorizontal: 8 },
  modeSelected: { backgroundColor: COLORS.primaryLight },
  mixedToggle: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderRadius: 12, backgroundColor: COLORS.background },
  mixedSymbol: { fontFamily: FONTS.extraBold, fontSize: 20, color: COLORS.primaryDark }, mixedForm: { padding: 12, gap: 12, backgroundColor: COLORS.background, borderRadius: 16 },
  mixedField: { flex: 1, gap: 6 }, mixedInput: { minHeight: 48, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, padding: 8, fontFamily: FONTS.bold, color: COLORS.textPrimary, fontSize: 18, backgroundColor: COLORS.surface },
  mixedInsert: { minHeight: 48, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.primaryDark, borderRadius: 12 },
  expressionInput: { fontFamily: FONTS.bold, fontSize: 28, textAlign: 'right', color: COLORS.textPrimary, minHeight: 48, borderRadius: 8 },
  fractionInput: { fontSize: 14, color: COLORS.textMuted, minHeight: 32 },
  fractionPreview: { fontFamily: FONTS.bold, fontSize: 26, color: COLORS.textPrimary },
  result: { alignSelf: 'flex-end', maxWidth: '100%' }, answer: { fontFamily: FONTS.extraBold, fontSize: 32, color: COLORS.primaryDark },
  caption: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: COLORS.textMuted, textAlign: 'right' },
  toolbar: { flexDirection: 'row', flexWrap: 'wrap', gap: 4 }, tool: { flexGrow: 1, flexDirection: 'row', gap: 4, alignItems: 'center', justifyContent: 'center', minHeight: 48, paddingHorizontal: 4, borderRadius: 12 },
  toolText: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark },
  keypad: { gap: 8 }, row: { flexDirection: 'row', gap: 8 }, key: { flex: 1, minHeight: 52, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surfaceSubdued, borderRadius: 16, paddingVertical: 4 },
  operator: { backgroundColor: COLORS.primaryLight }, equals: { backgroundColor: COLORS.primaryDark },
  keyText: { fontFamily: FONTS.extraBold, fontSize: 25, color: COLORS.textPrimary }, white: { color: COLORS.surface }, pressed: { opacity: .65 },
  fractionKey: { minWidth: 18, alignItems: 'stretch' }, fractionLetter: { fontFamily: FONTS.bold, fontSize: 15, lineHeight: 19, textAlign: 'center', color: COLORS.primaryDark }, bar: { height: 1.5, backgroundColor: COLORS.primaryDark },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: COLORS.errorText },
  remainder: { minHeight: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: COLORS.primaryLight },
  detailsScroll: { maxHeight: 210, borderRadius: 16, backgroundColor: COLORS.background },
  details: { padding: 12, gap: 12 }, step: { gap: 4 },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary }, historyHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  historyItem: { minHeight: 48, justifyContent: 'center', paddingVertical: 8, borderTopWidth: 1, borderColor: COLORS.border },
});
