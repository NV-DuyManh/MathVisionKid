import React, { useCallback, useContext, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, IS_STUDENT_WEB, WEB_DESIGN } from '../../constants/theme';
import { getCurriculumProblem, getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { recognitionDraftStore, logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { AuthContext } from '../../context/AuthContext';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { loadLessons } from '../../features/tutoring/learningHistory';
import { MathText } from '../../components/domain/MathText';
import { getLessonArtwork } from '../../features/lesson-artwork/lessonArtwork';

export default function LessonsScreen() {
  const insets = useSafeAreaInsets(), router = useRouter();
  const auth = useContext(AuthContext);
  const params = useLocalSearchParams<{ section?: string }>();
  const [pageWidth, setPageWidth] = useState(0);
  const [grade, setGrade] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [query, setQuery] = useState('');
  const [sectionSelection, setSectionSelection] = useState<{ source: string; value: string | null } | null>(null);
  const [collapsedSections, setCollapsedSections] = useState<string[]>([]);
  const [opened, setOpened] = useState<string | null>(null), [hint, setHint] = useState(false);
  const owner = auth?.user?.id || auth?.user?.userId;
  const [savedProgress, setSavedProgress] = useState<{ owner: string; ids: Set<string> } | null>(null);
  const [progressUnavailable, setProgressUnavailable] = useState(false);
  useFocusEffect(useCallback(() => {
    if (!IS_STUDENT_WEB || !owner) return;
    let active = true;
    setSavedProgress(null);
    setProgressUnavailable(false);
    void loadLessons(owner).then(lessons => {
      if (active) setSavedProgress({ owner, ids: new Set(lessons.flatMap(lesson => {
        const problem = getCurriculumProblem(lesson.problemText);
        return problem ? [problem.id] : [];
      })) });
    }).catch(() => { if (active) setProgressUnavailable(true); });
    return () => { active = false; };
  }, [owner]));
  const registeredGrade = Number(auth?.user?.gradeLevel ?? auth?.user?.grade);
  const hasRegisteredGrade = Number.isInteger(registeredGrade) && registeredGrade >= 1 && registeredGrade <= 5;
  const activeGrade = hasRegisteredGrade ? registeredGrade as 1 | 2 | 3 | 4 | 5 : grade;
  const problems = getProblemsByGrade(activeGrade);
  const savedIds = savedProgress?.owner === owner ? savedProgress?.ids : undefined;
  const savedCount = problems.filter(problem => savedIds?.has(problem.id)).length;
  const sections = [...new Set(problems.map(problem => problem.section))];
  const sectionSource = IS_STUDENT_WEB ? JSON.stringify([activeGrade, params.section]) : 'native';
  const requestedSection = IS_STUDENT_WEB && typeof params.section === 'string' && sections.includes(params.section) ? params.section : null;
  const section = sectionSelection?.source === sectionSource ? sectionSelection.value : requestedSection;
  const setSection = (value: string | null) => setSectionSelection({ source: sectionSource, value });
  const searchText = query.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLocaleLowerCase('vi');
  const visibleProblems = problems.filter(problem => {
    const searchable = IS_STUDENT_WEB
      ? `${problem.title} ${problem.topic} ${problem.problemText} ${problem.bookSeries} ${problem.difficulty}`
      : `${problem.title} ${problem.topic}`;
    return (!section || problem.section === section)
      && searchable.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLocaleLowerCase('vi').includes(searchText);
  }).sort((first, second) => IS_STUDENT_WEB ? first.order - second.order
    : (first.week ?? first.order) - (second.week ?? second.order) || first.order - second.order);
  const gradeControls = <View style={[styles.grades, IS_STUDENT_WEB && styles.webGrades]}>{([1, 2, 3, 4, 5] as const).map(item => <Pressable key={item} accessibilityRole="button"
      accessibilityLabel={'Chọn Lớp ' + item} accessibilityState={{ selected: grade === item }} aria-pressed={grade === item}
      onPress={() => { setGrade(item); setOpened(null); setHint(false); }}
      style={({ pressed }) => [styles.grade, grade === item && (IS_STUDENT_WEB ? styles.webGradeSelected : styles.gradeSelected), pressed && styles.pressed]}>
      <Text style={[styles.gradeText, IS_STUDENT_WEB && styles.webSecondary, grade === item && styles.white]}>Lớp {item}</Text>
    </Pressable>)}</View>;

  const filters = <View style={styles.filters}>
    <View style={styles.search}><Ionicons name="search-outline" size={20} color={COLORS.primaryDark} accessible={false} />
      <TextInput accessibilityLabel="Tìm bài học" value={query} onChangeText={setQuery} placeholder="Tìm bài học, chủ đề…" placeholderTextColor={COLORS.textMuted} style={styles.searchInput} />
      {query ? <Pressable accessibilityRole="button" accessibilityLabel="Xóa tìm kiếm bài học" onPress={() => setQuery('')} style={styles.clearSearch}><Ionicons name="close" size={18} color={COLORS.textSecondary} accessible={false} /></Pressable> : null}
    </View>
    <View style={styles.sectionFilters}>{[null, ...sections].map(item => <Pressable key={item ?? 'all'} accessibilityRole="button" accessibilityLabel={item ?? 'Tất cả chủ đề'} accessibilityState={{ selected: section === item }} aria-pressed={section === item}
      onPress={() => { setSection(item); setOpened(null); }} style={({ pressed }) => [styles.sectionFilter, section === item && styles.sectionFilterSelected, pressed && styles.pressed]}><Text style={[styles.filterLabel, section === item && styles.filterLabelSelected]}>{item ?? 'Tất cả'}</Text></Pressable>)}</View>
  </View>;
  const lessonList = <>
    <View style={styles.headingRow}><Text accessibilityRole="header" style={styles.heading}>Chương trình học của em</Text><Text accessibilityLiveRegion="polite" style={[styles.count, IS_STUDENT_WEB && styles.webSecondary]}>{visibleProblems.length} bài học</Text></View>
    {sections.filter(name => visibleProblems.some(problem => problem.section === name)).map(name => {
      const sectionProblems = visibleProblems.filter(problem => problem.section === name);
      const isExpanded = !IS_STUDENT_WEB || !!searchText || !collapsedSections.includes(name);
      const sectionId = `curriculum-section-${sections.indexOf(name)}`;
      return <View key={name} style={styles.sectionGroup}>
      {IS_STUDENT_WEB ? <Pressable accessibilityRole="button" accessibilityLabel={`Chủ đề ${name}`}
        accessibilityState={{ expanded: isExpanded }} aria-expanded={isExpanded} aria-controls={isExpanded ? sectionId : undefined}
        onPress={() => { setQuery(''); setCollapsedSections(current => isExpanded ? [...current.filter(item => item !== name), name] : current.filter(item => item !== name)); }}
        style={({ pressed }) => [styles.sectionToggle, pressed && styles.pressed]}>
        <View style={styles.copy}><Text accessibilityRole="header" style={styles.sectionHeading}>{name}</Text>
          <Text style={styles.description}>{sectionProblems.length} bài học{savedIds ? ` · ${sectionProblems.filter(problem => savedIds.has(problem.id)).length} bài đã lưu` : ''}</Text>
        </View>
        <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={20} color={COLORS.primaryDark} accessible={false} />
      </Pressable> : <Text accessibilityRole="header" style={styles.sectionHeading}>{name}</Text>}
      {isExpanded ? <View nativeID={sectionId} style={styles.list}>{sectionProblems.map(problem => <View key={problem.id} style={[styles.topic, IS_STUDENT_WEB ? styles.webTopic : { backgroundColor: getLessonArtwork(problem.id).color }]}>
      <Pressable accessibilityRole="button" accessibilityLabel={'Mở bài: ' + problem.title} accessibilityState={{ expanded: opened === problem.id }} aria-expanded={opened === problem.id} aria-controls={`lesson-detail-${problem.id}`}
        onPress={() => { setOpened(opened === problem.id ? null : problem.id); setHint(false); }} style={styles.topicRow}>
        <View style={[styles.topicIcon, { backgroundColor: getLessonArtwork(problem.id).color }]}>
          <Image source={getLessonArtwork(problem.id).source} style={styles.iconArt} resizeMode="contain" accessible={false} />
        </View>
        <View style={styles.copy}><Text style={[styles.topicTitle, IS_STUDENT_WEB && styles.webInk]}>{problem.title}</Text><Text style={[styles.description, IS_STUDENT_WEB && styles.webSecondary]}>{problem.week ? `Tuần ${problem.week} · ` : ''}{problem.topic}</Text>
          {IS_STUDENT_WEB && savedIds?.has(problem.id) ? <Text style={styles.savedLabel}>Đã lưu bài làm</Text> : null}
        </View>
        <Ionicons name={opened === problem.id ? 'chevron-up' : 'chevron-forward'} size={20} color={IS_STUDENT_WEB ? COLORS.primaryDark : '#7750E8'} accessible={false} />
      </Pressable>
      {opened === problem.id ? <View nativeID={`lesson-detail-${problem.id}`} style={styles.detail}>
        <View style={styles.tags}><Text style={styles.tag}>{problem.bookSeries}</Text><Text style={styles.tag}>{problem.difficulty}</Text></View>
        <MathText style={[styles.body, IS_STUDENT_WEB && styles.webProblem]}>{problem.problemText}</MathText>
        <Pressable accessibilityRole="button" accessibilityLabel={(hint ? 'Ẩn' : 'Xem') + ' gợi ý: ' + problem.title} accessibilityState={{ expanded: hint }} aria-expanded={hint} aria-controls={`lesson-hint-${problem.id}`}
          onPress={() => setHint(value => !value)} style={styles.hintButton}><Ionicons name="bulb-outline" size={19} color={COLORS.primaryDark} /><Text style={styles.link}>{hint ? 'Ẩn gợi ý' : 'Xem gợi ý cách giải'}</Text></Pressable>
        {hint ? <Text nativeID={`lesson-hint-${problem.id}`} style={[styles.body, IS_STUDENT_WEB && styles.webProblem]}>{problem.guidance}</Text> : null}
        <AppButton title="Học từng bước" accessibilityLabel={'Học từng bước: ' + problem.title} onPress={() => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } })} />
        <Pressable accessibilityRole="button" accessibilityLabel={'Chụp lời giải: ' + problem.title} onPress={() => {
          recognitionDraftStore.clearDraft(); logFlowDomain('ACQUIRE', 'MATH_TUTOR');
          router.push({ pathname: '/camera', params: { mode: 'MATH_TUTOR', problemText: problem.problemText } });
        }} style={styles.secondaryAction}><Ionicons name="camera-outline" size={19} color={COLORS.primaryDark} accessible={false} /><Text style={styles.link}>Chụp bài làm của em</Text></Pressable>
      </View> : null}
    </View>)}</View> : null}</View>;
    })}
    {visibleProblems.length === 0 ? <View style={styles.empty}><Ionicons name="search-outline" size={28} color={COLORS.primaryDark} accessible={false} /><Text style={styles.body}>Chưa tìm thấy bài phù hợp. Em thử tìm bằng từ khác nhé.</Text><AppButton title="Xem tất cả bài học" variant="secondary" onPress={() => { setQuery(''); setSection(null); }} /></View> : null}
  </>;
  const encouragement = <LinearGradient colors={['#EEE7FF', '#FAF7FF']} style={styles.encouragement}>
      <Image source={require('../../../assets/illustrations/robot-mascot.png')} style={styles.mascot} resizeMode="contain" accessible={false} />
      <View style={styles.copy}><Text style={styles.encouragementTitle}>Mỗi ngày, giỏi hơn một chút</Text><Text style={styles.body}>Chọn một bài, thử từng bước. Cùng khám phá Toán học nhé!</Text></View>
    </LinearGradient>;
  const webWide = IS_STUDENT_WEB && pageWidth >= 880;
  return <ScrollView style={[styles.screen, IS_STUDENT_WEB && styles.webScreen]} onLayout={event => setPageWidth(event.nativeEvent.layout.width)} showsVerticalScrollIndicator={false}
    contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: pageWidth >= 768 ? 32 : 108 }]}>
    <StudentPageHeader compact title="Bài học" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/account')} />
    {auth?.user && !hasRegisteredGrade ? <RecoveryNotice title="Chưa tải được lớp của em" message="Em tải lại hồ sơ để mở đúng chương trình học nhé."
      actions={[{ label: 'Tải lại hồ sơ', onPress: () => { void auth.refreshUser?.(); } }]} /> : IS_STUDENT_WEB ? (
      <View style={[styles.webLayout, webWide && styles.webLayoutWide]}>
        <View style={[styles.webStudyTools, webWide && styles.webStudyToolsWide]}>
          <Text accessibilityRole="header" style={styles.heading}>Bài học theo chủ đề</Text>
          {hasRegisteredGrade ? <Text style={styles.body}>Chọn một bài phù hợp với chương trình của em, rồi cùng học từng bước nhé.</Text> : gradeControls}
          {hasRegisteredGrade ? <View style={styles.progressCard}>
            <View style={styles.progressHeading}><Text style={styles.progressTitle}>Bài đã lưu của em</Text><Text accessibilityLiveRegion="polite" style={styles.progressCount}>{savedIds ? `${savedCount}/${problems.length}` : progressUnavailable ? '—' : '…'}</Text></View>
            <View accessibilityRole="progressbar" accessibilityLabel="Bài trong chương trình đã lưu trên thiết bị này" accessibilityState={{ busy: !savedIds && !progressUnavailable }} aria-busy={!savedIds && !progressUnavailable} accessibilityValue={{ min: 0, max: problems.length, ...(savedIds ? { now: savedCount } : {}) }} style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${savedCount / Math.max(1, problems.length) * 100}%` }]} />
            </View>
            <Text style={styles.progressNote}>{progressUnavailable ? 'Chưa tải được bài đã lưu. Em mở lại trang để thử nhé.' : 'Theo bài làm em đã lưu trên thiết bị này.'}</Text>
          </View> : null}
          {filters}
        </View>
        <View style={styles.webLessonList}>{lessonList}</View>
      </View>
    ) : <>{!hasRegisteredGrade && gradeControls}{filters}{lessonList}{encouragement}</>}
  </ScrollView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#FAF9FF' },
  content: { flexGrow: 1, paddingHorizontal: 20, width: '100%', maxWidth: 940, alignSelf: 'center' },
  grades: { flexDirection: 'row', gap: 6, marginBottom: 26, padding: 4, backgroundColor: '#F0EBFC', borderRadius: 18 },
  grade: { flex: 1, minHeight: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  gradeSelected: { backgroundColor: '#8554FF', boxShadow: '0 3px 8px #8452FF30' },
  gradeText: { fontFamily: FONTS.extraBold, fontSize: 13, color: '#71658E' }, white: { color: '#FFF' },
  headingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 15 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 18, color: COLORS.textPrimary }, count: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#786C94' },
  list: { gap: 12 }, topic: { borderRadius: 20, borderWidth: 1, borderColor: '#EEE7FB', overflow: 'hidden' },
  filters: { gap: 14, marginBottom: 24 }, search: { minHeight: 52, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border, borderRadius: 18 }, searchInput: { flex: 1, minWidth: 0, minHeight: 50, fontFamily: FONTS.regular, fontSize: 15, color: COLORS.textPrimary }, clearSearch: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  sectionFilters: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, sectionFilter: { minHeight: 44, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 16, backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border }, sectionFilterSelected: { backgroundColor: COLORS.primary, borderColor: COLORS.primary }, filterLabel: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.textSecondary }, filterLabelSelected: { color: '#FFFFFF' },
  sectionGroup: { marginBottom: 24, gap: 12 }, sectionHeading: { fontFamily: FONTS.extraBold, fontSize: 16, color: COLORS.textPrimary }, empty: { padding: 24, gap: 16, alignItems: 'center', backgroundColor: COLORS.surface, borderRadius: 20 },
  sectionToggle: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, paddingHorizontal: 6, borderRadius: 12 },
  topicRow: { flexDirection: 'row', alignItems: 'center', padding: 13, gap: 12, minHeight: 94 },
  topicIcon: { width: 54, height: 60, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }, iconArt: { width: 53, height: 54 },
  copy: { flex: 1, minWidth: 0 }, topicTitle: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23, color: '#2D2356' },
  description: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: '#786C94', marginTop: 3 },
  detail: { padding: 16, borderTopWidth: 1, borderColor: '#E7DFF5', gap: 14, backgroundColor: '#FFF' },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 }, tag: { fontFamily: FONTS.bold, fontSize: 11, color: '#76609B', backgroundColor: '#F3EEFC', padding: 6, borderRadius: 7 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: '#6B617F' },
  hintButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8 }, link: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  secondaryAction: { minHeight: 48, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  encouragement: { marginTop: 28, padding: 18, borderRadius: 23, flexDirection: 'row', alignItems: 'center', gap: 14, borderWidth: 1, borderColor: '#EDE3FB' },
  mascot: { width: 90, height: 110 }, encouragementTitle: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 23, color: '#49346D', marginBottom: 6 },
  pressed: { opacity: .7 },
  webScreen: { backgroundColor: WEB_DESIGN.colors.paper },
  webLayout: { gap: WEB_DESIGN.space.xl },
  webLayoutWide: { flexDirection: 'row', alignItems: 'flex-start' },
  webStudyTools: { gap: 10, minWidth: 0 },
  webStudyToolsWide: { width: 266 },
  webLessonList: { flex: 1, minWidth: 0 },
  webGrades: { gap: 4, marginBottom: 0, backgroundColor: WEB_DESIGN.colors.blueLight, borderRadius: WEB_DESIGN.radii.control },
  webGradeSelected: { backgroundColor: WEB_DESIGN.colors.blue },
  webInk: { color: WEB_DESIGN.colors.ink },
  webSecondary: { color: WEB_DESIGN.colors.mutedInk },
  webTopic: { backgroundColor: WEB_DESIGN.colors.white, borderColor: WEB_DESIGN.colors.paperLine },
  webProblem: { fontSize: WEB_DESIGN.typography.sizes.body, lineHeight: 25, color: WEB_DESIGN.colors.ink },
  progressCard: { gap: 10, padding: 15, borderRadius: 18, backgroundColor: '#F1EAFE', borderWidth: 1, borderColor: '#DFD1F8' },
  progressHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  progressTitle: { fontFamily: FONTS.extraBold, fontSize: 14, color: COLORS.textPrimary },
  progressCount: { fontFamily: FONTS.extraBold, fontSize: 14, color: COLORS.primaryDark },
  progressTrack: { height: 8, borderRadius: 5, overflow: 'hidden', backgroundColor: '#DDD1EF' },
  progressFill: { height: '100%', borderRadius: 5, backgroundColor: '#32B978' },
  progressNote: { fontFamily: FONTS.regular, fontSize: 11, lineHeight: 17, color: '#6B617F' },
  savedLabel: { fontFamily: FONTS.bold, fontSize: 12, color: '#217D51', marginTop: 5 },
});
