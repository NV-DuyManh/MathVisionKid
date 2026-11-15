import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { FONTS, WEB_DESIGN } from '../../constants/theme';
import apiClient from '../../services/api/apiClient';
import AssignedSubmission from '../../features/recognition/AssignedSubmission.web';

type Assignment = { assignmentId: string; className: string; teacherName: string; title: string; prompt: string; instructions?: string; maxScore: number; publishedAt: string };

export default function StudentAssignments() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const router = useRouter();
  const [items, setItems] = useState<Assignment[]>([]);
  const [selected, setSelected] = useState<Assignment | null>(null);
  const [retry, setRetry] = useState(0);
  const [request, setRequest] = useState<{ key: string; status: 'loading' | 'success' | 'error' }>({ key: '', status: 'loading' });
  const requestKey = `${id ? `assignment:${id}` : 'list'}:${retry}`;
  const handleUnavailable = useCallback(() => {
    setSelected(null);
    setRequest({ key: requestKey, status: 'error' });
  }, [requestKey]);
  const isCurrentRequest = request.key === requestKey;
  const isLoading = !isCurrentRequest || request.status === 'loading';
  const hasError = isCurrentRequest && request.status === 'error';
  const hasData = isCurrentRequest && request.status === 'success';
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const url = id ? `/student/assignments/${encodeURIComponent(id)}` : '/student/assignments';
    apiClient.get(url, { signal: controller.signal }).then(({ data }) => {
      if (!active) return;
      if (id) setSelected(data);
      else setItems(data);
      setRequest({ key: requestKey, status: 'success' });
    }).catch(() => {
      if (active) setRequest({ key: requestKey, status: 'error' });
    });
    return () => { active = false; controller.abort(); };
  }, [id, requestKey]);

  return <ScrollView contentContainerStyle={styles.container}>
    {id && <Pressable accessibilityRole="button" style={styles.back} onPress={() => router.replace('/(tabs)/assignments')}><Text style={styles.link}>‹ Quay lại Bài của em</Text></Pressable>}
    {hasData && id && selected && <Text accessibilityRole="header" style={styles.heading}>{selected.title}</Text>}
    {!id && <Text accessibilityRole="header" style={styles.heading}>Bài của em</Text>}
    {id && isLoading && <Text accessibilityRole="header" style={styles.heading}>Đang mở bài</Text>}
    {!selected && <Text style={styles.subheading}>Những bài cô/thầy đã giao cho lớp em.</Text>}
    {isLoading && <View style={styles.center}><ActivityIndicator accessibilityLabel="Đang tải bài tập" /><Text style={styles.copy}>Đang tải bài tập…</Text></View>}
    {hasError && <View style={styles.card}><Text accessibilityRole="alert" style={styles.copy}>{id ? 'Bài này không còn khả dụng hoặc em chưa được giao bài.' : 'Chưa tải được bài tập. Em thử lại nhé.'}</Text><Button label="Thử lại" onPress={() => setRetry(value => value + 1)} /></View>}
    {hasData && !id && items.length === 0 && <View style={styles.card}><Text style={styles.cardTitle}>Chưa có bài tập mới</Text><Text style={styles.copy}>Khi cô/thầy giao bài, bài sẽ hiện ở đây.</Text><Link href="/(tabs)/classes" asChild><Pressable style={styles.button}><Text style={styles.buttonText}>Xem lớp của em</Text></Pressable></Link></View>}
    {hasData && !id && items.map(item => <Link key={item.assignmentId}
      href={{ pathname: '/(tabs)/assignments', params: { id: item.assignmentId } }} asChild>
      <Pressable accessibilityRole="link" accessibilityLabel={`Mở bài ${item.title}, lớp ${item.className}`} style={styles.card}>
        <Text style={styles.cardTitle}>{item.title}</Text><Text style={styles.copy}>{item.className} · Cô/thầy {item.teacherName}</Text>
        <Text style={styles.preview} numberOfLines={2}>{item.prompt}</Text><Text style={styles.link}>Mở bài tập ›</Text>
      </Pressable>
    </Link>)}
    {hasData && id && selected && <>
      <Text style={styles.meta}>{selected.className} · Cô/thầy {selected.teacherName} · {selected.maxScore} điểm</Text>
      <View style={styles.card}><Text style={styles.cardTitle}>Đề bài</Text><Text selectable style={styles.prompt}>{selected.prompt}</Text></View>
      {!!selected.instructions && <View style={styles.card}><Text style={styles.cardTitle}>Hướng dẫn của cô/thầy</Text><Text selectable style={styles.copy}>{selected.instructions}</Text></View>}
      <View style={styles.note}><Text style={styles.copy}>Em hãy làm bài vào vở nhé!</Text></View>
      <AssignedSubmission key={id} assignmentId={id} maxScore={selected.maxScore} onUnavailable={handleUnavailable} />
    </>}
  </ScrollView>;
}

function Button({ label, onPress }: { label: string; onPress: () => void }) {
  return <Pressable accessibilityRole="button" onPress={onPress} style={styles.button}><Text style={styles.buttonText}>{label}</Text></Pressable>;
}

const styles = StyleSheet.create({
  container: { width: '100%', maxWidth: 760, alignSelf: 'center', padding: 20, paddingBottom: 120, gap: 14 },
  back: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start' },
  heading: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.black, fontSize: 30 },
  subheading: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 17, marginTop: -8, marginBottom: 4 },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: WEB_DESIGN.colors.paperLine, borderRadius: 18, padding: 20, gap: 10 },
  cardTitle: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.bold, fontSize: 21 },
  copy: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 17, lineHeight: 25 },
  preview: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 18, lineHeight: 28 },
  prompt: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.semiBold, fontSize: 23, lineHeight: 36 },
  meta: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 16 },
  link: { color: WEB_DESIGN.colors.blue, fontFamily: FONTS.bold, fontSize: 16, minHeight: 44, paddingTop: 8 },
  button: { backgroundColor: WEB_DESIGN.colors.blue, borderRadius: 12, minHeight: 48, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 18 },
  buttonText: { color: '#fff', fontFamily: FONTS.bold, fontSize: 17 },
  center: { alignItems: 'center', gap: 12, padding: 30 },
  note: { borderRadius: 16, padding: 18, backgroundColor: WEB_DESIGN.colors.blueLight },
});
