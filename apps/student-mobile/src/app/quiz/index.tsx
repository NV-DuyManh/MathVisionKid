import React, { useCallback, useContext, useRef, useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useRouter } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { quizApi, Quiz, QuizGroup, QuizLibrary, quizError } from '../../features/quiz/quizApi';
import { quizStyles as s } from '../../features/quiz/quizStyles';

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
  const [group, setGroup] = useState<QuizGroup>('PENDING'), [result, setResult] = useState<QuizLibrary | null>(null);
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [retry, setRetry] = useState(0);
  const [totalStars, setTotalStars] = useState<number | null>(null);
  const [showHelp, setShowHelp] = useState(false);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const chooseInitialGroup = useRef(true);
  useFocusEffect(useCallback(() => {
    void retry;
    active.current = true;
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setError(''); setResult(null); setTotalStars(null);
    let firstPage: QuizLibrary | null = null, unfinished: number | null = null;
    const openUnfinished = () => {
      if (!chooseInitialGroup.current || !firstPage || unfinished === null || abort.signal.aborted || !active.current) return;
      chooseInitialGroup.current = false;
      if (group === 'PENDING' && firstPage.totalElements === 0 && unfinished > 0) setGroup('IN_PROGRESS');
    };
    void quizApi.list(group, 0, abort.signal).then(data => { if (active.current && !abort.signal.aborted) { setResult(data); firstPage = data; openUnfinished(); } })
      .catch(failure => { if (active.current && !abort.signal.aborted) setError(quizError(failure)); })
      .finally(() => { if (active.current && !abort.signal.aborted) { setBusy(false); controller.current = null; } });
    void quizApi.count(abort.signal).then(data => { if (active.current && !abort.signal.aborted) { setTotalStars(data.totalStars); unfinished = data.pendingCount; openUnfinished(); } }).catch(() => {});
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
      if (quiz.replayMode === 'PRACTICE') return `Đã ôn lại · Không chấm điểm · Kỷ lục ${quiz.stars} sao`;
      if (quiz.completedWithSolution) {
        return `Hoàn thành cùng hướng dẫn · Kỷ lục ${quiz.stars} sao`;
      }
      return `Đã hoàn thành · ${quiz.stars} sao`;
    }
    return quiz.status === 'IN_PROGRESS' ? 'Đang làm dở' : 'Sẵn sàng để thử';
  };
  const empty = EMPTY[group];
  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Câu đố của em" showBack rightIcon="help-circle-outline" onRightPress={() => setShowHelp(value => !value)}
      rightAccessibilityLabel="Câu đố hoạt động thế nào?" rightAccessibilityState={{ expanded: showHelp }} />
    <ScrollView style={s.scroll} contentContainerStyle={l.content}>
      {showHelp ? <View style={l.help}><Text accessibilityRole="header" style={l.topic}>Luyện thêm từ bài em đã học</Text>
        <Text style={l.body}>Hoàn tất bài học hoặc phần nhận xét, rồi chọn làm ngay hay để sau. Câu đố có dữ kiện mới để em thử lại cách làm.</Text>
        <Text style={l.body}>Chỉ những dạng bài được hỗ trợ mới có câu đố. Bài đang dở và kết quả sẽ được lưu trong tài khoản của em.</Text></View> : null}
      <View style={l.intro}>
        <View style={l.introCopy}><Text accessibilityRole="header" style={l.heading}>Cùng Sao thử sức</Text><Text style={l.body}>Ôn lại từ những bài em đã học.</Text>
          {totalStars !== null && totalStars > 0 ? <View style={l.starPill}><Ionicons name="star" size={13} color="#936315" accessible={false} /><Text style={l.starText}>{totalStars} sao đã nhận</Text></View> : null}</View>
        <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={l.introMascot} accessible={false} />
      </View>
      <View style={l.groups}>{GROUPS.map(item => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={item.title}
        accessibilityState={{ selected: group === item.id }} onPress={() => selectGroup(item.id)}
        style={({ pressed }) => [l.group, group === item.id && l.selected, pressed && l.pressed]}><Text style={[l.groupText, group === item.id && l.selectedText]}>{item.title}</Text></Pressable>)}</View>
      {busy && !result ? <View style={l.loading} accessibilityRole="progressbar" accessibilityLabel="Đang tải câu đố" accessibilityState={{ busy: true }}>
        <ActivityIndicator color={COLORS.primaryDark} /><Text style={l.body}>Đang tải câu đố…</Text></View> : null}
      {error ? <View style={l.help}><Text accessibilityRole="alert" style={l.error}>{error}</Text><AppButton title="Thử lại" variant="secondary" onPress={() => result ? void more() : setRetry(value => value + 1)} /></View> : null}
      {result && !result.items.length ? <View style={l.empty}>
        <View style={l.emptyArt}><Image source={require('../../../assets/illustrations/mathvision-star.png')} style={l.emptyMascot} accessible={false} /></View>
        <Text accessibilityRole="header" style={l.emptyTitle}>{empty.title}</Text><Text style={l.emptyBody}>{empty.body}</Text>
        <View style={l.emptyAction}><AppButton title={empty.action} variant="secondary" onPress={() => group === 'PENDING' ? router.replace('/(tabs)/lessons') : selectGroup('PENDING')} /></View>
      </View> : null}
      {result?.items.map(quiz => <Pressable key={quiz.quizId} accessibilityRole="button"
        accessibilityLabel={`${quiz.topicName}. ${quiz.questionText}. ${statusLabel(quiz)}. ${quiz.status === 'COMPLETED' ? 'Xem lại' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục' : 'Bắt đầu'}`}
        onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} style={({ pressed }) => [l.card, pressed && l.pressed]}>
        <View style={l.cardHeading}><View style={l.topicIcon}><Ionicons name={quiz.status === 'COMPLETED' ? 'checkmark' : 'sparkles-outline'} size={18} color={COLORS.primaryDark} accessible={false} /></View>
          <Text style={l.topic}>{quiz.topicName}</Text></View>
        <MathText style={l.question}>{quiz.questionText}</MathText>
        <View style={l.cardFooter}><Text style={l.metadata}>{statusLabel(quiz)}</Text><View style={l.action}>
          <Text style={l.actionText}>{quiz.status === 'COMPLETED' ? 'Xem lại' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục' : 'Bắt đầu'}</Text><Ionicons name="arrow-forward" size={15} color={COLORS.primaryDark} accessible={false} /></View></View>
      </Pressable>)}
      {result && result.page + 1 < result.totalPages ? <AppButton title="Xem thêm câu đố" variant="secondary" disabled={busy} loading={busy} onPress={() => void more()} /> : null}
    </ScrollView>
  </SafeAreaView>;
}

const l = StyleSheet.create({
  content: { flexGrow: 1, width: '100%', maxWidth: 840, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 6, paddingBottom: 24, gap: 16 },
  intro: { flexDirection: 'row', alignItems: 'center', gap: 16, paddingVertical: 8 },
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
  card: { padding: 16, gap: 12, borderRadius: 21, backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E7E0F1' },
  cardHeading: { flexDirection: 'row', alignItems: 'center', gap: 9 }, topicIcon: { width: 32, height: 32, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0EAFF' },
  topic: { flexShrink: 1, fontFamily: FONTS.extraBold, fontSize: 14, lineHeight: 21, color: COLORS.textPrimary },
  question: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: COLORS.textSecondary },
  cardFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', borderTopWidth: 1, borderTopColor: '#F1ECF7', paddingTop: 10 },
  metadata: { flexShrink: 1, fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 19, color: COLORS.textSecondary },
  action: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingVertical: 5, paddingHorizontal: 10, borderRadius: 10, backgroundColor: '#F0EAFF' },
  actionText: { fontFamily: FONTS.bold, fontSize: 12, lineHeight: 18, color: COLORS.primaryDark },
});
