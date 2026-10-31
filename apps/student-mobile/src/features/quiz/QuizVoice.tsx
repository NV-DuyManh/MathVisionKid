import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { AudioPlayback } from '../tutoring/AudioPlayback';
import { saveNarration } from '../tutoring/narrationFile';
import { NARRATION_VOICES, NarrationVoice, readNarrationVoice, saveNarrationVoice } from '../tutoring/narrationVoices';
import { quizApi } from './quizApi';
import { quizStyles as s } from './quizStyles';

export function QuizVoice({ quizId }: { quizId: string }) {
  const [uri, setUri] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [voice, setVoice] = useState<NarrationVoice | null>(null), [ready, setReady] = useState(false);
  const controller = useRef<AbortController | null>(null), asset = useRef<ReturnType<typeof saveNarration> | null>(null);
  const active = useRef(false);
  useEffect(() => { let mounted = true; void readNarrationVoice().then(value => { if (mounted) setVoice(value); }); return () => { mounted = false; }; }, []);
  const cancel = useCallback(() => {
    const previous = controller.current; controller.current = null; previous?.abort();
    asset.current?.dispose(); asset.current = null; setUri(''); setBusy(false); setReady(false);
  }, []);
  useFocusEffect(useCallback(() => {
    active.current = true;
    const listener = AppState.addEventListener('change', state => { if (state !== 'active') cancel(); });
    return () => { active.current = false; listener.remove(); cancel(); };
  }, [quizId, cancel]));
  const prepare = async () => {
    if (!voice || controller.current || uri) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    let timer: ReturnType<typeof setTimeout> | undefined, timedOut = false;
    let cancelled: (() => void) | undefined;
    try {
      // Cover interceptors/refresh and an unresponsive native transport as well as HTTP.
      const bytes = await Promise.race([quizApi.audio(quizId, voice, abort.signal), new Promise<never>((_, reject) => {
        cancelled = () => reject(new Error('Cancelled'));
        abort.signal.addEventListener('abort', cancelled, { once: true });
        timer = setTimeout(() => { timedOut = true; abort.abort(); }, 45000);
      })]);
      if (!active.current || controller.current !== abort || abort.signal.aborted) return;
      asset.current = saveNarration(bytes); setUri(asset.current.uri);
    } catch { if (active.current && controller.current === abort && (timedOut || !abort.signal.aborted)) setError(timedOut ? 'Giọng đọc chuẩn bị lâu hơn dự kiến. Em thử lại nhé.' : 'Chưa tải được giọng đọc lúc này. Em có thể thử lại nhé.'); }
    finally {
      clearTimeout(timer); if (cancelled) abort.signal.removeEventListener('abort', cancelled);
      if (active.current && controller.current === abort) { controller.current = null; setBusy(false); }
    }
  };
  const playbackError = useCallback(() => {
    cancel(); setError('Chưa mở được âm thanh. Em thử tải giọng đọc lại nhé.');
  }, [cancel]);
  const playbackReady = useCallback(() => setReady(true), []);
  return <View style={{ gap: 10 }}>
    <View style={s.groups}>{NARRATION_VOICES.map(option => <AppButton key={option.id} title={`${voice === option.id ? '✓ ' : ''}${option.name}`} variant="secondary"
      accessibilityLabel={`${option.name}${voice === option.id ? ', đang chọn' : ''}`}
      onPress={() => { if (option.id !== voice) { cancel(); setVoice(option.id); setError(''); void saveNarrationVoice(option.id).catch(() => {}); } }} />)}</View>
    <Text accessibilityLiveRegion="polite" style={s.small}>{busy ? 'Đang tạo giọng đọc…' : uri ? ready ? 'Giọng đọc đã sẵn sàng. Em bấm phát để nghe nhé.' : 'Đang mở âm thanh…' : error ? 'Giọng đọc chưa sẵn sàng.' : 'Em chọn giọng rồi bấm nghe cách giải nhé.'}</Text>
    {!uri ? <AppButton title={busy ? 'Đang tạo giọng đọc…' : error ? 'Thử tải giọng đọc lại' : 'Nghe cách giải'} disabled={!voice || busy}
      icon={<Ionicons name="volume-high-outline" size={22} color="white" accessible={false} />} onPress={() => void prepare()} />
      : <AudioPlayback key={uri} uri={uri} title="Nghe cách giải" subtitle="Em bấm phát để nghe, có thể dừng hoặc tua lại" onError={playbackError} onReady={playbackReady} />}
    {error ? <Text accessibilityRole="alert" style={s.error}>{error} Em vẫn đọc được phần chữ bên dưới.</Text> : null}
  </View>;
}
