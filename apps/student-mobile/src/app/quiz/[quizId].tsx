import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { TaskProgress } from '../../components/ui/TaskProgress';
import { Quiz, quizApi, quizError } from '../../features/quiz/quizApi';
import { quizTime, submissionId, validQuizAnswer } from '../../features/quiz/quizInput';
import { QuizVoice, QuizNarrationPreparation } from '../../features/quiz/QuizVoice';
import { QuizHelp } from '../../features/quiz/QuizHelp';
import { useQuizActivity } from '../../features/quiz/useQuizActivity';
import { LessonSheet } from '../../features/tutoring/LessonSheet';
import { NarrationPreparation } from '../../features/tutoring/NarrationPreparation';
import { quizStyles as s } from '../../features/quiz/quizStyles';

function Reward({ stars }: { stars: number }) {
  const [opacity] = useState(() => new Animated.Value(1));
  useEffect(() => {
    let active = true;
    void AccessibilityInfo.isReduceMotionEnabled().then(reduced => {
      if (active && !reduced && stars > 0) { opacity.setValue(.3); Animated.timing(opacity, { toValue: 1, duration: 500, useNativeDriver: true }).start(); }
    });
    return () => { active = false; opacity.stopAnimation(); };
  }, [opacity, stars]);
  return <Animated.View style={[s.stars, { opacity }]} accessibilityLabel={`${stars} sao`}>
    {[0, 1, 2].map(index => <View key={index} style={s.resultMedal} accessible={false}><Ionicons name={index < stars ? 'star' : 'star-outline'} color={index < stars ? '#A66800' : '#88769C'} size={30} accessible={false} /></View>)}
  </Animated.View>;
}
export default function QuizScreen() {
  const { quizId } = useLocalSearchParams<{ quizId: string }>();
  const auth = useContext(AuthContext), owner = auth?.user?.id || auth?.user?.userId;
  return owner && typeof quizId === 'string' ? <Challenge key={`${owner}:${quizId}`} id={quizId} owner={owner} /> : null;
}
function Challenge({ id, owner }: { id: string; owner: string }) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [answer, setAnswer] = useState(''), [feedback, setFeedback] = useState('');
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true);
  const [tool, setTool] = useState<'audio' | 'ask' | 'menu' | 'solution' | 'history' | null>(null);
  const elapsed = useQuizActivity(quiz);
  const [retry, setRetry] = useState(0);
  const [invalidAnswer, setInvalidAnswer] = useState(false);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const pending = useRef<{ requestId: string; answer: string } | null>(null);
  const apply = useCallback((next: Quiz) => {
    setQuiz(next);
  }, []);
  useFocusEffect(useCallback(() => {
    void retry;
    active.current = true; setLoading(true); setError('');
    const abort = new AbortController(); controller.current = abort;
    void quizApi.get(id, abort.signal).then(next => { if (active.current && !abort.signal.aborted) apply(next); })
      .catch(failure => { if (active.current && !abort.signal.aborted) setError(quizError(failure)); })
      .finally(() => { if (active.current && !abort.signal.aborted) { setLoading(false); controller.current = null; } });
    const listener = AppState.addEventListener('change', state => { if (state === 'active') setRetry(value => value + 1); });
    return () => { active.current = false; abort.abort(); controller.current?.abort(); controller.current = null; listener.remove(); setBusy(false); };
  }, [id, retry, apply]));
  const perform = async (action: (signal: AbortSignal) => Promise<Quiz>) => {
    if (controller.current || loading) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try { const next = await action(abort.signal); if (active.current && !abort.signal.aborted) apply(next); }
    catch (failure) { if (active.current && !abort.signal.aborted) setError(quizError(failure)); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  };
  const submit = () => {
    if (!quiz || busy || loading || controller.current) return;
    if (!validQuizAnswer(answer, quiz.unit)) { setInvalidAnswer(true); setError('Em nhập một số, số thập phân hoặc phân số hợp lệ, ví dụ 48 hoặc 3/4 nhé.'); return; }
    setInvalidAnswer(false);
    if (!pending.current || pending.current.answer !== answer.trim()) pending.current = { requestId: submissionId(), answer: answer.trim() };
    const request = pending.current;
    void perform(async signal => {
      const result = await quizApi.submit(id, request.requestId, request.answer, signal);
      if (active.current && !signal.aborted) {
        pending.current = null;
        setFeedback(result.quiz.status === 'COMPLETED' ? result.quiz.completedWithSolution ? 'Em đã hoàn thành bài luyện tập cùng cách giải. Mình tiếp tục khám phá nhé!'
          : result.attempt.correct ? 'Đúng rồi! Em đã hoàn thành bài luyện tập này.' : 'Quiz này đã được hoàn thành. Em có thể xem lại những lần thử bên dưới nhé.'
          : result.quiz.wrongAttempts < 2 ? 'Chưa đúng rồi, nhưng em thử kiểm tra lại nhé!'
            : 'Em thử lại nhé! Sao cũng đã chuẩn bị Cách giải để cùng em tìm hiểu.');
      }
      return result.quiz;
    });
  };
  const replayQuiz = (mode: 'PRACTICE' | 'CHALLENGE' = 'CHALLENGE') => {
    void perform(async signal => {
      const next = await quizApi.replay(id, mode, signal);
      if (active.current && !signal.aborted) { setAnswer(''); setFeedback(''); pending.current = null; }
      return next;
    });
  };
  const saveForLater = () => { void perform(async signal => { const next = await quizApi.defer(id, signal); if (active.current && !signal.aborted) router.replace('/quiz' as never); return next; }); };
  const done = quiz?.status === 'COMPLETED', running = quiz?.status === 'IN_PROGRESS';
  const latestCompletion = quiz?.attempts.slice().reverse().find(attempt => attempt.correct);
  const earnedStars = latestCompletion?.stars ?? quiz?.stars ?? 0;

  return <QuizNarrationPreparation owner={owner} quizId={id} content={quiz?.explanationText ? 'SOLUTION' : 'QUESTION'} paragraphs={quiz && !loading && quiz.startedAt ? [quiz.explanationText || quiz.questionText] : []}>
  <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Thử thách nhỏ của em" showBack />
    <KeyboardAvoidingView style={s.scroll} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={s.scroll} contentContainerStyle={[s.content,s.workContent]} keyboardShouldPersistTaps="handled">
        {loading ? <View style={s.card}><TaskProgress steps={['Mở câu đố của em', 'Khôi phục tiến trình']} activeStep={1} /></View> : null}
        {error ? <View style={s.note}><Text nativeID="quiz-answer-error" accessibilityRole="alert" style={s.error}>{error}</Text><AppButton title={quiz ? 'Kiểm tra lại trạng thái' : 'Thử tải lại'} variant="secondary" disabled={busy || loading} onPress={() => setRetry(value => value + 1)} /></View> : null}
        {quiz && !loading ? <>
          <View style={[s.card,s.workCard]}>
            <View style={s.workTopline}>
              <View style={s.workBadge}><Ionicons name={done?'checkmark-circle-outline':'sparkles-outline'} size={16} color="#5637C9" accessible={false}/><Text style={s.workBadgeText}>{done?'ĐÃ HOÀN THÀNH':'CÙNG SAO THỬ SỨC'}</Text></View>
              <View style={s.clock}><Ionicons name="time-outline" size={16} color="#5637C9" accessible={false}/><Text style={s.clockText} accessibilityLabel={`Thời gian làm bài ${quizTime(done ? quiz.elapsedMillis : elapsed)}`}>{quizTime(done ? quiz.elapsedMillis : elapsed)}</Text></View>
            </View>
            <View style={s.questionPanel}>
              <Text style={s.workTopic}>Lớp {quiz.gradeLevel} · {quiz.topicName}</Text>
              <MathText style={s.quizQuestion}>{quiz.questionText}</MathText>
            </View>
            {done ? <View style={s.result}>
              <View style={s.resultPanel}>
              {quiz.replayMode !== 'PRACTICE' ? <Reward stars={earnedStars}/> : null}
              <Text style={[s.heading,{textAlign:'center'}]}>{quiz.completedWithSolution ? 'Cùng Sao hiểu thêm một bài!' : 'Em đã hoàn thành rồi!'}</Text>
              <Text style={[s.body,{textAlign:'center'}]}>{quiz.replayMode === 'PRACTICE' ? 'Em đã ôn lại bài cũ. Thành tích của em được giữ nguyên.' : `Lượt này: ${earnedStars} sao · Kỷ lục: ${quiz.stars} sao`}</Text>
              </View>
              <AppButton title="Thử thách nâng sao" style={s.workButton} disabled={busy} loading={busy} onPress={() => replayQuiz('CHALLENGE')}/>
              <AppButton title="Về trang chủ" style={s.workButton} variant="secondary" icon={<Ionicons name="home-outline" size={19} color="#7953D8"/>} onPress={() => router.replace('/(tabs)')}/>
              <AppButton title="Chọn câu đố khác" variant="ghost" onPress={() => router.replace('/quiz' as never)}/>
            </View> : running ? <>
              {quiz.replayMode === 'CHALLENGE' ? <Text style={s.small}>Thử thách nâng sao · Câu hỏi mới cho em</Text> : quiz.replayMode === 'PRACTICE' ? <Text style={s.small}>Ôn lại bài cũ · Giữ nguyên thành tích</Text> : null}
              <Text nativeID="quiz-answer-label" style={s.title}>Đáp án của em{quiz.unit ? ` (${quiz.unit})` : ''}</Text>
              <TextInput accessibilityLabel={`Đáp án của em${quiz.unit ? `, ${quiz.unit}` : ''}`} aria-describedby={invalidAnswer ? 'quiz-answer-help quiz-answer-error' : 'quiz-answer-help'} aria-invalid={invalidAnswer}
                value={answer} onChangeText={value => { setAnswer(value); setError(''); setInvalidAnswer(false); }} style={[s.input,s.workInput,invalidAnswer&&s.workInputError]} editable={!busy} maxLength={100}
                placeholder={quiz.answerFormat === 'FRACTION' ? 'Ví dụ: 3/4' : 'Em tính được…'} keyboardType={quiz.answerFormat === 'FRACTION' ? 'default' : 'decimal-pad'} returnKeyType="done" onSubmitEditing={submit}/>
              <Text nativeID="quiz-answer-help" style={s.small}>{quiz.answerFormat === 'FRACTION' ? 'Nhập phân số a/b hoặc số thập phân chính xác.' : 'Chỉ cần nhập kết quả cuối cùng.'}</Text>
              {feedback ? <Text accessibilityLiveRegion="polite" style={s.error}>{feedback}</Text> : null}
              <AppButton title="Hoàn thành" style={s.workButton} disabled={busy || !answer.trim()} loading={busy} onPress={submit}/>
              {quiz.solutionViewed ? <Text style={s.small}>{quiz.replayMode === 'PRACTICE' ? 'Em cứ luyện theo nhịp của mình nhé.' : 'Em đang luyện cùng hướng dẫn. Hoàn thành lượt này em nhận 1 sao.'}</Text> : null}
            </> : <>
              <Text style={s.body}>Sẵn sàng thử sức chưa em?</Text>
              <Text style={s.small}>Đúng trong 30 giây: 3 sao · đến 60 giây: 2 sao · sau đó: 1 sao. Đồng hồ chỉ tính khi em đang làm trong Quiz; rời màn hình sẽ tạm dừng.</Text>
              <AppButton title="Bắt đầu tính giờ" style={s.workButton} disabled={busy} loading={busy} onPress={() => void perform(signal => quizApi.start(id, signal))}/>
            </>}
            {quiz.startedAt ? <View style={[s.tools,s.workTools]}>
              {([['audio','volume-high-outline','Nghe giảng'],['ask','mic-outline','Hỏi bài'],['menu','ellipsis-horizontal','Xem thêm']] as const).map(([value,icon,label])=><Pressable key={value} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{disabled:busy}} disabled={busy} style={({pressed})=>[s.tool,s.workTool,pressed&&s.selected,busy&&{opacity:.5}]} onPress={()=>setTool(value)}>
                <Ionicons name={icon} size={22} color="#6940C9" accessible={false}/><Text style={s.toolLabel}>{label}</Text>
              </Pressable>)}
            </View> : null}
            {quiz.explanationText ? <Pressable accessibilityRole="button" accessibilityLabel="Xem cách giải" style={s.detailLink} onPress={()=>setTool('solution')}><Ionicons name="reader-outline" size={19} color="#7953D8"/><Text style={s.topic}>Xem cách giải</Text><Ionicons name="chevron-forward" size={17} color="#7953D8"/></Pressable> : null}
          </View>
          {!done ? <AppButton title="Lưu để làm sau" variant="ghost" disabled={busy} onPress={saveForLater}/> : null}
        </> : null}
        {!done ? <AppButton title="Trở về danh sách" variant="ghost" onPress={() => router.replace('/quiz' as never)} /> : null}
      </ScrollView>
    </KeyboardAvoidingView>
    {quiz && tool ? <LessonSheet title={{audio:'Nghe giảng',ask:'Hỏi bài',menu:'Em cần gì thêm?',solution:'Cách giải',history:'Những lần em đã thử'}[tool]} onClose={()=>setTool(null)}>
      {tool==='audio' ? <QuizVoice key={`${quiz.quizId}:${quiz.startedAt}:${!!quiz.explanationText}`} quizId={quiz.quizId} content={quiz.explanationText?'SOLUTION':'QUESTION'} paragraphs={[quiz.explanationText || quiz.questionText]}/> : null}
      {tool==='ask' ? <NarrationPreparation owner={owner}><QuizHelp quiz={quiz} onAssisted={apply} onReturn={()=>setTool(null)}/></NarrationPreparation> : null}
      {tool==='solution' ? <MathText style={s.body}>{quiz.explanationText || ''}</MathText> : null}
      {tool==='menu' ? <>
        {quiz.canRevealSolution && !quiz.solutionViewed && !done ? <AppButton title="Xem cách giải" variant="secondary" disabled={busy} onPress={()=>void perform(async signal=>{const next=await quizApi.reveal(id,signal);if(active.current&&!signal.aborted)setTool('solution');return next;})}/> : null}
        {quiz.explanationText ? <AppButton title="Xem cách giải" variant="secondary" onPress={()=>setTool('solution')}/> : null}
        {quiz.attempts.length ? <AppButton title={`Xem ${quiz.attempts.length} lần đã thử`} variant="secondary" onPress={()=>setTool('history')}/> : null}
        {done ? <AppButton title="Ôn lại bài cũ" variant="secondary" disabled={busy} onPress={()=>{setTool(null);replayQuiz('PRACTICE');}}/> : <AppButton title="Lưu để làm sau" variant="secondary" disabled={busy} onPress={saveForLater}/>}
        <AppButton title="Về trang chủ" variant="ghost" onPress={()=>router.replace('/(tabs)')}/>
      </> : null}
      {tool==='history' ? quiz.attempts.slice().reverse().map(attempt=><View key={attempt.number} style={s.note}>
        {attempt.questionText ? <MathText style={s.small}>{attempt.questionText}</MathText> : null}
        <Text style={s.title}>{`Lần ${attempt.number}: ${attempt.answer} · ${attempt.correct?'Đúng':'Chưa đúng'}`}</Text>
        <Text style={s.small}>{`${quizTime(attempt.elapsedMillis)} · ${attempt.stars || 0} sao · ${new Date(attempt.submittedAt).toLocaleDateString('vi-VN')}`}</Text>
      </View>) : null}
    </LessonSheet> : null}
  </SafeAreaView></QuizNarrationPreparation>;
}
