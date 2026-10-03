import React, { useContext, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { recognitionDraftStore, logFlowDomain, FlowDomain } from '../../features/recognition/state/recognitionDraftStore';
import { getAppBranding } from '../../config/appConfig';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HomeDashboard } from '../../components/home/HomeDashboard';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
export default function HomeScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    const userName = auth?.user?.name || 'em';
    const [showTipsModal, setShowTipsModal] = useState(false);
    const [showPrivacyInfoModal, setShowPrivacyInfoModal] = useState(false);
    const [showCurriculumModal, setShowCurriculumModal] = useState(false);
    const [selectedGrade, setSelectedGrade] = useState<1 | 2 | 3 | 4 | 5>(3);
    const [expandedProblemId, setExpandedProblemId] = useState<string | null>(null);
    const branding = getAppBranding();
    const insets = useSafeAreaInsets();
    const navigateToCamera = (mode: FlowDomain = 'MATH_TUTOR') => {
        recognitionDraftStore.clearDraft();
        logFlowDomain('ACQUIRE', mode);
        router.push({ pathname: '/camera' as any, params: { mode } });
    };
    return (<ScrollView style={styles.container} contentContainerStyle={[styles.content, { paddingTop: insets.top + 8 }]} showsVerticalScrollIndicator={false}>
      <HomeDashboard
        userName={userName}
        userKey={auth?.user?.id || auth?.user?.userId || auth?.user?.email}
        onAcquire={() => navigateToCamera('MATH_TUTOR')}
        onArithmetic={() => navigateToCamera('MATH_TUTOR')}
        onPractice={(grade) => {
            if (grade) setSelectedGrade(grade);
            setShowCurriculumModal(true);
        }}
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

      {/* Modal: Primary Math Curriculum Library */}
      <Modal visible={showCurriculumModal} transparent animationType="slide" onRequestClose={() => setShowCurriculumModal(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setShowCurriculumModal(false)}>
          <Pressable style={[styles.curriculumModalCard, SHADOWS.large]} onPress={() => { }}>
            <View style={styles.modalHeaderRow}>
              <View style={[styles.modalHeaderIconBadge, { backgroundColor: '#FEF3C7' }]}>
                <Ionicons name="school" size={22} color="#D97706"/>
              </View>
              <Text style={styles.modalTitle}>Kho đề toán SGK (Lớp 1 - 5)</Text>
              <TouchableOpacity onPress={() => setShowCurriculumModal(false)} style={styles.modalCloseBtn} accessibilityRole="button" accessibilityLabel="Đóng kho đề">
                <Ionicons name="close" size={20} color="#64748B"/>
              </TouchableOpacity>
            </View>

            {/* Grade Tabs: Lớp 1 to Lớp 5 */}
            <View style={styles.gradeTabRow}>
              {([1, 2, 3, 4, 5] as const).map((grade) => (<TouchableOpacity key={grade} style={[
                styles.gradeTabBtn,
                selectedGrade === grade && styles.gradeTabBtnActive
            ]} onPress={() => setSelectedGrade(grade)} accessibilityRole="button" accessibilityLabel={`Chọn Lớp ${grade}`} accessibilityState={{ selected: selectedGrade === grade }}>
                  <Text style={[
                styles.gradeTabBtnText,
                selectedGrade === grade && styles.gradeTabBtnTextActive
            ]}>
                    Lớp {grade}
                  </Text>
                </TouchableOpacity>))}
            </View>

            <ScrollView style={styles.problemListScroll} showsVerticalScrollIndicator={false} >
              {getProblemsByGrade(selectedGrade).map((p) => {
            const isExpanded = expandedProblemId === p.id;
            return (<View key={p.id} style={styles.curriculumProblemCard}>
                    <View style={styles.problemTagRow}>
                      <View style={styles.bookTag}>
                        <Text style={styles.bookTagText}>{p.bookSeries}</Text>
                      </View>
                      <View style={styles.difficultyTag}>
                        <Text style={styles.difficultyTagText}>{p.difficulty}</Text>
                      </View>
                    </View>

                    <Text style={styles.problemTopicText}>{p.topic}</Text>
                    <Text style={styles.problemTitleText}>{p.title}</Text>
                    <Text style={styles.problemBodyText}>{p.problemText}</Text>

                    {/* Direction only; the worked answer remains in curriculum data. */}
                    <TouchableOpacity style={styles.guidanceToggleBtn} onPress={() => setExpandedProblemId(isExpanded ? null : p.id)} accessibilityRole="button" accessibilityState={{ expanded: isExpanded }}>
                      <Ionicons name={isExpanded ? 'chevron-up' : 'bulb-outline'} size={16} color="#2563EB"/>
                      <Text style={styles.guidanceToggleText}>
                        {isExpanded ? 'Ẩn gợi ý cách giải' : 'Xem gợi ý cách giải'}
                      </Text>
                    </TouchableOpacity>

                    {isExpanded && (<View style={styles.guidanceContentBox}>
                        <Text style={styles.guidanceIntro}>{p.guidance}</Text>
                      </View>)}

                    {/* Action: Snap photo of written solution */}
                    <TouchableOpacity style={styles.solveNowBtn} onPress={() => {
                    setShowCurriculumModal(false);
                    router.push({ pathname: '/learning/math-guide' as any, params: { problemText: p.problemText } });
                }} activeOpacity={0.88} accessibilityRole="button" accessibilityLabel={`Học từng bước: ${p.title}`}>
                      <Ionicons name="bulb-outline" size={18} color="#FFFFFF" accessible={false}/>
                      <Text style={styles.solveNowBtnText}>Cùng em tìm cách giải</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.solveNowBtn} onPress={() => {
                    setShowCurriculumModal(false);
                    navigateToCamera('MATH_TUTOR');
                }} activeOpacity={0.88} accessibilityRole="button" accessibilityLabel="Chụp bài giải của em">
                      <Ionicons name="camera" size={16} color="#FFFFFF"/>
                      <Text style={styles.solveNowBtnText}>Chụp bài làm của em để chấm</Text>
                    </TouchableOpacity>
                  </View>);
        })}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </ScrollView>);
}
const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: COLORS.background },
    content: { paddingHorizontal: 20, paddingBottom: 112, maxWidth: 620, width: '100%', alignSelf: 'center' },
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
    curriculumModalCard: {
        width: '92%',
        maxWidth: 520,
        maxHeight: '82%',
        backgroundColor: '#FFFFFF',
        borderRadius: 24,
        padding: 20,
    },
    gradeTabRow: {
        flexDirection: 'row',
        backgroundColor: '#F1F5F9',
        borderRadius: 12,
        padding: 4,
        marginBottom: 14,
        gap: 4,
    },
    gradeTabBtn: {
        minHeight: 48, justifyContent: 'center',
        flex: 1,
        paddingVertical: 8,
        alignItems: 'center',
        borderRadius: 8,
    },
    gradeTabBtnActive: {
        backgroundColor: '#FFFFFF',
        ...SHADOWS.small,
    },
    gradeTabBtnText: {
        fontSize: 13,
        fontFamily: FONTS.semiBold,
        color: COLORS.textSecondary,
    },
    gradeTabBtnTextActive: {
        fontFamily: FONTS.extraBold,
        color: '#D97706',
    },
    problemListScroll: {
        maxHeight: 460,
    },
    curriculumProblemCard: {
        backgroundColor: '#F8FAFC',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: '#E2E8F0',
    },
    problemTagRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 6,
    },
    bookTag: {
        backgroundColor: '#EFF6FF',
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
    },
    bookTagText: {
        fontSize: 11,
        fontFamily: FONTS.bold,
        color: COLORS.primaryDark,
    },
    difficultyTag: {
        backgroundColor: '#FEF3C7',
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 6,
    },
    difficultyTagText: {
        fontSize: 11,
        fontFamily: FONTS.bold,
        color: '#D97706',
    },
    problemTopicText: {
        fontSize: 11,
        color: COLORS.textSecondary,
        marginBottom: 2,
        fontFamily: FONTS.semiBold,
    },
    problemTitleText: {
        fontSize: 14,
        fontFamily: FONTS.extraBold,
        color: COLORS.textPrimary,
        marginBottom: 6,
    },
    problemBodyText: {
        fontFamily: FONTS.regular,
        fontSize: 13,
        lineHeight: 19,
        color: '#334155',
        marginBottom: 10,
    },
    guidanceToggleBtn: {
        minHeight: 48,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 6,
        marginBottom: 8,
        alignSelf: 'flex-start',
    },
    guidanceToggleText: {
        fontSize: 12,
        fontFamily: FONTS.bold,
        color: COLORS.primaryDark,
    },
    guidanceContentBox: {
        backgroundColor: '#EFF6FF',
        borderRadius: 10,
        padding: 12,
        marginBottom: 12,
        borderLeftWidth: 3,
        borderLeftColor: '#2563EB',
    },
    guidanceIntro: {
        fontFamily: FONTS.regular,
        fontSize: 12,
        lineHeight: 17,
        color: '#1E40AF',
        marginBottom: 6,
    },
    solveNowBtn: {
        minHeight: 48,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        backgroundColor: '#D97706',
        borderRadius: 12,
        paddingVertical: 10,
        paddingHorizontal: 16,
        marginTop: 4,
    },
    solveNowBtnText: {
        color: '#FFFFFF',
        fontSize: 13,
        fontFamily: FONTS.bold,
    },
});
