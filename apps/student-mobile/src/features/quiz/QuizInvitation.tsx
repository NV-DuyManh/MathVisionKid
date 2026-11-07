import React, { useCallback, useContext, useRef, useState } from 'react';
import { Image, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { PendingTask } from '../../components/ui/PendingTask';
import { AuthContext } from '../../context/AuthContext';
import { quizApi, Quiz, quizError, quizErrorCode } from './quizApi';
import { quizStyles as s } from './quizStyles';

type Source = { sourceType: Quiz['sourceType']; sourceId: string };

export function QuizAfterLearningButton(props: Source) {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id || auth?.user?.userId || '';
  return <ReadyQuizEntry key={`${owner}:${props.sourceType}:${props.sourceId}`} {...props} />;
}

function ReadyQuizEntry({ sourceType, sourceId }: Source) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [busy, setBusy] = useState(true), [failed, setFailed] = useState(false), [retry, setRetry] = useState(0);
  useFocusEffect(useCallback(() => {
    const abort = new AbortController();
    setQuiz(null); setBusy(true); setFailed(false);
    // Publish to the library after completion even if the student goes straight home.
    void quizApi.fromLearning(sourceType, sourceId, abort.signal).then(response => {
      if (!abort.signal.aborted) setQuiz(response.quiz);
    }).catch(error => {
      if (!abort.signal.aborted) setFailed(!['QUIZ_UNSUPPORTED', 'QUIZ_SOURCE_NOT_COMPLETE', 'QUIZ_SOURCE_CHANGED'].includes(quizErrorCode(error) || ''));
    }).finally(() => { if (!abort.signal.aborted) setBusy(false); });
    return () => abort.abort();
  }, [sourceType, sourceId, retry]));

  if (busy) return <PendingTask title="Đang chuẩn bị Quiz…" detail="Sao đang kiểm tra câu luyện tập. Em có thể về trang chủ; bài đã hoàn thành vẫn được giữ."/>;
  if (failed) return <RecoveryNotice title="Chưa tải được Quiz" message="Bài học của em đã hoàn thành. Em có thể thử tải lại Quiz."
    actions={[{ label: 'Thử lại Quiz', icon: 'refresh-outline', onPress: () => setRetry(value => value + 1) }]} />;
  if (!quiz) return null;
  const title = quiz.status === 'COMPLETED' ? 'Xem kết quả Quiz' : quiz.status === 'IN_PROGRESS' ? 'Tiếp tục Quiz'
    : quiz.topicCode === 'CHECKED_SOURCE_REVIEW' ? 'Ôn lại bài vừa học' : 'Thử sức với Quiz';
  return <AppButton title={title} variant="secondary" onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />;
}

/** Only a verified server offer can open a Quiz. */
export function QuizInvitation({ sourceType, sourceId }: Source) {
  return <Invitation key={sourceType + ':' + sourceId} sourceType={sourceType} sourceId={sourceId} />;
}
function Invitation({ sourceType, sourceId }: Source) {
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null), [busy, setBusy] = useState(true), [offered, setOffered] = useState(false);
  const [error, setError] = useState('');
  const [replaying, setReplaying] = useState<'PRACTICE' | 'CHALLENGE' | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const controller = useRef<AbortController | null>(null), active = useRef(false);
  const prepare = useCallback(async () => {
    if (controller.current) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError(''); setUnavailable(false);
    try {
      const response = await quizApi.fromLearning(sourceType, sourceId, abort.signal);
      if (active.current && !abort.signal.aborted) { setQuiz(response.quiz); setOffered(response.offered); }
    } catch (failure) {
      if (active.current && !abort.signal.aborted) {
        setQuiz(null);
        setUnavailable(quizErrorCode(failure) === 'QUIZ_UNSUPPORTED');
        setError(quizError(failure));
      }
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
    const abort = new AbortController(); controller.current = abort; setBusy(true); setReplaying(mode); setError('');
    try {
      await quizApi.replay(quiz.quizId, mode, abort.signal);
      if (active.current && !abort.signal.aborted) router.push(`/quiz/${quiz.quizId}` as never);
    } catch (failure) {
      if (active.current && !abort.signal.aborted) setError(quizError(failure));
    } finally {
      if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); setReplaying(null); }
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
      <AppButton title="Làm lại" loadingTitle="Đang chuẩn bị câu mới…" disabled={busy} loading={replaying === 'CHALLENGE'} onPress={() => void handleReplay('CHALLENGE')} />
      <AppButton title="Ôn lại bài cũ" loadingTitle="Đang mở lại bài…" variant="secondary" disabled={busy} loading={replaying === 'PRACTICE'} onPress={() => void handleReplay('PRACTICE')} />
      <AppButton title="Xem kết quả" variant="ghost" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
    </>;
  };

  if (!quiz) return <View style={s.card}>
    <Text style={s.title}>{unavailable ? 'Chưa có Quiz cùng dạng' : 'Quiz sau bài học'}</Text>
    {busy ? <PendingTask title="Đang chuẩn bị Quiz…" detail="Sao đang kiểm tra câu luyện tập cho em."/> : <Text style={s.body} accessibilityLiveRegion="polite">{error}</Text>}
    {error && !unavailable ? <AppButton title="Thử lại Quiz" variant="secondary" disabled={busy} onPress={() => void prepare()} /> : null}
  </View>;
  return <View style={s.card}>
    {offered ? <>
      <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={s.mascot} accessible={false} />
      <Text style={s.heading}>{quiz.topicCode === 'CHECKED_SOURCE_REVIEW' ? 'Ôn chắc bài vừa học' : 'Một thử thách cùng Sao!'}</Text>
      <Text style={s.body}>{quiz.topicCode === 'CHECKED_SOURCE_REVIEW'
        ? 'Em ôn lại đề vừa làm để nhớ cách giải. Câu này giữ các dữ kiện của bài gốc.'
        : 'Em có thể luyện thêm một câu cùng dạng toán vừa học.'}</Text>
      <AppButton title="Làm ngay" disabled={busy} onPress={() => router.push(`/quiz/${quiz.quizId}` as never)} />
      <AppButton title="Để khi khác" variant="secondary" disabled={busy} loading={busy} onPress={() => void defer()} />
    </> : renderExistingQuiz()}
    {error ? <Text accessibilityRole="alert" style={s.error}>{error}</Text> : null}
  </View>;
}
