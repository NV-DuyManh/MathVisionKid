import React from 'react';
import { AudioPlayback } from './AudioPlayback';

export function QuestionRecording({ uri, durationMillis }: { uri: string; durationMillis: number }) {
  return <AudioPlayback key={uri} uri={uri} title="Câu hỏi vừa ghi" subtitle="Nghe lại trước khi gửi" durationHint={durationMillis / 1000} question />;
}
