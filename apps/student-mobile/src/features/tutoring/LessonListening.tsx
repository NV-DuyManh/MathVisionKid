import React, { useEffect, useRef, useState } from 'react';
import { AppState, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import { LessonNarration } from './LessonNarration';
import { LessonReply, LessonStep, TutorService } from './api/TutorService';

type Props = { scope: string; sessionId: string; revision: number; stepIndex: number;
  step?: Pick<LessonStep, 'kind' | 'title' | 'expression'> | null; paragraphs: string[]; onReturn: () => void };

export function LessonListening(props: Props) {
  // Scope includes owner, opened step and revision; stale audio or replies cannot cross lessons.
  return <ListeningStep key={JSON.stringify([props.scope, props.revision, props.stepIndex, props.paragraphs])} {...props} />;
}

function ListeningStep({ scope, sessionId, revision, stepIndex, step, paragraphs, onReturn }: Props) {
  const [ready, setReady] = useState(false), [choosing, setChoosing] = useState(false);
  const [reply, setReply] = useState<LessonReply | null>(null), [selected, setSelected] = useState('');
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
  const fraction = /\d\s*\/\s*\d/.test(step?.expression || '');
  const addFractions = fraction && /[+−-]/.test(step?.expression || '');
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
    <AppButton title="Dừng chờ" variant="secondary" onPress={() => { ++generation.current; request.current?.abort(); request.current = null; setPending(false); setNotice('Đã dừng. Em có thể chọn lại chỗ còn vướng.'); }} />
  </View>;
  return <View style={styles.stack}>
    {!choosing ? <>
      {reply ? <View style={styles.explanation} accessibilityLiveRegion="polite"><Text style={styles.eyebrow}>CHỖ EM ĐANG HỎI</Text><Text style={styles.title}>{selected}</Text>
        <MathText style={styles.body}>{reply.answer}</MathText>{reply.followUp ? <MathText style={styles.followUp}>{reply.followUp}</MathText> : null}</View> : null}
      <LessonNarration key={reply ? selected : 'original'} scope={`${scope}:${selected}`} paragraphs={reply ? [reply.spokenExplanation, reply.followUp] : paragraphs} onFinished={() => setReady(true)} />
      <View style={styles.insight}><Ionicons name="bulb" size={24} color="#EDB234" accessible={false} /><Text style={styles.insightText}>Nghe từng ý nhỏ, rồi thử làm nhé!</Text></View>
      {ready ? <View style={styles.checkIn} accessibilityLiveRegion="polite">
        <Pressable accessibilityRole="button" accessibilityLabel="Em đã hiểu" onPress={onReturn}>
          <LinearGradient colors={['#65E7A4', '#2DCA83']} style={styles.understood}><Ionicons name="checkmark" size={22} color="#FFF" /><Text style={styles.understoodText}>Em đã hiểu</Text></LinearGradient>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Em chưa hiểu" style={styles.notYet} onPress={() => { setChoosing(true); setNotice(''); setReply(null); setSelected(''); }}>
          <Ionicons name="help" size={22} color="#8555F7" /><Text style={styles.notYetText}>Em chưa hiểu</Text>
        </Pressable>
      </View> : <Pressable accessibilityRole="button" accessibilityLabel="Em đã đọc lời giảng" style={styles.read} onPress={() => setReady(true)}><Text style={styles.link}>Em đã đọc lời giảng</Text><Ionicons name="checkmark-circle-outline" size={21} color={COLORS.primaryDark} /></Pressable>}
    </> : <View style={styles.stack}>
      <Text style={styles.title}>Chọn chỗ em còn vướng</Text><Text style={styles.body}>Bạn mình sẽ giải thích phần đó nhé!</Text>
      <View accessibilityRole="radiogroup" accessibilityLabel="Chỗ em còn vướng" style={styles.choiceList}>{choices.map((choice, index) => <Pressable key={choice} accessibilityRole="radio" accessibilityLabel={choice} accessibilityState={{ checked: selected === choice }} onPress={() => { setSelected(choice); setNotice(''); }}
        style={({ pressed }) => [styles.choice, selected === choice && styles.choiceSelected, pressed && { opacity: .7 }]}><View style={styles.number}><Ionicons name={(['calculator-outline', 'add-circle', 'chatbubble-ellipses-outline'] as const)[index]} size={22} color="#A170FF" /></View><Text style={styles.choiceText}>{choice}</Text><Ionicons name={selected === choice ? 'radio-button-on' : 'radio-button-off'} size={20} color={selected === choice ? '#9A65FF' : '#DED2F1'} /></Pressable>)}</View>
      <AppButton title="Xem giải thích nhé!" disabled={!selected} onPress={() => { if (selected) void explain(selected); }} />
      <AppButton title="Quay lại lời giảng" variant="ghost" onPress={() => setChoosing(false)} />
    </View>}
    {notice ? <View style={styles.notice} accessibilityLiveRegion="polite"><Text style={styles.body}>{notice}</Text>{selected ? <AppButton title="Thử giải thích lại" variant="secondary" onPress={() => { void explain(selected); }} /> : null}</View> : null}
  </View>;
}
const styles = StyleSheet.create({
  stack: { gap: 15 }, title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 20, lineHeight: 28 },
  body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 15, lineHeight: 24 },
  eyebrow: { fontFamily: FONTS.extraBold, color: '#8C72AE', fontSize: 11, letterSpacing: 1.1 },
  checkIn: { gap: 10 }, understood: { minHeight: 51, borderRadius: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  understoodText: { fontFamily: FONTS.extraBold, color: '#124A36', fontSize: 15 },
  notYet: { minHeight: 49, borderRadius: 16, borderWidth: 1.5, borderColor: '#B99AFF', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  notYetText: { fontFamily: FONTS.extraBold, color: '#7550D0', fontSize: 15 },
  insight: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 13, borderRadius: 14, backgroundColor: '#FFF7E7' }, insightText: { flex: 1, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 20, color: '#8B714A' },
  choiceList: { gap: 10 }, choice: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, minHeight: 58, borderRadius: 15, borderWidth: 1.5, borderColor: '#EDE4FC', backgroundColor: '#FFF' },
  choiceSelected: { backgroundColor: '#F0E7FF', borderColor: '#B78DFF' },
  choiceText: { flex: 1, fontFamily: FONTS.bold, color: '#6B5295', fontSize: 14, lineHeight: 22 },
  number: { width: 30, height: 30, borderRadius: 9, backgroundColor: '#F3ECFF', alignItems: 'center', justifyContent: 'center' },
  read: { minHeight: 48, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 9 }, link: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 14 },
  explanation: { backgroundColor: '#F5EFFD', borderRadius: 24, padding: 21, gap: 14 }, followUp: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 16, lineHeight: 25 },
  waiting: { alignItems: 'center', paddingVertical: 48, gap: 23 }, notice: { borderRadius: 18, padding: 17, backgroundColor: '#FFF4E8', gap: 15 },
});
