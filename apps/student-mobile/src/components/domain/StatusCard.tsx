import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppCard } from '../ui/AppCard';
import { FONTS, COLORS, SIZES, IS_STUDENT_WEB } from '../../constants/theme';

interface StatusCardProps {
  title: string;
  subtitle?: string;
  status: 'success' | 'warning' | 'error' | 'info';
}

export const StatusCard: React.FC<StatusCardProps> = ({ title, subtitle, status }) => {
  const getConfig = () => {
    switch (status) {
      case 'success':
        return {
          icon: 'checkmark-circle' as const,
          color: COLORS.success,
          bgColor: '#F0FDF4',
          borderColor: '#BBF7D0',
          badgeText: 'Thành công',
        };
      case 'warning':
        return {
          icon: 'alert-circle' as const,
          color: COLORS.warning,
          bgColor: '#FFFBEB',
          borderColor: '#FDE68A',
          badgeText: 'Lưu ý',
        };
      case 'error':
        return {
          icon: 'close-circle' as const,
          color: COLORS.error,
          bgColor: '#FEF2F2',
          borderColor: '#FECACA',
          badgeText: 'Cần sửa',
        };
      case 'info':
        return {
          icon: 'information-circle' as const,
          color: COLORS.primary,
          bgColor: '#EFF6FF',
          borderColor: '#BFDBFE',
          badgeText: 'Thông tin',
        };
    }
  };

  const config = getConfig();

  if (IS_STUDENT_WEB) {
    return <View accessibilityLiveRegion="polite" style={[styles.webStatus, { backgroundColor: config.bgColor, borderColor: config.borderColor }]}>
      <Text accessibilityRole="header" aria-level={2} style={styles.webTitle}>{title}</Text>
      {subtitle && <Text style={[styles.subtitle, styles.webSubtitle]}>{subtitle}</Text>}
    </View>;
  }

  return (
    <AppCard
      style={[
        styles.container,
        { backgroundColor: config.bgColor, borderColor: config.borderColor },
      ]}
      variant="outlined"
      accessible
      accessibilityLabel={`${config.badgeText}: ${title}. ${subtitle || ''}`}
    >
      <View style={styles.content}>
        <View style={[styles.iconBadge, { backgroundColor: config.borderColor }]}>
          <Ionicons name={config.icon} size={28} color={config.color} />
        </View>
        <View style={styles.textContainer}>
          <Text style={styles.title}>{title}</Text>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      </View>
    </AppCard>
  );
};

const styles = StyleSheet.create({
  webStatus: { padding: 16, borderWidth: 1, borderRadius: 16, marginBottom: 16 },
  webTitle: { fontFamily: FONTS.extraBold, color: COLORS.textPrimary, fontSize: 22, lineHeight: 29 },
  webSubtitle: { fontSize: 16, lineHeight: 24, marginTop: 6 },
  container: {
    marginBottom: SIZES.medium,
    padding: SIZES.large,
    borderRadius: SIZES.cardRadius,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  iconBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  textContainer: {
    marginLeft: SIZES.medium,
    flex: 1,
  },
  title: {
    fontSize: 17,
    fontFamily: FONTS.bold,
    color: COLORS.textPrimary,
    marginBottom: 4,
    lineHeight: 22,
  },
  subtitle: {
    fontFamily: FONTS.regular,
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  },
});
