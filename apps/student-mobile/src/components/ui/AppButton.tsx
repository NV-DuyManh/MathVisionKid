import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle, TextStyle, View } from 'react-native';
import { FONTS, COLORS, SIZES, SHADOWS } from '../../constants/theme';

interface AppButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outlined' | 'danger' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  icon?: React.ReactNode;
  accessibilityLabel?: string;
}

export const AppButton: React.FC<AppButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
  textStyle,
  icon,
  accessibilityLabel,
}) => {
  const getBackgroundColor = () => {
    if (disabled) return COLORS.border;
    switch (variant) {
      case 'primary': return COLORS.primary;
      case 'secondary': return COLORS.surfaceSubdued;
      case 'danger': return COLORS.error;
      case 'outlined':
      case 'ghost': return 'transparent';
      default: return COLORS.primary;
    }
  };

  const getTextColor = () => {
    if (disabled) return COLORS.textMuted;
    switch (variant) {
      case 'primary': return COLORS.surface;
      case 'secondary': return COLORS.primaryDark;
      case 'danger': return COLORS.surface;
      case 'outlined': return COLORS.primary;
      case 'ghost': return COLORS.textSecondary;
      default: return COLORS.surface;
    }
  };

  const isInteractive = !disabled && !loading;

  return (
    <TouchableOpacity
      style={[
        styles.container,
        { backgroundColor: getBackgroundColor() },
        variant === 'primary' && isInteractive && SHADOWS.small,
        variant === 'secondary' && styles.secondaryBorder,
        variant === 'outlined' && styles.outlined,
        style,
      ]}
      onPress={onPress}
      disabled={!isInteractive}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
      accessibilityState={{ disabled: !isInteractive, busy: loading }}
    >
      {loading ? (
        <View style={styles.loadingContent}>
          <Text style={[styles.text, { color: getTextColor() }]}>Đang xử lý…</Text>
          <View style={[styles.loadingTrack, { backgroundColor: getTextColor() + '44' }]}>
            <View style={[styles.loadingBar, { backgroundColor: getTextColor() }]} />
          </View>
        </View>
      ) : (
        <View style={styles.innerContent}>
          {icon && <View style={styles.iconContainer}>{icon}</View>}
          <Text style={[styles.text, { color: getTextColor() }, textStyle]}>
            {title}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    minHeight: 52,
    borderRadius: SIZES.buttonRadius,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SIZES.xlarge,
    paddingVertical: 12,
  },
  innerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    marginRight: SIZES.small,
  },
  text: {
    fontSize: 16,
    fontFamily: FONTS.bold,
    letterSpacing: 0.2,
    textAlign: 'center',
    flexShrink: 1,
  },
  outlined: {
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  secondaryBorder: {
    borderWidth: 1,
    borderColor: '#E1D7F7',
  },
  loadingContent: { alignItems: 'center', gap: 6 },
  loadingTrack: { width: 90, height: 4, borderRadius: 2, overflow: 'hidden' },
  loadingBar: { width: 40, height: 4, marginLeft: 25, borderRadius: 2 },
});
