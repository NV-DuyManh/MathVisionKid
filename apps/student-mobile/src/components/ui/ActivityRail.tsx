import React from 'react';
import { StyleSheet, View } from 'react-native';
import { COLORS } from '../../constants/theme';

/** Activity only: no invented percentage or remaining time. */
export function ActivityRail({ label = 'Đang xử lý' }: { label?: string }) {
  return <View style={styles.track} accessibilityRole="progressbar" accessibilityLabel={label} accessibilityState={{ busy: true }}>
    <View style={styles.bar} />
  </View>;
}
const styles = StyleSheet.create({
  track: { width: 110, height: 8, borderRadius: 4, backgroundColor: '#E8E1FB', overflow: 'hidden', alignSelf: 'center', marginVertical: 12 },
  bar: { width: 40, height: 8, marginLeft: 35, borderRadius: 4, backgroundColor: COLORS.primary },
});
