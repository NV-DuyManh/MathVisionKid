import React, { useState } from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { PersonalMetrics, PersonalPanel, personalWebStyles as web } from './PersonalWeb';
import { StudentAvatar } from './ProfileCards';
import { RankEmblem } from './RankEmblem';
import { useStudentProfile } from './useStudentProfile';
import { ProfileProgress } from './ProfileProgress';
import { ParentProfilePinDialog } from './ParentModePreview';
import { storeParentModeHandoff } from './parentModeHandoff';

export type NotebookTab = 'saved' | 'work' | 'notes';
export type NotebookCounts = Record<NotebookTab, number>;

export function ProfileIdentity({ owner, counts, wide, canOpenParentMode }: {
  owner?: string; counts?: NotebookCounts; wide: boolean; canOpenParentMode: boolean;
}) {
  const router = useRouter();
  const [showParentPin, setShowParentPin] = useState(false);
  const { value, failed, retry } = useStudentProfile(owner);
  return <>
    <LinearGradient colors={['#FCFAFF', '#EDE3FD', '#D8C7F8']} start={{ x: 0, y: .3 }} end={{ x: 1, y: .8 }}
      style={[styles.hero, wide && styles.heroWide]}>
      <View style={styles.identity}>
        <View style={styles.avatar}><StudentAvatar id={value?.avatar ?? 'star'} photo={value?.avatarPhoto} size={wide ? 64 : 52} /></View>
        <View style={styles.heroInfo}>
          <Text accessibilityRole="header" style={styles.heroName}>{value?.displayName || 'Hồ sơ học tập'}</Text>
          {value?.gradeLevel && <Text style={styles.heroSub}>Khối {value.gradeLevel}</Text>}
          {value && <View style={styles.titleBadge}><RankEmblem name={value.rank.name} size={30} /><Text style={styles.heroSub}>{value.rank.name}</Text></View>}
        </View>
      </View>
      <View style={styles.heroActions}>
        <AppButton title="Chỉnh sửa hồ sơ" variant="secondary" style={styles.heroAction}
          onPress={() => router.push('/account')} />
        {canOpenParentMode && <AppButton title="Góc phụ huynh" variant="secondary" style={styles.parentAction}
          icon={<Ionicons name="lock-closed-outline" size={18} color={STUDENT_WEB.primary} accessible={false} aria-hidden />}
          onPress={() => setShowParentPin(true)} />}
      </View>
    </LinearGradient>
    <PersonalMetrics metrics={[
      { label: 'Bài đã lưu', amount: counts?.saved, icon: 'bookmark-outline', tone: 'purple' },
      { label: 'Bài làm', amount: counts?.work, icon: 'create-outline', tone: 'blue' },
      { label: 'Sao đã nhận', amount: value?.stars, icon: 'medal-outline', tone: 'green' },
    ]} />
    <ProfileProgress value={value} failed={failed} retry={retry} wide={wide} />
    {showParentPin && canOpenParentMode && owner && <ParentProfilePinDialog key={owner} owner={owner} onExit={() => setShowParentPin(false)} onOpen={settings => {
      storeParentModeHandoff(owner, settings);
      setShowParentPin(false);
      router.push('/parent-mode');
    }} />}
  </>;
}

export function NotebookAside({ counts, onCapture }: { counts?: NotebookCounts; onCapture: () => void }) {
  return <View style={web.stack}>
    <View style={[web.panel, styles.coach]}>
      <Image source={require('../../../assets/illustrations/web/robot-mascot.webp')} style={styles.mascot} resizeMode="contain" accessible={false} aria-hidden />
      <Text accessibilityRole="header" style={web.heading}>Cùng em học bài mới</Text>
      <AppButton title="Chụp bài toán" accessibilityLabel="Mở máy ảnh để học bài mới" onPress={onCapture} />
    </View>
    {counts && <PersonalPanel title="Sổ học tập của em">
      <Text style={web.body}>{counts.saved} bài đã lưu</Text>
      {counts.saved > 0 && [{ label: 'Bài có bài làm', count: counts.work }, { label: 'Bài có ghi chú', count: counts.notes }].map(({ label, count }) =>
        <View key={label} style={styles.archiveMetric}>
          <View style={styles.archiveMetricLabel}><Text style={web.body}>{label}</Text><Text style={web.body}>{count}/{counts.saved}</Text></View>
          <View accessibilityRole="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={counts.saved} aria-valuenow={count} style={styles.track}>
            <View style={[styles.bar, { width: (count * 100 / counts.saved) + '%' }]} />
          </View>
        </View>)}
    </PersonalPanel>}
  </View>;
}

const styles = StyleSheet.create({
  hero: { gap: 14, padding: 14, borderRadius: 18, borderWidth: 1, borderColor: STUDENT_WEB.border },
  heroWide: { flexDirection: 'row', alignItems: 'center', padding: 18, gap: 18 },
  identity: { flexDirection: 'row', alignItems: 'center', gap: 12, flexGrow: 1, minWidth: 0 },
  avatar: { padding: 4, borderRadius: 41, backgroundColor: '#FFFFFFB0' },
  heroInfo: { flex: 1, minWidth: 0, gap: 5 },
  heroActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  heroAction: { paddingHorizontal: 12, flexGrow: 1, backgroundColor: STUDENT_WEB.surface },
  parentAction: { paddingHorizontal: 12, flexGrow: 1, backgroundColor: STUDENT_WEB.soft, borderColor: STUDENT_WEB.primary },
  heroName: { color: STUDENT_WEB.ink, fontFamily: FONTS.black, fontSize: 24, lineHeight: 29 },
  titleBadge: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 5 },
  heroSub: { color: STUDENT_WEB.muted, fontFamily: FONTS.bold, fontSize: 14, lineHeight: 21 },
  archiveMetric: { gap: 4 },
  archiveMetricLabel: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  track: { height: 7, backgroundColor: '#E9DEF8', borderRadius: 5, overflow: 'hidden' },
  bar: { height: 7, backgroundColor: '#7445DB', borderRadius: 5 },
  coach: { backgroundColor: '#F0E9FF' },
  mascot: { width: 112, height: 112, alignSelf: 'center' },
});
