import React, { useCallback, useRef, useState } from 'react';
import { Image, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { quizApi, Quiz, quizError } from './quizApi';
import { quizStyles as s } from './quizStyles';

/** Only mounted after completion. A verified server offer is required before showing any invitation. */
export function QuizInvitation({ sourceType, sourceId }: { sourceType: 'LESSON' | 'WORK_REVIEW'; sourceId: string }) {
  return <Invitation key={`${sourceType}:${sourceId}`} sourceType={sourceType} sourceId={sourceId} />;
}
function Invitation({ sourceType, sourceId }: { sourceType: 'LESSON' | 'WORK_REVIEW'; sourceId: string }) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [busy, setBusy] = useState(false), [offered, setOffered] = useState(false);
  const [error, setError] = useState('');
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const prepare = useCallback(async () => {
    if (controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      const response = await quizApi.fromLearning(sourceType, sourceId, abort.signal);
      if (active.current && !abort.signal.aborted) { setQuiz(response.quiz); setOffered(response.offered); }
    } catch (failure) {
      if (active.current && !abort.signal.aborted) setError(quizError(failure));
    } finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  }, [sourceType, sourceId]);
  useFocusEffect(React.useCallback(() => {
    active.current = true;
    void prepare();
    return () => { active.current = false; controller.current?.abort(); controller.current = null; setBusy(false); };
  }, [prepare]));
  const defer = async () => {
    if (!quiz || controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      await quizApi.defer(quiz.quizId, abort.signal);
      if (active.current && !abort.signal.aborted) router.replace('/(tabs)');
    } catch (failure) { if (active.current && !abort.signal.aborted) setError(quizError(failure)); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  };
  const handleReplay = async (mode: 'PRACTICE' | 'CHALLENGE' = 'CHALLENGE') => {
    if (!quiz || controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      await quizApi.replay(quiz.quizId, mode, abort.signal);
      if (active.current && !abort.signal.aborted) router.push(`/quiz/${quiz.quizId}` as never);
    } catch (failure) {
      if (active.current && !abort.signal.aborted) setError(quizError(failure));
    } finally {
      if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); }
    }
  };

  const renderExistingQuiz = () => {
    if (!quiz) return null;
    if (quiz.status === 'READY' || quiz.status === 'DEFERRED') {
      return <>
        <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
        <Text style={s.heading}>Quiz đang chờ em!</Text>
        <Text style={s.body}>Em đã có một Quiz từ bài này rồi. Quiz đang chờ em làm nhé!</Text>
        <AppButton title="Làm Quiz" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
        <AppButton title="Để khi khác" variant="secondary" disabled={busy} loading={busy} onPress={() => void defer()} />
      </>;
    }
    if (quiz.status === 'IN_PROGRESS') {
      return <>
        <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
        <Text style={s.heading}>Quiz đang làm dở</Text>
        <Text style={s.body}>Em đang làm dở Quiz của bài này.</Text>
        <AppButton title="Tiếp tục làm" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
        <AppButton title="Để khi khác" variant="secondary" disabled={busy} loading={busy} onPress={() => void defer()} />
      </>;
    }
    // COMPLETED
    return <>
      <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
      <Text style={s.heading}>Em đã hoàn thành Quiz này!</Text>
      <Text style={s.body}>Em đã hoàn thành Quiz của bài này rồi! Em có thể thử thách câu hỏi mới để nâng sao, hoặc ôn lại câu hỏi cũ nhé.</Text>
      <AppButton title="Làm lại" disabled={busy} loading={busy} onPress={() => void handleReplay('CHALLENGE')} />
      <AppButton title="Ôn lại bài cũ" variant="secondary" disabled={busy} loading={busy} onPress={() => void handleReplay('PRACTICE')} />
      <AppButton title="Xem kết quả" variant="ghost" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
    </>;
  };

  // A failed/unsupported offer must not become a second error screen after a completed lesson.
  if (!quiz) return null;
  return <View style={s.card}>
    {offered && quiz ? <>
      <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
      <Text style={s.heading}>Một thử thách cùng Sao!</Text>
      <Text style={s.body}>Em có thể luyện thêm một câu cùng dạng toán vừa học.</Text>
      <AppButton title="Làm ngay" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
      <AppButton title="Để khi khác" variant="secondary" disabled={busy} loading={busy} onPress={() => void defer()} />
    </> : renderExistingQuiz()}
    {error ? <Text accessibilityRole="alert" style={s.error}>{error}</Text> : null}
    {sourceType === 'WORK_REVIEW' ? <AppButton title="Về trang chủ" variant="ghost" onPress={() => router.replace('/(tabs)')} /> : null}
  </View>;
}
