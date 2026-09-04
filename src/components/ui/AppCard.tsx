import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';

interface AppCardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'elevated' | 'flat' | 'outlined';
}

export const AppCard: React.FC<AppCardProps> = ({ children, style, variant = 'elevated' }) => {
  return (
    <View style={[
      styles.card,
      variant === 'elevated' && SHADOWS.small,
      variant === 'outlined' && styles.outlined,
      style
    ]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.cardRadius,
    padding: SIZES.medium,
  },
  outlined: {
    borderWidth: 1,
    borderColor: COLORS.border,
  }
});
