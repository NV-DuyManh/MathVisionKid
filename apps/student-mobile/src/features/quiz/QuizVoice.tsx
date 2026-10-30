import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';
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
  const [voice, setVoice] = useState<NarrationVoice | null>(null);
  const controller = useRef<AbortController | null>(null), asset = useRef<ReturnType<typeof saveNarration> | null>(null);
  const active = useRef(false);
  useEffect(() => { let mounted = true; void readNarrationVoice().then(value => { if (mounted) setVoice(value); }); return () => { mounted = false; }; }, []);
  useFocusEffect(useCallback(() => {
    active.current = true;
    return () => { active.current = false; controller.current?.abort(); controller.current = null; asset.current?.dispose(); asset.current = null; setUri(''); setBusy(false); };
  }, []));
  const prepare = async () => {
    if (!voice || controller.current || uri) return;
    const abort = new AbortController(); controller.current = abort; setBusy(true); setError('');
    try {
      const bytes = await quizApi.audio(quizId, voice, abort.signal);
      if (!active.current || abort.signal.aborted) return;
      asset.current = saveNarration(bytes); setUri(asset.current.uri);
    } catch { if (active.current && !abort.signal.aborted) setError('Chưa tải được giọng đọc lúc này. Em có thể thử lại nhé.'); }
    finally { if (active.current && !abort.signal.aborted) { controller.current = null; setBusy(false); } }
  };
  return <View style={{ gap: 10 }}>
    <View style={s.groups}>{NARRATION_VOICES.map(option => <AppButton key={option.id} title={`${voice === option.id ? '✓ ' : ''}${option.name}`} variant="secondary" disabled={busy}
      accessibilityLabel={`${option.name}, ${option.description}${voice === option.id ? ', đang chọn' : ''}`}
      onPress={() => { if (option.id !== voice) { setUri(''); asset.current?.dispose(); asset.current = null; setVoice(option.id); setError(''); void saveNarrationVoice(option.id).catch(() => {}); } }} />)}</View>
    {!uri ? <AppButton title={error ? 'Thử tải giọng đọc lại' : 'Nghe cách giải'} disabled={!voice || busy} loading={busy}
      icon={<Ionicons name="volume-high-outline" size={22} color="white" accessible={false} />} onPress={() => void prepare()} />
      : <AudioPlayback key={uri} uri={uri} title="Nghe cách giải" subtitle="Em bấm phát để nghe, có thể dừng hoặc tua lại" />}
    {error ? <Text accessibilityRole="alert" style={s.error}>{error} Em vẫn đọc được phần chữ bên dưới.</Text> : null}
  </View>;
}
