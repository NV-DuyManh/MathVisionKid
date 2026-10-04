import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, Image, Alert, Pressable, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Gesture, GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useDerivedValue, useAnimatedReaction, useAnimatedStyle, runOnJS, SharedValue } from 'react-native-reanimated';
import { FONTS, COLORS } from '../constants/theme';
import { AppHeader } from '../components/ui/AppHeader';
import { AppButton } from '../components/ui/AppButton';
import { ActivityRail } from '../components/ui/ActivityRail';
import { ImageDraft, recognitionDraftStore, resolveFlowDomain } from '../features/recognition/state/recognitionDraftStore';
import { normalizeLocalFileUri, resolveSafeCropImage } from '../features/recognition/image/imagePipeline';
import { Rect, CropHandle, calculateDrag, calculateResize, cropHandlePoint, closestCropHandle } from '../utils/cropGeometry';
import { exportCropImage, normalizeRotation, rotatedFrame } from '../utils/cropRotation';

const CORNERS = ['tl', 'tr', 'bl', 'br'] as const;
const EDGES = ['top', 'right', 'bottom', 'left'] as const;
const HANDLE_LABELS = { tl: 'góc trên trái', tr: 'góc trên phải', bl: 'góc dưới trái', br: 'góc dưới phải', top: 'cạnh trên', right: 'cạnh phải', bottom: 'cạnh dưới', left: 'cạnh trái' };
const INSET = { x: 0.1, y: 0.1, w: 0.8, h: 0.8 };

/** The ruler and image move on the UI thread; no image export during interaction. */
function StraightenRuler({ angle, disabled }: { angle: SharedValue<number>; disabled: boolean }) {
  const width = useSharedValue(1);
  const [label, setLabel] = useState(0);
  useAnimatedReaction(() => Math.round(angle.get() * 10) / 10, value => runOnJS(setLabel)(value));
  const update = (x: number) => {
    'worklet';
    angle.set(Math.round((Math.max(0, Math.min(1, x / width.get())) * 90 - 45) * 10) / 10);
  };
  const pan = Gesture.Pan().enabled(!disabled).minDistance(0).onBegin(e => update(e.x)).onUpdate(e => update(e.x));
  const marker = useAnimatedStyle(() => ({ left: `${(angle.get() + 45) / 90 * 100}%` }));
  return <View style={styles.rulerBlock}>
    <View style={styles.rulerHeading}><Text style={styles.controlTitle}>Căn thẳng</Text>
      <Text style={styles.angleLabel}>{label > 0 ? '+' : ''}{label.toFixed(1).replace('.', ',')}°</Text></View>
    <GestureDetector gesture={pan}><Animated.View style={styles.ruler} onLayout={e => { width.set(e.nativeEvent.layout.width); }}
      accessible accessibilityRole="adjustable" accessibilityLabel="Góc căn thẳng ảnh"
      accessibilityValue={{ min: -45, max: 45, now: label, text: `${label} độ` }}
      accessibilityState={{ disabled }} accessibilityActions={[{ name: 'increment' }, { name: 'decrement' }]}
      onAccessibilityAction={e => { if (!disabled) angle.set(Math.max(-45, Math.min(45, angle.get() + (e.nativeEvent.actionName === 'increment' ? 0.5 : -0.5)))); }}>
      <View pointerEvents="none" style={styles.ticks}>{Array.from({ length: 31 }, (_, i) => <View key={i} style={[styles.tick, i % 5 === 0 && styles.majorTick]} />)}</View>
      <View pointerEvents="none" style={styles.degreeLabels}>{[-45, -30, -15, 0, 15, 30, 45].map(n => <Text key={n} style={styles.degreeText}>{n}°</Text>)}</View>
      <Animated.View pointerEvents="none" style={[styles.angleMarker, marker]}><View style={styles.markerDot} /></Animated.View>
    </Animated.View></GestureDetector>
  </View>;
}

export default function CropScreen() {
  const params = useLocalSearchParams<{ uri?: string; retrySubmissionId?: string; originalImageUri?: string }>();
  const draft = recognitionDraftStore.getDraft();
  const one = (value?: string | string[]) => Array.isArray(value) ? value[0] : value;
  const original = one(params.originalImageUri) || draft?.originalImageUri || draft?.originalUri || draft?.sourceImageUri || draft?.rawUri || one(params.uri) || '';
  const source = draft?.privacyImageUri || original;
  return <CropEditor key={`${source}:${draft?.imageSessionId}`} draft={draft} source={source} original={original}
    retrySubmissionId={draft?.retrySubmissionId || one(params.retrySubmissionId)} />;
}

function CropEditor({ draft, source, original, retrySubmissionId }: { draft: ImageDraft | null; source: string; original: string; retrySubmissionId?: string }) {
  const router = useRouter();
  const { width, height } = useWindowDimensions();
  const landscape = width > height && height < 550;
  const [image, setImage] = useState<{ uri: string; width: number; height: number } | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mounted = useRef(true), lock = useRef(false);
  const viewport = useSharedValue({ w: 0, h: 0 });
  const size = useSharedValue({ w: 0, h: 0 });
  const fine = useSharedValue(0), turns = useSharedValue(0);
  const crop = useSharedValue<Rect>({ x: 0, y: 0, w: 0, h: 0 });
  const start = useSharedValue<Rect>({ x: 0, y: 0, w: 0, h: 0 });
  const dragHandle = useSharedValue<CropHandle | null>(null);
  const pointerStart = useSharedValue({ x: 0, y: 0 });
  const totalAngle = useDerivedValue(() => normalizeRotation(turns.get() * 90 + fine.get()));
  const frame = useDerivedValue(() => rotatedFrame(size.get().w, size.get().h, totalAngle.get(), viewport.get().w, viewport.get().h));
  const disabled = !image || loadError || processing;

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    void (async () => {
      try {
        // A failed masked image must never fall back to an unmasked photo.
        const result = await resolveSafeCropImage(source, draft?.isMasked || source === draft?.privacyImageUri ? [] : [original]);
        if (!result.finalUri) throw new Error('Missing photo');
        const dimensions = await new Promise<{ w: number; h: number }>((resolve, reject) => Image.getSize(result.finalUri!, (w, h) => resolve({ w, h }), reject));
        if (cancelled) return;
        size.set(dimensions);
        setImage({ uri: result.finalUri, width: dimensions.w, height: dimensions.h });
      } catch { if (!cancelled) setLoadError(true); }
    })();
    return () => { cancelled = true; mounted.current = false; };
  }, [source, original, draft?.isMasked, draft?.privacyImageUri, size]);

  // Preserve the selection's relative position while rotating or relaying out.
  useAnimatedReaction(() => frame.get(), (next, previous) => {
    if (!next.w || !next.h || !size.get().w) return;
    const selection = previous?.w && previous?.h && crop.get().w ? {
      x: (crop.get().x - previous.x) / previous.w, y: (crop.get().y - previous.y) / previous.h,
      w: crop.get().w / previous.w, h: crop.get().h / previous.h,
    } : INSET;
    crop.set({ x: next.x + next.w * selection.x, y: next.y + next.h * selection.y, w: next.w * selection.w, h: next.h * selection.h });
  });
  const imageStyle = useAnimatedStyle(() => ({
    position: 'absolute', width: size.get().w * frame.get().scale, height: size.get().h * frame.get().scale,
    left: (viewport.get().w - size.get().w * frame.get().scale) / 2,
    top: (viewport.get().h - size.get().h * frame.get().scale) / 2,
    transform: [{ rotate: `${totalAngle.get()}deg` }],
  }));
  const cropStyle = useAnimatedStyle(() => ({ left: crop.get().x, top: crop.get().y, width: crop.get().w, height: crop.get().h }));
  const gridStyle = useAnimatedStyle(() => ({ opacity: Math.min(crop.get().w, crop.get().h) >= 48 ? 1 : 0 }));
  const cornerStyle = useAnimatedStyle(() => ({ width: Math.min(22, Math.max(4, crop.get().w / 2)), height: Math.min(22, Math.max(4, crop.get().h / 2)) }));
  const topShade = useAnimatedStyle(() => ({ top: 0, left: 0, width: viewport.get().w, height: Math.max(0, crop.get().y) }));
  const bottomShade = useAnimatedStyle(() => ({ top: crop.get().y + crop.get().h, left: 0, width: viewport.get().w, height: Math.max(0, viewport.get().h - crop.get().y - crop.get().h) }));
  const leftShade = useAnimatedStyle(() => ({ left: 0, top: crop.get().y, width: Math.max(0, crop.get().x), height: crop.get().h }));
  const rightShade = useAnimatedStyle(() => ({ left: crop.get().x + crop.get().w, top: crop.get().y, width: Math.max(0, viewport.get().w - crop.get().x - crop.get().w), height: crop.get().h }));
  const gesture = (handle: CropHandle | null = null) => Gesture.Pan().enabled(!disabled).maxPointers(1).minDistance(1)
    .onBegin(e => {
      const box = crop.get();
      start.set({ ...box });
      pointerStart.set({ x: e.absoluteX, y: e.absoluteY });
      if (handle) {
        const point = cropHandlePoint(handle, box);
        dragHandle.set(closestCropHandle(point.x + e.x - 24, point.y + e.y - 24, box));
      } else dragHandle.set(null);
    })
    .onUpdate(e => {
      const f = frame.get();
      const bounds = { minX: f.x, minY: f.y, maxX: f.x + f.w, maxY: f.y + f.h };
      const handle = dragHandle.get();
      // The handle moves while resizing. Screen coordinates keep the same finger anchor.
      const dx = e.absoluteX - pointerStart.get().x, dy = e.absoluteY - pointerStart.get().y;
      crop.set(handle ? calculateResize(handle, dx, dy, start.get(), bounds)
        : calculateDrag(dx, dy, start.get(), bounds));
    });
  const select = (full = false) => {
    const f = frame.get(), s = full ? { x: 0, y: 0, w: 1, h: 1 } : INSET;
    crop.set({ x: f.x + f.w * s.x, y: f.y + f.h * s.y, w: f.w * s.w, h: f.h * s.h });
  };
  const reset = () => { turns.set(0); fine.set(0); select(); };
  const done = async () => {
    if (disabled || lock.current || !image) return;
    const f = frame.get(), c = crop.get();
    if (!f.w || !f.h || !c.w || !c.h) return;
    lock.current = true; setProcessing(true);
    try {
      const result = await exportCropImage(image.uri, totalAngle.get(), {
        x: (c.x - f.x) / f.w, y: (c.y - f.y) / f.h, w: c.w / f.w, h: c.h / f.h,
      });
      if (!mounted.current || recognitionDraftStore.getDraft()?.imageSessionId !== draft?.imageSessionId) return;
      recognitionDraftStore.updateDraft({ croppedImageUri: normalizeLocalFileUri(result.uri), uri: normalizeLocalFileUri(result.uri), width: result.width, height: result.height });
      const mode = resolveFlowDomain(null, draft?.mode);
      const path = mode === 'MATH_TUTOR' ? '/learning/math-guide' : mode === 'ARITHMETIC' ? '/preview' : mode === 'OCR_PILOT' ? '/recognition/line-crop' : '/recognition/multiline-review';
      router.push({ pathname: path as any, params: { retrySubmissionId, originalImageUri: original } });
    } catch {
      if (mounted.current) Alert.alert('Chưa cắt được ảnh', 'Ảnh của em vẫn được giữ. Em chọn vùng lớn hơn hoặc thử lại nhé.');
    } finally { lock.current = false; if (mounted.current) setProcessing(false); }
  };

  return <GestureHandlerRootView style={styles.screen}><SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <AppHeader title="Cắt & căn thẳng" showBack />
    <View style={styles.tip}><Ionicons name="crop-outline" size={18} color={COLORS.primaryDark} /><Text style={styles.tipText}>Kéo cạnh hoặc góc để cắt. Kéo thanh để căn thẳng.</Text></View>
    <View style={[styles.body, landscape && styles.landscape]}>
      <View style={styles.canvas} onLayout={e => { viewport.set({ w: e.nativeEvent.layout.width, h: e.nativeEvent.layout.height }); }}>
        {image ? <Animated.Image source={{ uri: image.uri }} style={imageStyle} resizeMode="stretch" onError={() => setLoadError(true)} accessibilityLabel="Ảnh bài tập đang căn chỉnh" /> : null}
        {image && !loadError ? <>
          {[topShade, bottomShade, leftShade, rightShade].map((shade, i) => <Animated.View key={i} pointerEvents="none" style={[styles.shade, shade]} />)}
          <Animated.View style={[styles.crop, cropStyle]}>
            <GestureDetector gesture={gesture()}><Animated.View style={StyleSheet.absoluteFill} /></GestureDetector>
            <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, gridStyle]}>
              {[33.33, 66.67].map(n => <React.Fragment key={n}><View style={[styles.horizontal, { top: `${n}%` }]} /><View style={[styles.vertical, { left: `${n}%` }]} /></React.Fragment>)}
            </Animated.View>
            {EDGES.map(edge => <GestureDetector key={edge} gesture={gesture(edge)}>
              <Animated.View accessibilityLabel={`Kéo ${HANDLE_LABELS[edge]}`} style={[styles.handle, styles[`${edge}Handle`]]}>
                <View pointerEvents="none" style={edge === 'top' || edge === 'bottom' ? styles.horizontalGrip : styles.verticalGrip} />
              </Animated.View>
            </GestureDetector>)}
            {CORNERS.map(corner => <GestureDetector key={corner} gesture={gesture(corner)}>
              <Animated.View accessibilityLabel={`Kéo ${HANDLE_LABELS[corner]}`} style={[styles.handle, styles[corner]]}><Animated.View pointerEvents="none" style={[styles.corner, styles[`${corner}Visual`], cornerStyle]} /></Animated.View>
            </GestureDetector>)}
          </Animated.View>
        </> : null}
        {!image && !loadError ? <View style={styles.loading}><ActivityRail label="Đang mở ảnh" /></View> : null}
        {loadError ? <View style={styles.loading}><Ionicons name="image-outline" size={40} color="white" /><Text style={styles.lightText}>Chưa mở được ảnh bài tập</Text><AppButton title="Chọn lại ảnh" onPress={() => router.back()} /></View> : null}
      </View>
      <View style={[styles.footer, landscape && styles.landscapeFooter]}>
        <View style={styles.controls}>
          <Pressable accessibilityRole="button" accessibilityLabel="Xoay ảnh 90 độ" disabled={disabled} onPress={() => { turns.set((turns.get() + 1) % 4); }} style={({ pressed }) => [styles.rotateButton, pressed && styles.pressed, disabled && styles.disabled]}>
            <Ionicons name="refresh-outline" size={24} color={COLORS.primaryDark} /><Text style={styles.rotateLabel}>Xoay 90°</Text>
          </Pressable>
          <StraightenRuler angle={fine} disabled={disabled} />
        </View>
        <View style={styles.secondaryRow}>
          <Pressable accessibilityRole="button" accessibilityLabel="Đặt lại ảnh và khung cắt" disabled={disabled} style={styles.secondary} onPress={reset}><Ionicons name="refresh" size={17} color={COLORS.primaryDark} /><Text style={styles.secondaryText}>Đặt lại</Text></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Dùng toàn ảnh" disabled={disabled} style={styles.secondary} onPress={() => select(true)}><Ionicons name="expand" size={17} color={COLORS.primaryDark} /><Text style={styles.secondaryText}>Toàn ảnh</Text></Pressable>
        </View>
        <AppButton title={processing ? 'Đang lưu ảnh…' : 'Dùng ảnh này'} accessibilityLabel="Xác nhận cắt ảnh" onPress={done} disabled={disabled} loading={processing} />
      </View>
    </View>
  </SafeAreaView></GestureHandlerRootView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background }, body: { flex: 1 }, landscape: { flexDirection: 'row' },
  tip: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 18, paddingVertical: 10, backgroundColor: COLORS.surfaceSubdued },
  tipText: { flex: 1, color: COLORS.textPrimary, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 18 },
  canvas: { flex: 1, overflow: 'hidden', backgroundColor: '#10121D' },
  shade: { position: 'absolute', backgroundColor: 'rgba(0,0,0,0.58)' },
  crop: { position: 'absolute', borderWidth: 1.5, borderColor: '#FFFFFF' },
  horizontal: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: 'rgba(255,255,255,0.35)' },
  vertical: { position: 'absolute', top: 0, bottom: 0, width: 1, backgroundColor: 'rgba(255,255,255,0.35)' },
  handle: { position: 'absolute', width: 48, height: 48, zIndex: 10 },
  topHandle: { left: '50%', top: -24, transform: [{ translateX: -24 }] },
  bottomHandle: { left: '50%', bottom: -24, transform: [{ translateX: -24 }] },
  leftHandle: { left: -24, top: '50%', transform: [{ translateY: -24 }] },
  rightHandle: { right: -24, top: '50%', transform: [{ translateY: -24 }] },
  horizontalGrip: { position: 'absolute', width: 24, height: 4, top: 22, left: 12, borderRadius: 2, backgroundColor: '#FFF' },
  verticalGrip: { position: 'absolute', width: 4, height: 24, top: 12, left: 22, borderRadius: 2, backgroundColor: '#FFF' },
  corner: { position: 'absolute', width: 22, height: 22, borderColor: '#FFFFFF' },
  tl: { left: -24, top: -24 }, tr: { right: -24, top: -24 }, bl: { left: -24, bottom: -24 }, br: { right: -24, bottom: -24 },
  tlVisual: { top: 20, left: 20, borderTopWidth: 4, borderLeftWidth: 4 }, trVisual: { top: 20, right: 20, borderTopWidth: 4, borderRightWidth: 4 },
  blVisual: { bottom: 20, left: 20, borderBottomWidth: 4, borderLeftWidth: 4 }, brVisual: { bottom: 20, right: 20, borderBottomWidth: 4, borderRightWidth: 4 },
  loading: { ...StyleSheet.absoluteFill as object, justifyContent: 'center', alignItems: 'center', gap: 16, padding: 24 },
  lightText: { color: '#FFF', fontFamily: FONTS.bold, fontSize: 17 },
  footer: { paddingHorizontal: 20, paddingVertical: 14, gap: 8, backgroundColor: COLORS.surface }, landscapeFooter: { width: 320, justifyContent: 'center' },
  controls: { flexDirection: 'row', alignItems: 'center', gap: 20 },
  rotateButton: { width: 64, minHeight: 64, borderRadius: 18, backgroundColor: COLORS.surfaceSubdued, alignItems: 'center', justifyContent: 'center', gap: 3 },
  rotateLabel: { fontFamily: FONTS.bold, fontSize: 11, color: COLORS.primaryDark }, pressed: { opacity: 0.65 }, disabled: { opacity: 0.4 },
  rulerBlock: { flex: 1, paddingHorizontal: 8 }, rulerHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  controlTitle: { color: COLORS.textPrimary, fontFamily: FONTS.bold, fontSize: 13 }, angleLabel: { color: COLORS.primaryDark, fontFamily: FONTS.extraBold, fontSize: 16 },
  ruler: { height: 60, marginTop: 4 }, ticks: { height: 26, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' },
  tick: { width: 1, height: 12, backgroundColor: '#B6AEC9' }, majorTick: { height: 22, width: 2, backgroundColor: '#8F839F' },
  degreeLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 }, degreeText: { color: COLORS.textSecondary, fontFamily: FONTS.semiBold, fontSize: 10 },
  angleMarker: { position: 'absolute', top: 0, height: 31, width: 3, backgroundColor: COLORS.primary, transform: [{ translateX: -1.5 }] },
  markerDot: { width: 9, height: 9, borderRadius: 5, backgroundColor: COLORS.primary, marginLeft: -3, marginTop: -3 },
  secondaryRow: { flexDirection: 'row', justifyContent: 'space-between' }, secondary: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 14 },
  secondaryText: { fontFamily: FONTS.bold, fontSize: 13, color: COLORS.primaryDark },
});
