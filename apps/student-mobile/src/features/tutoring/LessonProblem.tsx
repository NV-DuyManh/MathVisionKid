import React, { useId, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';

/** Stays above the working area; long questions scroll without pushing the task away. */
export function LessonProblem({ problem, imageUri, onEdit }: { problem: string; imageUri?: string; onEdit: () => void }) {
  const [expanded, setExpanded] = useState(true);
  const [showImage, setShowImage] = useState(false);
  const [contentHeight, setContentHeight] = useState(0);
  const contentId = useId();
  const { height } = useWindowDimensions();
  const maxBodyHeight = Math.max(64, Math.min(124, height * .17));
  return <View style={styles.card} testID="lesson-problem-reference">
    <View style={styles.header}>
      <Pressable accessibilityRole="button" accessibilityLabel={expanded ? 'Thu gọn đề bài' : 'Mở đề bài'}
        accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? contentId : undefined}
        onPress={() => setExpanded(value => !value)} style={({ pressed }) => [styles.toggle, pressed && styles.pressed]}>
        <View style={styles.icon}><Ionicons name="document-text-outline" size={18} color={COLORS.primaryDark} accessible={false} /></View>
        <View style={styles.heading}><Text style={styles.title}>Đề bài</Text>
          {!expanded ? <Text numberOfLines={1} style={styles.preview}>{problem}</Text>
            : contentHeight > maxBodyHeight + 1 ? <Text style={styles.preview}>Cuộn để đọc hết</Text> : null}</View>
        <Text style={styles.action}>{expanded ? 'Thu gọn' : 'Mở đề'}</Text>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
      {imageUri ? <Pressable accessibilityRole="button" accessibilityLabel={showImage ? 'Ẩn ảnh đề bài' : 'Xem ảnh đề bài'}
        accessibilityState={{ expanded: showImage }} onPress={() => { setExpanded(true); setShowImage(value => !value); }}
        style={({ pressed }) => [styles.edit, pressed && styles.pressed]}>
        <Ionicons name="image-outline" size={19} color={COLORS.primaryDark} accessible={false} />
      </Pressable> : null}
      <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh đề bài" onPress={onEdit}
        style={({ pressed }) => [styles.edit, pressed && styles.pressed]}>
        <Ionicons name="create-outline" size={20} color={COLORS.primaryDark} accessible={false} />
      </Pressable>
    </View>
    {expanded ? <ScrollView nativeID={contentId} testID="lesson-problem-content" nestedScrollEnabled tabIndex={0} accessibilityLabel="Nội dung đề bài"
      onContentSizeChange={(_, value) => setContentHeight(value)}
      style={[styles.content, { maxHeight: maxBodyHeight, ...(contentHeight > 0 ? { height: Math.min(contentHeight, maxBodyHeight) } : {}) }]} contentContainerStyle={styles.words}>
      <MathText style={styles.body}>{problem}</MathText>
      {imageUri && showImage ? <Image source={{ uri: imageUri }} resizeMode="contain" style={styles.photo} accessibilityLabel="Ảnh đề bài đã che thông tin" /> : null}
    </ScrollView> : null}
  </View>;
}

const styles = StyleSheet.create({
  card: { backgroundColor: COLORS.surface, borderRadius: 14, borderWidth: 1, borderColor: COLORS.border, overflow: 'hidden' },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, gap: 2, backgroundColor: '#FCFAFF' },
  toggle: { flex: 1, minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 10, paddingHorizontal: 2 },
  icon: { width: 26, alignItems: 'center', justifyContent: 'center' },
  heading: { flex: 1 }, title: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 13, lineHeight: 18 },
  preview: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 11, lineHeight: 15 },
  action: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 11, lineHeight: 16 },
  edit: { width: 48, height: 48, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  pressed: { backgroundColor: COLORS.surfaceSubdued }, content: { borderTopWidth: 1, borderTopColor: COLORS.border },
  words: { paddingHorizontal: 12, paddingVertical: 8, gap: 8 }, body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
  photo: { width: '100%', height: 132, borderRadius: 12, backgroundColor: COLORS.background },
});
