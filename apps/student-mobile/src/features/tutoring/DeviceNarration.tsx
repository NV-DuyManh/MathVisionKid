import React, { useEffect, useRef, useState } from 'react';
import { AppState, Platform, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { FONTS, COLORS } from '../../constants/theme';
import { getAvailableVoicesAsync, speak, stop } from './speechOutput';
import { narrationChunks, vietnameseVoices } from './narration';
import { preparePlaybackSession } from './playbackSession';

/** Independent of the server's voice provider. Device engines may need a Vietnamese voice installed. */
export function DeviceNarration({ paragraphs, onFinished, onReturn }: { paragraphs: string[]; onFinished?: () => void; onReturn?: () => void }) {
  const [voice, setVoice] = useState(''), [state, setState] = useState('loading');
  const [lookup, setLookup] = useState(0);
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
  }, [navigation, lookup]);
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
          onDone: () => { if (id === generation.current) { clearTimeout(watchdog.current); next(index + 1); } }, onError: fail });
      } catch { fail(); }
    };
    watchdog.current = setTimeout(fail, 8000);
    try { await stop(); if (id !== generation.current) return; if (Platform.OS !== 'web') await preparePlaybackSession(); if (id === generation.current) next(0); } catch { fail(); }
  };
  if (state === 'unavailable' || state === 'failed') return <RecoveryNotice
    title={state === 'unavailable' ? 'Chưa có giọng Việt trên thiết bị' : 'Giọng thiết bị chưa phát được'}
    message="Em vẫn có thể mở lời giảng để đọc."
    actions={[
      { label: 'Thử lại', accessibilityLabel: 'Thử lại giọng thiết bị', icon: 'refresh-outline', onPress: () => { if (voice) void play(); else { setVoice(''); setState('loading'); setLookup(value => value + 1); } } },
      ...(onReturn ? [{ label: 'Giọng chính', accessibilityLabel: 'Quay lại giọng đã chọn', onPress: onReturn }] : []),
    ]} />;
  return <View style={styles.player}>
    <View style={styles.heading}><View style={styles.icon}><Ionicons name="headset-outline" size={24} color={COLORS.primaryDark} accessible={false}/></View>
      <View style={{flex:1,minWidth:0}}><Text style={styles.title}>Cùng nghe bài nhé</Text><Text style={styles.caption}>Giọng có sẵn · Tiếng Việt</Text></View></View>
    <View style={styles.status}><Ionicons name={state==='speaking'?'volume-high-outline':'flash-outline'} color="#286B57" size={16} accessible={false}/><Text accessibilityLiveRegion="polite" style={[styles.caption,styles.statusText]}>
      {state === 'loading' ? 'Đang mở giọng đọc trên máy…' : state === 'speaking' ? 'Đang đọc · Em có thể dừng bất cứ lúc nào' : 'Bấm phát để nghe. Âm sắc tùy thiết bị.'}
    </Text></View>
    {voice ? <AppButton title={state === 'speaking' ? 'Dừng đọc' : 'Phát giọng có sẵn'} style={{borderRadius:18}} icon={<Ionicons name={state==='speaking'?'stop':'play'} size={20} color="white" accessible={false}/>} onPress={() => { void play(); }} /> : null}
  </View>;
}
const styles=StyleSheet.create({
  player:{gap:16,padding:18,borderRadius:24,borderWidth:1,borderColor:'#E4DCEF',backgroundColor:COLORS.surface},
  heading:{flexDirection:'row',alignItems:'center',gap:10},icon:{width:40,height:44,borderRadius:15,alignItems:'center',justifyContent:'center',backgroundColor:COLORS.primaryLight},
  title:{fontFamily:FONTS.extraBold,fontSize:16,lineHeight:23,color:COLORS.textPrimary},caption:{fontFamily:FONTS.regular,fontSize:12,lineHeight:20,color:COLORS.textSecondary},
  status:{flexDirection:'row',alignItems:'center',gap:8,padding:12,borderRadius:14,backgroundColor:'#F0F8F3'},statusText:{flex:1,color:'#286B57'},
});
