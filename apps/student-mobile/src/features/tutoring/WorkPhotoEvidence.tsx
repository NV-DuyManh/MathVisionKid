import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Image, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { trimWorkReviewLine, type NotebookLine } from './api/TutorService';

export type WorkPhotoEvidenceRow = {
  lineIndex: number;
  sourceText: string;
  status: 'OK' | 'FIX' | 'UNSURE';
  feedback: string;
  hints: string[];
};
type Props = {
  imageUri: string;
  lines: NotebookLine[];
  rows: WorkPhotoEvidenceRow[];
  selectedLine: number | null;
  onSelectLine: (index: number) => void;
  presentation?: 'full' | 'photo' | 'lines';
  issuesOnly?: boolean;
};
const STATUS = {
  OK: { label: 'Đã kiểm tra đúng', color: COLORS.success },
  FIX: { label: 'Cùng sửa bước này', color: '#8C5900' },
  UNSURE: { label: 'Cần đối chiếu', color: COLORS.primaryDark },
};

function validBox(box: NotebookLine['box']): box is [number, number, number, number] {
  return Array.isArray(box) && box.length === 4
    && box.every(value => Number.isInteger(value) && value >= 0 && value <= 1000)
    && box[0] < box[2] && box[1] < box[3];
}

export function WorkPhotoEvidence(props: Props) {
  const [reload, setReload] = useState(0);
  // Every source and retry owns its load callbacks, so old dimensions cannot reach a new photo.
  return <WorkPhotoSource key={`${props.imageUri}:${reload}`} {...props} onReload={() => setReload(value => value + 1)} />;
}

function WorkPhotoSource({ imageUri, lines, rows, selectedLine, onSelectLine, onReload, presentation = 'full', issuesOnly = false }: Props & { onReload: () => void }) {
  const [size, setSize] = useState<{ width: number; height: number } | null>(null);
  const [failed, setFailed] = useState(false);
  const imageFailed = useRef(false);
  const [focused, setFocused] = useState<number | 'reload' | null>(null);
  // The web image loader subscribes to this callback; row focus must not restart the image load.
  const failImage = useCallback(() => { imageFailed.current = true; setFailed(true); setSize(null); }, []);
  useEffect(() => {
    let active = true;
    if (imageUri && presentation !== 'lines') Image.getSize(imageUri, (width, height) => {
      if (!active || imageFailed.current) return;
      if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0
        || !Number.isFinite(width / height) || width / height <= 0) {
        failImage(); return;
      }
      setSize({ width, height });
    }, () => {
      if (active) failImage();
    });
    return () => { active = false; };
  }, [imageUri, failImage, presentation]);
  const evidence = lines.map((line, index) => {
    const sourceText = trimWorkReviewLine(line.text);
    const matches = rows.filter(row => row.lineIndex === index && row.sourceText === sourceText);
    const matched = matches.length === 1 ? matches[0] : undefined;
    // Unclear handwriting must be checked before any mathematical correction or praise.
    const status = line.uncertain ? 'UNSURE' : matched?.status ?? 'UNSURE';
    return { line, sourceText, status };
  });
  const ratio = size ? size.width / size.height : 1;

  return <View style={styles.content}>
    {presentation === 'full' ? <><Text style={styles.title}>Nhìn lại bài em đã viết</Text>
    <Text style={styles.body}>{imageUri && lines.some(line => validBox(line.box))
      ? 'Vùng bôi vàng trên ảnh là dòng cần em sửa. Số trên ảnh trùng với số dòng bên dưới; em chọn dòng đó để xem gợi ý nhé.'
        : 'Em chọn một dòng bên dưới để xem nhận xét. Chỗ chưa xác định được vị trí trên ảnh sẽ được đối chiếu bằng nội dung nhé.'}</Text></> : null}
    {presentation !== 'lines' ? imageUri && !failed ? <View testID="work-evidence-photo-frame"
      style={[styles.photoFrame, { aspectRatio: ratio, maxWidth: size ? Math.min(640, 480 * ratio) : 640 }]}>
      <Image source={{ uri: imageUri }} testID="work-evidence-photo" resizeMode="contain" style={StyleSheet.absoluteFill}
        accessible accessibilityLabel="Ảnh bài em đã làm, các vùng được đánh số theo dòng bên dưới"
        onError={failImage} />
      {size ? evidence.map(({ line, status }, index) => {
        if (!validBox(line.box) || (issuesOnly && status === 'OK')) return null;
        const [left, top, right, bottom] = line.box;
        return <View key={index} testID={`work-evidence-region-${index}`} pointerEvents="none" accessible={false}
          focusable={false} aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
          style={[styles.region, { left: `${left / 10}%`, top: `${top / 10}%`, width: `${(right - left) / 10}%`,
            height: `${(bottom - top) / 10}%`, borderColor: STATUS[status].color,
            backgroundColor: status === 'FIX' ? 'rgba(255, 221, 0, 0.32)' : 'transparent',
            borderWidth: selectedLine === index ? 4 : 2, borderStyle: status === 'UNSURE' ? 'dashed' : 'solid' }]}>
          <View style={[styles.marker, top > 0 && { top: -20 }]}><Text allowFontScaling={false} style={styles.markerText}>{index + 1}</Text></View>
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
    </View> : null}
    {presentation !== 'lines' && !!imageUri && !failed && !size ? <Text style={styles.body} accessibilityLiveRegion="polite">Đang mở ảnh bài làm…</Text> : null}
    {presentation !== 'lines' && rows.some(row => row.status === 'FIX' && !validBox(lines[row.lineIndex]?.box)) ? <Text style={styles.caption}>Chưa xác định được vị trí một số dòng cần sửa trên ảnh. Em xem nội dung dòng bên dưới nhé.</Text> : null}
    {presentation !== 'photo' ? evidence.map(({ sourceText, status }, index) => issuesOnly && status === 'OK' ? null : <View key={index} style={styles.lineContent}>
      <Pressable testID={`work-evidence-line-${index}`} accessibilityRole="button" focusable
        accessibilityLabel={`Dòng ${index + 1}: ${sourceText}. ${STATUS[status].label}.`}
        accessibilityHint="Chọn để xem nhận xét cho dòng này" aria-pressed={selectedLine === index}
        accessibilityState={Platform.OS === 'web' ? undefined : { selected: selectedLine === index }}
        onPress={() => onSelectLine(index)} onFocus={() => setFocused(index)} onBlur={() => setFocused(null)}
        style={({ pressed }) => [styles.line, selectedLine === index && styles.selected,
          focused === index && styles.focused, pressed && styles.pressed]}>
        <View accessible={false} aria-hidden accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={styles.lineContent}>
          <Text style={styles.label}>{`Dòng ${index + 1} · ${STATUS[status].label}`}</Text>
          <MathText style={styles.body}>{sourceText}</MathText>
          {selectedLine === index ? <Text style={styles.caption}>Đang xem dòng này</Text> : null}
        </View>
      </Pressable>
    </View>) : null}
  </View>;
}

const styles = StyleSheet.create({
  content: { gap: 12 },
  title: { color: COLORS.textPrimary, fontSize: 20, lineHeight: 28, fontFamily: FONTS.extraBold },
  body: { color: COLORS.textSecondary, fontSize: 15, lineHeight: 23, fontFamily: FONTS.regular },
  label: { color: COLORS.textPrimary, fontSize: 15, lineHeight: 22, fontFamily: FONTS.bold },
  caption: { color: COLORS.primaryDark, fontSize: 14, lineHeight: 21, fontFamily: FONTS.bold },
  photoFrame: { width: '100%', alignSelf: 'center', position: 'relative', overflow: 'hidden', backgroundColor: COLORS.surfaceSubdued },
  region: { position: 'absolute' },
  marker: { position: 'absolute', top: 0, left: 0, minWidth: 20, height: 20, paddingHorizontal: 2,
    backgroundColor: COLORS.textPrimary, alignItems: 'center', justifyContent: 'center' },
  markerText: { color: COLORS.surface, fontFamily: FONTS.bold, fontSize: 12, lineHeight: 16 },
  lineContent: { gap: 6 },
  line: { minHeight: SIZES.minTouchTarget, width: '100%', borderWidth: 2, borderColor: COLORS.textSecondary,
    backgroundColor: COLORS.surface, borderRadius: 12, padding: 12, justifyContent: 'center' },
  selected: { borderColor: COLORS.primaryDark, backgroundColor: COLORS.primaryLight },
  focused: { borderColor: COLORS.textPrimary, borderStyle: 'dashed' },
  pressed: { opacity: 0.7 },
  notice: { gap: 8 },
});
