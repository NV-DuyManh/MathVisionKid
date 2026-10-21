import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AppIllustration } from '../ui/AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';

export function LearningJourney({ desktop, onPractice, onAcquire }: { desktop: boolean; onPractice: () => void; onAcquire: () => void }) {
  return <View style={styles.section} testID="learning-journey">
    <Text style={styles.heading} accessibilityRole="header">Hành trình học tập của em</Text>
    <View style={[styles.map, desktop && styles.mapDesktop]}>
      {desktop ? <>
        <Svg width="100%" height={154} viewBox="0 0 1000 180" preserveAspectRatio="none" style={styles.road} aria-hidden={true}>
          <Path d="M15 156C-4 58 99 30 187 70S344 119 439 77 572 56 667 94 819 104 914 72 980 105 987 154" fill="none" stroke="#E6DEFC" strokeWidth={18} />
          <Path d="M15 153C-4 55 99 27 187 67S344 116 439 74 572 53 667 91 819 101 914 69 980 102 987 151" fill="none" stroke="#D6C9F7" strokeWidth={10} />
          <Path d="M15 153C-4 55 99 27 187 67S344 116 439 74 572 53 667 91 819 101 914 69 980 102 987 151" fill="none" stroke="#F8F4FF" strokeWidth={1.5} strokeDasharray="6 12" />
        </Svg>
        <AppIllustration source={require('../../../assets/illustrations/cactus-island.png')} style={[styles.island, { left: '20%' }]} accessible={false} />
        <AppIllustration source={require('../../../assets/illustrations/cactus-island.png')} style={[styles.island, { left: '65%' }]} accessible={false} />
      </> : <View style={styles.straightRoad} accessible={false}>{[1, 2, 3].map(i => <View key={i} style={styles.diamond} />)}</View>}
      <View style={styles.stops}>
        {[
          ['Ôn tập', 'Kiến thức cơ bản', onPractice], ['Luyện tập', 'Làm bài theo chủ đề', onPractice],
          ['Khám phá', 'Bài toán quanh em', onAcquire], ['Kiểm tra', 'Cùng xem bài làm', onAcquire],
        ].map(([title, detail, onPress], index) => <Pressable key={String(title)} accessibilityRole="button" accessibilityLabel={`${title}. ${detail}`}
          onPress={onPress as () => void} style={({ pressed }) => [styles.stop, pressed && { opacity: .72 }]}>
          <View style={styles.medalShadow}><LinearGradient colors={index % 2 ? ['#FFE8A0', '#EFB63E'] : ['#B194FD', '#6941E8']} style={styles.medal}>
            <Text style={[styles.number, index % 2 === 1 && { color: '#6742CB' }]}>{index + 1}</Text>
          </LinearGradient><Ionicons name="sparkles" size={16} color="#F3C65D" style={styles.spark} accessible={false} /></View>
          <Text style={styles.label}>{String(title)}</Text><Text style={styles.detail}>{String(detail)}</Text>
        </Pressable>)}
      </View>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  section: { marginTop: 4, marginBottom: 24 }, heading: { fontFamily: FONTS.extraBold, fontSize: 22, color: COLORS.textPrimary, marginBottom: 10 },
  map: { height: 164, position: 'relative', paddingTop: 12 }, mapDesktop: { height: 184 },
  road: { position: 'absolute', left: 0, right: 0, top: 0 }, straightRoad: { position: 'absolute', top: 42, height: 7, width: '100%', backgroundColor: '#D9CCF6', flexDirection: 'row', justifyContent: 'space-evenly', alignItems: 'center', borderRadius: 6 },
  diamond: { width: 9, height: 9, backgroundColor: '#FFF', borderWidth: 2, borderColor: '#BAA3EA', transform: [{ rotate: '45deg' }] },
  island: { position: 'absolute', width: 110, height: 95, top: -12 }, stops: { flexDirection: 'row', justifyContent: 'space-between', width: '100%' },
  stop: { flex: 1, minWidth: 0, alignItems: 'center', paddingHorizontal: 4, paddingTop: 5, paddingBottom: 9, borderRadius: 18 },
  medalShadow: { width: 63, height: 59, borderRadius: 32, alignItems: 'center', backgroundColor: '#ECE3FB', padding: 4, marginBottom: 7 },
  medal: { width: 49, height: 49, borderRadius: 25, borderWidth: 3, borderColor: '#FFF', alignItems: 'center', justifyContent: 'center' },
  number: { color: '#FFF8BF', fontFamily: FONTS.black, fontSize: 25, lineHeight: 34 }, spark: { position: 'absolute', right: -2, top: 0 },
  label: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 16, textAlign: 'center', marginTop: 3 },
  detail: { fontFamily: FONTS.regular, color: '#756D92', fontSize: 12, lineHeight: 18, textAlign: 'center', marginTop: 5 },
});
