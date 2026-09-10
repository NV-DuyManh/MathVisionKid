import React, { useContext } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { COLORS, SIZES, SHADOWS } from '../../constants/theme';
import { AppHeader } from '../../components/ui/AppHeader';
import { AppCard } from '../../components/ui/AppCard';
import { AuthContext } from '../../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const auth = useContext(AuthContext);
  const user = auth?.user;

  const handleLogout = () => {
    Alert.alert(
      'Đăng xuất',
      'Em có chắc chắn muốn đăng xuất không?',
      [
        { text: 'Hủy', style: 'cancel' },
        { text: 'Đăng xuất', style: 'destructive', onPress: () => auth?.logout() },
      ]
    );
  };

  const menuItems = [
    {
      icon: 'shield-checkmark-outline' as const,
      label: 'Bảo mật & Dữ liệu riêng tư',
      sublabel: 'Ảnh được bảo vệ theo chuẩn riêng tư',
    },
    {
      icon: 'language-outline' as const,
      label: 'Ngôn ngữ hiển thị',
      sublabel: 'Tiếng Việt',
    },
    {
      icon: 'help-circle-outline' as const,
      label: 'Hướng dẫn sử dụng',
      sublabel: 'Cách chụp bài rõ nét',
    },
    {
      icon: 'information-circle-outline' as const,
      label: 'Thông tin ứng dụng',
      sublabel: 'MathVision Kids v1.0.0',
    },
  ];

  return (
    <View style={styles.container}>
      <AppHeader title="Hồ sơ của em" />
      <ScrollView contentContainerStyle={styles.content}>
        {/* Student identity card */}
        <AppCard style={styles.card} variant="elevated">
          <View style={[styles.avatarBadge, SHADOWS.small]}>
            <Ionicons name="school" size={36} color={COLORS.primary} />
          </View>
          <Text style={styles.name}>{user?.name || user?.email || 'Học sinh'}</Text>
          <View style={styles.gradePill}>
            <Text style={styles.gradeText}>
              {user?.grade ? `Học sinh Lớp ${user.grade}` : 'Học sinh Tiểu học'}
            </Text>
          </View>
        </AppCard>

        {/* Menu items card */}
        <AppCard style={styles.menuCard} variant="outlined">
          {menuItems.map((item, index) => (
            <View key={item.label}>
              <View style={styles.menuItem}>
                <View style={styles.menuIconContainer}>
                  <Ionicons name={item.icon} size={22} color={COLORS.primary} />
                </View>
                <View style={styles.menuTextContainer}>
                  <Text style={styles.menuLabel}>{item.label}</Text>
                  <Text style={styles.menuSublabel}>{item.sublabel}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={COLORS.textMuted} />
              </View>
              {index < menuItems.length - 1 && <View style={styles.divider} />}
            </View>
          ))}
        </AppCard>

        {/* Logout button */}
        <TouchableOpacity
          style={styles.logoutButton}
          onPress={handleLogout}
          accessibilityRole="button"
          accessibilityLabel="Đăng xuất khỏi ứng dụng"
        >
          <Ionicons name="log-out-outline" size={22} color={COLORS.error} />
          <Text style={styles.logoutText}>Đăng xuất</Text>
        </TouchableOpacity>
      </ScrollView>
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
    paddingBottom: SIZES.xxlarge,
    maxWidth: 600,
    width: '100%',
    alignSelf: 'center',
  },
  card: {
    alignItems: 'center',
    paddingVertical: SIZES.xxlarge,
    marginBottom: SIZES.large,
  },
  avatarBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.surfaceSubdued,
    borderWidth: 2,
    borderColor: '#BFDBFE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: SIZES.medium,
  },
  name: {
    fontSize: 22,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: 6,
  },
  gradePill: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: SIZES.medium,
    paddingVertical: 4,
    borderRadius: SIZES.pillRadius,
  },
  gradeText: {
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.primary,
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
    marginBottom: SIZES.xlarge,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SIZES.medium,
    minHeight: SIZES.minTouchTarget,
  },
  menuIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceSubdued,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SIZES.medium,
  },
  menuTextContainer: {
    flex: 1,
  },
  menuLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 2,
  },
  menuSublabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginLeft: 56,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: SIZES.minTouchTarget,
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: SIZES.buttonRadius,
    paddingHorizontal: SIZES.large,
  },
  logoutText: {
    marginLeft: SIZES.small,
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.error,
  },
});
