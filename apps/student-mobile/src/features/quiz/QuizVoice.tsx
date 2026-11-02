import React, { useCallback } from 'react';
import { LessonNarration } from '../tutoring/LessonNarration';
import { NarrationPreparation, useNarrationPreparation } from '../tutoring/NarrationPreparation';
import type { downloadNarration } from '../tutoring/narrationApi';
import { DEFAULT_NARRATION_VOICE, type NarrationVoice } from '../tutoring/narrationVoices';
import { quizApi } from './quizApi';

type Script = { quizId: string; paragraphs?: string[]; content?: 'QUESTION'|'SOLUTION' };
const sourceFor = (quizId: string, content: string) => ({ sessionId: `quiz:${quizId}:${content}`, revision: 0 });

/** Mount with the question, not with the audio sheet. Never warm an unrevealed solution. */
export function QuizNarrationPreparation({ owner, quizId, paragraphs = [], content = 'SOLUTION', children }: Script & { owner: string; children: React.ReactNode }) {
  const download = useCallback<typeof downloadNarration>((source, _parts, signal, voice = DEFAULT_NARRATION_VOICE) => {
    if (source.sessionId !== sourceFor(quizId,content).sessionId) return Promise.reject(new Error('Chưa mở đúng lời giảng.'));
    return quizApi.audio(quizId, voice, signal, content);
  }, [quizId, content]);
  return <NarrationPreparation owner={owner} download={download}>
    <WarmQuiz quizId={quizId} paragraphs={paragraphs} content={content}/>{children}
  </NarrationPreparation>;
}
function WarmQuiz({ quizId, paragraphs = [], content = 'SOLUTION' }: Script) {
  useNarrationPreparation(sourceFor(quizId, content), paragraphs, { wholeLesson: false });
  return null;
}

/** Same voice picker/player as the lesson. Only server-authorized Quiz text is synthesized. */
export function QuizVoice({ quizId, paragraphs = [], content = 'SOLUTION' }: Script) {
  const load = useCallback((voice: NarrationVoice, signal: AbortSignal) => quizApi.audio(quizId,voice,signal,content),[quizId,content]);
  return <LessonNarration scope={`quiz:${quizId}:${content}`} source={sourceFor(quizId,content)} paragraphs={paragraphs} audioLoader={load}/>;
}
