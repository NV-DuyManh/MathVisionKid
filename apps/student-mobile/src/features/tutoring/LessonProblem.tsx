import React, { useId, useState } from 'react';
import { Image, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { problemPresentation } from '../../components/domain/problemPresentation';
import { isCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { COLORS, FONTS } from '../../constants/theme';
import { LessonSheet } from './LessonSheet';

/** Stays above the working area; long questions scroll without pushing the task away. */
export function LessonProblem({ problem, imageUri, onEdit, sidePanel = false }: { problem: string; imageUri?: string; onEdit?: () => void; sidePanel?: boolean }) {
  const [open, setOpen] = useState(true);
  const [showImage, setShowImage] = useState(false);
  const [fullOpen, setFullOpen] = useState(false);
  const [contentHeight, setContentHeight] = useState(0);
  const contentId = useId();
  const { width, height } = useWindowDimensions();
  const canCollapse = Platform.OS !== 'web' || isCompactStudentWeb(width);
  const expanded = !canCollapse || open;
  const maxBodyHeight = sidePanel ? Math.max(180, height - 300) : Math.max(64, Math.min(124, height * .17));
  const heading = <>
    <View style={styles.icon}><Ionicons name="document-text-outline" size={18} color={COLORS.primaryDark} accessible={false} /></View>
    <View style={styles.heading}><Text accessibilityRole={canCollapse ? undefined : 'header'} style={styles.title}>Đề bài</Text>
      {!expanded ? <Text numberOfLines={1} style={styles.preview}>{problem}</Text>
        : contentHeight > maxBodyHeight + 1 ? <Text style={styles.preview}>Cuộn để đọc hết</Text> : null}</View>
  </>;
  return <View style={styles.card} testID="lesson-problem-reference">
    <View style={styles.header}>
      {canCollapse ? <Pressable accessibilityRole="button" accessibilityLabel={expanded ? 'Thu gọn đề bài' : 'Mở đề bài'}
        accessibilityState={{ expanded }} aria-expanded={expanded} aria-controls={expanded ? contentId : undefined}
        onPress={() => setOpen(value => !value)} style={({ pressed }) => [styles.toggle, pressed && styles.pressed]}>
        {heading}
        <Text style={styles.action}>{expanded ? 'Thu gọn' : 'Xem đầy đủ'}</Text>
        <Ionicons name={expanded ? 'chevron-up' : 'chevron-down'} size={17} color={COLORS.primaryDark} accessible={false} />
      </Pressable> : <View style={styles.toggle}>{heading}</View>}
      {imageUri && Platform.OS !== 'web' ? <Pressable accessibilityRole="button" accessibilityLabel={showImage ? 'Xem đề bài bằng chữ' : 'Xem ảnh đề bài'}
        accessibilityState={{ selected: showImage }} aria-pressed={showImage} onPress={() => { setOpen(true); setShowImage(value => !value); setContentHeight(0); }}
        style={({ pressed }) => [styles.edit, pressed && styles.pressed]}>
        <Ionicons name="image-outline" size={19} color={COLORS.primaryDark} accessible={false} />
      </Pressable> : null}
      {onEdit && <Pressable accessibilityRole="button" accessibilityLabel="Chỉnh đề bài" onPress={onEdit}
        style={({ pressed }) => [styles.edit, pressed && styles.pressed]}>
        <Ionicons name="create-outline" size={20} color={COLORS.primaryDark} accessible={false} />
      </Pressable>}
    </View>
    {expanded && imageUri && Platform.OS === 'web' ? <View style={styles.modes} accessibilityRole="radiogroup" accessibilityLabel="Cách xem đề bài">
      {[false, true].map(mode => <Pressable key={String(mode)} accessibilityRole="radio"
        accessibilityLabel={mode ? 'Xem ảnh đề bài' : 'Xem đề bài bằng chữ'} accessibilityState={{ checked: showImage === mode }} aria-checked={showImage === mode}
        onPress={() => { setShowImage(mode); setContentHeight(0); }}
        style={({ pressed }) => [styles.mode, showImage === mode && styles.selectedMode, pressed && styles.pressed]}>
        <Ionicons name={mode ? 'image-outline' : 'document-text-outline'} size={17} color={showImage === mode ? '#FFF' : COLORS.primaryDark} accessible={false} />
        <Text style={[styles.modeLabel, showImage === mode && styles.selectedLabel]}>{mode ? 'Ảnh' : 'Văn bản'}</Text>
      </Pressable>)}
    </View> : null}
    {expanded ? <ScrollView nativeID={contentId} testID="lesson-problem-content" nestedScrollEnabled tabIndex={0} accessibilityLabel="Nội dung đề bài"
      onContentSizeChange={(_, value) => setContentHeight(value)}
      style={[styles.content, { maxHeight: maxBodyHeight, ...(contentHeight > 0 ? { height: Math.min(contentHeight, maxBodyHeight) } : {}) }]} contentContainerStyle={styles.words}>
      {imageUri && showImage ? <Image source={{ uri: imageUri }} resizeMode="contain" style={[styles.photo, sidePanel && { height: Math.min(360, maxBodyHeight - 16) }]} accessibilityLabel="Ảnh đề bài đã che thông tin" />
        : <MathText style={[styles.body, sidePanel && styles.sideText]}>{problemPresentation(problem)}</MathText>}
    </ScrollView> : null}
    {expanded && contentHeight > maxBodyHeight + 1 ? <Pressable accessibilityRole="button" accessibilityLabel="Đọc toàn bộ đề bài" onPress={() => setFullOpen(true)} style={styles.readFull}>
      <Text style={styles.action}>Đọc toàn bộ đề</Text><Ionicons name="expand-outline" size={16} color={COLORS.primaryDark} accessible={false} />
    </Pressable> : null}
    {fullOpen ? <LessonSheet title="Toàn bộ đề bài" onClose={() => setFullOpen(false)}>
      <MathText style={styles.fullText}>{problemPresentation(problem)}</MathText>
      {imageUri ? <Image source={{ uri: imageUri }} resizeMode="contain" style={styles.fullPhoto} accessibilityLabel="Ảnh đề bài đã che thông tin" /> : null}
    </LessonSheet> : null}
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
  modes: { flexDirection: 'row', gap: 4, padding: 4, marginHorizontal: 8, marginBottom: 8, borderRadius: 12, backgroundColor: COLORS.surfaceSubdued },
  mode: { flex: 1, minHeight: 44, borderRadius: 9, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  selectedMode: { backgroundColor: COLORS.primaryDark }, modeLabel: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark }, selectedLabel: { color: '#FFF' },
  words: { paddingHorizontal: 12, paddingVertical: 8, gap: 8 }, body: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
  sideText: { fontSize: 16, lineHeight: 26, color: COLORS.textPrimary },
  photo: { width: '100%', height: 132, borderRadius: 12, backgroundColor: COLORS.background },
  fullPhoto: { width: '100%', height: 280 }, fullText: { fontFamily: FONTS.regular, fontSize: 16, lineHeight: 26, color: COLORS.textPrimary },
  readFull: { minHeight: 36, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', gap: 6, borderTopWidth: 1, borderTopColor: COLORS.border },
});
