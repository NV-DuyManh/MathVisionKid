import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppCard } from '../ui/AppCard';
import { COLORS, SIZES } from '../../constants/theme';

interface HintCardProps {
  hint: string;
}

export const HintCard: React.FC<HintCardProps> = ({ hint }) => {
  return (
    <AppCard style={styles.container} variant="elevated">
      <View style={styles.header}>
        <Ionicons name="bulb" size={24} color={COLORS.warning} />
        <Text style={styles.title}>Gợi ý từ MathVision</Text>
      </View>
      <Text style={styles.hintText}>{hint}</Text>
    </AppCard>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFBEB',
    borderColor: '#FEF3C7',
    borderWidth: 1,
    marginBottom: SIZES.medium,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SIZES.small,
  },
  title: {
    marginLeft: SIZES.small,
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.warning,
  },
  hintText: {
    fontSize: 15,
    color: COLORS.textPrimary,
    lineHeight: 22,
  }
});
