import React, { useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, FONTS } from '../../constants/theme';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { recognitionDraftStore, logFlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { AppButton } from '../../components/ui/AppButton';
import { QuizShortcut } from '../../features/quiz/QuizShortcut';

export default function LessonsScreen() {
  const insets = useSafeAreaInsets(), router = useRouter();
  const [pageWidth, setPageWidth] = useState(0);
  const [grade, setGrade] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [opened, setOpened] = useState<string | null>(null), [hint, setHint] = useState(false);
  const problems = getProblemsByGrade(grade);
  return <ScrollView style={styles.screen} onLayout={event => setPageWidth(event.nativeEvent.layout.width)} showsVerticalScrollIndicator={false}
    contentContainerStyle={[styles.content, { paddingTop: insets.top + 12, paddingBottom: pageWidth >= 768 ? 32 : 108 }]}>
    <StudentPageHeader compact title="Bài học" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/(tabs)/profile')} />
    <View style={styles.grades}>{([1, 2, 3, 4, 5] as const).map(item => <Pressable key={item} accessibilityRole="button"
      accessibilityLabel={'Chọn Lớp ' + item} accessibilityState={{ selected: grade === item }}
      onPress={() => { setGrade(item); setOpened(null); setHint(false); }}
      style={({ pressed }) => [styles.grade, grade === item && styles.gradeSelected, pressed && styles.pressed]}>
      <Text style={[styles.gradeText, grade === item && styles.white]}>Lớp {item}</Text>
    </Pressable>)}</View>
    <QuizShortcut />
    <View style={styles.headingRow}><Text style={styles.heading}>Hôm nay em học gì?</Text><Text style={styles.count}>{problems.length} bài học</Text></View>
    <View style={styles.list}>{problems.map((problem, index) => <View key={problem.id} style={[styles.topic, { backgroundColor: index % 2 ? '#FFF8E8' : '#F3EFFF' }]}>
      <Pressable accessibilityRole="button" accessibilityLabel={'Mở bài: ' + problem.title} accessibilityState={{ expanded: opened === problem.id }}
        onPress={() => { setOpened(opened === problem.id ? null : problem.id); setHint(false); }} style={styles.topicRow}>
        <View style={[styles.topicIcon, { backgroundColor: index % 2 ? '#FFF0BD' : '#E9DDFF' }]}>
          <Image source={index % 2 ? require('../../../assets/illustrations/approved/calculator.webp') : require('../../../assets/illustrations/approved/practice.webp')} style={styles.iconArt} resizeMode="contain" accessible={false} />
        </View>
        <View style={styles.copy}><Text style={styles.topicTitle}>{problem.topic}</Text><Text style={styles.description}>{problem.title}</Text></View>
        <Ionicons name={opened === problem.id ? 'chevron-up' : 'chevron-forward'} size={20} color="#7750E8" accessible={false} />
      </Pressable>
      {opened === problem.id ? <View style={styles.detail}>
        <View style={styles.tags}><Text style={styles.tag}>{problem.bookSeries}</Text><Text style={styles.tag}>{problem.difficulty}</Text></View>
        <Text style={styles.body}>{problem.problemText}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel={(hint ? 'Ẩn' : 'Xem') + ' gợi ý: ' + problem.title} accessibilityState={{ expanded: hint }}
          onPress={() => setHint(value => !value)} style={styles.hintButton}><Ionicons name="bulb-outline" size={19} color={COLORS.primaryDark} /><Text style={styles.link}>{hint ? 'Ẩn gợi ý' : 'Xem gợi ý cách giải'}</Text></Pressable>
        {hint ? <Text style={styles.body}>{problem.guidance}</Text> : null}
        <AppButton title="Cùng em tìm cách giải" accessibilityLabel={'Học từng bước: ' + problem.title} onPress={() => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } })} />
        <AppButton title="Chụp bài làm của em" accessibilityLabel={'Chụp lời giải: ' + problem.title} variant="secondary" onPress={() => {
          recognitionDraftStore.clearDraft(); logFlowDomain('ACQUIRE', 'MATH_TUTOR');
          router.push({ pathname: '/camera', params: { mode: 'MATH_TUTOR', problemText: problem.problemText } });
        }} />
      </View> : null}
    </View>)}</View>
    <LinearGradient colors={['#EEE7FF', '#FAF7FF']} style={styles.encouragement}>
      <Image source={require('../../../assets/illustrations/mathvision-star.png')} style={styles.mascot} resizeMode="contain" accessible={false} />
      <View style={styles.copy}><Text style={styles.encouragementTitle}>Mỗi ngày, giỏi hơn một chút</Text><Text style={styles.body}>Chọn một bài, thử từng bước. Sao Nhỏ cùng em khám phá nhé!</Text></View>
    </LinearGradient>
  </ScrollView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#FAF9FF' },
  content: { flexGrow: 1, paddingHorizontal: 20, width: '100%', maxWidth: 940, alignSelf: 'center' },
  grades: { flexDirection: 'row', gap: 6, marginBottom: 26, padding: 4, backgroundColor: '#F0EBFC', borderRadius: 18 },
  grade: { flex: 1, minHeight: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  gradeSelected: { backgroundColor: '#8554FF', boxShadow: '0 3px 8px #8452FF30' },
  gradeText: { fontFamily: FONTS.extraBold, fontSize: 13, color: '#71658E' }, white: { color: '#FFF' },
  headingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 15 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 18, color: COLORS.textPrimary }, count: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#786C94' },
  list: { gap: 12 }, topic: { borderRadius: 20, borderWidth: 1, borderColor: '#EEE7FB', overflow: 'hidden' },
  topicRow: { flexDirection: 'row', alignItems: 'center', padding: 13, gap: 12, minHeight: 94 },
  topicIcon: { width: 54, height: 60, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }, iconArt: { width: 53, height: 54 },
  copy: { flex: 1, minWidth: 0 }, topicTitle: { fontFamily: FONTS.extraBold, fontSize: 16, lineHeight: 23, color: '#2D2356' },
  description: { fontFamily: FONTS.regular, fontSize: 12, lineHeight: 18, color: '#786C94', marginTop: 3 },
  detail: { padding: 16, borderTopWidth: 1, borderColor: '#E7DFF5', gap: 14, backgroundColor: '#FFF' },
  tags: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 }, tag: { fontFamily: FONTS.bold, fontSize: 11, color: '#76609B', backgroundColor: '#F3EEFC', padding: 6, borderRadius: 7 },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: '#6B617F' },
  hintButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8 }, link: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  encouragement: { marginTop: 28, padding: 18, borderRadius: 23, flexDirection: 'row', alignItems: 'center', gap: 14, borderWidth: 1, borderColor: '#EDE3FB' },
  mascot: { width: 90, height: 110 }, encouragementTitle: { fontFamily: FONTS.extraBold, fontSize: 17, lineHeight: 23, color: '#49346D', marginBottom: 6 },
  pressed: { opacity: .7 },
});
