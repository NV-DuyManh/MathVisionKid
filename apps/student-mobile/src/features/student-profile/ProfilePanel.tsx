import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, Switch, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { COLORS } from '../../constants/theme';
import { LessonSheet } from '../tutoring/LessonSheet';
import { avatars, ProfileRankCard, ProfileStats, profileStyles as s, StudentAvatar } from './ProfileCards';
import { profileApi, type ProfileEdit, type StudentProfile } from './profileApi';
import { useStudentProfile } from './useStudentProfile';

export function ProfilePanel({ owner, logout }: { owner: string; logout: () => Promise<void> }) {
  const router = useRouter();
  const profile = useStudentProfile(owner);
  const [sheet, setSheet] = useState<'edit' | 'logout' | null>(null);
  const [leaving, setLeaving] = useState(false);
  const [logoutError, setLogoutError] = useState(false);
  const logoutLock = useRef(false);
  const value = profile.value;
  const confirmLogout = async () => {
    if (logoutLock.current) return;
    logoutLock.current = true; setLeaving(true); setLogoutError(false);
    try { await logout(); } catch { setLogoutError(true); }
    finally { logoutLock.current = false; setLeaving(false); }
  };
  return <>
    <View style={s.card}>
      <View style={s.row}>
        <StudentAvatar id={value?.avatar ?? 'star'} size={64} />
        <View style={{ flex: 1, minWidth: 150 }}>
          <Text accessibilityRole="header" style={s.heading}>{value?.displayName ?? 'Hồ sơ của em'}</Text>
          {value?.gradeLevel != null && <Text style={s.body}>Khối {value.gradeLevel}</Text>}
          {value?.classrooms.map(room => <Text key={room.id} style={s.body}>{room.name}</Text>)}
          {value?.joinedAt && <Text style={s.body}>Tham gia {new Date(value.joinedAt).toLocaleDateString('vi-VN')}</Text>}
        </View>
      </View>
      {value && <AppButton title="Sửa hồ sơ" variant="secondary" onPress={() => setSheet('edit')} />}
      <AppButton title="Quyền riêng tư" variant="ghost" onPress={() => router.push('/privacy')} />
      <AppButton title="Đăng xuất" variant="outlined" style={s.logoutButton} textStyle={s.logoutLabel}
        icon={<Ionicons name="log-out-outline" size={23} color={COLORS.errorText} accessible={false} aria-hidden />}
        onPress={() => { setLogoutError(false); setSheet('logout'); }} />
    </View>
    {value ? <>
      <ProfileRankCard profile={value} />
      <ProfileStats profile={value} />
      <AppButton title="Danh hiệu và bảng xếp hạng" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
    </> : profile.failed ? <RecoveryNotice title="Chưa tải được hồ sơ" message="Em kiểm tra kết nối rồi thử lại nhé."
      actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại hồ sơ', icon: 'refresh-outline', onPress: profile.retry }]} />
      : <ActivityIndicator accessibilityLabel="Đang tải hồ sơ" />}
    {sheet === 'edit' && value && <ProfileEditor profile={value} onClose={() => setSheet(null)}
      onSave={updated => { profile.accept(updated); setSheet(null); }} />}
    {sheet === 'logout' && <LessonSheet title="Đăng xuất" compact onClose={() => { if (!leaving) setSheet(null); }}>
      <Text style={s.body}>Em có muốn đăng xuất khỏi tài khoản này?</Text>
      {logoutError && <Text accessibilityRole="alert" style={s.error}>Chưa đăng xuất được. Em thử lại nhé.</Text>}
      <AppButton title="Xác nhận đăng xuất" variant="danger" loading={leaving} loadingTitle="Đang đăng xuất…"
        icon={<Ionicons name="log-out-outline" size={22} color={COLORS.surface} accessible={false} aria-hidden />}
        onPress={() => { void confirmLogout(); }} />
      <AppButton title="Ở lại" variant="secondary" disabled={leaving} onPress={() => setSheet(null)} />
    </LessonSheet>}
  </>;
}

function ProfileEditor({ profile, onClose, onSave }: { profile: StudentProfile; onClose: () => void; onSave: (profile: StudentProfile) => void }) {
  const [edit, setEdit] = useState<ProfileEdit>({ displayName: profile.displayName, avatar: profile.avatar,
    leaderboardVisible: profile.leaderboardVisible, selectedTitle: profile.selectedTitle });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);
  const save = async () => {
    if (request.current) return;
    const name = edit.displayName.trim().normalize('NFC');
    if (!/^[\p{L}\p{M}][\p{L}\p{M} .’'-]{0,39}$/u.test(name)) {
      setError('Em nhập tên gồm chữ cái, dài tối đa 40 ký tự nhé.');
      return;
    }
    const call = new AbortController(); request.current = call;
    setBusy(true); setError('');
    try {
      const updated = await profileApi.update({ ...edit, displayName: name }, call.signal);
      if (!call.signal.aborted) onSave(updated);
    } catch {
      if (!call.signal.aborted) setError('Chưa lưu được hồ sơ. Em kiểm tra thông tin và kết nối rồi thử lại nhé.');
    } finally { request.current = null; if (!call.signal.aborted) setBusy(false); }
  };
  return <LessonSheet title="Sửa hồ sơ" onClose={() => { if (!busy) onClose(); }} footer={<>
    {error !== '' && <Text accessibilityRole="alert" style={[s.error, { marginBottom: 8 }]}>{error}</Text>}
    <AppButton title="Lưu hồ sơ" loading={busy} loadingTitle="Đang lưu…" onPress={() => { void save(); }} />
  </>}>
    <Text style={s.heading}>Tên hiển thị</Text>
    <TextInput accessibilityLabel="Tên hiển thị" style={s.input} value={edit.displayName} maxLength={40} editable={!busy}
      onChangeText={displayName => setEdit(p => ({ ...p, displayName }))} />
    <Text style={s.heading}>Hình đại diện</Text>
    <View style={s.row}>{avatars.map(avatar => <Pressable key={avatar.id} accessibilityRole="button" accessibilityLabel={avatar.name}
      accessibilityState={{ selected: edit.avatar === avatar.id, disabled: busy }} disabled={busy}
      style={[s.chip, edit.avatar === avatar.id && s.selected]} onPress={() => setEdit(p => ({ ...p, avatar: avatar.id }))}>
      <StudentAvatar id={avatar.id} size={34} />
    </Pressable>)}</View>
    <View style={s.row}><Text style={[s.body, { flex: 1 }]}>Tham gia bảng xếp hạng bằng bí danh</Text>
      <Switch accessibilityLabel="Tham gia bảng xếp hạng bằng bí danh" disabled={busy} value={edit.leaderboardVisible}
        onValueChange={leaderboardVisible => setEdit(p => ({ ...p, leaderboardVisible }))} /></View>
    <Text style={s.body}>Bảng xếp hạng hiển thị bí danh, hình đại diện và sao của em.</Text>
    <Text style={s.heading}>Danh hiệu trên hồ sơ</Text>
    <View style={s.row}>{[{ id: null, name: 'Để trống' }, ...profile.titles.filter(t => t.unlocked)].map(title => <Pressable
      key={title.id ?? 'none'} accessibilityRole="button" accessibilityState={{ selected: edit.selectedTitle === title.id, disabled: busy }}
      disabled={busy} style={[s.chip, edit.selectedTitle === title.id && s.selected]}
      onPress={() => setEdit(p => ({ ...p, selectedTitle: title.id }))}><Text style={s.body}>{title.name}</Text></Pressable>)}</View>
  </LessonSheet>;
}
