import React, { useCallback, useContext, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { COLORS, FONTS } from '../../constants/theme';
import { onQuizChanged, quizApi } from './quizApi';

export function QuizShortcut() {
  const auth = useContext(AuthContext);
  const scope = auth?.user?.id || auth?.user?.userId;
  return scope ? <Shortcut key={scope} /> : null;
}
function Shortcut() {
  const router = useRouter();
  const [count, setCount] = useState<number | null>(null), [error, setError] = useState(false);
  useFocusEffect(useCallback(() => {
    let active = true, sequence = 0;
    const abort = new AbortController();
    const refresh = () => {
      const current = ++sequence;
      void quizApi.count(abort.signal).then(result => {
        if (active && current === sequence) { setCount(result.pendingCount); setError(false); }
      }).catch(() => { if (active && !abort.signal.aborted && current === sequence) { setCount(null); setError(true); } });
    };
    refresh(); const unsubscribe = onQuizChanged(refresh);
    return () => { active = false; abort.abort(); unsubscribe(); };
  }, []));
  return <View style={styles.outer}>
    <Pressable accessibilityRole="button" accessibilityLabel={`Quiz của em${count ? `, ${count} Quiz chưa hoàn thành` : ''}`}
      onPress={() => router.push('/quiz' as never)} style={({ pressed }) => [styles.card, pressed && { opacity: .75 }]}>
      <View style={styles.icon}><Ionicons name="star-outline" size={30} color={COLORS.primaryDark} accessible={false} /></View>
      <View style={styles.copy}><Text style={styles.title}>Quiz của em</Text><Text style={styles.body}>Thử sức với những câu đố được tạo từ bài em vừa học</Text></View>
      {count !== null && count > 0 ? <View style={styles.badge} accessible={false}><Text style={styles.badgeText}>{count > 99 ? '99+' : count}</Text></View> : null}
      <Ionicons name="chevron-forward" color={COLORS.primaryDark} size={20} accessible={false} />
    </Pressable>
    {error ? <Pressable accessibilityRole="button" onPress={() => router.push('/quiz' as never)} style={styles.retry}><Text style={styles.body}>Chưa tải được số Quiz. Mở danh sách để thử lại.</Text></Pressable> : null}
  </View>;
}
const styles = StyleSheet.create({
  outer: { marginBottom: 20, gap: 8 }, card: { minHeight: 96, padding: 16, gap: 12, flexDirection: 'row', alignItems: 'center', borderRadius: 24, borderWidth: 1, borderColor: '#DFD0F5', backgroundColor: '#F5EFFF' },
  icon: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#E9DDFB' },
  copy: { flex: 1, minWidth: 0, gap: 4 }, title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 19 },
  body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
  badge: { minWidth: 26, minHeight: 26, borderRadius: 15, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center', backgroundColor: '#A73568' },
  badgeText: { color: '#FFF', fontSize: 13, fontFamily: FONTS.bold }, retry: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 12 },
});
