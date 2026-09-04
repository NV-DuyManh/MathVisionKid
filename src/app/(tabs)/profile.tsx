import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SIZES } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppCard } from '../../components/ui/AppCard';

export default function ProfileScreen() {
  return (
    <View style={styles.container}>
      <AppHeader title="Hồ sơ của em" />
      <View style={styles.content}>
        <AppCard style={styles.card}>
          <Text style={styles.name}>Minh</Text>
          <Text style={styles.info}>Học sinh · Lớp 3</Text>
        </AppCard>

        <AppCard style={styles.menuCard} variant="outlined">
          <Text style={styles.menuItem}>Bảo mật & Dữ liệu</Text>
          <View style={styles.divider} />
          <Text style={styles.menuItem}>Ngôn ngữ (Tiếng Việt)</Text>
          <View style={styles.divider} />
          <Text style={styles.menuItem}>Trợ giúp</Text>
          <View style={styles.divider} />
          <Text style={styles.menuItem}>Thông tin ứng dụng</Text>
          <View style={styles.divider} />
          <Text style={styles.logout}>Đăng xuất</Text>
        </AppCard>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.medium,
  },
  card: {
    alignItems: 'center',
    paddingVertical: SIZES.xlarge,
    marginBottom: SIZES.large,
  },
  name: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 8,
  },
  info: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
  },
  menuItem: {
    padding: SIZES.large,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  logout: {
    padding: SIZES.large,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
  }
});
