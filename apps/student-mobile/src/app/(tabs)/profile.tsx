import React, { useCallback, useContext, useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SHADOWS, IS_STUDENT_WEB } from '../../constants/theme';
import { loadLessons, SavedLesson } from '../../features/tutoring/learningHistory';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { recognitionDraftStore } from '../../features/recognition/state/recognitionDraftStore';

import { PersonalPageHeader, PersonalPanel, personalWebStyles as web } from '../../features/student-profile/PersonalWeb';
import { NotebookAside, ProfileIdentity, ProfileShortcuts, type NotebookTab, type NotebookCounts } from '../../features/student-profile/ProfileWeb';

export default function ProfileScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId || auth?.user?.email;
  return <ProfileContent key={owner ?? 'signed-out'} owner={owner} />;
}

export function ProfileContent({ owner, savedOnly = false, initialTab = 'saved' }: {
  owner?: string; savedOnly?: boolean; initialTab?: NotebookTab;
}) {
  const router = useRouter();
  const [pageWidth, setPageWidth] = useState(0), [tab, setTab] = useState<NotebookTab>(initialTab);
  const [lessons, setLessons] = useState<SavedLesson[]>([]), [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0), [loading, setLoading] = useState(true);
  const [menu, setMenu] = useState<SavedLesson | null>(null);
  const [oldestFirst, setOldestFirst] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true;
    setLessons([]); setError(false); setLoading(true); setMenu(null);
    loadLessons(owner).then(items => { if (active) setLessons(items); }).catch(() => { if (active) setError(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  // The retry key intentionally reruns this focused-screen request and cancels the previous one.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [owner, attempt]));
  const capture = () => { recognitionDraftStore.clearDraft(); router.push({ pathname: '/camera', params: { mode: 'MATH_TUTOR' } }); };
  const open = (lesson: SavedLesson) => router.push({ pathname: '/learning/math-guide', params: { problemText: lesson.problemText, workText: lesson.workText, lessonId: lesson.id, reflection: lesson.reflection } });
  const work = lessons.filter(item => item.workText.trim());
  const notes = lessons.filter(item => item.reflection.trim());
  const matching = tab === 'work' ? work : tab === 'notes' ? notes : lessons;
  const items = IS_STUDENT_WEB ? [...matching].sort((a, b) => oldestFirst ? a.timestamp - b.timestamp : b.timestamp - a.timestamp) : matching;
  const counts: NotebookCounts | undefined = error || loading ? undefined : { saved: lessons.length, work: work.length, notes: notes.length };
  const webWide = IS_STUDENT_WEB && pageWidth >= 840;
  const notebookGrid = webWide && pageWidth >= 1160 && !savedOnly;
  const games = <Pressable accessibilityRole="button" accessibilityLabel="Trò chơi rèn luyện cho em"
    onPress={() => router.push('/games')}
    style={({ pressed }) => [styles.games, pressed && styles.pressed]}>
    <Ionicons name="game-controller-outline" size={26} color={COLORS.primaryDark} accessible={false} />
    <Text style={styles.gamesTitle}>Trò chơi rèn luyện cho em</Text>
    <Ionicons name="chevron-forward" size={22} color={COLORS.primaryDark} accessible={false} />
  </Pressable>;
  const notebook = <>
      <View style={[styles.tabs, IS_STUDENT_WEB && styles.webTabs]}>{([['saved', 'Bài đã lưu'], ['work', 'Bài làm'], ['notes', 'Ghi chú']] as const).map(([value, label]) => <Pressable
        key={value} accessibilityRole={IS_STUDENT_WEB ? 'button' : 'tab'} accessibilityLabel={label}
        accessibilityState={IS_STUDENT_WEB ? undefined : { selected: tab === value }} aria-pressed={IS_STUDENT_WEB ? tab === value : undefined}
        onPress={() => setTab(value)} style={[styles.tab, tab === value && (IS_STUDENT_WEB ? styles.webSelected : styles.tabSelected)]}>
        <Text style={[styles.tabText, IS_STUDENT_WEB && styles.webSecondary, tab === value && styles.white]}>{label}</Text>
      </Pressable>)}</View>
      <View style={styles.listHeading}>
        <Text accessibilityRole={IS_STUDENT_WEB ? 'header' : undefined} style={styles.heading}>{tab === 'saved' ? 'Những bài học của em' : tab === 'work' ? 'Bài em đã viết' : 'Điều em ghi nhớ'}</Text>
        {(!IS_STUDENT_WEB || (!error && !loading)) && <Text style={[styles.count, IS_STUDENT_WEB && styles.webSecondary]}>{items.length} bài</Text>}
      </View>
      {IS_STUDENT_WEB && items.length > 1 && <Pressable accessibilityRole="button"
        accessibilityLabel={oldestFirst ? 'Sắp xếp bài mới nhất trước' : 'Sắp xếp bài cũ nhất trước'}
        onPress={() => setOldestFirst(value => !value)} style={styles.sortButton}>
        <Ionicons name="swap-vertical-outline" size={18} color={STUDENT_WEB.primary} accessible={false} />
        <Text style={styles.sortLabel}>{oldestFirst ? 'Cũ nhất trước' : 'Mới nhất trước'}</Text>
      </Pressable>}
      {tab === 'work' ? <Text style={[styles.caption, IS_STUDENT_WEB && styles.webSecondary]}>Nội dung em đã lưu bằng chữ. Ảnh riêng tư không lưu trong góc học tập.</Text> : null}
      {error ? <RecoveryNotice title="Chưa mở được bài đã lưu" message="Em thử lại nhé." actions={[
        { label: 'Thử lại', accessibilityLabel: 'Tải lại bài đã lưu', icon: 'refresh-outline', onPress: () => setAttempt(value => value + 1) },
      ]} /> : loading ? <ActivityIndicator accessibilityLabel="Đang mở bài đã lưu" color={COLORS.primary} />
        : items.length ? <View style={[styles.list, notebookGrid && styles.notebookGrid]}>{items.map((lesson, index) => <View key={lesson.id} style={[styles.lesson, IS_STUDENT_WEB && styles.webLesson, notebookGrid && styles.notebookTile]}>
          <Pressable accessibilityRole="button" accessibilityLabel={'Học tiếp: ' + (lesson.problemText || lesson.workText).slice(0, 60)}
            onPress={() => open(lesson)} style={({ pressed }) => [styles.lessonOpen, pressed && styles.pressed]}>
            <View style={[styles.thumbnail, IS_STUDENT_WEB && styles.webThumbnail,
              { backgroundColor: ['#F0EBF9', '#FFF3DF', '#EAF3FD'][index % 3] }]}
              accessible={false} importantForAccessibility="no-hide-descendants" aria-hidden>
              {IS_STUDENT_WEB ? <Ionicons name={tab === 'notes' ? 'document-text-outline' : tab === 'work' ? 'create-outline' : 'book-outline'}
                size={25} color={STUDENT_WEB.primary} accessible={false} /> : <>
                <View style={styles.paperLines}>{[0, 1, 2, 3, 4].map(line => <View key={line} style={styles.paperLine} />)}</View>
                <MathText style={styles.thumbnailText}>{(tab === 'notes' ? lesson.reflection : lesson.workText || lesson.problemText).slice(0, 65)}</MathText>
              </>}
            </View>
            <View style={styles.copy}><MathText style={styles.lessonTitle}>{lesson.problemText || lesson.workText}</MathText>
              <Text style={[styles.date, IS_STUDENT_WEB && styles.webSecondary]}>{new Date(lesson.timestamp).toLocaleDateString('vi-VN')} · {lesson.reviewedSteps} bước đã xem</Text>
              {tab === 'notes' ? <MathText style={styles.note}>{lesson.reflection}</MathText> : null}</View>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={'Tùy chọn bài ' + (index + 1)} onPress={() => setMenu(lesson)} style={styles.more}>
            <Ionicons name="ellipsis-vertical" size={20} color="#9C87C8" /></Pressable>
        </View>)}</View> : <View style={[styles.empty, IS_STUDENT_WEB && styles.webEmpty]}>
          <Image source={require('../../../assets/illustrations/approved/saved.webp')} style={styles.art} resizeMode="contain" accessible={false} />
          <Text style={styles.emptyTitle}>{tab === 'notes' ? 'Ghi lại cách nghĩ của em' : tab === 'work' ? 'Chưa có bài làm đã lưu' : 'Bài học hay, mình giữ lại nhé!'}</Text>
          <Text style={[styles.emptyText, IS_STUDENT_WEB && styles.webSecondary]}>{tab === 'notes' ? 'Khi lưu bài, em viết một điều vừa hiểu. Ghi chú sẽ xuất hiện ở đây.' : 'Chụp bài toán, cùng học từng bước rồi lưu lại để lần sau học tiếp.'}</Text>
          <AppButton title="Chụp bài toán" onPress={capture} />
        </View>}
  </>;
  return <SafeAreaView style={[styles.screen, IS_STUDENT_WEB && styles.webScreen]} onLayout={event => setPageWidth(event.nativeEvent.layout.width)} edges={['top']}>
    <ScrollView contentContainerStyle={[styles.content, pageWidth >= 768 && styles.contentWide, IS_STUDENT_WEB && styles.webContent]} showsVerticalScrollIndicator={false}>
      {IS_STUDENT_WEB ? <PersonalPageHeader title={savedOnly ? 'Bài đã lưu' : 'Góc học tập của em'}
        onBack={() => savedOnly ? router.replace('/(tabs)/profile') : router.replace('/(tabs)')}
        backLabel={savedOnly ? 'Về trang của em' : 'Về trang chủ'} onAccount={() => router.push('/account')} />
        : <StudentPageHeader compact title="Của em" onBack={() => router.replace('/(tabs)')} />}
      {IS_STUDENT_WEB ? <>
        {!savedOnly && <ProfileIdentity owner={owner} counts={counts} />}
        <View style={[web.columns, webWide && web.wide]}>
          <View style={[web.stack, webWide && web.mainGrow]}>
            <PersonalPanel title={savedOnly ? 'Sổ học tập' : 'Bài học đã lưu trên thiết bị'} icon="bookmark-outline">
              {notebook}
            </PersonalPanel>
            {tab === 'saved' && notes.length > 0 && <PersonalPanel title="Ghi chú gần đây" icon="document-text-outline">
              <View style={styles.noteGrid}>{notes.slice(0, 2).map(lesson => <Pressable key={lesson.id}
                accessibilityRole="button" accessibilityLabel={'Xem ghi chú của bài: ' + (lesson.problemText || lesson.workText).slice(0, 60)}
                onPress={() => setMenu(lesson)} style={({ pressed }) => [styles.notePreview, pressed && styles.pressed]}>
                <MathText style={styles.lessonTitle}>{(lesson.problemText || lesson.workText).slice(0, 100)}</MathText>
                <MathText style={styles.note}>{lesson.reflection.slice(0, 145)}</MathText>
                <Text style={[styles.date, styles.webSecondary]}>{new Date(lesson.timestamp).toLocaleDateString('vi-VN')}</Text>
              </Pressable>)}</View>
            </PersonalPanel>}
          </View>
          <View style={[web.stack, webWide && web.sideGrow]}>
            {!savedOnly && <ProfileShortcuts onCapture={capture} />}
            <NotebookAside counts={counts} savedOnly={savedOnly} wide={false} onCapture={capture} />
          </View>
        </View>
      </> : <>{games}{notebook}</>}
    </ScrollView>
    {menu ? <LessonSheet title="Bài học của em" onClose={() => setMenu(null)}>
      <MathText style={styles.emptyText}>{menu.problemText || menu.workText}</MathText>
      <AppButton title="Mở bài học" onPress={() => { const selected = menu; setMenu(null); open(selected); }} />
      {menu.reflection ? <><Text style={styles.heading}>Ghi chú của em</Text><MathText style={styles.emptyText}>{menu.reflection}</MathText></> : null}
      <AppButton title="Đóng" variant="secondary" onPress={() => setMenu(null)} />
    </LessonSheet> : null}
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#FAF9FF' },
  content: { flexGrow: 1, padding: 20, paddingTop: 12, paddingBottom: 108, width: '100%', maxWidth: 960, alignSelf: 'center', gap: 16 }, contentWide: { paddingBottom: 32 },
  tabs: { flexDirection: 'row', gap: 4, padding: 4, backgroundColor: '#F0EBFA', borderRadius: 15 },
  tab: { flex: 1, minHeight: 44, justifyContent: 'center', alignItems: 'center', borderRadius: 12 }, tabSelected: { backgroundColor: '#8951FF', boxShadow: '0 3px 7px #8B52FF25' },
  tabText: { fontFamily: FONTS.extraBold, fontSize: 13, color: '#7C6B9C' }, white: { color: '#FFF' },
  listHeading: { flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'space-between', marginTop: 7 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 17, color: COLORS.textPrimary }, count: { fontFamily: FONTS.bold, color: '#8E7DA8', fontSize: 12 },
  list: { gap: 12 }, lesson: { flexDirection: 'row', alignItems: 'center', borderRadius: 19, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#EEE8F7', padding: 9, boxShadow: '0 3px 12px #47307505' },
  lessonOpen: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 90 }, copy: { flex: 1, minWidth: 0 },
  thumbnail: { width: 74, height: 78, borderRadius: 13, padding: 8, overflow: 'hidden', justifyContent: 'center', borderWidth: 1, borderColor: '#E3DCED' },
  thumbnailText: { fontFamily: FONTS.regular, fontSize: 10, lineHeight: 17, color: '#786B8F', transform: [{ rotate: '-3deg' }] },
  paperLines: { ...StyleSheet.absoluteFill, paddingTop: 12, gap: 12 }, paperLine: { height: 1, backgroundColor: '#B4A7CC40' },
  lessonTitle: { fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 21, color: '#40335D' }, date: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 18, color: '#8C7E9E', marginTop: 5 },
  note: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: '#6D6085', marginTop: 6 }, more: { width: 44, height: 52, alignItems: 'center', justifyContent: 'center' },
  empty: { alignItems: 'center', padding: 24, borderRadius: 24, backgroundColor: '#F3EEFD', gap: 17 }, art: { width: 136, height: 132 },
  emptyTitle: { fontFamily: FONTS.extraBold, fontSize: 20, color: '#4F3973', textAlign: 'center' }, emptyText: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: '#7A6B92' },
  caption: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 19, color: '#8B7DA1' },
  games: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 64, padding: 20, borderRadius: 25, backgroundColor: COLORS.surface, ...SHADOWS.small },
  gamesTitle: { flex: 1, minWidth: 0, fontFamily: FONTS.bold, fontSize: 17, lineHeight: 26, color: COLORS.textPrimary },
  error: { fontFamily: FONTS.regular, fontSize: 14, color: COLORS.errorText }, pressed: { opacity: .7 },
  webScreen: { backgroundColor: STUDENT_WEB.background },
  webContent: { maxWidth: 1440, paddingTop: 16, paddingHorizontal: 18 },
  webTabs: { backgroundColor: STUDENT_WEB.soft, borderRadius: 14 },
  sortButton: { minHeight: 44, borderRadius: 14, borderWidth: 1, borderColor: STUDENT_WEB.border, paddingHorizontal: 10, gap: 7, flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-end' },
  sortLabel: { color: STUDENT_WEB.primary, fontFamily: FONTS.bold, fontSize: 13 },
  notebookGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  notebookTile: { width: '48.5%', flexGrow: 1, maxWidth: '50%' },
  noteGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  notePreview: { padding: 13, gap: 2, flexGrow: 1, flexBasis: 165, minWidth: 0, backgroundColor: '#FFF2D7', borderRadius: 13 },
  webSelected: { backgroundColor: '#713CF7', boxShadow: '0 3px 9px #6631DC4D' },
  webSecondary: { color: STUDENT_WEB.muted },
  webThumbnail: { width: 61, height: 61, alignItems: 'center', borderColor: 'transparent' },
  webLesson: { borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.background, boxShadow: 'none' },
  webEmpty: { borderWidth: 1, borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.background },
});
