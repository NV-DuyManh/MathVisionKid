import React, { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { Image, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { DivisionCheck, TutorService, WrittenDivision } from './api/TutorService';

type Props = { division: WrittenDivision; imageUri: string; uncertain: boolean; onChange: (value: WrittenDivision) => void };

function DivisionField({ label, value, onChangeText, inputRef, error, maxLength = 24 }: {
  label: string; value: string; onChangeText: (text: string) => void;
  inputRef: (value: TextInput | null) => void; error?: string; maxLength?: number;
}) {
  return <View style={styles.field}>
    <Text style={styles.label}>{label}</Text>
    <TextInput ref={inputRef} accessibilityLabel={label} accessibilityHint="Đối chiếu với ảnh rồi sửa nếu chưa đúng"
      value={value} onChangeText={onChangeText} keyboardType="number-pad" maxLength={maxLength}
      placeholder="Chưa đọc rõ" style={[styles.input, !!error && styles.flagged]} />
    {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}
  </View>;
}

export function DivisionReview({ division, imageUri, uncertain, onChange }: Props) {
  const [confirmed, setConfirmed] = useState(false);
  const [result, setResult] = useState<DivisionCheck | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [repairing, setRepairing] = useState(false);
  const [hintCount, setHintCount] = useState(0);
  const request = useRef<AbortController | null>(null);
  const fieldRefs = useRef<Record<string, TextInput | null>>({});
  useFocusEffect(useCallback(() => () => {
    request.current?.abort(); request.current = null; setBusy(false);
  }, []));
  const change = (next: WrittenDivision) => {
    request.current?.abort(); request.current = null;
    setBusy(false); setConfirmed(false); setResult(null); setHintCount(0); setError(''); onChange(next);
  };
  const check = async () => {
    if (!confirmed || request.current) return;
    const abort = new AbortController(); request.current = abort; setBusy(true); setError('');
    try {
      const response = await TutorService.checkDivision(division, true, abort.signal);
      if (abort.signal.aborted) return;
      setResult(response); setHintCount(0);
      if (response.status === 'TRY_AGAIN') setRepairing(true);
      if (response.status !== 'CORRECT') {
        const field = response.field === 'rows' ? `row-${response.rowIndex ?? 0}` : response.field;
        fieldRefs.current[field]?.focus();
      }
    } catch (failure: any) {
      if (!abort.signal.aborted) setError(failure?.response?.status === 401
        ? 'Phiên học đã hết hạn. Em đăng nhập lại rồi kiểm tra tiếp nhé.'
        : 'Chưa kiểm tra được lúc này. Các số em đã sửa vẫn được giữ; em thử lại nhé.');
    } finally {
      if (request.current === abort) { request.current = null; setBusy(false); }
    }
  };
  const incomplete = !/^[0-9]+$/.test(division.dividend) || !/^[0-9]+$/.test(division.divisor)
    || !division.quotient || !/^[0-9]+$/.test(division.quotient)
    || !division.rows.length || division.rows.some(row => !row.trim() || !/^[0-9 +\-−]+$/.test(row));
  const hints = result?.status === 'TRY_AGAIN' ? result.hints ?? [] : [];
  return <View style={styles.card}>
    <View style={styles.titleRow}><Ionicons name="calculator-outline" color={COLORS.primaryDark} size={24} /><Text style={styles.title}>Phép chia em đã làm</Text></View>
    <Text style={styles.body}>Nhìn ảnh và kiểm tra từng số bên dưới. Nếu mình đọc khác bài em viết, em sửa ngay tại ô đó nhé.</Text>
    {imageUri ? <Image source={{ uri: imageUri }} resizeMode="contain" style={styles.photo} accessibilityLabel="Ảnh phép chia để đối chiếu từng hàng" /> : null}
    {uncertain ? <Text style={styles.notice}>Có nét chữ cần nhìn lại. Mình giữ nguyên cả những số có thể em đã tính sai.</Text> : null}
    <View style={styles.operands}>
      <DivisionField label="Số bị chia" value={division.dividend} onChangeText={text => change({ ...division, dividend: text })}
        inputRef={ref => { fieldRefs.current.dividend = ref; }} error={result?.field === 'dividend' ? result.message : undefined} />
      <DivisionField label="Số chia" value={division.divisor} onChangeText={text => change({ ...division, divisor: text })}
        inputRef={ref => { fieldRefs.current.divisor = ref; }} error={result?.field === 'divisor' ? result.message : undefined} />
    </View>
    <DivisionField label="Thương em viết" value={division.quotient ?? ''} onChangeText={text => change({ ...division, quotient: text || null })}
      inputRef={ref => { fieldRefs.current.quotient = ref; }} error={result?.field === 'quotient' ? result.message : undefined} />
    <Text style={styles.label}>Các hàng tính từ trên xuống</Text>
    <Text style={styles.body}>Cách viết gọn: mỗi hàng là số vừa hạ xuống; hàng cuối là số dư. Giữ cả số 0 ở đầu hàng như trong ảnh.</Text>
    {division.rows.map((row, index) => <View style={styles.row} key={index}>
      <DivisionField label={index === division.rows.length - 1 ? `Hàng ${index + 1} · Số dư cuối` : `Hàng ${index + 1}`} value={row} maxLength={40}
        onChangeText={text => change({ ...division, rows: division.rows.map((item, i) => i === index ? text : item) })}
        inputRef={ref => { fieldRefs.current[`row-${index}`] = ref; }} error={result?.field === 'rows' && result.rowIndex === index ? result.message : undefined} />
      {index < division.rows.length - 1 && division.rows.length < 30 ? <Pressable accessibilityRole="button"
        accessibilityLabel={`Thêm hàng sau hàng ${index + 1}`} style={({ pressed }) => [styles.remove, pressed && styles.pressed]}
        onPress={() => change({ ...division, rows: [...division.rows.slice(0, index + 1), '', ...division.rows.slice(index + 1)] })}>
        <Ionicons name="add-circle-outline" size={23} color={COLORS.primaryDark} />
      </Pressable> : null}
      <Pressable accessibilityRole="button" accessibilityLabel={`Xóa hàng ${index + 1}`} style={({ pressed }) => [styles.remove, pressed && styles.pressed]}
        onPress={() => change({ ...division, rows: division.rows.filter((_, i) => i !== index) })}>
        <Ionicons name="close-circle-outline" size={23} color={COLORS.primaryDark} />
      </Pressable>
    </View>)}
    {division.rows.length < 30 ? <AppButton title="Thêm hàng bị thiếu" variant="secondary" onPress={() => change({ ...division, rows: [...division.rows, ''] })} /> : null}
    {incomplete ? <Text style={styles.notice}>Em điền những ô còn trống hoặc có dấu [?] trước khi kiểm tra nhé.</Text> : null}
    <Pressable accessibilityRole="checkbox" aria-checked={confirmed} accessibilityState={{ checked: confirmed, disabled: !!incomplete || busy }}
      accessibilityLabel={repairing ? 'Em đã kiểm tra phần vừa sửa' : 'Em đã đối chiếu các số với ảnh'} disabled={!!incomplete || busy}
      style={({ pressed }) => [styles.confirm, pressed && styles.pressed, incomplete && styles.disabled]}
      onPress={() => setConfirmed(value => !value)}>
      <Ionicons name={confirmed ? 'checkbox' : 'square-outline'} color={COLORS.primaryDark} size={26} />
      <Text style={[styles.body, styles.flex]}>{repairing ? 'Em đã kiểm tra phần vừa sửa' : 'Em đã đối chiếu các số với ảnh'}</Text>
    </Pressable>
    <AppButton title={result?.status === 'CORRECT' ? 'Đã kiểm tra phép chia' : 'Kiểm tra phép chia'} onPress={() => void check()}
      loading={busy} disabled={!confirmed || busy || result?.status === 'CORRECT'} />
    {result ? <View style={result.status === 'CORRECT' ? styles.success : styles.feedback} accessibilityLiveRegion="polite">
      <Text style={styles.label}>{result.status === 'CORRECT' ? 'Em làm đúng rồi!' : result.status === 'TRY_AGAIN' ? 'Cùng sửa một chỗ nhé' : 'Cần nhìn lại hàng tính'}</Text>
      <Text style={styles.body}>{result.message}</Text>
      {result.status !== 'CORRECT' ? <Text style={styles.body}>Em sửa ô được nhắc tới, đối chiếu lại rồi bấm kiểm tra. Mình sẽ xem tiếp các hàng còn lại.</Text> : null}
      {hintCount < hints.length ? <AppButton title={hintCount === 0 ? 'Gợi ý sửa bước này' : 'Gợi ý rõ hơn'} variant="secondary"
        onPress={() => setHintCount(count => Math.min(count + 1, hints.length))} /> : null}
      {hints.slice(0, hintCount).map((hint, index) => <View key={index} style={styles.hint}>
        <Text style={styles.label}>Gợi ý {index + 1} · Chia, nhân, trừ, hạ</Text>
        <Text style={styles.body}>{hint}</Text>
      </View>)}
    </View> : null}
    {error ? <Text style={styles.error} accessibilityRole="alert">{error}</Text> : null}
    <Text style={styles.caption}>Phần này kiểm tra phép chia. Nếu đây là bước trong bài toán có lời văn, vẫn cần đề bài để đối chiếu cách giải.</Text>
  </View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: COLORS.surface, borderRadius: 24, padding: 20, gap: 14, ...SHADOWS.small },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  title: { flex: 1, fontSize: 21, fontFamily: FONTS.extraBold, color: COLORS.textPrimary },
  body: { fontSize: 15, lineHeight: 23, fontFamily: FONTS.regular, color: COLORS.textSecondary },
  label: { fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold, color: COLORS.textPrimary },
  field: { flex: 1, minWidth: 120, gap: 7 }, flex: { flex: 1 },
  photo: { width: '100%', aspectRatio: 1, backgroundColor: COLORS.surfaceSubdued, borderRadius: 16 },
  operands: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  input: { minHeight: 52, borderRadius: 14, borderWidth: 1.5, borderColor: '#D7CDF2', padding: 12, backgroundColor: COLORS.surfaceSubdued, color: COLORS.textPrimary, fontSize: 21, fontFamily: FONTS.bold },
  flagged: { borderColor: '#963E22', backgroundColor: '#FFF3ED' },
  row: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
  remove: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 14 },
  confirm: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 12 },
  pressed: { opacity: 0.7 }, disabled: { opacity: 0.5 },
  notice: { color: '#70441E', fontSize: 14, lineHeight: 21, fontFamily: FONTS.medium },
  error: { color: '#963E22', fontSize: 14, lineHeight: 21, fontFamily: FONTS.semiBold },
  feedback: { backgroundColor: '#FFF3ED', borderRadius: 16, padding: 16, gap: 8 },
  hint: { backgroundColor: COLORS.surface, borderRadius: 12, padding: 12, gap: 6 },
  success: { backgroundColor: '#E9F5EF', borderRadius: 16, padding: 16, gap: 8 },
  caption: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 18, fontFamily: FONTS.regular },
});
