import React, { useContext, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { LessonSheet } from '../tutoring/LessonSheet';
import { COLORS, FONTS } from '../../constants/theme';
import { StudentAvatar, avatars } from './ProfileCards';
import { useStudentProfile } from './useStudentProfile';
import { profileApi, type ProfileEdit, type StudentProfile } from './profileApi';

export function AccountScreen({ owner }: { owner: string }) {
  const router = useRouter(), auth = useContext(AuthContext), profile = useStudentProfile(owner);
  const { width } = useWindowDimensions();
  const [confirmLogout, setConfirmLogout] = useState(false), [leaving, setLeaving] = useState(false);
  const [logoutError, setLogoutError] = useState(false);
  const logoutLock = useRef(false);
  const logout = async () => {
    if (logoutLock.current) return;
    logoutLock.current = true; setLeaving(true); setLogoutError(false);
    try { await auth?.logout(); } catch { setLogoutError(true); } finally { logoutLock.current = false; setLeaving(false); }
  };
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <KeyboardAvoidingView style={s.screen} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.content}>
        <StudentPageHeader compact title="Hồ sơ của em" showAvatar={false} backLabel="Quay lại" onBack={() => router.canGoBack() ? router.back() : router.replace('/(tabs)')} />
        {profile.value ? <View style={[s.columns, width >= 900 && s.wide]}>
          <AccountEditor profile={profile.value} onSave={profile.accept} />
          <View style={[s.side, width >= 900 && { maxWidth: 320 }]}>
            <PasswordCard available={profile.value.passwordLoginAvailable !== false} />
            <View style={s.card}>
              <View style={s.sectionTitle}><Ionicons accessible={false} aria-hidden name="school-outline" size={22} color={COLORS.primaryDark} /><Text accessibilityRole="header" style={s.heading}>Góc học tập</Text></View>
              <Text style={s.body}>{profile.value.gradeLevel ? `Khối ${profile.value.gradeLevel}` : 'Chưa có thông tin khối lớp'}</Text>
              {profile.value.classrooms.map(item => <Text style={s.body} key={item.id}>{item.name}</Text>)}
              <Text style={s.hint}>Giáo viên quản lý lớp học và khối lớp của em.</Text>
              <AppButton title="Xem thành tích" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
            </View>
            <AppButton title="Đăng xuất" variant="ghost" icon={<Ionicons accessible={false} aria-hidden name="log-out-outline" color={COLORS.textSecondary} size={20} />} onPress={() => setConfirmLogout(true)} />
          </View>
        </View> : profile.failed ? <RecoveryNotice title="Chưa tải được hồ sơ" message="Em kiểm tra kết nối rồi thử lại nhé."
          actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại hồ sơ', icon: 'refresh-outline', onPress: profile.retry }]} /> : <ActivityIndicator accessibilityLabel="Đang tải hồ sơ" />}
      </ScrollView>
    </KeyboardAvoidingView>
    {confirmLogout && <LessonSheet title="Đăng xuất" compact onClose={() => { if (!leaving) setConfirmLogout(false); }}>
      <Text style={s.body}>Em có muốn đăng xuất khỏi tài khoản này?</Text>
      {logoutError && <Text accessibilityRole="alert" style={s.error}>Chưa đăng xuất được. Em thử lại nhé.</Text>}
      <AppButton title="Xác nhận đăng xuất" variant="danger" loading={leaving} loadingTitle="Đang đăng xuất…" onPress={() => { void logout(); }} />
      <AppButton title="Ở lại" variant="secondary" disabled={leaving} onPress={() => setConfirmLogout(false)} />
    </LessonSheet>}
  </SafeAreaView>;
}

function AccountEditor({ profile, onSave }: { profile: StudentProfile; onSave: (value: StudentProfile) => void }) {
  const auth = useContext(AuthContext);
  const { width } = useWindowDimensions();
  const [edit, setEdit] = useState<ProfileEdit>({ displayName: profile.displayName, avatar: profile.avatar,
    leaderboardVisible: profile.leaderboardVisible, selectedTitle: profile.selectedTitle });
  const [photoSelected, setPhotoSelected] = useState(Boolean(profile.avatarPhoto));
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const lifetime = useRef(new AbortController()), lock = useRef(false);
  useEffect(() => { const controller = new AbortController(); lifetime.current = controller; return () => controller.abort(); }, []);
  const dirty = edit.displayName !== profile.displayName || edit.avatar !== profile.avatar || edit.selectedTitle !== profile.selectedTitle
    || edit.leaderboardVisible !== profile.leaderboardVisible || photoSelected !== Boolean(profile.avatarPhoto);
  const save = async () => {
    const signal = lifetime.current.signal;
    if (lock.current) return;
    const displayName = edit.displayName.trim().normalize('NFC');
    if (!/^[\p{L}\p{M}][\p{L}\p{M} .’'-]{0,39}$/u.test(displayName)) { setError('Em nhập tên gồm chữ cái, dài tối đa 40 ký tự nhé.'); return; }
    lock.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const next = await profileApi.update({ ...edit, displayName, removePhoto: !photoSelected }, signal);
      if (!signal.aborted) {
        onSave(next); setEdit({ ...edit, displayName: next.displayName }); setNotice('Đã lưu hồ sơ của em.');
        void auth?.refreshUser?.().catch(() => {});
      }
    } catch { if (!signal.aborted) setError('Chưa lưu được hồ sơ. Em kiểm tra kết nối rồi thử lại nhé.'); }
    finally { lock.current = false; if (!signal.aborted) setBusy(false); }
  };
  const choosePhoto = async () => {
    const signal = lifetime.current.signal;
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: true, aspect: [1, 1], quality: .85, exif: false });
      if (result.canceled || !result.assets?.[0] || signal.aborted) return;
      const asset = result.assets[0];
      if (!asset.width || !asset.height || asset.width * asset.height > 40_000_000) throw new Error('Image size');
      const side = Math.min(asset.width, asset.height);
      const context = ImageManipulator.manipulate(asset.uri);
      context.crop({ originX: Math.floor((asset.width - side) / 2), originY: Math.floor((asset.height - side) / 2), width: side, height: side }).resize({ width: 320, height: 320 });
      const image = await context.renderAsync();
      const file = await image.saveAsync({ format: SaveFormat.PNG });
      if (signal.aborted) return;
      const next = await profileApi.uploadPhoto(file.uri, signal);
      if (!signal.aborted) { onSave(next); setPhotoSelected(true); setNotice('Đã cập nhật ảnh đại diện.'); }
    } catch { if (!signal.aborted) setError('Chưa cập nhật được ảnh. Em kiểm tra ảnh và kết nối rồi thử lại nhé.'); }
    finally { lock.current = false; if (!signal.aborted) setBusy(false); }
  };
  return <View style={[s.card, s.editor]}>
    <View style={s.identity}>
      <View style={s.avatarRing}><StudentAvatar id={edit.avatar} photo={photoSelected ? profile.avatarPhoto : null} size={88} /></View>
      <View style={{ flex: 1, gap: 5 }}><Text accessibilityRole="header" style={s.name}>{profile.displayName}</Text><Text style={s.hint}>Ảnh và tên hiển thị của em</Text></View>
    </View>
    <AppButton title="Chọn ảnh từ thiết bị" variant="secondary" disabled={busy} icon={<Ionicons accessible={false} aria-hidden name="image-outline" size={20} color={COLORS.primaryDark} />} onPress={() => { void choosePhoto(); }} />
    <Text style={s.hint}>Hoặc chọn một người bạn nhỏ:</Text>
    <View style={[s.avatars, width < 600 && s.phoneAvatars]}>{avatars.map(avatar => <Pressable key={avatar.id} accessibilityRole="button" accessibilityLabel={`Chọn hình ${avatar.name}`}
      accessibilityState={{ selected: !photoSelected && edit.avatar === avatar.id, disabled: busy }} disabled={busy}
      onPress={() => { setPhotoSelected(false); setEdit(value => ({ ...value, avatar: avatar.id })); setNotice(''); }}
      style={[s.avatarChoice, !photoSelected && edit.avatar === avatar.id && s.chosen]}><StudentAvatar id={avatar.id} size={40} /></Pressable>)}</View>
    {profile.avatarPhoto && !photoSelected && <Pressable accessibilityRole="button" accessibilityLabel="Giữ ảnh đã tải lên" disabled={busy} onPress={() => setPhotoSelected(true)}><Text style={s.link}>Giữ ảnh đã tải lên</Text></Pressable>}
    <View style={s.divider} />
    <Text nativeID="account-name-label" style={s.label}>Tên hiển thị</Text>
    <TextInput accessibilityLabel="Tên hiển thị" aria-labelledby="account-name-label" aria-describedby="account-name-help account-editor-error" aria-invalid={Boolean(error) && !/^[\p{L}\p{M}][\p{L}\p{M} .’'-]{0,39}$/u.test(edit.displayName.trim())} style={s.input}
      value={edit.displayName} maxLength={40} autoComplete="name" editable={!busy} onChangeText={displayName => { setEdit(value => ({ ...value, displayName })); setNotice(''); }} />
    <Text nativeID="account-name-help" style={s.hint}>Tên em muốn thầy cô và bạn bè gọi. Tối đa 40 ký tự.</Text>
    {profile.titles.some(title => title.unlocked) && <>
      <Text style={s.label}>Danh hiệu yêu thích</Text>
      <View style={s.avatars}>{[{ id: null, name: 'Chưa chọn' }, ...profile.titles.filter(title => title.unlocked)].map(title => <Pressable key={title.id ?? 'none'}
        accessibilityRole="button" accessibilityState={{ selected: edit.selectedTitle === title.id, disabled: busy }} disabled={busy}
        onPress={() => setEdit(value => ({ ...value, selectedTitle: title.id }))} style={[s.titleChoice, edit.selectedTitle === title.id && s.chosen]}><Text style={s.body}>{title.name}</Text></Pressable>)}</View>
    </>}
    <View style={s.divider} />
    <View style={s.privacy}><Ionicons accessible={false} aria-hidden name="shield-checkmark-outline" size={22} color={COLORS.primaryDark} /><Text accessibilityRole="header" style={[s.label, { flex: 1 }]}>Quyền riêng tư</Text></View>
    <View style={s.privacy}><Text style={[s.body, { flex: 1 }]}>Tham gia bảng xếp hạng bằng bí danh</Text><Switch accessibilityLabel="Tham gia bảng xếp hạng bằng bí danh" disabled={busy}
      value={edit.leaderboardVisible} onValueChange={leaderboardVisible => setEdit(value => ({ ...value, leaderboardVisible }))} /></View>
    <Text style={s.hint}>Ảnh tải lên chỉ hiện trong tài khoản của em. Bảng xếp hạng dùng bí danh và hình có sẵn, không hiển thị tên hay ảnh cá nhân.</Text>
    {error !== '' && <Text nativeID="account-editor-error" accessibilityRole="alert" style={s.error}>{error}</Text>}
    {notice !== '' && <Text accessibilityLiveRegion="polite" style={s.success}>{notice}</Text>}
    <AppButton title="Lưu thay đổi" loading={busy} loadingTitle="Đang cập nhật…" disabled={!dirty} onPress={() => { void save(); }} />
    {!dirty && !notice && <Text style={s.hint}>Thông tin của em đã được lưu.</Text>}
  </View>;
}

function PasswordCard({ available }: { available: boolean }) {
  const auth = useContext(AuthContext);
  const [expanded, setExpanded] = useState(false), [show, setShow] = useState(false), [busy, setBusy] = useState(false);
  const [current, setCurrent] = useState(''), [next, setNext] = useState(''), [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState(''), [notice, setNotice] = useState('');
  const lifetime = useRef(new AbortController()), lock = useRef(false);
  useEffect(() => { const controller = new AbortController(); lifetime.current = controller; return () => controller.abort(); }, []);
  const submit = async () => {
    const signal = lifetime.current.signal;
    if (lock.current) return;
    setError(''); setNotice('');
    if (!current) { setError('Em nhập mật khẩu hiện tại nhé.'); return; }
    if (next.length < 8) { setError('Mật khẩu mới cần ít nhất 8 ký tự.'); return; }
    if (next !== confirmation) { setError('Hai lần nhập mật khẩu mới chưa giống nhau.'); return; }
    if (next === current) { setError('Em chọn mật khẩu mới khác mật khẩu hiện tại nhé.'); return; }
    lock.current = true; setBusy(true);
    try {
      if (!auth?.changePassword) throw new Error('Authentication unavailable');
      await auth.changePassword(current, next, signal);
      if (!signal.aborted) {
        setCurrent(''); setNext(''); setConfirmation(''); setExpanded(false); setShow(false);
        setNotice('Đã đổi mật khẩu. Các phiên đăng nhập khác đã kết thúc.');
      }
    } catch (failure: any) {
      const code = failure.response?.data?.error?.code;
      if (!signal.aborted) setError(code === 'PASSWORD_CURRENT_INVALID' ? 'Mật khẩu hiện tại chưa đúng. Em kiểm tra lại nhé.'
        : code === 'PASSWORD_TRY_LATER' ? 'Em đã nhập sai nhiều lần. Em thử lại sau 15 phút nhé.'
          : code === 'PASSWORD_INPUT_INVALID' ? 'Mật khẩu mới hơi dài. Em dùng ít ký tự hơn nhé.'
            : code === 'PASSWORD_PROVIDER_MANAGED' ? 'Em đổi mật khẩu tại dịch vụ em dùng để đăng nhập nhé.'
              : 'Chưa nhận được kết quả đổi mật khẩu. Em kiểm tra kết nối rồi đăng nhập lại để xác nhận nhé.');
    } finally { lock.current = false; if (!signal.aborted) setBusy(false); }
  };
  return <View style={s.card}>
    <View style={s.sectionTitle}><Ionicons accessible={false} aria-hidden name="lock-closed-outline" size={22} color={COLORS.primaryDark} /><Text accessibilityRole="header" style={s.heading}>An toàn tài khoản</Text></View>
    {!available ? <Text style={s.body}>Em đang dùng tài khoản liên kết. Em đổi mật khẩu tại dịch vụ em dùng để đăng nhập nhé.</Text> : <>
      <Text style={s.hint}>Giữ mật khẩu cho riêng mình. Em có thể nhờ bố mẹ hỗ trợ.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Đổi mật khẩu" accessibilityState={{ expanded, disabled: busy }} aria-expanded={expanded} aria-controls="account-password-fields"
        disabled={busy} style={s.passwordToggle} onPress={() => { setExpanded(value => !value); setError(''); setNotice(''); }}><Text style={s.link}>Đổi mật khẩu</Text><Ionicons accessible={false} aria-hidden name={expanded ? 'chevron-up' : 'chevron-forward'} size={18} color={COLORS.primaryDark} /></Pressable>
      {expanded && <View nativeID="account-password-fields" style={{ gap: 10 }}>
        {[['Mật khẩu hiện tại', current, setCurrent], ['Mật khẩu mới', next, setNext], ['Nhập lại mật khẩu mới', confirmation, setConfirmation]].map(([label, value, setter], index) => <View key={String(label)} style={{ gap: 6 }}>
          <Text style={s.label}>{String(label)}</Text><TextInput accessibilityLabel={String(label)} aria-describedby="account-password-help account-password-error" style={s.input} value={value as string} editable={!busy} secureTextEntry={!show}
            autoComplete={index === 0 ? 'current-password' : 'new-password'} autoCapitalize="none" autoCorrect={false} maxLength={index === 0 ? 200 : 72}
            onChangeText={setter as (value: string) => void} />
        </View>)}
        <Text nativeID="account-password-help" style={s.hint}>Mật khẩu mới có ít nhất 8 ký tự.</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} style={s.passwordToggle} onPress={() => setShow(value => !value)}><Text style={s.link}>{show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}</Text></Pressable>
        <AppButton title="Cập nhật mật khẩu" loading={busy} loadingTitle="Đang đổi mật khẩu…" onPress={() => { void submit(); }} />
      </View>}
    </>}
    {error !== '' && <Text nativeID="account-password-error" accessibilityRole="alert" style={s.error}>{error}</Text>}
    {notice !== '' && <Text accessibilityLiveRegion="polite" style={s.success}>{notice}</Text>}
  </View>;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: 20, paddingBottom: 36, width: '100%', maxWidth: 1040, alignSelf: 'center', gap: 12 },
  columns: { gap: 18 }, wide: { flexDirection: 'row', alignItems: 'flex-start' }, side: { flex: 1, gap: 18, minWidth: 0 }, editor: { flex: 1.5, minWidth: 0 },
  card: { padding: 22, borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, gap: 14 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: 18 }, avatarRing: { padding: 6, borderRadius: 54, backgroundColor: COLORS.primaryLight },
  name: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 30, color: COLORS.textPrimary }, heading: { fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary, flexShrink: 1 },
  sectionTitle: { flexDirection: 'row', alignItems: 'center', gap: 10 }, label: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary }, hint: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: COLORS.textSecondary },
  input: { minHeight: 50, paddingHorizontal: 14, paddingVertical: 12, borderRadius: 14, borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.background, fontFamily: FONTS.semiBold, fontSize: 16, color: COLORS.textPrimary },
  avatars: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, avatarChoice: { padding: 5, borderRadius: 30, borderWidth: 2, borderColor: 'transparent' },
  phoneAvatars: { width: '100%', maxWidth: 220, alignSelf: 'center', justifyContent: 'space-between' },
  titleChoice: { paddingVertical: 10, paddingHorizontal: 12, borderRadius: 12, borderWidth: 2, borderColor: COLORS.border }, chosen: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  divider: { height: 1, backgroundColor: COLORS.border, marginVertical: 3 }, privacy: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  link: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark }, passwordToggle: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: COLORS.errorText }, success: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: '#176A50' },
});
