import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Image, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { trimWorkReviewLine, type NotebookLine, type WorkReviewRow } from './api/TutorService';
import { analyzeRowPresentation, isWorkReviewIssue, type IncompleteCheckResult } from './workReviewAnalysis';

export type WorkPhotoEvidenceRow = WorkReviewRow;

type Props = {
  imageUri: string;
  lines: NotebookLine[];
  rows: WorkPhotoEvidenceRow[];
  selectedLine: number | null;
  onSelectLine: (index: number) => void;
  presentation?: 'full' | 'photo' | 'lines';
  issuesOnly?: boolean;
  showFeedback?: boolean;
  problemText?: string;
  incompleteInfo?: IncompleteCheckResult | null;
};

function validBox(box: NotebookLine['box']): box is [number, number, number, number] {
  return Array.isArray(box) && box.length === 4
    && box.every(value => Number.isInteger(value) && value >= 0 && value <= 1000)
    && box[0] < box[2] && box[1] < box[3];
}

export function WorkPhotoEvidence(props: Props) {
  const [reload, setReload] = useState(0);
  return <WorkPhotoSource key={`${props.imageUri}:${reload}`} {...props} onReload={() => setReload(value => value + 1)} />;
}

function WorkPhotoSource({
  imageUri,
  lines,
  rows,
  selectedLine,
  onSelectLine,
  onReload,
  presentation = 'full',
  issuesOnly = false,
  showFeedback = false,
  problemText = '',
  incompleteInfo,
}: Props & { onReload: () => void }) {
  const [size, setSize] = useState<{ width: number; height: number } | null>(null);
  const [failed, setFailed] = useState(false);
  const imageFailed = useRef(false);
  const [focused, setFocused] = useState<number | 'reload' | null>(null);

  const failImage = useCallback(() => {
    imageFailed.current = true;
    setFailed(true);
    setSize(null);
  }, []);

  useEffect(() => {
    let active = true;
    if (imageUri && presentation !== 'lines') {
      Image.getSize(imageUri, (width, height) => {
        if (!active || imageFailed.current) return;
        if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0
          || !Number.isFinite(width / height) || width / height <= 0) {
          failImage();
          return;
        }
        setSize({ width, height });
      }, () => {
        if (active) failImage();
      });
    }
    return () => { active = false; };
  }, [imageUri, failImage, presentation]);

  const evidence = lines.map((line, index) => {
    const sourceText = trimWorkReviewLine(line.text);
    const matches = rows.filter(row => row.lineIndex === index && row.sourceText === sourceText);
    const matched = matches.length === 1 ? matches[0] : undefined;
    const rawStatus = line.uncertain ? 'UNSURE' : matched?.status ?? 'UNSURE';

    // Rich analysis for error type, color, and labels
    const analysis = analyzeRowPresentation(
      sourceText,
      problemText,
      rawStatus,
      matched?.feedback,
      matched?.hints,
      matched?.errorKind
    );

    return { line, sourceText, analysis, rowKind: matched?.rowKind };
  });

  const ratio = size ? size.width / size.height : 1;
  const visibleIssue = ({ sourceText, analysis, rowKind }: (typeof evidence)[number]) =>
    !issuesOnly || isWorkReviewIssue({ sourceText, status: analysis.status, errorKind: analysis.errorKind, rowKind });

  return <View style={styles.content}>
    {presentation === 'full' ? <>
      <Text style={styles.title}>Nhìn lại bài em đã viết</Text>
      <Text style={styles.body}>{imageUri && lines.some(line => validBox(line.box))
        ? 'Vùng bôi màu trên ảnh là dòng cần em sửa. Số trên ảnh trùng với số dòng bên dưới; em chọn dòng đó để xem gợi ý nhé.'
        : 'Em chọn một dòng bên dưới để xem nhận xét. Chỗ chưa xác định được vị trí trên ảnh sẽ được đối chiếu bằng nội dung nhé.'}</Text>
    </> : null}

    {presentation !== 'lines' ? (imageUri && !failed ? <View testID="work-evidence-photo-frame"
      style={[styles.photoFrame, { aspectRatio: ratio, maxWidth: size ? Math.min(640, 480 * ratio) : 640 }]}>
      <Image source={{ uri: imageUri }} testID="work-evidence-photo" resizeMode="contain" style={StyleSheet.absoluteFill}
        accessible accessibilityLabel="Ảnh bài em đã làm, các vùng được đánh số theo dòng bên dưới"
        onError={failImage} />
      {size ? evidence.map((item, index) => {
        const { line, sourceText, analysis } = item;
        if (!validBox(line.box) || !visibleIssue(item)) return null;
        const [left, top, right, bottom] = line.box;
        const isFix = analysis.status === 'FIX';
        const isRed = isFix && analysis.badgeColor === '#DC2626';
        const regionBorder = isRed ? '#DC2626' : isFix ? '#8C5900' : analysis.badgeColor;
        const regionBg = isRed ? 'rgba(220, 38, 38, 0.22)' : isFix ? 'rgba(255, 221, 0, 0.32)' : 'transparent';

        return <View key={index} testID={`work-evidence-region-${index}`} pointerEvents="none" accessible={false}
          focusable={false} aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
          style={[styles.region, {
            left: `${left / 10}%`, top: `${top / 10}%`, width: `${(right - left) / 10}%`,
            height: `${(bottom - top) / 10}%`, borderColor: regionBorder,
            backgroundColor: regionBg,
            borderWidth: selectedLine === index ? 4 : 2,
            borderStyle: analysis.status === 'UNSURE' ? 'dashed' : 'solid',
          }]}>
          <View style={[styles.marker, top > 0 && { top: -20 }, { backgroundColor: regionBorder }]}>
            <Text allowFontScaling={false} style={styles.markerText}>{index + 1}</Text>
          </View>
        </View>;
      }) : null}
    </View> : <View style={styles.notice}>
      <Text style={styles.body} accessibilityLiveRegion="polite">{imageUri
        ? 'Chưa mở được ảnh. Em vẫn có thể xem từng dòng bên dưới.'
        : 'Chưa có ảnh để đối chiếu. Em vẫn có thể xem từng dòng bên dưới.'}</Text>
      {imageUri ? <Pressable accessibilityRole="button" accessibilityLabel="Mở lại ảnh bài làm" focusable
        onPress={onReload} onFocus={() => setFocused('reload')} onBlur={() => setFocused(null)}
        style={({ pressed }) => [styles.line, focused === 'reload' && styles.focused, pressed && styles.pressed]}>
        <Text style={styles.label}>Mở lại ảnh bài làm</Text>
      </Pressable> : null}
    </View>) : null}

    {presentation !== 'lines' && !!imageUri && !failed && !size ? <Text style={styles.body} accessibilityLiveRegion="polite">Đang mở ảnh bài làm…</Text> : null}
    {presentation !== 'lines' && rows.some(row => (issuesOnly ? isWorkReviewIssue(row) : row.status === 'FIX') && !validBox(lines[row.lineIndex]?.box)) ? <Text style={styles.caption}>Chưa xác định được vị trí một số dòng cần sửa trên ảnh. Em xem nội dung dòng bên dưới nhé.</Text> : null}

    {presentation !== 'photo' ? <>
      {evidence.map((item, index) => {
        const { sourceText, analysis } = item;
        if (!visibleIssue(item)) return null;
        const isSelected = selectedLine === index;
        const feedback = showFeedback && analysis.status === 'FIX' ? analysis.detailedFeedback : '';
        return <View key={index} style={styles.lineContent}>
          <Pressable testID={`work-evidence-line-${index}`} accessibilityRole="button" focusable
            accessibilityLabel={`Dòng ${index + 1}: ${sourceText}. ${analysis.label}.${feedback ? ` ${feedback}` : ''}`}
            accessibilityHint="Chọn để xem nhận xét cho dòng này" aria-pressed={isSelected}
            accessibilityState={Platform.OS === 'web' ? undefined : { selected: isSelected }}
            onPress={() => onSelectLine(index)} onFocus={() => setFocused(index)} onBlur={() => setFocused(null)}
            style={({ pressed }) => [
              styles.line,
              { borderColor: isSelected ? analysis.badgeColor : analysis.badgeBorder, backgroundColor: isSelected ? analysis.badgeBg : COLORS.surface },
              isSelected && { borderWidth: 2.5 },
              focused === index && styles.focused,
              pressed && styles.pressed,
            ]}>
            <View accessible={false} aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.lineContent}>
              <View style={styles.lineHeaderRow}>
                <View style={[styles.statusTag, { backgroundColor: analysis.badgeBg, borderColor: analysis.badgeBorder }]}>
                  <Text style={[styles.statusTagText, { color: analysis.badgeColor }]}>{`Dòng ${index + 1} · ${analysis.label}`}</Text>
                </View>
                {isSelected ? <Text style={styles.selectedCaption}>Đang xem dòng này</Text> : null}
              </View>
              <MathText style={styles.body}>{sourceText}</MathText>
              {feedback ? <Text style={styles.body}>{feedback}</Text> : null}
            </View>
          </Pressable>
        </View>;
      })}

      {/* When the problem is incomplete, show the missing step card in ORANGE */}
      {incompleteInfo?.isIncomplete ? (
        <View style={styles.incompleteStepCard}>
          <View style={styles.incompleteHeader}>
            <Ionicons name="time" size={18} color="#EA580C" />
            <Text style={styles.incompleteLabel}>Bước tiếp theo · Chưa hoàn thành (thiếu bước)</Text>
          </View>
          <Text style={styles.incompleteSummary}>{incompleteInfo.nextStepSummary}</Text>
        </View>
      ) : null}
    </> : null}
  </View>;
}

const styles = StyleSheet.create({
  content: { gap: 12 },
  title: { color: COLORS.textPrimary, fontSize: 20, lineHeight: 28, fontFamily: FONTS.extraBold },
  body: { color: COLORS.textSecondary, fontSize: 15, lineHeight: 23, fontFamily: FONTS.regular },
  label: { color: COLORS.textPrimary, fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold },
  caption: { color: COLORS.primaryDark, fontSize: 14, lineHeight: 21, fontFamily: FONTS.bold },
  selectedCaption: { color: COLORS.primaryDark, fontSize: 12, lineHeight: 18, fontFamily: FONTS.bold },
  photoFrame: { width: '100%', alignSelf: 'center', position: 'relative', overflow: 'hidden', backgroundColor: COLORS.surfaceSubdued },
  region: { position: 'absolute' },
  marker: { position: 'absolute', top: 0, left: 0, minWidth: 20, height: 20, paddingHorizontal: 3,
    backgroundColor: COLORS.textPrimary, alignItems: 'center', justifyContent: 'center', borderRadius: 4 },
  markerText: { color: COLORS.surface, fontFamily: FONTS.bold, fontSize: 12, lineHeight: 16 },
  lineContent: { gap: 6 },
  lineHeaderRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  statusTag: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, borderWidth: 1, alignSelf: 'flex-start' },
  statusTagText: { fontFamily: FONTS.bold, fontSize: 13, lineHeight: 18 },
  line: { minHeight: SIZES.minTouchTarget, width: '100%', borderWidth: 1.5, borderColor: COLORS.border,
    backgroundColor: COLORS.surface, borderRadius: 12, padding: 12, justifyContent: 'center' },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  pressed: { opacity: 0.7 },
  notice: { gap: 8 },
  incompleteStepCard: {
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#FFF7ED',
    borderWidth: 1.5,
    borderColor: '#FB923C',
    borderStyle: 'dashed',
    gap: 6,
  },
  incompleteHeader: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  incompleteLabel: { fontFamily: FONTS.bold, fontSize: 14, lineHeight: 20, color: '#C2410C' },
  incompleteSummary: { fontFamily: FONTS.medium, fontSize: 14, lineHeight: 21, color: '#9A3412' },
});
