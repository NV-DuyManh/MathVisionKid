import React, { useContext, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { isCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { LessonSheet } from '../tutoring/LessonSheet';
import { COLORS, FONTS, IS_STUDENT_WEB } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { StudentAvatar } from './ProfileCards';
import { PersonalPageHeader } from './PersonalWeb';
import { LogoutSheet } from './LogoutSheet';
import { useStudentProfile } from './useStudentProfile';
import { profileApi, type ProfileEdit, type StudentProfile } from './profileApi';
import { tokenStorage } from '../../services/auth/tokenStorage';

export function AccountScreen({ owner, openPrivacy = false, openLogout = false }: { owner: string; openPrivacy?: boolean; openLogout?: boolean }) {
  const router = useRouter(), profile = useStudentProfile(owner);
  const { width } = useWindowDimensions();
  const desktopWeb = IS_STUDENT_WEB && !isCompactStudentWeb(width);
  const [contentWidth, setContentWidth] = useState(0);
  const wide = desktopWeb ? contentWidth >= 850 : width >= 900;
  const [confirmLogout, setConfirmLogout] = useState(false);
  const closeLogout = () => {
    setConfirmLogout(false);
    if (openLogout) router.setParams({ section: undefined });
  };
  const goBack = () => router.canGoBack() ? router.back() : router.replace('/(tabs)/profile');
  return <SafeAreaView style={[s.screen, desktopWeb && s.webScreen]} edges={['top', 'bottom']}>
    <KeyboardAvoidingView style={[s.screen, desktopWeb && s.webScreen]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[s.content, desktopWeb && s.webContent]}>
        {desktopWeb ? <PersonalPageHeader title="Hồ sơ của em" backLabel="Quay lại" onBack={goBack} />
          : <StudentPageHeader compact title="Hồ sơ của em" showAvatar={false} backLabel="Quay lại" onBack={goBack} />}
        <View style={[s.columns, wide && s.wide, desktopWeb && s.webColumns]}
          onLayout={desktopWeb ? event => setContentWidth(event.nativeEvent.layout.width) : undefined}>
          <View style={[s.editor, wide && s.editorWide]}>
            {profile.value ? <AccountEditor profile={profile.value} onSave={profile.accept} openPrivacy={openPrivacy} />
              : !profile.failed && <ActivityIndicator accessibilityLabel="Đang tải hồ sơ" />}
            {profile.failed && <RecoveryNotice dialog={!profile.value} title={profile.value ? 'Chưa cập nhật được hồ sơ' : 'Chưa tải được hồ sơ'}
              message={profile.value ? 'Em đang xem thông tin đã tải trước đó.' : 'Em kiểm tra kết nối rồi thử lại nhé.'}
              actions={[{ label: 'Thử lại', accessibilityLabel: 'Tải lại hồ sơ', icon: 'refresh-outline', onPress: profile.retry }]} />}
          </View>
          <View style={[s.side, wide && (desktopWeb ? s.webSide : { flex: 1, maxWidth: 320 })]}>
            {profile.value && <PasswordCard available={profile.value.passwordLoginAvailable !== false}
              googleLinked={profile.value.googleLinked === true} />}
            <AppButton title="Đăng xuất" variant="ghost" style={desktopWeb ? s.webLogout : undefined}
              icon={<Ionicons accessible={false} aria-hidden name="log-out-outline" color={desktopWeb ? '#9A3152' : COLORS.textSecondary} size={20} />}
              onPress={() => setConfirmLogout(true)} />
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
    {(confirmLogout || openLogout) && <LogoutSheet onClose={closeLogout} />}
  </SafeAreaView>;
}

const webSwitchTrack = { false: '#BCB0D0', true: STUDENT_WEB.primary };
const DISPLAY_NAME_PATTERN = /^[\p{L}\p{M}\p{Nd}][\p{L}\p{M}\p{Nd} .’'-]*$/u;
type PrivacyEdit = Pick<ProfileEdit, 'leaderboardVisible' | 'leaderboardNameHidden' | 'leaderboardPhotoVisible'>;

function AccountEditor({ profile, onSave, openPrivacy }: {
  profile: StudentProfile; onSave: (value: StudentProfile) => void; openPrivacy: boolean;
}) {
  const auth = useContext(AuthContext);
  const { width } = useWindowDimensions();
  const compact = width < 480;
  const [nameDraft, setNameDraft] = useState<string>();
  const [privacyDraft, setPrivacyDraft] = useState<{ revision?: string; edit: PrivacyEdit }>();
  const [needsPrivacyReload, setNeedsPrivacyReload] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [photoFailed, setPhotoFailed] = useState(false);
  const [avatarHovered, setAvatarHovered] = useState(false), [avatarFocused, setAvatarFocused] = useState(false);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const lifetime = useRef(new AbortController()), lock = useRef(false);
  useEffect(() => { const controller = new AbortController(); lifetime.current = controller; return () => controller.abort(); }, []);
  useEffect(() => {
    if (!IS_STUDENT_WEB || !openPrivacy) return;
    const frame = requestAnimationFrame(() => {
      const section = document.getElementById('account-privacy-heading');
      section?.setAttribute('tabindex', '-1');
      section?.focus({ preventScroll: true });
      section?.scrollIntoView({ block: 'start' });
    });
    return () => cancelAnimationFrame(frame);
  }, [openPrivacy]);
  // A newly loaded revision replaces the privacy snapshot the draft was based on.
  const privacyEdit = !needsPrivacyReload && privacyDraft?.revision === profile.privacyRevision ? privacyDraft?.edit : undefined;
  const editPrivacy = (patch: PrivacyEdit) => {
    if (needsPrivacyReload || lock.current) return;
    setPrivacyDraft(previous => ({
      revision: profile.privacyRevision,
      edit: { ...(previous?.revision === profile.privacyRevision ? previous?.edit : undefined), ...patch },
    }));
    setNotice('');
    setError('');
  };
  const leaderboardVisible = privacyEdit?.leaderboardVisible ?? profile.leaderboardVisible;
  const leaderboardNameHidden = privacyEdit?.leaderboardNameHidden ?? profile.leaderboardNameHidden ?? true;
  const nameInput = nameDraft ?? profile.displayName;
  const photoVisible = leaderboardVisible && (privacyEdit?.leaderboardPhotoVisible ?? profile.leaderboardPhotoVisible ?? false);
  const privacyChanges: PrivacyEdit = {
    leaderboardVisible: leaderboardVisible === profile.leaderboardVisible ? undefined : leaderboardVisible,
    leaderboardNameHidden: leaderboardNameHidden === (profile.leaderboardNameHidden ?? true) ? undefined : leaderboardNameHidden,
    leaderboardPhotoVisible: privacyEdit?.leaderboardPhotoVisible === undefined || photoVisible === (profile.leaderboardPhotoVisible ?? false)
      ? undefined : photoVisible,
  };
  const privacyChanged = Object.values(privacyChanges).some(value => value !== undefined);
  const displayName = nameInput.trim().normalize('NFC');
  const nameChanged = nameDraft !== undefined && displayName !== profile.displayName;
  const dirty = nameChanged || privacyChanged;
  const invalidName = !DISPLAY_NAME_PATTERN.test(displayName) || displayName.split(/ +/, 51).length > 50;
  const save = async () => {
    const signal = lifetime.current.signal;
    if (lock.current) return;
    setPhotoFailed(false);
    if (nameChanged && invalidName) { setError('Em nhập tên có chữ hoặc số, tối đa 50 từ nhé.'); return; }
    if (!dirty) { setEditingName(false); setNameDraft(undefined); return; }
    lock.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const next = await profileApi.update({ displayName: nameChanged ? displayName : undefined, ...privacyChanges,
        privacyRevision: privacyChanged ? profile.privacyRevision : undefined }, signal);
      if (!signal.aborted) {
        onSave(next);
        setNameDraft(undefined);
        setPrivacyDraft(undefined);
        setNotice('Đã lưu hồ sơ của em.'); setEditingName(false);
        void auth?.refreshUser?.().catch(() => {});
      }
    } catch (failure) {
      if (signal.aborted) return;
      const problem = failure as { code?: string; currentProfile?: StudentProfile } | null;
      if (problem?.code === 'PROFILE_PRIVACY_CONFLICT') {
        setPrivacyDraft(undefined);
        if (problem.currentProfile) {
          onSave(problem.currentProfile);
          setError('Quyền riêng tư hoặc ảnh đã thay đổi ở phiên khác. Em kiểm tra hồ sơ và chọn lại quyền chia sẻ nhé.');
        } else {
          setNeedsPrivacyReload(true);
          setEditingName(false);
        }
      } else if (problem?.code === 'PROFILE_NAME_UNCONFIRMED') {
        setError('Chưa xác nhận được tên hiển thị đã lưu. Em thử lại sau nhé.');
      } else {
        setError(problem?.code === 'PROFILE_PRIVACY_UNCONFIRMED'
          ? 'Chưa xác nhận được lựa chọn quyền riêng tư đã lưu. Lựa chọn của em vẫn được giữ; em thử lại sau nhé.'
          : 'Chưa lưu được hồ sơ. Em kiểm tra kết nối rồi thử lại nhé.');
      }
    }
    finally { lock.current = false; if (!signal.aborted) setBusy(false); }
  };
  const reloadPrivacy = async () => {
    if (lock.current) return;
    const signal = lifetime.current.signal;
    lock.current = true;
    setBusy(true);
    try {
      const current = await profileApi.reloadPrivacy(signal);
      if (signal.aborted) return;
      onSave(current);
      setNeedsPrivacyReload(false);
      setNotice('Đã tải lại hồ sơ. Em có thể chọn lại quyền chia sẻ.');
    } catch {
      // Keep the reload action available until the current snapshot can be read.
    } finally {
      lock.current = false;
      if (!signal.aborted) setBusy(false);
    }
  };
  const choosePhoto = async () => {
    const signal = lifetime.current.signal;
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(''); setNotice(''); setPhotoFailed(false);
    try {
      // Capture before the picker opens; retain its user gesture on web.
      const session = tokenStorage.getSessionId();
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
      const next = await profileApi.uploadPhoto(file.uri, signal, await session);
      if (!signal.aborted) {
        onSave(next);
        setPrivacyDraft(undefined);
        setNotice('Đã cập nhật ảnh đại diện.');
      }
    } catch {
      if (!signal.aborted) { setPhotoFailed(true); setError('Chưa cập nhật được ảnh. Em kiểm tra ảnh và kết nối rồi thử lại nhé.'); }
    }
    finally { lock.current = false; if (!signal.aborted) setBusy(false); }
  };
  return <View testID="account-profile-editor" style={[s.card, IS_STUDENT_WEB && s.webCard]}>
    {IS_STUDENT_WEB && <Text accessibilityRole="header" aria-level={2} style={s.heading}>Thông tin học sinh</Text>}
    <View style={[s.identity, IS_STUDENT_WEB && s.webIdentity, compact && { gap: 12 }]}>
      <Pressable accessibilityRole="button" accessibilityLabel="Thay ảnh đại diện" accessibilityHint="Chọn một ảnh từ thiết bị của em" disabled={busy}
        onHoverIn={() => setAvatarHovered(true)} onHoverOut={() => setAvatarHovered(false)} onFocus={() => setAvatarFocused(true)} onBlur={() => setAvatarFocused(false)}
        onPress={() => { void choosePhoto(); }} style={[s.avatarRing, avatarFocused && s.avatarFocus]}>
        <StudentAvatar id={profile.avatar} photo={profile.avatarPhoto} size={compact ? 64 : 88} />
        <View pointerEvents="none" accessible={false} aria-hidden testID="avatar-change-overlay" style={[s.avatarOverlay, { opacity: avatarHovered || avatarFocused ? 1 : 0 }]}><Ionicons name="camera-outline" size={23} color="#FFF" accessible={false} /><Text style={s.avatarOverlayText}>Thay ảnh</Text></View>
        <View pointerEvents="none" style={s.cameraBadge}><Ionicons name="camera" size={14} color={COLORS.primaryDark} accessible={false} /></View>
      </Pressable>
      <View style={s.nameRow}>
        {IS_STUDENT_WEB ? <View style={s.nameCopy}>
          <Text accessibilityRole="header" numberOfLines={2} style={[s.name, compact && { fontSize: 18, lineHeight: 25 }]}>{profile.displayName}</Text>
          {profile.gradeLevel !== null && <Text style={s.hint}>Lớp {profile.gradeLevel}</Text>}
        </View> : <Text accessibilityRole="header" numberOfLines={2} style={[s.name, s.nameCopy, compact && { fontSize: 18, lineHeight: 25 }]}>{profile.displayName}</Text>}
        <Pressable accessibilityRole="button" accessibilityLabel="Đổi tên hiển thị" disabled={busy} onPress={() => { setEditingName(true); setError(''); }} style={[s.editName, IS_STUDENT_WEB && s.webEditName]}>
          <Ionicons name="create-outline" size={22} color={COLORS.primaryDark} accessible={false} />
        </Pressable>
      </View>
    </View>
    <View style={s.divider} />
    <View style={s.privacy}>
      <Ionicons accessible={false} aria-hidden name="shield-checkmark-outline" size={22} color={COLORS.primaryDark} />
      <Text accessibilityRole="header" nativeID={IS_STUDENT_WEB ? 'account-privacy-heading' : undefined}
        style={[IS_STUDENT_WEB ? s.heading : s.label, { flex: 1 }]}>Quyền riêng tư</Text>
    </View>
    <View style={[s.privacy, IS_STUDENT_WEB && s.webPrivacyRow]}><Text style={[s.body, { flex: 1 }]}>Tham gia bảng xếp hạng</Text><Switch accessibilityLabel="Tham gia bảng xếp hạng" disabled={busy || needsPrivacyReload} trackColor={IS_STUDENT_WEB ? webSwitchTrack : undefined}
      value={leaderboardVisible} onValueChange={checked => editPrivacy({
        leaderboardVisible: checked, ...(!checked && { leaderboardPhotoVisible: false }),
      })} /></View>
    <View style={[s.privacy, IS_STUDENT_WEB && s.webPrivacyRow]}><Text style={[s.body, { flex: 1 }]}>Ẩn tên trên bảng xếp hạng</Text><Switch accessibilityLabel="Ẩn tên trên bảng xếp hạng" disabled={busy || needsPrivacyReload} trackColor={IS_STUDENT_WEB ? webSwitchTrack : undefined}
      value={leaderboardNameHidden} onValueChange={checked => editPrivacy({ leaderboardNameHidden: checked })} /></View>
    {IS_STUDENT_WEB && <View style={[s.privacy, s.webPrivacyRow]}>
      <Text style={[s.body, { flex: 1 }]}>Hiện ảnh hồ sơ trên bảng xếp hạng</Text>
      <Switch accessibilityLabel="Hiện ảnh hồ sơ trên bảng xếp hạng" accessibilityHint="Cho học sinh khác xem ảnh hiện tại của em"
        disabled={busy || needsPrivacyReload || !leaderboardVisible || !profile.avatarPhoto} trackColor={webSwitchTrack}
        value={photoVisible} onValueChange={checked => editPrivacy({ leaderboardPhotoVisible: checked })} />
    </View>}
    <Text style={s.hint}>{Platform.OS === 'web' && !leaderboardVisible ? 'Em đang ẩn khỏi bảng xếp hạng. Thành tích vẫn được lưu trong tài khoản của em.'
      : leaderboardNameHidden ? `Bạn bè sẽ thấy bí danh ${profile.publicAlias || 'động vật của em'}.` : 'Bạn bè sẽ thấy tên hiển thị của em trên bảng xếp hạng.'} {photoVisible ? 'Học sinh khác có thể thấy ảnh này, kể cả khi em dùng bí danh.' :
        'Học sinh khác sẽ thấy biểu tượng đại diện của em.'}</Text>
    {needsPrivacyReload && <RecoveryNotice title="Cần tải lại quyền riêng tư"
      message="Quyền riêng tư hoặc ảnh đã thay đổi ở phiên khác. Em kiểm tra kết nối rồi tải lại hồ sơ để xem lựa chọn hiện tại nhé."
      actions={[{ label: 'Tải lại hồ sơ', onPress: () => { void reloadPrivacy(); }, disabled: busy }]} />}
    {error !== '' && !editingName && (IS_STUDENT_WEB ? <RecoveryNotice dialog messageId="account-editor-error"
      title={photoFailed ? 'Chưa đổi được ảnh đại diện' : 'Chưa lưu được thay đổi'} message={error}
      actions={photoFailed || dirty ? [{ label: photoFailed ? 'Chọn lại ảnh' : 'Thử lưu lại',
        onPress: () => { void (photoFailed ? choosePhoto() : save()); }, disabled: busy }] : []} />
      : <Text nativeID="account-editor-error" accessibilityRole="alert" style={s.error}>{error}</Text>)}
    {notice !== '' && <Text accessibilityLiveRegion="polite" style={s.success}>{notice}</Text>}
    <AppButton title="Lưu thay đổi" loading={busy} loadingTitle="Đang cập nhật…" disabled={!dirty} onPress={() => { void save(); }} />
    {!dirty && !notice && !needsPrivacyReload && <Text style={s.hint}>Thông tin của em đã được lưu.</Text>}
    {editingName ? <LessonSheet title="Đổi tên của em" compact onClose={() => { if (!busy) { setNameDraft(undefined); setEditingName(false); setError(''); } }}>
      <TextInput accessibilityLabel="Tên hiển thị" aria-describedby={error ? 'account-name-help account-name-error' : 'account-name-help'} aria-invalid={Boolean(error) && invalidName} autoFocus autoComplete="name" style={s.input} editable={!busy}
        value={nameInput} onChangeText={next => { setNameDraft(next); setError(''); setNotice(''); }} />
      <Text nativeID="account-name-help" style={s.hint}>Tên có thể gồm chữ và số, tối đa 50 từ.</Text>
      {error ? <Text nativeID="account-name-error" accessibilityRole="alert" style={s.error}>{error}</Text> : null}
      <AppButton title="Lưu tên" loading={busy} onPress={() => { void save(); }} />
    </LessonSheet> : null}
  </View>;
}

function PasswordCard({ available, googleLinked }: { available: boolean; googleLinked: boolean }) {
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
  return <View style={[s.card, IS_STUDENT_WEB && s.webCard]}>
    <View style={[s.sectionTitle, IS_STUDENT_WEB && s.webSectionTitle]}><Ionicons accessible={false} aria-hidden name="lock-closed-outline" size={22} color={COLORS.primaryDark} /><Text accessibilityRole="header" style={s.heading}>An toàn tài khoản</Text></View>
    {!available && IS_STUDENT_WEB && googleLinked ? <>
      <Text style={s.hint}>Dùng mã xác nhận gửi qua email để đặt hoặc đổi mật khẩu MathVisionKid.</Text>
      <AppButton title="Đổi mật khẩu MathVisionKid" variant="secondary"
        onPress={() => window.location.assign('/login?reset=password')} />
    </> : !available ? <Text style={s.body}>Em đang dùng tài khoản liên kết. Em đổi mật khẩu tại dịch vụ em dùng để đăng nhập nhé.</Text> : <>
      <Text style={s.hint}>Giữ mật khẩu cho riêng mình. Em có thể nhờ bố mẹ hỗ trợ.</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="Đổi mật khẩu" accessibilityState={{ expanded, disabled: busy }} aria-expanded={expanded} aria-controls="account-password-fields"
        disabled={busy} style={[s.passwordToggle, IS_STUDENT_WEB && s.webPasswordToggle]} onPress={() => { setExpanded(value => !value); setError(''); setNotice(''); }}><Text style={s.link}>Đổi mật khẩu</Text><Ionicons accessible={false} aria-hidden name={expanded ? 'chevron-up' : 'chevron-forward'} size={18} color={COLORS.primaryDark} /></Pressable>
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
  webScreen: { backgroundColor: STUDENT_WEB.background },
  webContent: { paddingTop: 18, maxWidth: 1170, gap: 12 },
  webColumns: { gap: 15 },
  webSide: { flex: 1, maxWidth: 410 },
  webCard: { borderColor: STUDENT_WEB.border, borderRadius: 17, padding: 17 },
  webSectionTitle: { backgroundColor: '#EBE0FC', padding: 10, borderRadius: 12 },
  webIdentity: { backgroundColor: STUDENT_WEB.soft, borderRadius: 18, padding: 16 },
  webEditName: { borderRadius: 12, backgroundColor: STUDENT_WEB.surface },
  webLogout: { borderColor: '#F3CBDD', borderWidth: 1, borderRadius: 15, backgroundColor: '#FFF0F6' },
  webPrivacyRow: { minHeight: 46, backgroundColor: STUDENT_WEB.background, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 6 },
  webChosen: { borderColor: STUDENT_WEB.primary, backgroundColor: STUDENT_WEB.soft },
  webPasswordToggle: { backgroundColor: STUDENT_WEB.soft, borderRadius: 12, paddingHorizontal: 12 },
  content: { padding: 20, paddingBottom: 36, width: '100%', maxWidth: 1040, alignSelf: 'center', gap: 12 },
  columns: { gap: 18 }, wide: { flexDirection: 'row', alignItems: 'flex-start' }, side: { gap: 18, minWidth: 0 }, editor: { minWidth: 0, gap: 14 }, editorWide: { flex: 1.5 },
  card: { padding: 22, borderRadius: 24, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, gap: 14 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: 18 }, avatarRing: { padding: 6, borderRadius: 54, backgroundColor: COLORS.primaryLight },
  avatarFocus: { outlineStyle: 'solid', outlineColor: COLORS.primaryDark, outlineWidth: 2, outlineOffset: 3 },
  avatarOverlay: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, borderRadius: 54, backgroundColor: '#171044A6', alignItems: 'center', justifyContent: 'center', gap: 3 },
  avatarOverlayText: { fontFamily: FONTS.bold, fontSize: 11, color: '#FFF' }, cameraBadge: { position: 'absolute', right: 1, bottom: 1, width: 25, height: 25, borderRadius: 13, backgroundColor: COLORS.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border },
  nameRow: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 4 }, nameCopy: { flex: 1, minWidth: 0 }, editName: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  name: { fontFamily: FONTS.extraBold, fontSize: 23, lineHeight: 30, color: COLORS.textPrimary }, heading: { fontFamily: FONTS.bold, fontSize: 18, color: COLORS.textPrimary, flexShrink: 1 },
  sectionTitle: { flexDirection: 'row', alignItems: 'center', gap: 10 }, label: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary }, hint: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 20, color: COLORS.textSecondary },
  input: { minHeight: 50, paddingHorizontal: 14, paddingVertical: 12, borderRadius: 14, borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.background, fontFamily: FONTS.semiBold, fontSize: 16, color: COLORS.textPrimary },
  avatars: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chosen: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  divider: { height: 1, backgroundColor: COLORS.border, marginVertical: 3 }, privacy: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  link: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark }, passwordToggle: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: COLORS.errorText }, success: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: '#176A50' },
});
