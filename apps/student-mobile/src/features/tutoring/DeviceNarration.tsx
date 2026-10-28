import React, { useEffect, useRef, useState } from 'react';
import { AppState, Platform, Text, View } from 'react-native';
import { useNavigation } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { FONTS, COLORS } from '../../constants/theme';
import { getAvailableVoicesAsync, speak, stop } from './speechOutput';
import { narrationChunks, vietnameseVoices } from './narration';
import { preparePlaybackSession } from './playbackSession';

/** Independent of the server's voice provider. Device engines may need a Vietnamese voice installed. */
export function DeviceNarration({ paragraphs, onFinished }: { paragraphs: string[]; onFinished?: () => void }) {
  const [voice, setVoice] = useState(''), [state, setState] = useState('loading');
  const generation = useRef(0), navigation = useNavigation();
  const watchdog = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => { if (active) setState('unavailable'); }, 5000);
    void getAvailableVoicesAsync().then(voices => {
      if (!active) return;
      const selected = vietnameseVoices(voices)[0];
      setVoice(selected?.identifier || ''); setState(selected ? 'ready' : 'unavailable');
    }).catch(() => { if (active) setState('unavailable'); }).finally(() => clearTimeout(timer));
    const cancel = () => { ++generation.current; clearTimeout(watchdog.current); void stop().catch(() => {}); if (active) setState(value => value === 'speaking' ? 'ready' : value); };
    const blur = navigation.addListener('blur', cancel);
    const listener = AppState.addEventListener('change', next => { if (next !== 'active') cancel(); });
    return () => { active = false; cancel(); clearTimeout(timer); blur(); listener.remove(); };
  }, [navigation]);
  const play = async () => {
    const id = ++generation.current;
    clearTimeout(watchdog.current);
    if (state === 'speaking') { void stop().catch(() => {}); setState('ready'); return; }
    setState('speaking');
    const chunks = narrationChunks(paragraphs);
    const fail = () => { if (id === generation.current) { ++generation.current; clearTimeout(watchdog.current); void stop().catch(() => {}); setState('failed'); } };
    const next = (index: number) => {
      if (id !== generation.current) return;
      if (index >= chunks.length) { setState('ready'); onFinished?.(); return; }
      clearTimeout(watchdog.current); watchdog.current = setTimeout(fail, 8000);
      try {
        speak(chunks[index], { voice, language: 'vi-VN', rate: .9,
          onStart: () => { if (id === generation.current) { clearTimeout(watchdog.current); watchdog.current = setTimeout(fail, 90000); } },
          onDone: () => { clearTimeout(watchdog.current); next(index + 1); }, onError: fail });
      } catch { fail(); }
    };
    watchdog.current = setTimeout(fail, 8000);
    try { await stop(); if (id !== generation.current) return; if (Platform.OS !== 'web') await preparePlaybackSession(); if (id === generation.current) next(0); } catch { fail(); }
  };
  return <View style={{ gap: 10, padding: 16, borderRadius: 18, backgroundColor: '#F1EDFC' }}>
    <Text style={{ fontFamily: FONTS.bold, color: COLORS.textPrimary }}>Giọng Việt trên thiết bị</Text>
    <Text accessibilityLiveRegion="polite" style={{ fontFamily: FONTS.regular, fontSize: 13, lineHeight: 21, color: COLORS.textSecondary }}>
      {state === 'loading' ? 'Đang tìm giọng Việt, tối đa 5 giây…' : state === 'unavailable' ? 'Thiết bị chưa có giọng Việt phù hợp. Em có thể đọc lời giảng hoặc thử lại giọng chính.'
        : state === 'failed' ? 'Giọng thiết bị chưa phát được. Em có thể thử lại hoặc đọc lời giảng.' : 'Giọng có thể khác Nam Minh và Hoài My. Cách đọc này hỗ trợ dừng và nghe lại từ đầu; không có thanh tua.'}
    </Text>
    {voice ? <AppButton title={state === 'speaking' ? 'Dừng đọc' : 'Nghe từ đầu'} variant="secondary" onPress={() => { void play(); }} /> : null}
  </View>;
}
