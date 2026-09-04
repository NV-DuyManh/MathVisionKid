import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppCard } from '../ui/AppCard';
import { COLORS, SIZES } from '../../constants/theme';

interface StatusCardProps {
  title: string;
  subtitle?: string;
  status: 'success' | 'warning' | 'error' | 'info';
}

export const StatusCard: React.FC<StatusCardProps> = ({ title, subtitle, status }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'success': return COLORS.success;
      case 'warning': return COLORS.warning;
      case 'error': return COLORS.error;
      case 'info': return COLORS.primary;
    }
  };

  const getIconName = () => {
    switch (status) {
      case 'success': return 'checkmark-circle';
      case 'warning': return 'alert-circle';
      case 'error': return 'close-circle';
      case 'info': return 'information-circle';
    }
  };

  return (
    <AppCard style={styles.container}>
      <View style={styles.content}>
        <Ionicons name={getIconName()} size={32} color={getStatusColor()} />
        <View style={styles.textContainer}>
          <Text style={styles.title}>{title}</Text>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      </View>
    </AppCard>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: SIZES.medium,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  textContainer: {
    marginLeft: SIZES.medium,
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
  }
});
