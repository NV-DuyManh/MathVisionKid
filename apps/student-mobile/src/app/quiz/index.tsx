import React, { useCallback, useContext, useRef, useState } from 'react';
import { isCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, IS_STUDENT_WEB, WEB_DESIGN } from '../../constants/theme';
import { quizApi, Quiz, QuizGroup, QuizLibrary, quizError } from '../../features/quiz/quizApi';
import { quizStyles as s } from '../../features/quiz/quizStyles';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { CHALLENGE_COLORS as C, ChallengeWebStyles } from '../../components/ui/ChallengeVisuals';

const GROUPS: { id: QuizGroup; title: string }[] = [{ id: 'PENDING', title: 'Chờ làm' }, { id: 'IN_PROGRESS', title: 'Đang làm' }, { id: 'COMPLETED', title: 'Đã xong' }];
const EMPTY = {
  PENDING: { title: 'Chưa có câu đố mới', body: 'Hoàn tất một bài học hoặc phần nhận xét bài làm để mở một câu tương tự.', action: 'Chọn bài để học' },
  IN_PROGRESS: { title: 'Không có câu đang làm dở', body: 'Em có thể bắt đầu một câu mới trong mục Chờ làm.', action: 'Xem câu đang chờ' },
  COMPLETED: { title: 'Cùng tạo thành tích đầu tiên!', body: 'Những câu em làm xong sẽ được giữ ở đây để xem lại.', action: 'Xem câu đang chờ' },
};
export default function QuizLibraryScreen() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId;
  return owner ? <Library key={owner} /> : null;
}
function Library() {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const { width } = useWindowDimensions();
  const [pageWidth, setPageWidth] = useState(0);
  const compactWeb = isCompactStudentWeb(width);
  const showWorkspace = IS_STUDENT_WEB && !compactWeb;
  const desktop = showWorkspace && pageWidth >= 920;
  const Columns = showWorkspace ? View : React.Fragment;
  const [group, setGroup] = useState<QuizGroup>('PENDING'), [result, setResult] = useState<QuizLibrary | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [retry, setRetry] = useState(0);
  const [totalStars, setTotalStars] = useState<number | null>(null);
  const [unfinishedCount, setUnfinishedCount] = useState<number | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const chooseInitialGroup = useRef(true);
  useFocusEffect(useCallback(() => {
    void retry;
    active.current = true;
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setError(''); setResult(null); setTotalStars(null); setUnfinishedCount(null);
    let firstPage: QuizLibrary | null = null, unfinished: number | null = null;
    const openUnfinished = () => {
      if (!chooseInitialGroup.current || !firstPage || unfinished === null || abort.signal.aborted || !active.current) return;
      chooseInitialGroup.current = false;
      if (group === 'PENDING' && firstPage.totalElements === 0 && unfinished > 0) setGroup('IN_PROGRESS');
    };
    void quizApi.list(group, 0, abort.signal).then(data => { if (active.current && !abort.signal.aborted) { setResult(data); firstPage = data; openUnfinished(); } })
      .catch(failure => { if (active.current && !abort.signal.aborted) setError(quizError(failure)); })
      .finally(() => { if (active.current && !abort.signal.aborted) { setBusy(false); controller.current = null; } });
    void quizApi.count(abort.signal).then(data => {
      if (active.current && !abort.signal.aborted) {
        setTotalStars(IS_STUDENT_WEB ? data.verifiedStars ?? null : data.totalStars);
        setUnfinishedCount(data.pendingCount); unfinished = data.pendingCount; openUnfinished();
      }
    }).catch(() => {});
    return () => { active.current = false; abort.abort(); controller.current?.abort(); controller.current = null; };
  }, [group, retry]));
  const more = async () => {
    if (!result || busy || controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      const next = await quizApi.list(group, result.page + 1, abort.signal);
      if (active.current && !abort.signal.aborted) setResult(previous => previous ? { ...next, items: [...previous.items, ...next.items] } : next);
    } catch (failure) { if (active.current && !abort.signal.aborted) setError(quizError(failure)); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  };
  const selectGroup = (next: QuizGroup) => { chooseInitialGroup.current = false; setGroup(next); };
  const statusLabel = (quiz: Quiz) => {
    if (quiz.status === 'COMPLETED') {
      const unit = IS_STUDENT_WEB ? 'điểm luyện tập' : 'sao';
      if (quiz.replayMode === 'PRACTICE') return `Đã ôn lại · Không chấm điểm · Kỷ lục ${quiz.stars} ${unit}`;
      if (quiz.completedWithSolution) {
        return `Hoàn thành cùng hướng dẫn · Kỷ lục ${quiz.stars} ${unit}`;
      }
      return `Đã hoàn thành · ${quiz.stars} ${unit}`;
    }
    return quiz.status === 'IN_PROGRESS' ? 'Đang làm dở' : 'Sẵn sàng để thử';
  };
  const empty = EMPTY[group];
  const grade = Number(auth?.user?.gradeLevel);
  const topics = IS_STUDENT_WEB && Number.isInteger(grade) && grade >= 1 && grade <= 5
    ? [...new Set(getProblemsByGrade(grade as 1 | 2 | 3 | 4 | 5).map(problem => problem.section))].slice(0, 3) : [];
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}
    onLayout={showWorkspace ? event => setPageWidth(event.nativeEvent.layout.width) : undefined}>
    <ChallengeWebStyles />
    {!showWorkspace && <AppHeader title="Câu đố của em" showBack rightIcon="help-circle-outline" onRightPress={() => setShowHelp(value => !value)}
      rightAccessibilityLabel="Câu đố hoạt động thế nào?" rightAccessibilityState={{ expanded: showHelp }} />}
    <ScrollView style={s.scroll} contentContainerStyle={[l.content, showWorkspace && l.webContent]} {...(IS_STUDENT_WEB ? { dataSet: { challenge: 'true' } } : {})}>
      <Columns {...(showWorkspace ? { style: desktop ? l.webLayout : undefined } : {})}>
      <Columns {...(showWorkspace ? { style: [l.column, desktop && l.webMain] } : {})}>
      {showHelp ? <View style={l.help}><Text accessibilityRole="header" style={l.topic}>Luyện thêm từ bài em đã học</Text>
        <Text style={l.body}>Hoàn tất bài học hoặc phần nhận xét, rồi chọn làm ngay hay để sau. Câu đố có dữ kiện mới để em thử lại cách làm.</Text>
        <Text style={l.body}>Chỉ những dạng bài được hỗ trợ mới có câu đố. Bài đang dở và kết quả sẽ được lưu trong tài khoản của em.</Text></View> : null}
      {showWorkspace ? <View style={l.webHero}>
        {desktop && <View style={l.webHeroBadge}><Ionicons name="clipboard" size={44} color="#FFD657" accessible={false} /></View>}
        <View style={l.introCopy}>
          <Text accessibilityRole="header" style={l.webHeroTitle}>Câu đố của em</Text>
          <Text style={l.webHeroCopy}>Ôn lại cách làm từ những bài em đã học.</Text>
          <Pressable accessibilityRole="button" style={l.webHeroAction} onPress={() => {
            const next = result?.items.find(item => item.status !== 'COMPLETED');
            if (next) router.push(`/quiz/${next.quizId}` as never);
            else if (group !== 'PENDING') selectGroup('PENDING');
            else router.push('/(tabs)/lessons');
          }} disabled={busy && !result} accessibilityState={{ disabled: busy && !result }}>
            <Ionicons name="play" size={15} color={STUDENT_WEB.ink} accessible={false} /><Text style={l.webHeroActionText}>Thử sức ngay</Text>
          </Pressable>
        </View>
        <AppIllustration source={require('../../../assets/illustrations/web/robot-mascot.webp')} style={l.heroMascot} accessible={false} />
        {showWorkspace && <Pressable accessibilityRole="button" accessibilityLabel="Câu đố hoạt động thế nào?" accessibilityState={{ expanded: showHelp }}
          onPress={() => setShowHelp(value => !value)} style={l.webHeroHelp}><Ionicons name="help-circle-outline" size={23} color="#FFF" accessible={false} /></Pressable>}
      </View> : <View style={[l.intro, compactWeb && l.compactIntro]}>
        <View style={l.introCopy}><Text accessibilityRole="header" style={l.heading}>Cùng thử sức</Text><Text style={l.body}>Ôn lại từ những bài em đã học.</Text>
          {totalStars !== null && totalStars > 0 ? <View style={l.starPill}><Ionicons name="star" size={13} color="#936315" accessible={false} /><Text style={l.starText}>{totalStars} sao đã nhận</Text></View> : null}</View>
        <Image source={require('../../../assets/illustrations/robot-mascot.png')} style={l.introMascot} accessible={false} />
      </View>}
      <View style={[l.groups, IS_STUDENT_WEB && l.webGroups]}>{GROUPS.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={item.title}
        accessibilityState={{ selected: group === item.id }} onPress={() => selectGroup(item.id)}
        style={({ pressed }) => [l.group, showWorkspace && l.webGroup, group === item.id && (showWorkspace ? l.webSelected : l.selected), pressed && l.pressed]}>
          {showWorkspace && <Ionicons name={item.id === 'PENDING' ? 'hourglass-outline' : item.id === 'IN_PROGRESS' ? 'play-outline' : 'checkmark-circle-outline'}
            size={17} color={group === item.id ? '#FFF' : STUDENT_WEB.primary} accessible={false} />}
          <Text style={[l.groupText, group === item.id && (showWorkspace ? l.webSelectedText : l.selectedText)]}>{item.title}{showWorkspace && group === item.id && result ? ` (${result.totalElements})` : ''}</Text>
        </Pressable>)}</View>
      {showWorkspace && <View style={l.listHeading}><Ionicons name="list-outline" color={STUDENT_WEB.primary} size={21} accessible={false} /><Text accessibilityRole="header" style={l.topic}>Danh sách câu đố</Text></View>}
      {busy && !result ? <View style={l.loading} accessibilityRole="progressbar" accessibilityLabel="Đang tải câu đố" accessibilityState={{ busy: true }}>
        <ActivityIndicator color={COLORS.primaryDark} /><Text style={l.body}>Đang tải câu đố…</Text></View> : null}
      {error ? IS_STUDENT_WEB ? <RecoveryNotice dialog
        title={result ? 'Chưa tải được các câu đố tiếp theo' : 'Chưa mở được danh sách câu đố'} message={error}
        actions={[
          { label: result ? 'Tải thêm lần nữa' : 'Tải lại danh sách', onPress: () => result ? void more() : setRetry(value => value + 1), disabled: busy },
          ...(!result ? [{ label: 'Về trang chủ', onPress: () => router.replace('/(tabs)' as never) }] : []),
        ]} /> : <View style={l.help}><Text accessibilityRole="alert" style={l.error}>{error}</Text><AppButton title="Thử lại" variant="secondary" onPress={() => result ? void more() : setRetry(value => value + 1)} /></View> : null}
      {result && !result.items.length ? <View style={[l.empty, showWorkspace && l.webEmpty]}>
        <View style={l.emptyArt}><Image source={require('../../../assets/illustrations/robot-mascot.png')} style={l.emptyMascot} accessible={false} /></View>
        <Text accessibilityRole="header" style={l.emptyTitle}>{empty.title}</Text><Text style={l.emptyBody}>{empty.body}</Text>
        <View style={l.emptyAction}><AppButton title={empty.action} variant="secondary" onPress={() => group === 'PENDING' ? router.replace('/(tabs)/lessons') : selectGroup('PENDING')} /></View>
      </View> : null}
      {result?.items.map(quiz => <Pressable key={quiz.quizId} accessibilityRole="button"
        accessibilityLabel={`${quiz.topicName}. ${quiz.questionText}. ${statusLabel(quiz)}. ${quiz.status === 'COMPLETED' ? 'Xem lại' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục' : 'Bắt đầu'}`}
        onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} style={({ pressed }) => [l.card, IS_STUDENT_WEB && l.webCard, { borderLeftColor: quiz.status === 'COMPLETED' ? C.green : quiz.status === 'IN_PROGRESS' ? '#BA781E' : C.primary }, pressed && l.pressed]}>
        <View style={l.cardHeading}><View style={[l.topicIcon,{backgroundColor: quiz.status === 'COMPLETED' ? '#E5F5ED' : quiz.status === 'IN_PROGRESS' ? '#FFF3D6' : C.lavender}]}><Ionicons name={quiz.status === 'COMPLETED' ? 'checkmark-done' : quiz.status === 'IN_PROGRESS' ? 'hourglass-outline' : 'flag-outline'} size={23} color={quiz.status === 'COMPLETED' ? C.green : C.deepPurple} accessible={false} /></View>
          <View style={l.cardTopic}><Text style={l.grade}>LỚP {quiz.gradeLevel} · {quiz.status === 'COMPLETED' ? 'ĐÃ HOÀN THÀNH' : quiz.status === 'IN_PROGRESS' ? 'ĐANG LÀM' : 'CHỜ KHÁM PHÁ'}</Text><Text style={l.topic}>{quiz.topicName}</Text></View></View>
        <MathText style={l.question}>{quiz.questionText}</MathText>
        <View style={l.cardFooter}><Text style={l.metadata}>{statusLabel(quiz)}</Text><View style={l.action}>
          <Text style={l.actionText}>{quiz.status === 'COMPLETED' ? 'Xem lại' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục' : 'Bắt đầu'}</Text><Ionicons name="arrow-forward" size={15} color={COLORS.primaryDark} accessible={false} /></View></View>
      </Pressable>)}
      {result && result.page + 1 < result.totalPages ? <AppButton title="Xem thêm câu đố" loadingTitle="Đang tải thêm câu đố…" variant="secondary" disabled={busy} loading={busy} onPress={() => void more()} /> : null}
      </Columns>
      {showWorkspace && <View style={[l.column, desktop && l.webAside]}>
        <View style={l.dashboardCard}>
          <Text accessibilityRole="header" style={l.topic}>Tiến độ câu đố</Text>
          {unfinishedCount !== null && <View style={l.dashboardMetric}>
            <Text style={l.dashboardNumber}>{unfinishedCount}</Text><Text style={l.body}>Câu chưa hoàn thành</Text>
          </View>}
          {unfinishedCount === null && totalStars === null && <Text style={l.body}>{busy ? 'Đang tải tiến độ…' : 'Chưa xem được tiến độ lúc này.'}</Text>}
        </View>
        <View style={l.dashboardCard}>
          <Text accessibilityRole="header" style={l.topic}>Sao đã nhận được</Text>
          {totalStars !== null && <View style={[l.dashboardMetric, l.starsMetric]}>
            <Ionicons name="star" size={22} color="#945F08" accessible={false} />
            <Text style={l.dashboardNumber}>{totalStars}</Text><Text style={l.body}>sao từ câu đố</Text>
          </View>}
          <AppButton title="Xem thành tích học tập" variant="secondary" onPress={() => router.push('/(tabs)/achievements')} />
        </View>
        {topics.length > 0 && <View style={l.dashboardCard}>
          <Text accessibilityRole="header" style={l.topic}>Gợi ý chủ đề luyện tập</Text>
          {topics.map(section => <Pressable key={section} accessibilityRole="button" style={l.suggestedTopic}
            onPress={() => router.push({ pathname: '/(tabs)/lessons', params: { section } })}>
            <Ionicons name="book-outline" size={18} color={STUDENT_WEB.primary} accessible={false} />
            <Text style={l.suggestedTitle}>{section}</Text>
            <Ionicons name="chevron-forward" size={17} color={STUDENT_WEB.primary} accessible={false} />
          </Pressable>)}
        </View>}
      </View>}
      </Columns>
    </ScrollView>
  </SafeAreaView>;
}

const l = StyleSheet.create({
  content: { flexGrow: 1, width: '100%', maxWidth: 840, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 6, paddingBottom: 24, gap: 16 },
  webContent: { maxWidth: '100%', paddingTop: 18, paddingHorizontal: 22 },
  webLayout: { flexDirection: 'row', gap: 20, alignItems: 'flex-start' },
  column: { minWidth: 0, gap: 16, marginBottom: 16 },
  webMain: { flex: 1, minWidth: 0 },
  webAside: { width: 292, flexShrink: 0 },
  webHero: { flexDirection: 'row', alignItems: 'center', gap: 14, minHeight: 176, borderRadius: 24, padding: 22, overflow: 'hidden', backgroundColor: C.ink },
  heroMascot: { width: '30%', maxWidth: 180, height: 134 },
  webHeroBadge: { width: 75, height: 79, borderRadius: 23, justifyContent: 'center', alignItems: 'center', backgroundColor: '#FFFFFF20', transform: [{ rotate: '-8deg' }] },
  webHeroHelp: { position: 'absolute', right: 7, top: 4, width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  webHeroTitle: { color: '#FFD95E', fontFamily: FONTS.black, fontSize: 30, lineHeight: 36 },
  webGroup: { flexDirection: 'row', gap: 5, borderRadius: 22 },
  webSelected: { backgroundColor: C.deepPurple, borderColor: C.deepPurple },
  webSelectedText: { color: '#FFFFFF', fontFamily: FONTS.extraBold },
  listHeading: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  webEmpty: { minHeight: 190, paddingVertical: 14, borderWidth: 1, borderColor: STUDENT_WEB.border, borderRadius: 17, backgroundColor: STUDENT_WEB.surface },
  webHeroCopy: { color: '#F5EEFF', fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21 },
  webHeroAction: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', justifyContent: 'center', minHeight: 44, backgroundColor: STUDENT_WEB.gold, marginTop: 7, borderRadius: 12, paddingHorizontal: 15, gap: 7 },
  webHeroActionText: { color: STUDENT_WEB.ink, fontFamily: FONTS.extraBold, fontSize: 14 },
  dashboardCard: { borderRadius: 20, borderWidth: 1, borderColor: STUDENT_WEB.border, backgroundColor: STUDENT_WEB.surface, gap: 12, padding: 18 },
  dashboardMetric: { flexDirection: 'row', alignItems: 'baseline', gap: 9 },
  dashboardNumber: { color: STUDENT_WEB.primary, fontFamily: FONTS.black, fontSize: 23 },
  starsMetric: { alignItems: 'center', backgroundColor: '#FFF4D3', minHeight: 53, borderRadius: 14, paddingHorizontal: 12 },
  suggestedTopic: { flexDirection: 'row', alignItems: 'center', gap: 10, borderRadius: 14, paddingHorizontal: 11, minHeight: 45, backgroundColor: STUDENT_WEB.soft },
  suggestedTitle: { flex: 1, minWidth: 0, color: STUDENT_WEB.ink, fontFamily: FONTS.bold, fontSize: 13 },
  compactIntro: { paddingHorizontal: 16, borderWidth: 1, borderColor: COLORS.border, borderRadius: WEB_DESIGN.radii.notebook, backgroundColor: COLORS.surface },
  intro: { flexDirection: 'row', alignItems: 'center', gap: 16, paddingVertical: 8 },
  webGroups: { backgroundColor: STUDENT_WEB.soft, borderRadius: WEB_DESIGN.radii.control },
  webCard: { borderColor: C.line, borderRadius: 20 },
  introCopy: { flex: 1, minWidth: 0, gap: 5 }, introMascot: { width: 72, height: 78, resizeMode: 'contain' },
  heading: { fontFamily: FONTS.extraBold, fontSize: 21, lineHeight: 29, color: COLORS.textPrimary },
  body: { fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: COLORS.textSecondary },
  starPill: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#FFF4D9', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  starText: { fontFamily: FONTS.bold, fontSize: 11, lineHeight: 17, color: '#805A17' },
  groups: { flexDirection: 'row', gap: 4, padding: 4, borderRadius: 17, backgroundColor: '#EEE8F8' },
  group: { flex: 1, minWidth: 0, minHeight: 44, paddingVertical: 10, paddingHorizontal: 4, alignItems: 'center', justifyContent: 'center', borderRadius: 13, borderWidth: 1, borderColor: 'transparent' },
  groupText: { fontFamily: FONTS.semiBold, color: COLORS.textSecondary, fontSize: 13, lineHeight: 19, textAlign: 'center' },
  selected: { backgroundColor: '#FFF', borderColor: '#DFD5F2' }, selectedText: { fontFamily: FONTS.extraBold, color: COLORS.primaryDark },
  pressed: { opacity: .72 }, loading: { paddingVertical: 24, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  help: { padding: 16, gap: 10, borderRadius: 18, backgroundColor: '#F0EAFB', borderWidth: 1, borderColor: '#E4DCF2' },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 22, color: '#913E27' },
  empty: { flex: 1, minHeight: 300, alignItems: 'center', justifyContent: 'center', gap: 10, paddingHorizontal: 12, paddingVertical: 28 },
  emptyArt: { width: 104, height: 104, backgroundColor: '#EEE8FC', borderRadius: 36, alignItems: 'center', justifyContent: 'center', marginBottom: 4 },
  emptyMascot: { width: 90, height: 96, resizeMode: 'contain' },
  emptyTitle: { fontFamily: FONTS.extraBold, fontSize: 18, lineHeight: 26, color: COLORS.textPrimary, textAlign: 'center' },
  emptyBody: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: COLORS.textSecondary, textAlign: 'center', maxWidth: 330 },
  emptyAction: { width: '100%', maxWidth: 260, paddingTop: 10 },
  card: { padding: 20, gap: 16, borderRadius: 21, backgroundColor: '#FFF', borderWidth: 1, borderLeftWidth: 5, borderColor: C.line },
  cardHeading: { flexDirection: 'row', alignItems: 'center', gap: 12 }, topicIcon: { width: 46, height: 46, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: C.lavender },
  cardTopic: { flex: 1, minWidth: 0, gap: 4 }, grade: { fontFamily: FONTS.extraBold, fontSize: 10, lineHeight: 16, letterSpacing: .6, color: C.deepPurple },
  topic: { flexShrink: 1, fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 21, color: COLORS.textPrimary },
  question: { fontFamily: FONTS.semiBold, fontSize: 16, lineHeight: 26, color: C.ink },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', borderTopWidth: 1, borderTopColor: '#F1ECF7', paddingTop: 10 },
  metadata: { flexShrink: 1, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 19, color: COLORS.textSecondary },
  action: { flexDirection: 'row', alignItems: 'center', gap: 6, minHeight: 44, paddingVertical: 8, paddingHorizontal: 14, borderRadius: 12, backgroundColor: C.lavender },
  actionText: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 18, color: COLORS.primaryDark },
});
