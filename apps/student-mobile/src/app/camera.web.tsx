import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TouchableOpacity, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../components/ui/AppButton';
import { COLORS, FONTS, SIZES } from '../constants/theme';
import { recognitionDraftStore, resolveFlowDomain } from '../features/recognition/state/recognitionDraftStore';
import { normalizeImageDraft } from '../features/recognition/image/imagePipeline';

export default function WebCameraScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string; problemText?: string; retrySubmissionId?: string }>();
  const [permission, requestPermission] = useCameraPermissions();
  const compact = useWindowDimensions().height < 500;
  const camera = useRef<CameraView>(null);
  const preview = useRef<View>(null);
  const [context] = useState(() => recognitionDraftStore.getDraft()?.lessonContext);
  const mode = resolveFlowDomain(params.mode || 'MATH_TUTOR', null);
  const [focused, setFocused] = useState(true);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const [torch, setTorch] = useState(false);
  const [busy, setBusy] = useState(false);
  const [askingPermission, setAskingPermission] = useState(false);
  const active = useRef(true);
  const lock = useRef(false);
  const permissionLock = useRef(false);
  useFocusEffect(useCallback(() => {
    active.current = true;
    setFocused(true);
    setError(false);
    return () => {
      active.current = false;
      setFocused(false);
      setReady(false);
      setTorch(false);
    };
  }, []));

  const openCamera = async () => {
    if (permissionLock.current || lock.current) return;
    permissionLock.current = true;
    setAskingPermission(true);
    setReady(false);
    setError(false);
    try {
      const result = await requestPermission();
      if (active.current && !result.granted) setError(true);
    } catch { if (active.current) setError(true); }
    finally { permissionLock.current = false; if (active.current) setAskingPermission(false); }
  };
  const acquire = async (source: 'LIVE' | 'CAMERA' | 'GALLERY') => {
    if (lock.current || !active.current || (source === 'LIVE' && (!ready || error || !focused || !camera.current))) return;
    lock.current = true;
    setBusy(true);
    try {
      const options: ImagePicker.ImagePickerOptions = { mediaTypes: ['images'], allowsEditing: false, quality: 1, cameraType: ImagePicker.CameraType.back };
      let asset;
      if (source === 'LIVE') {
        asset = await camera.current!.takePictureAsync({ quality: 1, base64: false });
      } else {
        // Keep the fallback chooser inside the tap's user activation.
        const result = await (source === 'CAMERA' ? ImagePicker.launchCameraAsync(options) : ImagePicker.launchImageLibraryAsync(options));
        if (result.canceled || !result.assets?.[0]) return;
        asset = result.assets[0];
      }
      if (!asset || !active.current) return;
      const draft = await normalizeImageDraft(asset.uri, asset.width, asset.height, source === 'GALLERY' ? 'GALLERY' : 'CAMERA');
      if (!active.current) return;
      draft.mode = mode;
      draft.lessonContext = mode === 'MATH_TUTOR' ? context : undefined;
      draft.retrySubmissionId = mode === 'ARITHMETIC' ? params.retrySubmissionId : undefined;
      draft.problemText = typeof params.problemText === 'string' ? params.problemText.slice(0, 4000) : undefined;
      recognitionDraftStore.setDraft(draft);
      // Stop the preview before opening privacy.
      setFocused(false);
      setReady(false);
      router.push('/privacy');
    } catch {
      if (active.current) Alert.alert('Chưa chụp được ảnh', 'Em giữ chắc tay rồi thử lại, hoặc chọn ảnh trong thư viện nhé.');
    } finally { lock.current = false; if (active.current) setBusy(false); }
  };
  const toggleTorch = () => {
    const video = (preview.current as unknown as HTMLElement | null)?.querySelector?.('video');
    const stream = video?.srcObject as MediaStream | null;
    const capabilities = stream?.getVideoTracks()[0]?.getCapabilities?.() as (MediaTrackCapabilities & { torch?: boolean }) | undefined;
    if (!capabilities?.torch) {
      Alert.alert('Chưa bật được đèn', 'Máy ảnh này chưa hỗ trợ bật đèn tại đây. Em chọn nơi đủ sáng để chụp nhé.');
      return;
    }
    setTorch(value => !value);
  };
  const unavailable = error || permission?.status === 'denied';
  const live = focused && permission?.granted && !error;
  const canCapture = Boolean(live && ready);
  useEffect(() => {
    if (!live || ready) return;
    const deadline = setTimeout(() => setError(true), 15000);
    return () => clearTimeout(deadline);
  }, [live, ready]);
  const label = context?.purpose === 'ADD_WORK' ? 'Chụp bài em đã làm' : context?.purpose === 'ADD_PROBLEM' ? 'Chụp thêm đề bài' : 'Chụp bài toán để cùng học';
  return <View style={styles.screen}>
    <View ref={preview} style={StyleSheet.absoluteFill}>
      {live ? <CameraView ref={camera} style={StyleSheet.absoluteFill} facing="back" autofocus="on" enableTorch={torch}
        onCameraReady={() => setReady(true)} onMountError={() => { setReady(false); setError(true); setTorch(false); }} /> : null}
    </View>
    <SafeAreaView style={styles.overlay}>
      <View style={[styles.header, compact && styles.compactHeader]}>
        <TouchableOpacity style={styles.iconButton} accessibilityRole="button" accessibilityLabel="Đóng máy ảnh, quay lại"
          onPress={() => router.canGoBack() ? router.back() : router.replace('/(tabs)' as any)}>
          <Ionicons name="close" size={26} color="white" />
        </TouchableOpacity>
        <View style={styles.badge}><Ionicons name="bulb-outline" size={18} color="white" /><Text style={styles.badgeText}>{label}</Text></View>
        <TouchableOpacity style={styles.iconButton} accessibilityRole="button" accessibilityLabel="Xem hướng dẫn chụp ảnh"
          onPress={() => Alert.alert('Chụp rõ bài toán', 'Đặt trọn một bài toán vào khung. Chọn nơi đủ sáng, giữ chắc tay và đợi chữ rõ rồi chụp. Em sẽ cắt ảnh và che thông tin riêng tư ở bước tiếp theo.')}>
          <Ionicons name="help-circle-outline" size={26} color="white" />
        </TouchableOpacity>
      </View>
      <View style={styles.scanArea}>
        {!compact ? <View style={styles.pill}><Ionicons name="scan-outline" size={18} color="white" /><Text style={styles.instruction}>Đặt trọn một bài toán vào khung</Text></View> : null}
        <View style={[styles.frame, compact && styles.compactFrame]}>
          <View pointerEvents="none" style={[styles.corner, styles.topLeft]} /><View pointerEvents="none" style={[styles.corner, styles.topRight]} />
          <View pointerEvents="none" style={[styles.corner, styles.bottomLeft]} /><View pointerEvents="none" style={[styles.corner, styles.bottomRight]} />
          {!canCapture ? <View style={[styles.notice, compact && styles.compactNotice]}>
            {!compact ? <Ionicons name="camera-outline" size={36} color="white" /> : null}
            <Text style={[styles.noticeText, compact && styles.compactNoticeText]}>{unavailable ? 'Chưa mở được máy ảnh. Em thử lại hoặc chụp bằng máy ảnh của điện thoại nhé.' : live ? 'Đang mở máy ảnh…' : askingPermission ? 'Chọn cho phép máy ảnh trong thông báo đang mở. Em cũng có thể chọn ảnh từ thư viện.' : 'Cho phép mở máy ảnh để ngắm và chụp bài toán nhé.'}</Text>
            {live || busy || askingPermission ? <ActivityIndicator color="white" /> : <AppButton title={unavailable ? 'Thử mở lại máy ảnh' : 'Cho phép mở máy ảnh'} onPress={() => void openCamera()} />}
            {unavailable ? <AppButton title="Chụp bằng máy ảnh điện thoại" disabled={busy} onPress={() => void acquire('CAMERA')} /> : null}
          </View> : null}
        </View>
        {!compact ? <View style={styles.pill}><Ionicons name="information-circle-outline" size={16} color="white" /><Text style={styles.instruction}>Chỉ chụp một bài toán mỗi lần</Text></View> : null}
      </View>
      <View style={[styles.footer, compact && styles.compactFooter]}>
        <TouchableOpacity style={[styles.footerAction, compact && styles.compactFooterAction]} accessibilityRole="button" accessibilityLabel="Chọn ảnh từ thư viện" disabled={busy} onPress={() => void acquire('GALLERY')}>
          <View style={styles.iconButton}><Ionicons name="images-outline" size={24} color="white" /></View><Text style={styles.footerText}>Thư viện</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.shutter, compact && styles.compactShutter, (!canCapture || busy) && styles.disabled]} accessibilityRole="button" accessibilityLabel="Chụp ảnh bài toán"
          accessibilityState={{ disabled: !canCapture || busy, busy }} disabled={!canCapture || busy} onPress={() => void acquire('LIVE')}>
          {busy ? <ActivityIndicator color="white" /> : <View style={[styles.shutterInner, compact && styles.compactShutterInner]} />}
        </TouchableOpacity>
        <TouchableOpacity style={[styles.footerAction, compact && styles.compactFooterAction]} accessibilityRole="button" accessibilityLabel={torch ? 'Tắt đèn pin' : 'Bật đèn pin'}
          accessibilityState={{ disabled: !canCapture || busy, selected: torch }} disabled={!canCapture || busy} onPress={toggleTorch}>
          <View style={styles.iconButton}><Ionicons name={torch ? 'flash' : 'flash-off-outline'} size={24} color={torch ? COLORS.warning : 'white'} /></View>
          <Text style={styles.footerText}>{torch ? 'Tắt đèn' : 'Bật đèn'}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  </View>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#080B16' }, overlay: { flex: 1, backgroundColor: 'rgba(15,23,42,0.15)' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, padding: SIZES.medium },
  iconButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(15,23,42,0.65)', alignItems: 'center', justifyContent: 'center' },
  badge: { flexDirection: 'row', gap: 6, flexShrink: 1, alignItems: 'center', borderRadius: 24, padding: 10, backgroundColor: 'rgba(15,23,42,0.65)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  badgeText: { fontFamily: FONTS.bold, fontSize: 13, color: 'white', flexShrink: 1, textAlign: 'center' },
  scanArea: { flex: 1, minHeight: 0, alignItems: 'center', justifyContent: 'center', paddingHorizontal: SIZES.medium, gap: 12 },
  pill: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(15,23,42,0.75)', padding: 10, borderRadius: 24 },
  instruction: { fontFamily: FONTS.bold, fontSize: 13, color: 'white', flexShrink: 1, textAlign: 'center' },
  frame: { flex: 1, minHeight: 0, width: '100%', maxWidth: 340, maxHeight: 420, alignItems: 'center', justifyContent: 'center' },
  corner: { position: 'absolute', width: 36, height: 36, borderColor: 'white' },
  topLeft: { top: 0, left: 0, borderTopWidth: 4, borderLeftWidth: 4, borderTopLeftRadius: 16 },
  topRight: { top: 0, right: 0, borderTopWidth: 4, borderRightWidth: 4, borderTopRightRadius: 16 },
  bottomLeft: { bottom: 0, left: 0, borderBottomWidth: 4, borderLeftWidth: 4, borderBottomLeftRadius: 16 },
  bottomRight: { bottom: 0, right: 0, borderBottomWidth: 4, borderRightWidth: 4, borderBottomRightRadius: 16 },
  notice: { width: '100%', maxWidth: 290, padding: 16, gap: 14, alignItems: 'center', borderRadius: 20, backgroundColor: 'rgba(15,23,42,0.9)' },
  noticeText: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 22, color: 'white', textAlign: 'center' },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', padding: SIZES.medium, marginTop: 12, backgroundColor: 'rgba(15,23,42,0.75)' },
  footerAction: { alignItems: 'center', width: 80, minHeight: 64, gap: 6 }, footerText: { fontFamily: FONTS.semiBold, color: 'white', fontSize: 12 },
  shutter: { width: 76, height: 76, borderRadius: 38, borderWidth: 3, borderColor: 'white', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.3)' },
  shutterInner: { width: 60, height: 60, borderRadius: 30, backgroundColor: 'white' }, disabled: { opacity: 0.5 },
  compactHeader: { padding: 8 }, compactFrame: { maxWidth: 600 },
  compactNotice: { maxWidth: 440, padding: 8, gap: 8 }, compactNoticeText: { fontSize: 13, lineHeight: 18 },
  compactFooter: { padding: 8, marginTop: 8 }, compactFooterAction: { flexDirection: 'row', width: 110, minHeight: 48 },
  compactShutter: { width: 60, height: 60, borderRadius: 30 }, compactShutterInner: { width: 46, height: 46, borderRadius: 23 },
});
