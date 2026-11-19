import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { PersonalLink, PersonalMetrics, PersonalPanel, personalWebStyles as web } from './PersonalWeb';
import { StudentAvatar } from './ProfileCards';
import { useStudentProfile } from './useStudentProfile';

export type NotebookTab = 'saved' | 'work' | 'notes';
export type NotebookCounts = Record<NotebookTab, number>;

export function ProfileIdentity({ owner, counts }: { owner?: string; counts?: NotebookCounts }) {
  const router = useRouter();
  const { value } = useStudentProfile(owner);
  const selectedTitle = value?.titles.find(title => title.id === value.selectedTitle);
  return <>
    <LinearGradient colors={['#FCFAFF', '#EDE3FD', '#D8C7F8']} start={{ x: 0, y: .3 }} end={{ x: 1, y: .8 }} style={styles.hero}>
      <View style={styles.avatar}><StudentAvatar id={value?.avatar ?? 'star'} photo={value?.avatarPhoto} size={64} /></View>
      <View style={styles.heroInfo}>
        <Text accessibilityRole="header" style={styles.heroName}>{value?.displayName || 'Hồ sơ học tập'}</Text>
        {value?.gradeLevel && <Text style={styles.heroSub}>Khối {value.gradeLevel}{selectedTitle ? ' · ' + selectedTitle.name : ''}</Text>}
        {!value?.gradeLevel && selectedTitle && <Text style={styles.heroSub}>{selectedTitle.name}</Text>}
      </View>
      <AppButton title="Chỉnh sửa hồ sơ" variant="secondary" onPress={() => router.push('/account')} />
    </LinearGradient>
    <PersonalMetrics metrics={[
      { label: 'Bài đã lưu', amount: counts?.saved, icon: 'bookmark-outline', tone: 'purple' },
      { label: 'Bài làm', amount: counts?.work, icon: 'create-outline', tone: 'blue' },
      { label: 'Sao đã nhận', amount: value?.stars, icon: 'star-outline', tone: 'yellow' },
      { label: 'Danh hiệu mở khóa', amount: value?.titles.filter(title => title.unlocked).length, icon: 'medal-outline', tone: 'green' },
    ]} />
  </>;
}

export function ProfileShortcuts({ onCapture }: { onCapture: () => void }) {
  const router = useRouter();
  return <PersonalPanel title="Góc học tập" icon="sparkles-outline">
    <PersonalLink label="Trò chơi luyện tập" accessibilityLabel="Trò chơi rèn luyện cho em" description="Ôn kiến thức qua trò chơi" icon="game-controller-outline" tone="yellow" onPress={() => router.push('/games')} />
    <PersonalLink label="Hỏi AI toán học" description="Chụp đề để nhận hướng dẫn" icon="camera-outline" tone="purple" onPress={onCapture} />
    <PersonalLink label="Xem tiến độ học tập" icon="stats-chart-outline" tone="green" onPress={() => router.push('/progress')} />
  </PersonalPanel>;
}

export function NotebookAside({ counts, savedOnly, wide, onCapture }: {
  counts?: NotebookCounts; savedOnly: boolean; wide: boolean; onCapture: () => void;
}) {
  const router = useRouter();
  return <View style={[web.stack, wide && web.sideGrow]}>
    {savedOnly && <View style={[web.panel, styles.coach]}>
      <Image source={require('../../../assets/illustrations/web/robot-mascot.webp')} style={styles.mascot} resizeMode="contain" accessible={false} aria-hidden />
      <Text accessibilityRole="header" style={web.heading}>Cùng em học bài mới</Text>
      <AppButton title="Chụp bài toán" accessibilityLabel="Mở máy ảnh để học bài mới" onPress={onCapture} />
    </View>}
    {savedOnly && counts && <PersonalPanel title="Sổ học tập của em">
      <Text style={web.body}>{counts.saved} bài đã lưu</Text>
      {counts.saved > 0 && [{ label: 'Bài có bài làm', count: counts.work }, { label: 'Bài có ghi chú', count: counts.notes }].map(({ label, count }) =>
        <View key={label} style={styles.archiveMetric}>
          <View style={styles.archiveMetricLabel}><Text style={web.body}>{label}</Text><Text style={web.body}>{count}/{counts.saved}</Text></View>
          <View accessibilityRole="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={counts.saved} aria-valuenow={count} style={styles.track}>
            <View style={[styles.bar, { width: (count * 100 / counts.saved) + '%' }]} />
          </View>
        </View>)}
    </PersonalPanel>}
    {!savedOnly && <PersonalPanel title="Hồ sơ và quyền riêng tư">
      <PersonalLink label="Cài đặt tài khoản" icon="settings-outline" tone="purple" onPress={() => router.push('/account')} />
      <PersonalLink label="Quyền riêng tư" icon="shield-checkmark-outline" tone="green" onPress={() => router.push({ pathname: '/account', params: { section: 'privacy' } })} />
    </PersonalPanel>}
  </View>;
}

const styles = StyleSheet.create({
  hero: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 13, padding: 14, borderRadius: 18, borderWidth: 1, borderColor: STUDENT_WEB.border },
  avatar: { padding: 4, borderRadius: 41, backgroundColor: '#FFFFFFB0' },
  heroInfo: { flexGrow: 1, flexBasis: 155, minWidth: 0, gap: 5 },
  heroName: { color: STUDENT_WEB.ink, fontFamily: FONTS.black, fontSize: 24, lineHeight: 29 },
  heroSub: { color: STUDENT_WEB.muted, fontFamily: FONTS.bold, fontSize: 14, lineHeight: 21 },
  archiveMetric: { gap: 4 },
  archiveMetricLabel: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  track: { height: 7, backgroundColor: '#E9DEF8', borderRadius: 5, overflow: 'hidden' },
  bar: { height: 7, backgroundColor: '#7445DB', borderRadius: 5 },
  coach: { backgroundColor: '#F0E9FF' },
  mascot: { width: 112, height: 112, alignSelf: 'center' },
});
