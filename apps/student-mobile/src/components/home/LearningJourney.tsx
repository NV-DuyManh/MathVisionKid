import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';

export function LearningJourney({ desktop, onPractice, onAcquire }: { desktop: boolean; onPractice: () => void; onAcquire: () => void }) {
  return <View style={styles.section} testID="learning-journey">
    <Text style={styles.heading} accessibilityRole="header">Hành trình học tập</Text>
    <View style={[styles.map, desktop && styles.mapDesktop]}>
      <View style={styles.road} pointerEvents="none" />
      <View style={styles.stops}>
        {[
          ['Ôn tập', 'Kiến thức cơ bản', onPractice], ['Luyện tập', 'Làm bài theo chủ đề', onPractice],
          ['Khám phá', 'Bài toán quanh em', onAcquire],
        ].map(([title, detail, onPress], index) => <Pressable key={String(title)} accessibilityRole="button" accessibilityLabel={`${title}. ${detail}`}
          onPress={onPress as () => void} style={({ pressed }) => [styles.stop, pressed && { opacity: .72 }]}>
          <View style={styles.medalShadow}><LinearGradient colors={index === 2 ? ['#FFE8A0', '#EFB63E'] : ['#B194FD', '#6941E8']} style={styles.medal}>
            <Text style={[styles.number, index === 2 && { color: '#6742CB' }]}>{index + 1}</Text>
          </LinearGradient><Ionicons name="sparkles" size={16} color="#F3C65D" style={styles.spark} accessible={false} /></View>
          <Text style={[styles.label, !desktop && styles.labelMobile]}>{String(title)}</Text>
        </Pressable>)}
      </View>
    </View>
  </View>;
}
const styles = StyleSheet.create({
  section: { marginTop: 4, marginBottom: 19 }, heading: { fontFamily: FONTS.extraBold, fontSize: 21, color: COLORS.textPrimary, marginBottom: 10 },
  map: { minHeight: 104, position: 'relative', paddingTop: 12 }, mapDesktop: { minHeight: 118 },
  road: { position: 'absolute', left: 0, right: 0, top: 43, height: 6, borderRadius: 4, backgroundColor: '#DFD0F2' },
  island: { position: 'absolute', width: 110, height: 95, top: -12 }, stops: { flexDirection: 'row', justifyContent: 'space-between', width: '100%' },
  stop: { flex: 1, minWidth: 0, alignItems: 'center', paddingHorizontal: 4, paddingTop: 5, paddingBottom: 9, borderRadius: 18 },
  lowStop: { marginTop: 36 }, labelMobile: { fontSize: 13, lineHeight: 18 },
  medalShadow: { width: 63, height: 59, borderRadius: 32, alignItems: 'center', backgroundColor: '#ECE3FB', padding: 4, marginBottom: 7 },
  medal: { width: 49, height: 49, borderRadius: 25, borderWidth: 3, borderColor: '#FFF', alignItems: 'center', justifyContent: 'center' },
  number: { color: '#FFF8BF', fontFamily: FONTS.black, fontSize: 25, lineHeight: 34 }, spark: { position: 'absolute', right: -2, top: 0 },
  label: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 16, textAlign: 'center', marginTop: 3 },
  detail: { fontFamily: FONTS.regular, color: '#756D92', fontSize: 12, lineHeight: 18, textAlign: 'center', marginTop: 5 },
});
