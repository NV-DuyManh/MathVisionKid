import React, { useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { recognitionDraftStore, logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';

export default function LessonsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [grade, setGrade] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [expanded, setExpanded] = useState<string | null>(null);
  const capture = () => {
    recognitionDraftStore.clearDraft();
    logFlowDomain('ACQUIRE', 'HANDWRITING_TEXT');
    router.push({ pathname: '/camera' as any, params: { mode: 'HANDWRITING_TEXT' } });
  };
  return <ScrollView style={styles.screen} showsVerticalScrollIndicator={false}
    contentContainerStyle={[styles.content, { paddingTop: insets.top + 22 }]}>
    <Text style={styles.title} accessibilityRole="header">Bài học</Text>
    <Text style={styles.subtitle}>Mỗi ngày, khám phá một điều mới!</Text>
    <LinearGradient colors={['#EEE9FF', '#F7F4FF']} style={styles.hero}>
      <View style={styles.heroCopy}><Text style={styles.heroTitle}>Cùng em luyện Toán</Text>
        <Text style={styles.body}>Chọn lớp của em, đọc đề và thử viết lời giải nhé.</Text></View>
      <Image source={require('../../../assets/illustrations/practice-notebook.png')} style={styles.art} resizeMode="contain" accessible={false} />
    </LinearGradient>
    <View style={styles.grades}>
      {([1, 2, 3, 4, 5] as const).map(item => <Pressable key={item} accessibilityRole="button"
        accessibilityLabel={`Chọn Lớp ${item}`} accessibilityState={{ selected: grade === item }}
        onPress={() => { setGrade(item); setExpanded(null); }}
        style={({ pressed }) => [styles.grade, grade === item && styles.gradeSelected, pressed && styles.pressed]}>
        <Text style={[styles.gradeText, grade === item && styles.gradeTextSelected]}>Lớp {item}</Text>
      </Pressable>)}
    </View>
    <Text style={styles.sectionTitle}>Bài luyện tập cho em</Text>
    {getProblemsByGrade(grade).map(problem => <View key={problem.id} style={[styles.problem, SHADOWS.small]}>
      <View style={styles.tags}><Text style={styles.bookTag}>{problem.bookSeries}</Text><Text style={styles.levelTag}>{problem.difficulty}</Text></View>
      <Text style={styles.topic}>{problem.topic}</Text><Text style={styles.problemTitle}>{problem.title}</Text>
      <Text style={styles.body}>{problem.problemText}</Text>
      <Pressable onPress={() => setExpanded(expanded === problem.id ? null : problem.id)} accessibilityRole="button"
        accessibilityState={{ expanded: expanded === problem.id }} accessibilityLabel={`${expanded === problem.id ? 'Ẩn' : 'Xem'} gợi ý: ${problem.title}`} style={styles.hintButton}>
        <Ionicons name="bulb-outline" size={19} color={COLORS.primary} accessible={false} />
        <Text style={styles.hintText}>{expanded === problem.id ? 'Ẩn gợi ý' : 'Xem gợi ý cách giải'}</Text>
        <Ionicons name={expanded === problem.id ? 'chevron-up' : 'chevron-down'} size={17} color={COLORS.primary} accessible={false} />
      </Pressable>
      {expanded === problem.id && <View style={styles.guidance}>
        <Text style={styles.body}>{problem.guidance}</Text><Text style={styles.solutionTitle}>Bài giải tham khảo</Text>
        {problem.sampleSolution.lines.map((line, index) => <Text key={index} style={styles.solution}>{line}</Text>)}
      </View>}
      <Pressable onPress={capture} accessibilityRole="button" accessibilityLabel={`Chụp lời giải: ${problem.title}`}
        style={({ pressed }) => [styles.capture, pressed && styles.pressed]}>
        <Ionicons name="camera-outline" size={21} color={COLORS.surface} accessible={false} /><Text style={styles.captureText}>Chụp bài làm của em</Text>
      </Pressable>
    </View>)}
  </ScrollView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  content: { paddingHorizontal: 20, paddingBottom: 116, maxWidth: 620, width: '100%', alignSelf: 'center' },
  title: { fontFamily: FONTS.black, fontSize: 30, color: COLORS.textPrimary },
  subtitle: { fontFamily: FONTS.regular, fontSize: 15, color: COLORS.textSecondary, marginTop: 5, marginBottom: 20 },
  hero: { flexDirection: 'row', alignItems: 'center', borderRadius: 26, padding: 20, marginBottom: 22 },
  heroCopy: { flex: 1 },
  heroTitle: { fontFamily: FONTS.extraBold, fontSize: 22, color: COLORS.textPrimary, marginBottom: 8 },
  art: { width: '34%', height: 112, marginLeft: 8 },
  grades: { flexDirection: 'row', gap: 6, marginBottom: 24 },
  grade: { flex: 1, minHeight: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EEEBF6' },
  gradeSelected: { backgroundColor: COLORS.primary },
  gradeText: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.textSecondary },
  gradeTextSelected: { color: COLORS.surface },
  sectionTitle: { fontFamily: FONTS.extraBold, fontSize: 20, color: COLORS.textPrimary, marginBottom: 15 },
  problem: { backgroundColor: COLORS.surface, borderRadius: 24, padding: 20, marginBottom: 18 },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 10 },
  bookTag: { fontFamily: FONTS.bold, fontSize: 11, color: COLORS.primaryDark, backgroundColor: COLORS.primaryLight, paddingHorizontal: 9, paddingVertical: 5, borderRadius: 8 },
  levelTag: { fontFamily: FONTS.bold, fontSize: 11, color: '#9F7028', backgroundColor: '#FFF3D5', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 8 },
  topic: { fontFamily: FONTS.semiBold, fontSize: 12, color: COLORS.textMuted, marginBottom: 5 },
  problemTitle: { fontFamily: FONTS.extraBold, fontSize: 19, color: COLORS.textPrimary, marginBottom: 10 },
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary },
  hintButton: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8 },
  hintText: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark, flex: 1 },
  guidance: { backgroundColor: '#F7F4FF', padding: 15, borderRadius: 17, marginBottom: 14 },
  solutionTitle: { fontFamily: FONTS.extraBold, fontSize: 14, color: COLORS.textPrimary, marginTop: 12, marginBottom: 6 },
  solution: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  capture: { backgroundColor: COLORS.primary, borderRadius: 25, minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 10 },
  captureText: { fontFamily: FONTS.extraBold, fontSize: 15, color: COLORS.surface },
  pressed: { opacity: 0.7 },
});
