import { Link, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { FONTS, WEB_DESIGN } from '../../../constants/theme';
import apiClient from '../../../services/api/apiClient';

type Assignment = { className: string; teacherName: string; title: string; prompt: string; instructions?: string; maxScore: number };

export default function StudentAssignmentDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [item, setItem] = useState<Assignment | null>(null);
  const [request, setRequest] = useState<{ id: string; status: 'loading' | 'ready' | 'error' }>({ id, status: 'loading' });
  const isCurrent = request.id === id;
  const loading = !isCurrent || request.status === 'loading';
  const error = isCurrent && request.status === 'error';
  const currentItem = isCurrent && request.status === 'ready' ? item : null;
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    apiClient.get(`/student/assignments/${encodeURIComponent(id ?? '')}`, { signal: controller.signal })
      .then(({ data }) => {
        if (active) {
          setItem(data);
          setRequest({ id, status: 'ready' });
        }
      })
      .catch(() => {
        if (active) {
          setItem(null);
          setRequest({ id, status: 'error' });
        }
      });
    return () => { active = false; controller.abort(); };
  }, [id]);

  return <ScrollView contentContainerStyle={styles.container}>
    <Link href="/(tabs)/assignments" asChild><Pressable accessibilityRole="link" style={styles.back}><Text style={styles.link}>‹ Quay lại Bài của em</Text></Pressable></Link>
    {loading && <View style={styles.center}><ActivityIndicator accessibilityLabel="Đang tải bài tập" /><Text style={styles.copy}>Đang mở bài…</Text></View>}
    {error && <View style={styles.card}><Text accessibilityRole="alert" style={styles.copy}>Bài này không còn khả dụng hoặc em chưa được giao bài.</Text><Link href="/(tabs)/assignments" asChild><Pressable style={styles.button}><Text style={styles.buttonText}>Về danh sách bài</Text></Pressable></Link></View>}
    {loading && <Text accessibilityRole="header" style={styles.heading}>Đang mở bài</Text>}
    {currentItem && <>
      <Text accessibilityRole="header" style={styles.heading}>{currentItem.title}</Text>
      <Text style={styles.meta}>{currentItem.className} · Cô/thầy {currentItem.teacherName} · {currentItem.maxScore} điểm</Text>
      <View style={styles.card}><Text accessibilityRole="header" style={styles.cardTitle}>Đề bài</Text><Text selectable style={styles.prompt}>{currentItem.prompt}</Text></View>
      {!!currentItem.instructions && <View style={styles.card}><Text accessibilityRole="header" style={styles.cardTitle}>Hướng dẫn của cô/thầy</Text><Text selectable style={styles.copy}>{currentItem.instructions}</Text></View>}
      <View style={styles.note}><Text style={styles.noteText}>Em hãy làm bài vào vở nhé!</Text></View>
    </>}
  </ScrollView>;
}

const styles = StyleSheet.create({
  container: { width: '100%', maxWidth: 760, alignSelf: 'center', padding: 20, paddingBottom: 120, gap: 16 },
  back: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start' },
  heading: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.black, fontSize: 30, lineHeight: 38 },
  meta: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 16 },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: WEB_DESIGN.colors.paperLine, borderRadius: 18, padding: 22, gap: 12 },
  cardTitle: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.bold, fontSize: 21 },
  prompt: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.semiBold, fontSize: 23, lineHeight: 36 },
  copy: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 18, lineHeight: 29 },
  link: { color: WEB_DESIGN.colors.blue, fontFamily: FONTS.bold, fontSize: 16 },
  note: { borderRadius: 16, padding: 18, backgroundColor: WEB_DESIGN.colors.blueLight },
  noteText: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.bold, fontSize: 19, textAlign: 'center' },
  button: { backgroundColor: WEB_DESIGN.colors.blue, borderRadius: 12, minHeight: 48, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  buttonText: { color: '#fff', fontFamily: FONTS.bold, fontSize: 17 }, center: { alignItems: 'center', gap: 12, padding: 30 },
});
