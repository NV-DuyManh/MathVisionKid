import React, { useId, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import type { LessonResponse } from './api/TutorService';

/** Reading support follows checked choices; it never grades or solves a step. */
export function ProblemSummary({ lesson, compact = false }: { lesson: LessonResponse; compact?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [focused, setFocused] = useState(false);
  const contentId = useId();
  if (lesson.understandingSteps !== 3) return null;
  const reading = lesson.step?.kind === 'UNDERSTAND';
  const fact = lesson.completed[0]?.kind === 'UNDERSTAND' ? lesson.completed[0].answer : '';
  const question = lesson.completed[1]?.kind === 'UNDERSTAND' ? lesson.completed[1].answer : '';
  const summary = fact && question && lesson.stepIndex >= 2 ? lesson.summary : null;
  const open = reading || expanded;
  if (compact) return <View style={styles.content}>
    <View style={styles.givens}><Text style={styles.label}>Đã biết</Text>
      {(summary?.givens || (fact ? [fact] : [])).map((value, index) => <MathText key={index} style={styles.body}>{value}</MathText>)}
      {!summary && !fact ? <Text style={styles.body}>Em chọn dữ kiện trong bước hiểu đề trước nhé.</Text> : null}
    </View><View style={styles.asked}><Text style={styles.label}>Cần tìm</Text>
      <MathText style={styles.body}>{summary?.question || question || 'Em tìm câu hỏi trong đề nhé.'}</MathText></View>
    <Text style={styles.caption}>Em đối chiếu lại các số và đơn vị với đề gốc nhé.</Text>
  </View>;
  return <View style={styles.card}>
    {reading ? <Text style={styles.title}>Em tập tóm tắt đề</Text> : <Pressable accessibilityRole="button"
      accessibilityLabel="Xem lại tóm tắt đề" aria-expanded={open} aria-controls={contentId}
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} onPress={() => setExpanded(value => !value)}
      style={({ pressed }) => [styles.toggle, focused && styles.focused, pressed && styles.pressed]}>
      <Text style={styles.title}>Tóm tắt đề của em</Text><Text style={styles.link}>{open ? 'Thu gọn' : 'Xem lại'}</Text>
    </Pressable>}
    {open ? <View nativeID={contentId} style={styles.content}>
      <Text style={styles.body}>Tóm tắt giúp em tách điều đã biết và điều cần tìm. Chưa cần ghi phép tính hoặc đáp số.</Text>
      <Text style={styles.body}>1. Tìm các số, đơn vị và mối liên hệ đề cho biết.</Text>
      <Text style={styles.body}>2. Tìm câu hỏi: đề muốn em tìm điều gì?</Text>
      <Text style={styles.body}>3. Đọc lại hai phần rồi đối chiếu với đề.</Text>
      {summary ? <Text style={styles.link}>Bản tóm tắt từ đề</Text> : null}
      <View style={styles.givens} accessibilityLiveRegion="polite">
        <Text style={styles.label}>Đã biết</Text>
        {summary ? summary.givens.map((value, index) => <View key={index} style={styles.line}>
          <Text style={styles.bullet} accessible={false}>•</Text><View style={styles.flex}><MathText style={styles.body}>{value}</MathText></View>
        </View>) : fact ? <>
          <Text style={styles.label}>Dữ kiện em vừa chọn</Text><MathText style={styles.body}>{fact}</MathText>
          <Text style={styles.caption}>Đây là một dữ kiện. Em mở lại đề để nhìn các dữ kiện còn lại nhé.</Text>
        </> : <Text style={styles.caption}>Em chọn điều đã biết trong bước học phía trên. Giữ đúng số và đơn vị nhé.</Text>}
      </View>
      <View style={styles.asked} accessibilityLiveRegion="polite">
        <Text style={styles.label}>Cần tìm</Text>
        {summary || question ? <MathText style={styles.body}>{summary?.question || question}</MathText>
          : <Text style={styles.caption}>Sau khi tìm dữ kiện, em chọn câu nêu điều đề đang hỏi.</Text>}
      </View>
      <Text style={styles.caption}>{summary ? 'Em đối chiếu bản tóm tắt với đề gốc, nhất là các số, đơn vị và quan hệ giữa các lượng.'
        : 'Em chọn ở các bước học; mình sẽ ghi lại những ý đã được kiểm tra ở đây.'}</Text>
    </View> : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { padding: 16, gap: 12, borderRadius: 20, borderWidth: 1, borderColor: COLORS.border, backgroundColor: COLORS.surface },
  title: { color: COLORS.textPrimary, fontFamily: FONTS.extraBold, fontSize: 20 },
  body: { color: COLORS.textPrimary, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25 },
  label: { color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 16, lineHeight: 24 },
  link: { color: COLORS.primaryDark, fontFamily: FONTS.bold, fontSize: 15, lineHeight: 23 },
  caption: { color: COLORS.textSecondary, fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23 },
  content: { gap: 10 },
  givens: { backgroundColor: '#F1ECFF', borderRadius: 14, padding: 14, gap: 9 },
  asked: { backgroundColor: '#EAF6F0', borderRadius: 14, padding: 14, gap: 9 },
  line: { flexDirection: 'row', gap: 8 }, flex: { flex: 1 },
  bullet: { color: COLORS.primaryDark, fontSize: 18, lineHeight: 25 },
  toggle: { minHeight: 48, padding: 4, gap: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 2, borderColor: 'transparent', borderRadius: 12, flexWrap: 'wrap' },
  focused: { borderColor: COLORS.primaryDark, borderStyle: 'dashed' }, pressed: { opacity: 0.75 },
});
