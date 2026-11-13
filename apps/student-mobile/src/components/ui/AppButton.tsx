import React from 'react';
import { ActivityIndicator, TouchableOpacity, Text, StyleSheet, ViewStyle, TextStyle, View } from 'react-native';
import { FONTS, COLORS, SIZES, SHADOWS, IS_STUDENT_WEB, WEB_DESIGN } from '../../constants/theme';

interface AppButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outlined' | 'danger' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
  loadingTitle?: string;
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
  loadingTitle = 'Đang xử lý…',
  style,
  textStyle,
  icon,
  accessibilityLabel,
}) => {
  const getBackgroundColor = () => {
    if (disabled && !loading) return COLORS.border;
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
    if (disabled && !loading) return COLORS.textMuted;
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
        variant === 'primary' && isInteractive && (IS_STUDENT_WEB ? styles.webRaised : SHADOWS.small),
        variant === 'secondary' && styles.secondaryBorder,
        variant === 'outlined' && styles.outlined,
        style,
        IS_STUDENT_WEB && styles.webShape,
      ]}
      onPress={onPress}
      disabled={!isInteractive}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
      accessibilityState={{ disabled: !isInteractive, busy: loading }}
      aria-busy={loading}
      {...(IS_STUDENT_WEB && variant === 'primary' ? { dataSet: { studentPrimary: 'true' } } : {})}
    >
      {loading ? (
        <View style={styles.loadingContent}>
          <ActivityIndicator size="small" color={getTextColor()} accessible={false} />
          <Text accessibilityLiveRegion="polite" style={[styles.text, { color: getTextColor() }, textStyle]}>{loadingTitle}</Text>
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
  webShape: { borderRadius: WEB_DESIGN.components.action.radius },
  webRaised: { borderBottomWidth: 3, borderBottomColor: '#173FAE' },
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
    borderColor: IS_STUDENT_WEB ? WEB_DESIGN.colors.line : '#E1D7F7',
  },
  loadingContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
});
