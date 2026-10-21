import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import {LessonClip} from './LessonClip';
import { COLORS, FONTS } from '../../constants/theme';

const CLIPS = {
  fraction: [
    { id: 'parts', title: 'Một phần ba nghĩa là gì?', choice: 'Hiểu một phân số', source: require('../../../assets/videos/fraction-intro.mp4'), transcript: 'Chia đều một hình thành ba phần có diện tích bằng nhau. Chọn một phần. Tử số đếm phần đã chọn, mẫu số đếm phần của cả hình.' },
    { id: 'equal', title: 'Vì sao cần phần cùng kích thước?', choice: 'Vì sao cùng kích thước?', source: require('../../../assets/videos/common-parts.mp4'), transcript: 'Hai hình nguyên bằng nhau có thể được chia khác nhau. Chia nhỏ thành những phần cùng kích thước để đếm theo cùng một loại phần. Lượng đã tô vẫn giữ nguyên.' },
  ],
  reading: [{ id: 'summary', title: 'Tóm tắt đề, chưa cần tính', choice: 'Tóm tắt đề', source: require('../../../assets/videos/problem-summary.mp4'), transcript: 'Đọc chậm từng câu. Ghi số lượng và điều đề cho biết vào phần Đã biết. Ghi điều đề hỏi vào phần Cần tìm. Chưa cần tính đáp số ở bước này.' }],
};

export function LessonVideo({ reading }: { reading: boolean }) {
  const clips = reading ? CLIPS.reading : CLIPS.fraction;
  const [selected, setSelected] = useState(0);
  const clip = clips[selected] || clips[0];
  return <View style={styles.stack}>
    <Text style={styles.caption}>VÍ DỤ MINH HỌA · 12 GIÂY</Text><Text style={styles.heading}>{clip.title}</Text>
    <Text style={styles.body}>Xem hình chuyển động để hiểu ý. Đây là ví dụ riêng, em dùng cách nghĩ này cho bài của mình nhé.</Text>
    {clips.length > 1 ? <View style={styles.choices}>{clips.map((item, index) => <Pressable key={item.id} accessibilityRole="button" accessibilityLabel={item.choice} aria-pressed={selected === index}
      style={[styles.choice, selected === index && styles.active]} onPress={() => setSelected(index)}><Text style={styles.link}>{item.choice}</Text></Pressable>)}</View> : null}
    <LessonClip key={clip.id} source={clip.source} />
    <View style={styles.transcript}><Text style={styles.link}>Nhớ ý này</Text><Text style={styles.body}>{clip.transcript}</Text></View>
  </View>;
}

const styles = StyleSheet.create({
  stack: { gap: 16 }, caption: { fontFamily: FONTS.extraBold, fontSize: 11, color: '#8C72A9', letterSpacing: 1 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 22, lineHeight: 30, color: COLORS.textPrimary }, body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: COLORS.textSecondary },
  choices: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 }, choice: { paddingVertical: 13, paddingHorizontal: 15, minHeight: 48, borderRadius: 18, borderWidth: 1.5, borderColor: '#DDD1F1' }, active: { backgroundColor: '#EEE5FC', borderColor: '#906BCD' },
  link: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark }, video: { width: '100%', aspectRatio: 16 / 9, borderRadius: 21, backgroundColor: '#F0EAFB' },
  transcript: { padding: 20, borderRadius: 22, backgroundColor: '#F4EFFB', gap: 10 },
});
