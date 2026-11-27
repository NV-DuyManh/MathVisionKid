import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Path } from 'react-native-svg';
import { COLORS, FONTS } from '../../constants/theme';
import { AppIllustration } from '../ui/AppIllustration';

const stageColors = [
  { gradient: ['#7852E5', '#6440D8'], ring: '#EDE3FF', ink: '#FFFFFF' },
  { gradient: ['#2873DA', '#1854BA'], ring: '#DBEEFF', ink: '#FFFFFF' },
  { gradient: ['#83E9C7', '#45C7A5'], ring: '#D9F6EC', ink: '#123D34' },
  { gradient: ['#FFE89F', '#EFB63E'], ring: '#FFF1CC', ink: '#613C08' },
] as const;

type Grove = { left: `${number}%`; size: number; top?: number; bottom?: number };
const scenery: Record<'desktop' | 'compact', Grove[]> = {
  desktop: [
    { left: '5%', top: 10, size: 44 },
    { left: '24%', top: 19, size: 58 },
    { left: '49%', top: 9, size: 51 },
    { left: '75%', top: 20, size: 56 },
    { left: '95%', top: 8, size: 43 },
    { left: '25%', top: 110, size: 53 },
    { left: '48%', top: 104, size: 40 },
    { left: '52%', top: 120, size: 31 },
    { left: '75%', top: 110, size: 55 },
  ],
  compact: [
    { left: '8%', top: 6, size: 35 },
    { left: '33%', top: 0, size: 41 },
    { left: '63%', top: 2, size: 36 },
    { left: '91%', top: 4, size: 41 },
    { left: '22%', bottom: 1, size: 33 },
    { left: '48%', bottom: 5, size: 39 },
    { left: '75%', bottom: 0, size: 34 },
  ],
};

export function LearningJourney({ desktop, webMap, onPractice, onAcquire, onCheck }: {
  desktop: boolean; webMap: boolean; onPractice: () => void; onAcquire: () => void; onCheck: () => void;
}) {
  const stages = [
    { title: 'Ôn tập', detail: 'Kiến thức cơ bản', onPress: onPractice },
    { title: 'Luyện tập', detail: 'Làm bài theo chủ đề', onPress: onPractice },
    { title: 'Khám phá', detail: 'Bài toán quanh em', onPress: onAcquire },
    { title: 'Kiểm tra', detail: 'Thử sức với câu đố', onPress: onCheck },
  ];
  return <View style={styles.section} testID="learning-journey">
    <Text style={styles.heading} accessibilityRole="header">Hành trình học tập</Text>
    <View style={[styles.map, desktop && styles.mapDesktop, webMap && styles.webMap]}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none" accessible={false} aria-hidden>
        {scenery[webMap ? 'desktop' : 'compact'].map(({ left, top, bottom, size }, index) =>
          <AppIllustration key={`${left}:${top ?? bottom}`} source={require('../../../assets/illustrations/web/cactus-island.webp')}
            style={[styles.grove, { left, top, bottom, width: size, height: size * .73,
              transform: [{ translateX: -size / 2 }, { scaleX: index % 2 ? -1 : 1 }] }]} accessible={false} />)}
      </View>
      {webMap ? <View style={styles.curve} pointerEvents="none" accessible={false}>
        <Svg width="100%" height={88} viewBox="0 0 400 88" preserveAspectRatio="none">
          <Path d="M0 47 C20 27 29 26 50 39 S115 67 150 55 S215 25 250 39 S315 68 350 55 S382 39 400 37" stroke="#DCD1FE" strokeWidth={10} fill="none" />
          <Path d="M0 47 C20 27 29 26 50 39 S115 67 150 55 S215 25 250 39 S315 68 350 55 S382 39 400 37" stroke="#FFFFFF" strokeWidth={2} strokeDasharray="4 5" fill="none" />
        </Svg>
      </View> : <View style={styles.road} pointerEvents="none" />}
      <View style={styles.stops}>
        {stages.map(({ title, detail, onPress }, index) => <Pressable key={title} accessibilityRole="button" accessibilityLabel={`${title}. ${detail}`}
          onPress={onPress} style={({ pressed }) => [styles.stop, webMap && index % 2 === 1 && styles.lowStop, pressed && { opacity: .72 }]}>
          <View style={[styles.medalShadow, { backgroundColor: stageColors[index].ring }]}><LinearGradient colors={stageColors[index].gradient} style={styles.medal}>
            <Text style={[styles.number, { color: stageColors[index].ink }]}>{index + 1}</Text>
          </LinearGradient><Ionicons name="sparkles" size={16} color="#F3C65D" style={styles.spark} accessible={false} /></View>
          <Text style={[styles.label, !desktop && styles.labelMobile]}>{title}</Text>
          {webMap && desktop && <Text style={styles.detail}>{detail}</Text>}
        </Pressable>)}
      </View>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  section: { marginTop: 4, marginBottom: 19 }, heading: { fontFamily: FONTS.extraBold, fontSize: 21, color: COLORS.textPrimary, marginBottom: 10 },
  map: { minHeight: 104, position: 'relative', paddingTop: 36, paddingBottom: 29 }, mapDesktop: { minHeight: 118 },
  webMap: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 20, backgroundColor: COLORS.surface, paddingTop: 39, paddingBottom: 0 },
  curve: { position: 'absolute', top: 31, left: 0, right: 0 },
  road: { position: 'absolute', left: 0, right: 0, top: 67, height: 6, borderRadius: 4, backgroundColor: '#DFD0F2' },
  grove: { position: 'absolute' }, stops: { flexDirection: 'row', justifyContent: 'space-between', width: '100%' },
  stop: { flex: 1, minWidth: 0, alignItems: 'center', paddingHorizontal: 4, paddingTop: 5, paddingBottom: 9, borderRadius: 18 },
  lowStop: { marginTop: 16 }, labelMobile: { fontSize: 13, lineHeight: 18 },
  medalShadow: { width: 63, height: 59, borderRadius: 32, alignItems: 'center', backgroundColor: '#ECE3FB', padding: 4, marginBottom: 7 },
  medal: { width: 49, height: 49, borderRadius: 25, borderWidth: 3, borderColor: '#FFF', alignItems: 'center', justifyContent: 'center' },
  number: { color: '#FFF8BF', fontFamily: FONTS.black, fontSize: 25, lineHeight: 34 }, spark: { position: 'absolute', right: -2, top: 0 },
  label: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 16, textAlign: 'center', marginTop: 3 },
  detail: { fontFamily: FONTS.regular, color: '#756D92', fontSize: 12, lineHeight: 18, textAlign: 'center', marginTop: 5 },
});
