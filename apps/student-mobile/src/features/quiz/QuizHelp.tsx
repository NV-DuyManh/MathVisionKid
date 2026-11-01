import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { LessonQuestion } from '../tutoring/LessonQuestion';
import { LessonResponse, TutorService } from '../tutoring/api/TutorService';
import { Quiz, quizApi, quizError } from './quizApi';
import { quizStyles as s } from './quizStyles';

/** A real lesson context gives Quiz the same recording and Q&A flow. Help is recorded by the server. */
export function QuizHelp({ quiz, onAssisted, onReturn }: { quiz: Quiz; onAssisted: (quiz: Quiz) => void; onReturn: () => void }) {
  const [lesson, setLesson] = useState<LessonResponse | null>(null), [error, setError] = useState(''), [retry, setRetry] = useState(0);
  const { quizId, startedAt, questionText } = quiz;
  useEffect(() => {
    const abort = new AbortController(); setError('');
    void (async () => {
      const assisted = await quizApi.help(quizId, abort.signal);
      if (abort.signal.aborted) return;
      onAssisted(assisted);
      const context = await TutorService.startLesson(questionText, '', { problemConfirmed: true, workConfirmed: false, guidedUnderstanding: true, startWithReading: true }, abort.signal);
      if (!abort.signal.aborted) setLesson(context);
    })().catch(failure => { if (!abort.signal.aborted) setError(quizError(failure)); });
    return () => abort.abort();
  }, [quizId, startedAt, questionText, onAssisted, retry]);
  if (lesson) return <LessonQuestion sessionId={lesson.sessionId} revision={lesson.revision} stepIndex={lesson.stepIndex} scope={`quiz-help:${quizId}:${startedAt}`} onReturn={onReturn}/>;
  return <View style={s.note}>
    {error ? <><Text accessibilityRole="alert" style={s.error}>{error}</Text><AppButton title="Thử lại" variant="secondary" onPress={() => setRetry(value => value + 1)}/></>
      : <><ActivityIndicator color="#7953D8"/><Text style={s.body} accessibilityLiveRegion="polite">Mình đang mở phần hỏi bài…</Text></>}
  </View>;
}
