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
  const [count, setCount] = useState<number | null>(null);
  useFocusEffect(useCallback(() => {
    let active = true, sequence = 0;
    const abort = new AbortController();
    const refresh = () => {
      const current = ++sequence;
      void quizApi.count(abort.signal).then(result => {
        if (active && current === sequence) setCount(result.pendingCount);
      }).catch(() => { if (active && !abort.signal.aborted && current === sequence) setCount(null); });
    };
    refresh(); const unsubscribe = onQuizChanged(refresh);
    return () => { active = false; abort.abort(); unsubscribe(); };
  }, []));
  return <View style={styles.outer}>
    <Pressable accessibilityRole="button" accessibilityLabel={`Câu đố của em${count ? `, ${count} câu chưa hoàn thành` : ''}`}
      onPress={() => router.push('/quiz' as never)} style={({ pressed }) => [styles.card, pressed && { opacity: .75 }]}>
      <View style={styles.icon}><Ionicons name="sparkles-outline" size={22} color={COLORS.primaryDark} accessible={false} /></View>
      <View style={styles.copy}><Text style={styles.title}>Câu đố của em</Text><Text style={styles.body}>Luyện lại từ bài em vừa học</Text></View>
      {count !== null && count > 0 ? <View style={styles.badge} accessible={false}><Text style={styles.badgeText}>{count > 99 ? '99+' : count}</Text></View> : null}
      <Ionicons name="chevron-forward" color={COLORS.primaryDark} size={20} accessible={false} />
    </Pressable>
  </View>;
}
const styles = StyleSheet.create({
  outer: { marginBottom: 20 }, card: { minHeight: 72, paddingVertical: 12, paddingHorizontal: 14, gap: 12, flexDirection: 'row', alignItems: 'center', borderRadius: 18, borderWidth: 1, borderColor: '#E8E1F4', backgroundColor: '#FFF' },
  icon: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: '#F0EAFF' },
  copy: { flex: 1, minWidth: 0, gap: 2 }, title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 15, lineHeight: 21 },
  body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 12, lineHeight: 18 },
  badge: { minWidth: 25, minHeight: 25, borderRadius: 13, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EFE8FD' },
  badgeText: { color: COLORS.primaryDark, fontSize: 12, fontFamily: FONTS.bold },
});
