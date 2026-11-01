import React, { useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';

type Props = {
  problem: string; work: string; problemImage: string; workImage: string; photoCurrent: boolean;
  disabled: boolean; onEdit: (field: 'problem' | 'work') => void; onConfirm: () => void;
};

/** Transcription confirmation is separate from the mathematical review. */
export function WorkReviewPreparation({ problem, work, problemImage, workImage, photoCurrent, disabled, onEdit, onConfirm }: Props) {
  const [section, setSection] = useState<'problem' | 'work'>('work');
  const source = section === 'work' ? work : problem;
  const photo = section === 'work' ? workImage : problemImage;
  const unclear = problem.includes('[?]') || work.includes('[?]');
  return <View style={s.card}>
    <View style={s.headingRow}><View style={s.icon}><Ionicons name="scan-outline" size={21} color={COLORS.primaryDark} accessible={false} /></View>
      <View style={s.copy}><Text style={s.eyebrow}>1 · ĐỌC BÀI LÀM</Text><Text accessibilityRole="header" style={s.title}>Mình đã đọc được như sau</Text></View></View>
    <Text style={s.body}>Đối chiếu phần chữ với ảnh. Chỉ chỉnh nếu có số hoặc dấu chưa đúng; bước sau mình sẽ nhận xét bài em đã làm.</Text>
    <View style={s.tabs}>{(['problem', 'work'] as const).map(field => <Pressable key={field} accessibilityRole="button"
      accessibilityLabel={field === 'problem' ? 'Đối chiếu đề bài' : 'Đối chiếu bài làm'} accessibilityState={{ selected: section === field }}
      onPress={() => setSection(field)} style={({ pressed }) => [s.tab, section === field && s.activeTab, pressed && s.pressed]}>
      <Text style={[s.tabText, section === field && s.activeText]}>{field === 'problem' ? 'Đề bài' : 'Bài em đã viết'}{(field === 'problem' ? problem : work).includes('[?]') ? ' · Chưa rõ' : ''}</Text>
    </Pressable>)}</View>
    {photo ? <View style={s.photoFrame}><Image source={{ uri: photo }} style={s.photo} resizeMode="contain"
      accessibilityLabel={section === 'problem' ? 'Ảnh đề bài' : photoCurrent ? 'Ảnh bài em đã làm' : 'Ảnh trước khi sửa bài bằng chữ'} /></View> : null}
    {section === 'work' && photo && !photoCurrent ? <Text style={s.note}>Ảnh trước khi sửa. Nhận xét tiếp theo sẽ dựa trên phần chữ mới bên dưới.</Text> : null}
    <View style={s.transcript}><MathText style={s.body}>{source}</MathText></View>
    <Pressable accessibilityRole="button" accessibilityLabel={section === 'problem' ? 'Chỉnh đề bài' : 'Chỉnh chỗ chưa đọc đúng'}
      onPress={() => onEdit(section)} disabled={disabled} style={({ pressed }) => [s.edit, pressed && s.pressed]}>
      <Ionicons name="create-outline" size={18} color={COLORS.primaryDark} accessible={false} /><Text style={s.editText}>Chỉnh phần chữ này</Text>
    </Pressable>
    {unclear ? <Text accessibilityRole="alert" style={s.note}>Còn ký hiệu [?] chưa đọc rõ. Em đối chiếu cả hai mục và chỉnh lại trước khi nhận xét nhé.</Text> : null}
    <AppButton title="Nội dung đã đúng · Xem nhận xét" disabled={disabled || unclear || !problem.trim() || !work.trim()} onPress={onConfirm} />
    <Text style={s.caption}>Bấm tiếp nghĩa là em xác nhận phần chữ của đề và bài làm đã khớp. Không cần giải lại hay tóm tắt đề.</Text>
  </View>;
}
const s = StyleSheet.create({
  card: { backgroundColor: '#FFF', borderRadius: 22, borderWidth: 1, borderColor: '#E6DFF0', padding: 16, gap: 12 },
  headingRow: { flexDirection: 'row', alignItems: 'center', gap: 10 }, icon: { width: 40, height: 40, borderRadius: 13, backgroundColor: '#F0EAFF', alignItems: 'center', justifyContent: 'center' },
  copy: { flex: 1, gap: 3 }, eyebrow: { fontFamily: FONTS.extraBold, color: COLORS.primaryDark, fontSize: 11, lineHeight: 17 },
  title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 18, lineHeight: 25 },
  body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 23 },
  tabs: { flexDirection: 'row', gap: 4, padding: 4, borderRadius: 14, backgroundColor: '#F0EBF8' },
  tab: { flex: 1, minHeight: 44, alignItems: 'center', justifyContent: 'center', padding: 8, borderRadius: 11 },
  activeTab: { backgroundColor: '#FFF' }, tabText: { fontFamily: FONTS.semiBold, color: COLORS.textSecondary, fontSize: 13, lineHeight: 20, textAlign: 'center' },
  activeText: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold }, pressed: { opacity: .7 },
  photoFrame: { borderRadius: 14, overflow: 'hidden', backgroundColor: '#F6F3FC' }, photo: { width: '100%', height: 210 },
  transcript: { padding: 12, borderRadius: 13, backgroundColor: '#FAF8FD' },
  edit: { alignSelf: 'flex-start', minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 4 },
  editText: { fontFamily: FONTS.bold, fontSize: 13, lineHeight: 20, color: COLORS.primaryDark },
  caption: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 12, lineHeight: 19 },
  note: { fontFamily: FONTS.semiBold, color: '#855325', fontSize: 13, lineHeight: 21 },
});
