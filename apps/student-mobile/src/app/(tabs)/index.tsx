import React, { useContext, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal, Pressable, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS, SHADOWS, IS_STUDENT_WEB, MATHVISION_COLORS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { recognitionDraftStore, logFlowDomain, FlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { getAppBranding } from '../../config/appConfig';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HomeDashboard } from '../../components/home/HomeDashboard';
import { isCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
export default function HomeScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    const userName = auth?.user?.displayName || auth?.user?.name || 'em';
    const [showTipsModal, setShowTipsModal] = useState(false);
    const [showPrivacyInfoModal, setShowPrivacyInfoModal] = useState(false);
    const [heroVisible, setHeroVisible] = useState(true);
    const branding = getAppBranding();
    const insets = useSafeAreaInsets();
    const { width } = useWindowDimensions();
    const navigateToCamera = (mode: FlowDomain = 'MATH_TUTOR') => {
        recognitionDraftStore.clearDraft();
        logFlowDomain('ACQUIRE', mode);
        router.push({ pathname: '/camera' as any, params: { mode } });
    };
    return (<ScrollView style={[styles.container, isCompactStudentWeb(width) && styles.compactWebBackground]} onScroll={event => setHeroVisible(event.nativeEvent.contentOffset.y < 340)} scrollEventThrottle={100} contentContainerStyle={[styles.content, { flexGrow: 1, paddingTop: insets.top + 12, paddingBottom: 108 + insets.bottom }, width >= 768 && { maxWidth: width >= 1200 ? 1360 : 1040, paddingHorizontal: width >= 1200 ? 30 : 24, paddingTop: insets.top + 20, paddingBottom: 28 }, IS_STUDENT_WEB && width >= 768 && { maxWidth: '100%', paddingHorizontal: 24 }]} showsVerticalScrollIndicator={false}>
      <HomeDashboard
        userName={userName}
        heroVisible={heroVisible}
        userKey={auth?.user?.id || auth?.user?.userId || auth?.user?.email}
        onAcquire={() => navigateToCamera('MATH_TUTOR')}
        onArithmetic={() => navigateToCamera('MATH_TUTOR')}
        onPractice={() => router.push('/(tabs)/lessons')}
        onTips={() => setShowTipsModal(true)}
        onPrivacy={() => setShowPrivacyInfoModal(true)}
      />


      {/* Modal: Helpful Photo Tips */}
      <Modal visible={showTipsModal} transparent animationType="fade" onRequestClose={() => setShowTipsModal(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setShowTipsModal(false)}>
          <Pressable style={[styles.modalCard, SHADOWS.large]} onPress={() => { }}>
            <View style={styles.modalHeaderRow}>
              <View style={[styles.modalHeaderIconBadge, { backgroundColor: '#FEF3C7' }]}>
                <Ionicons name="bulb" size={22} color="#D97706"/>
              </View>
              <Text style={styles.modalTitle}>Mẹo chụp ảnh rõ nét</Text>
              <TouchableOpacity onPress={() => setShowTipsModal(false)} style={styles.modalCloseBtn} accessibilityRole="button" accessibilityLabel="Đóng mẹo chụp ảnh">
                <Ionicons name="close" size={20} color="#64748B"/>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <View style={styles.tipRow}>
              <View style={[styles.tipBullet, { backgroundColor: '#ECFDF5' }]}>
                <Ionicons name="sunny" size={16} color="#059669"/>
              </View>
              <View style={styles.tipTextCol}>
                <Text style={styles.tipTitle}>Đủ ánh sáng</Text>
                <Text style={styles.tipDesc}>
                  Chụp ở nơi có ánh sáng đều, tránh để bóng tay hoặc điện thoại đè lên trang vở.
                </Text>
              </View>
            </View>

            <View style={styles.tipRow}>
              <View style={[styles.tipBullet, { backgroundColor: '#EFF6FF' }]}>
                <Ionicons name="phone-portrait" size={16} color="#2563EB"/>
              </View>
              <View style={styles.tipTextCol}>
                <Text style={styles.tipTitle}>Chụp thẳng góc</Text>
                <Text style={styles.tipDesc}>
                  Giữ điện thoại song song với mặt phẳng vở, không chụp từ góc quá nghiêng.
                </Text>
              </View>
            </View>

            <View style={styles.tipRow}>
              <View style={[styles.tipBullet, { backgroundColor: '#FAF5FF' }]}>
                <Ionicons name="scan" size={16} color="#7C3AED"/>
              </View>
              <View style={styles.tipTextCol}>
                <Text style={styles.tipTitle}>Căn trọn khung hình</Text>
                <Text style={styles.tipDesc}>
                  Để bài làm nằm gọn trong khung hình, không để mất chữ ở mép trên hoặc mép dưới.
                </Text>
              </View>
            </View>

            </ScrollView>
            <TouchableOpacity style={styles.modalPrimaryBtn} onPress={() => setShowTipsModal(false)} accessibilityRole="button">
              <Text style={styles.modalPrimaryBtnText}>Đã hiểu rồi</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Modal: Student Privacy Information */}
      <Modal visible={showPrivacyInfoModal} transparent animationType="fade" onRequestClose={() => setShowPrivacyInfoModal(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setShowPrivacyInfoModal(false)}>
          <Pressable style={[styles.modalCard, SHADOWS.large]} onPress={() => { }}>
            <View style={styles.modalHeaderRow}>
              <View style={[styles.modalHeaderIconBadge, { backgroundColor: '#DCFCE7' }]}>
                <Ionicons name="shield-checkmark" size={22} color="#16A34A"/>
              </View>
              <Text style={styles.modalTitle}>Bảo vệ thông tin cá nhân</Text>
              <TouchableOpacity onPress={() => setShowPrivacyInfoModal(false)} style={styles.modalCloseBtn} accessibilityRole="button" accessibilityLabel="Đóng thông tin bảo mật">
                <Ionicons name="close" size={20} color="#64748B"/>
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <Text style={styles.privacyModalIntro}>
              {branding.name} cam kết giữ an toàn tối đa cho học sinh:
            </Text>

            <View style={styles.tipRow}>
              <View style={[styles.tipBullet, { backgroundColor: '#F0FDF4' }]}>
                <Ionicons name="eye-off" size={16} color="#16A34A"/>
              </View>
              <View style={styles.tipTextCol}>
                <Text style={styles.tipTitle}>Che phần thông tin nhạy cảm</Text>
                <Text style={styles.tipDesc}>
                  Trước khi nhận diện, em có thể dùng ngón tay kéo thả các ô màu đen để che tên, trường lớp hoặc số điện thoại.
                </Text>
              </View>
            </View>

            <View style={styles.tipRow}>
              <View style={[styles.tipBullet, { backgroundColor: '#EFF6FF' }]}>
                <Ionicons name="lock-closed" size={16} color="#2563EB"/>
              </View>
              <View style={styles.tipTextCol}>
                <Text style={styles.tipTitle}>Bảo mật trên thiết bị</Text>
                <Text style={styles.tipDesc}>
                  Vùng che được xử lý trực tiếp trước khi gửi ảnh, đảm bảo không ai thấy được thông tin bị ẩn.
                </Text>
              </View>
            </View>

            </ScrollView>
            <TouchableOpacity style={styles.modalPrimaryBtn} onPress={() => setShowPrivacyInfoModal(false)} accessibilityRole="button">
              <Text style={styles.modalPrimaryBtnText}>Đã hiểu rồi</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>


    </ScrollView>);
}
const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: COLORS.background },
    compactWebBackground: { backgroundColor: MATHVISION_COLORS.background },
    content: { paddingHorizontal: 20, paddingBottom: 112, maxWidth: 1440, width: '100%', alignSelf: 'center' },
    modalBody: { flexGrow: 0, flexShrink: 1 },
    /* Modals */
    modalBackdrop: {
        flex: 1,
        backgroundColor: 'rgba(15, 23, 42, 0.55)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    modalCard: {
        backgroundColor: '#FFFFFF',
        borderRadius: 24,
        padding: 22,
        width: '100%',
        maxWidth: 480,
        maxHeight: '85%',
    },
    modalHeaderRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 18,
    },
    modalHeaderIconBadge: {
        width: 40,
        height: 40,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    modalTitle: {
        flex: 1,
        fontSize: 18,
        fontFamily: FONTS.extraBold,
        color: COLORS.textPrimary,
    },
    modalCloseBtn: {
        minWidth: 48, minHeight: 48, alignItems: 'center', justifyContent: 'center',
    },
    tipRow: {
        flexDirection: 'row',
        alignItems: 'flex-start',
        gap: 12,
        marginBottom: 16,
    },
    tipBullet: {
        width: 32,
        height: 32,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: 2,
    },
    tipTextCol: {
        flex: 1,
    },
    tipTitle: {
        fontSize: 14,
        fontFamily: FONTS.bold,
        color: COLORS.textPrimary,
        marginBottom: 2,
    },
    tipDesc: {
        fontFamily: FONTS.regular,
        fontSize: 13,
        color: COLORS.textSecondary,
        lineHeight: 18,
    },
    privacyModalIntro: {
        fontFamily: FONTS.regular,
        fontSize: 14,
        color: '#334155',
        lineHeight: 20,
        marginBottom: 14,
    },
    modalPrimaryBtn: {
        minHeight: 48,
        backgroundColor: COLORS.primary,
        borderRadius: 16,
        paddingVertical: 14,
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: 10,
    },
    modalPrimaryBtnText: {
        fontSize: 15,
        fontFamily: FONTS.bold,
        color: '#FFFFFF',
    },
});
