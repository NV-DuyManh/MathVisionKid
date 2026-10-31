import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, AppState, KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from 'react-native';
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
import { QuizVoice } from '../../features/quiz/QuizVoice';
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
    {[0, 1, 2].map(index => <Ionicons key={index} name={index < stars ? 'star' : 'star-outline'} color={index < stars ? '#A66800' : '#88769C'} size={34} accessible={false} />)}
  </Animated.View>;
}
export default function QuizScreen() {
  const { quizId } = useLocalSearchParams<{ quizId: string }>();
  const auth = useContext(AuthContext), owner = auth?.user?.id || auth?.user?.userId;
  return owner && typeof quizId === 'string' ? <Challenge key={`${owner}:${quizId}`} id={quizId} /> : null;
}
function Challenge({ id }: { id: string }) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [answer, setAnswer] = useState(''), [feedback, setFeedback] = useState('');
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [elapsed, setElapsed] = useState(0);
  const [retry, setRetry] = useState(0);
  const [invalidAnswer, setInvalidAnswer] = useState(false);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const baseline = useRef({ elapsed: 0, received: 0 });
  const pending = useRef<{ requestId: string; answer: string } | null>(null);
  const apply = useCallback((next: Quiz) => {
    setQuiz(next); baseline.current = { elapsed: next.elapsedMillis, received: performance.now() }; setElapsed(next.elapsedMillis);
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
  useEffect(() => {
    if (quiz?.status !== 'IN_PROGRESS') return;
    const timer = setInterval(() => setElapsed(baseline.current.elapsed + Math.max(0, performance.now() - baseline.current.received)), 1000);
    return () => clearInterval(timer);
  }, [quiz?.status]);
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
  const bestAttemptStars = Math.max(0, ...(quiz?.attempts.map(a => a.stars || 0) || [0]));

  return <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
    <AppHeader title="Thử thách nhỏ của em" showBack />
    <KeyboardAvoidingView style={s.scroll} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView style={s.scroll} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        {loading ? <View style={s.card}><TaskProgress steps={['Mở câu đố của em', 'Khôi phục tiến trình']} activeStep={1} /></View> : null}
        {error ? <View style={s.card}><Text nativeID="quiz-answer-error" accessibilityRole="alert" style={s.error}>{error}</Text><AppButton title={quiz ? 'Kiểm tra lại trạng thái' : 'Thử tải lại'} variant="secondary" disabled={busy || loading} onPress={() => setRetry(value => value + 1)} /></View> : null}
        {quiz && !loading ? <>
          <View style={s.card}>
            <Text style={s.topic}>{quiz.topicName} · Lớp {quiz.gradeLevel}</Text>
            {running && quiz.replayMode === 'CHALLENGE' ? (
              <Text style={[s.small, { color: '#0F766E', fontWeight: 'bold', marginBottom: 4 }]}>
                ★ Thử thách nâng sao: Câu hỏi biến thể mới. Giải đúng trong 30 giây để đạt 3 sao!
              </Text>
            ) : null}
            {running && quiz.replayMode === 'PRACTICE' ? (
              <Text style={[s.small, { color: '#4B5563', fontStyle: 'italic', marginBottom: 4 }]}>
                📖 Ôn lại bài cũ: Luyện tập lại bài toán ban đầu (lượt này không cộng thêm sao).
              </Text>
            ) : null}
            <MathText style={s.question}>{quiz.questionText}</MathText>
            <Text style={s.title}>{done ? 'Thời gian giải' : 'Thời gian đã giải'}: {quizTime(done ? quiz.elapsedMillis : elapsed)}</Text>
            {quiz.elapsedMillis >= 3600000 ? <Text style={s.small}>Giờ:phút:giây, tính từ lúc bắt đầu lượt này, kể cả khi em rời bài. Thử thách mới có thời gian riêng.</Text> : null}
            {!running && !done ? <><Text style={s.body}>Đúng trong 30 giây: 3 sao · đến 60 giây: 2 sao · sau đó: 1 sao.</Text>
              <Text style={s.small}>Thời gian tính liên tục sau khi bấm Bắt đầu, kể cả khi em rời màn hình. Em cứ giải theo nhịp của mình nhé.</Text>
              <AppButton title="Bắt đầu tính giờ" disabled={busy} loading={busy} onPress={() => void perform(signal => quizApi.start(id, signal))} /></> : null}
            {running ? <>
              <Text nativeID="quiz-answer-label" style={s.title}>Đáp án của em{quiz.unit ? ` (${quiz.unit})` : ''}</Text>
              <TextInput accessibilityLabel={`Đáp án của em${quiz.unit ? `, ${quiz.unit}` : ''}`} aria-describedby={invalidAnswer ? 'quiz-answer-help quiz-answer-error' : 'quiz-answer-help'} aria-invalid={invalidAnswer}
                value={answer} onChangeText={value => { setAnswer(value); setError(''); setInvalidAnswer(false); }}
                style={s.input} editable={!busy} maxLength={100} placeholder={quiz.answerFormat === 'FRACTION' ? 'Ví dụ: 3/4' : 'Em tính được…'}
                keyboardType={quiz.answerFormat === 'FRACTION' ? 'default' : 'decimal-pad'} returnKeyType="done" onSubmitEditing={submit} />
              <Text nativeID="quiz-answer-help" style={s.small}>{quiz.answerFormat === 'FRACTION' ? 'Em có thể nhập phân số a/b hoặc số thập phân chính xác.' : 'Chỉ cần nhập kết quả cuối cùng, không cần nhập phép tính.'}</Text>
              <AppButton title="Hoàn thành" disabled={busy || !answer.trim()} loading={busy} onPress={submit} />
              {quiz.canRevealSolution && !quiz.solutionViewed ? <AppButton title="Cách giải" variant="secondary" disabled={busy} onPress={() => void perform(signal => quizApi.reveal(id, signal))} /> : null}
              {quiz.solutionViewed ? <Text style={s.small}>{quiz.replayMode === 'PRACTICE' ? 'Em đang ôn lại bài cũ, không chấm điểm và giữ nguyên thành tích.' : 'Em đang luyện cùng cách giải. Hoàn thành lượt này em nhận 1 sao; mình cứ tiếp tục học nhé.'}</Text> : null}
            </> : null}
            {feedback ? <Text accessibilityLiveRegion="polite" style={done ? s.success : s.body}>{feedback}</Text> : null}
          </View>
          {done ? <View style={s.card}>
            {quiz.replayMode !== 'PRACTICE' ? <Reward stars={earnedStars} /> : null}
            <Text style={s.heading}>{quiz.completedWithSolution ? 'Cùng Sao hiểu thêm một bài!' : 'Em đã hoàn thành bài luyện tập này!'}</Text>
            <Text style={s.body}>{quiz.replayMode === 'PRACTICE' ? 'Ôn lại bài cũ – Không chấm điểm. Thành tích của em được giữ nguyên.'
              : quiz.completedWithSolution ? `Hoàn thành với hướng dẫn – Lượt này em nhận ${earnedStars} sao. Kỷ lục của em: ${quiz.stars} sao. Em có thể thử thách mới để nâng sao nhé!`
              : `Lượt này em nhận ${earnedStars} sao. Kỷ lục của em: ${quiz.stars} sao.`}</Text>
            <AppButton title="Thử thách nâng sao" disabled={busy} loading={busy} onPress={() => replayQuiz('CHALLENGE')} />
            <AppButton title="Ôn lại bài cũ" variant="secondary" disabled={busy} loading={busy} onPress={() => replayQuiz('PRACTICE')} />
            <AppButton title="Về Quiz của em" variant="ghost" onPress={() => router.replace('/quiz' as never)} />
          </View> : null}
          {quiz.explanationText ? <View style={s.card}><Text style={s.heading}>Cách giải</Text><QuizVoice key={`${quiz.quizId}:${quiz.startedAt}`} quizId={quiz.quizId} /><MathText style={s.body}>{quiz.explanationText}</MathText></View> : null}
          {quiz.attempts.length ? <View style={s.card}><Text style={s.title}>Những lần em đã thử</Text>
            {quiz.attempts.map(attempt => {
              const isBest = attempt.correct && bestAttemptStars > 0 && (attempt.stars === bestAttemptStars);
              return <View key={attempt.number} style={[s.note, isBest ? { borderColor: '#A66800', borderWidth: 1.5, backgroundColor: '#FFFDF5' } : null]}>
                {attempt.questionText ? <MathText style={s.small}>{attempt.questionText}</MathText> : null}
                <Text style={s.body}>
                  {`Lần ${attempt.number}: ${attempt.answer} · ${attempt.correct ? (attempt.stars ? `${attempt.stars} sao` : attempt.mode === 'PRACTICE' ? 'Đúng (Ôn lại bài)' : attempt.solutionViewed ? 'Đúng (Xem giải)' : 'Đúng') : 'Chưa đúng'}`}
                  {isBest ? '  ★ Kỷ lục tốt nhất' : ''}
                </Text>
                <Text style={s.small}>{`${quizTime(attempt.elapsedMillis)} · ${new Date(attempt.submittedAt).toLocaleString('vi-VN')}`}</Text>
              </View>;
            })}
            <Text style={s.small}>{`${quiz.attempts.length} lần thử · ${quiz.wrongAttempts} lần chưa đúng`}</Text>
          </View> : null}
          {!done ? <AppButton title="Lưu để làm sau" variant="secondary" disabled={busy} onPress={saveForLater} /> : null}
        </> : null}
        <AppButton title="Trở về danh sách" variant="ghost" onPress={() => router.replace('/quiz' as never)} />
      </ScrollView>
    </KeyboardAvoidingView>
  </SafeAreaView>;
}
