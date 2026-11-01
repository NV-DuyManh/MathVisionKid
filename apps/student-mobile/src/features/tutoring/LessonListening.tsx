import React, { useEffect, useRef, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { LessonNarration } from './LessonNarration';
import { LessonReply, LessonStep, TutorService } from './api/TutorService';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { useNarrationPreparation } from './NarrationPreparation';

type Props = { scope: string; sessionId: string; revision: number; stepIndex: number;
  step?: Pick<LessonStep, 'kind' | 'title' | 'expression'> | null; paragraphs: string[]; onReturn: () => void };

export function LessonListening(props: Props) {
  // Scope includes owner, opened step and revision; stale audio or replies cannot cross lessons.
  return <ListeningStep key={JSON.stringify([props.scope, props.revision, props.stepIndex, props.paragraphs])} {...props} />;
}

function ListeningStep({ scope, sessionId, revision, stepIndex, step, paragraphs, onReturn }: Props) {
  const [ready, setReady] = useState(false), [choosing, setChoosing] = useState(false);
  const [reply, setReply] = useState<LessonReply | null>(null), [selected, setSelected] = useState('');
  useNarrationPreparation(reply ? { sessionId, revision } : null, reply ? [reply.spokenExplanation, reply.followUp] : [], { wholeLesson: false });
  const [pending, setPending] = useState(false), [notice, setNotice] = useState('');
  const request = useRef<AbortController | null>(null), mounted = useRef(true), generation = useRef(0);
  useEffect(() => {
    mounted.current = true;
    const listener = AppState.addEventListener('change', state => {
      if (state !== 'active' && request.current) {
        ++generation.current; request.current.abort(); request.current = null;
        setPending(false); setNotice('Đã dừng giải thích. Em có thể thử lại khi sẵn sàng.');
      }
    });
    return () => { mounted.current = false; request.current?.abort(); listener.remove(); };
  }, []);
  const expression = step?.expression || '';
  const writtenFractions = expression.match(/\d+\s*\/\s*\d+/g) || [];
  const context = [step?.title, ...paragraphs].join(' ');
  // A slash is also ordinary division, e.g. floor area / tile area. It does
  // not imply that the learner needs a numerator/denominator lesson.
  const addFractions = writtenFractions.length >= 2 && /[+−-]/.test(expression);
  const fraction = addFractions || /phân số|tử số|mẫu số|quy đồng/i.test(context);
  const choices = step?.kind === 'UNDERSTAND' ? ['Đề bài đã cho biết gì?', 'Đề bài muốn tìm gì?', 'Em chưa hiểu một từ trong đề']
    : [addFractions ? 'Vì sao phải quy đồng?' : 'Vì sao chọn phép tính này?', 'Em chưa biết bắt đầu từ đâu', fraction ? 'Tử số và mẫu số nghĩa là gì?' : 'Đơn vị này nghĩa là gì?'];
  const explain = async (choice: string) => {
    if (request.current) return;
    const controller = new AbortController(), id = ++generation.current;
    request.current = controller;
    setPending(true); setNotice(''); setSelected(choice); setReply(null);
    try {
      const result = await TutorService.askLesson({ sessionId, revision, stepIndex,
        question: `${choice} Em chưa hiểu chỗ này trong bước đang học. Giải thích chậm bằng một hình dung quen thuộc, rồi gợi một việc nhỏ để em tự thử; đừng cho đáp số.` }, controller.signal);
      if (mounted.current && generation.current === id) { setReply(result); setChoosing(false); setReady(false); }
    } catch {
      if (mounted.current && generation.current === id) setNotice('Chưa giải thích được lúc này. Em giữ lựa chọn này và thử lại nhé.');
    } finally {
      if (mounted.current && generation.current === id) { request.current = null; setPending(false); }
    }
  };
  if (pending) return <View style={styles.waiting} accessibilityLiveRegion="polite">
    <Ionicons name="chatbubble-ellipses-outline" size={34} color={COLORS.primaryDark} />
    <Text style={styles.title}>Mình cùng gỡ chỗ này nhé</Text><Text style={styles.body}>{selected}</Text>
    <TaskProgress steps={['Chỗ cần hỏi đã chọn', 'Soạn lời giải thích', 'Mở lời giải thích']} activeStep={1} />
    <AppButton title="Dừng chờ" variant="secondary" onPress={() => { ++generation.current; request.current?.abort(); request.current = null; setPending(false); setNotice('Đã dừng. Em có thể chọn lại chỗ còn vướng.'); }} />
  </View>;
  return <View style={styles.stack}>
    {!choosing ? <>
      {reply ? <View style={styles.explanation} accessibilityLiveRegion="polite"><Text style={styles.eyebrow}>CHỖ EM ĐANG HỎI</Text><Text style={styles.title}>{selected}</Text>
        <MathText style={styles.body}>{reply.answer}</MathText>{reply.followUp ? <MathText style={styles.followUp}>{reply.followUp}</MathText> : null}</View> : null}
      <LessonNarration key={reply ? selected : 'original'} scope={`${scope}:${selected}`} source={{ sessionId, revision }} paragraphs={reply ? [reply.spokenExplanation, reply.followUp] : paragraphs} onFinished={() => setReady(true)} />
      {ready ? <View style={styles.checkIn} accessibilityLiveRegion="polite">
        <Pressable accessibilityRole="button" accessibilityLabel="Em đã hiểu" onPress={onReturn} style={({ pressed }) => [styles.understood, pressed && { opacity: .7 }]}>
          <Ionicons name="checkmark-circle" size={20} color="#236747" accessible={false} /><Text style={styles.understoodText}>Đã hiểu</Text>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Em chưa hiểu" style={styles.notYet} onPress={() => { setChoosing(true); setNotice(''); setReply(null); setSelected(''); }}>
          <Ionicons name="help-circle-outline" size={20} color="#6F568C" accessible={false} /><Text style={styles.notYetText}>Chưa hiểu</Text>
        </Pressable>
      </View> : <Pressable accessibilityRole="button" accessibilityLabel="Em đã đọc lời giảng" style={styles.read} onPress={() => setReady(true)}><Text style={styles.link}>Em đã đọc lời giảng</Text><Ionicons name="checkmark-circle-outline" size={21} color={COLORS.primaryDark} /></Pressable>}
    </> : <View style={styles.stack}>
      <Text style={styles.title}>Chọn chỗ em còn vướng</Text><Text style={styles.body}>Bạn mình sẽ giải thích phần đó nhé!</Text>
      <View style={styles.choiceList}>{choices.map((choice, index) => <Pressable key={choice} accessibilityRole="button" accessibilityLabel={choice} accessibilityState={{ selected: selected === choice }} aria-pressed={selected === choice} onPress={() => { setSelected(choice); setNotice(''); }}
        style={({ pressed }) => [styles.choice, selected === choice && styles.choiceSelected, pressed && { opacity: .7 }]}><View style={styles.number}><Ionicons name={(['calculator-outline', 'add-circle-outline', 'chatbubble-ellipses-outline'] as const)[index]} size={21} color="#7854B3" accessible={false} /></View><Text style={styles.choiceText}>{choice}</Text><Ionicons name={selected === choice ? 'checkmark-circle' : 'ellipse-outline'} size={20} color={selected === choice ? '#7950DA' : '#9C8AAD'} accessible={false} /></Pressable>)}</View>
      <AppButton title="Xem giải thích nhé!" disabled={!selected} onPress={() => { if (selected) void explain(selected); }} />
      <AppButton title="Quay lại lời giảng" variant="ghost" onPress={() => setChoosing(false)} />
    </View>}
    {notice ? <View style={styles.notice} accessibilityLiveRegion="polite"><Text style={styles.body}>{notice}</Text>{selected ? <AppButton title="Thử giải thích lại" variant="secondary" onPress={() => { void explain(selected); }} /> : null}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 12 }, title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 18, lineHeight: 24 },
  body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 14, lineHeight: 22 },
  eyebrow: { fontFamily: FONTS.extraBold, color: '#8C72AE', fontSize: 11, letterSpacing: 1.1 },
  checkIn: { gap: 10, flexDirection: 'row', flexWrap: 'wrap' }, understood: { flex: 1, minWidth: 104, minHeight: 50, paddingHorizontal: 10, borderRadius: 15, backgroundColor: '#E7F6EE', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  understoodText: { fontFamily: FONTS.bold, color: '#236747', fontSize: 13 },
  notYet: { flex: 1, minWidth: 104, minHeight: 50, paddingHorizontal: 10, borderRadius: 15, borderWidth: 1, borderColor: '#C8B8DD', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  notYetText: { fontFamily: FONTS.bold, color: '#6F568C', fontSize: 13 },
  choiceList: { gap: 10 }, choice: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, minHeight: 58, borderRadius: 15, borderWidth: 1.5, borderColor: '#EDE4FC', backgroundColor: '#FFF' },
  choiceSelected: { backgroundColor: '#F0E7FF', borderColor: '#B78DFF' },
  choiceText: { flex: 1, fontFamily: FONTS.bold, color: '#6B5295', fontSize: 14, lineHeight: 22 },
  number: { width: 30, height: 30, borderRadius: 9, backgroundColor: '#F3ECFF', alignItems: 'center', justifyContent: 'center' },
  read: { minHeight: 48, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9 }, link: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 14 },
  explanation: { backgroundColor: '#F5EFFD', borderRadius: 18, padding: 16, gap: 12 }, followUp: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 14, lineHeight: 22 },
  waiting: { alignItems: 'center', paddingVertical: 48, gap: 23 }, notice: { borderRadius: 18, padding: 17, backgroundColor: '#FFF4E8', gap: 15 },
});
