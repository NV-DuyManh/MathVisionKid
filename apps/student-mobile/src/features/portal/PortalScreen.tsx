import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  Image,
  useWindowDimensions,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { FONTS, COLORS } from '../../constants/theme';

interface DemoCalculation {
  grade: number;
  className: string;
  studentName: string;
  row1: string[];
  operator: string;
  row2: string[];
  resultRow: string[];
  errorCol: number;
  activeCol: number;
  speechText: string;
  replyResponse: string;
  answerText: string;
}

const DEMO_CALCULATIONS: Record<number, DemoCalculation> = {
  1: {
    grade: 1,
    className: 'Lớp 1B',
    studentName: 'Trần M***',
    row1: [' ', '7'],
    operator: '+',
    row2: [' ', '5'],
    resultRow: ['1', '1'],
    errorCol: 1,
    activeCol: 1,
    speechText: 'Chào con! 7 + 5 bằng bao nhiêu nhỉ? Con hãy đếm thêm từ 7 xem nào!',
    replyResponse: 'Chính xác rồi! 7 + 5 = 12 mới đúng con nhé. Giỏi lắm!',
    answerText: 'Con trả lời: 7 + 5 = 12',
  },
  2: {
    grade: 2,
    className: 'Lớp 2A',
    studentName: 'Lê H***',
    row1: ['4', '8'],
    operator: '+',
    row2: ['3', '6'],
    resultRow: ['7', '4'],
    errorCol: 0,
    activeCol: 0,
    speechText: 'Con cộng 8 + 6 = 14 viết 4 nhớ 1 rồi. Vậy 4 + 3 thêm 1 nhớ là mấy nhỉ?',
    replyResponse: 'Đúng rồi! 4 + 3 = 7, thêm 1 nhớ là 8. Kết quả đúng là 84 con nhé!',
    answerText: 'Con trả lời: 4 + 3 + 1 = 8',
  },
  3: {
    grade: 3,
    className: 'Lớp 3A',
    studentName: 'Nguyễn B***',
    row1: ['2', '4', '5'],
    operator: '+',
    row2: ['1', '7', '8'],
    resultRow: ['4', '1', '3'],
    errorCol: 1,
    activeCol: 1,
    speechText:
      'Chào con! Cô thấy con viết 245 + 178 = 413. Mình cùng kiểm tra từng cột nhé. Bắt đầu từ cột đơn vị: 5 + 8 bằng mấy?',
    replyResponse:
      'Đúng rồi! 5 + 8 = 13, viết 3 nhớ 1 sang cột chục. 4 + 7 = 11, thêm 1 nhớ là 12, viết 2 nhớ 1. Kết quả là 423 con nhé!',
    answerText: 'Con trả lời: 5 + 8 = 13',
  },
  4: {
    grade: 4,
    className: 'Lớp 4C',
    studentName: 'Phạm Q***',
    row1: ['1', '4', '2', '5'],
    operator: '+',
    row2: ['2', '8', '3', '7'],
    resultRow: ['4', '2', '5', '2'],
    errorCol: 2,
    activeCol: 2,
    speechText: 'Ở cột chục: 2 + 3 thêm 1 nhớ từ hàng đơn vị thì phải bằng mấy con nhỉ?',
    replyResponse: 'Tuyệt vời! 2 + 3 = 5, thêm 1 nhớ là 6. Kết quả chính xác là 4262!',
    answerText: 'Con trả lời: 2 + 3 + 1 = 6',
  },
  5: {
    grade: 5,
    className: 'Lớp 5B',
    studentName: 'Hoàng K***',
    row1: ['3', '4', ',', '8'],
    operator: '+',
    row2: ['1', '9', ',', '5'],
    resultRow: ['5', '3', ',', '3'],
    errorCol: 1,
    activeCol: 1,
    speechText:
      'Phép cộng số thập phân: 8 + 5 = 13 viết 3 nhớ 1. Đến cột hàng đơn vị: 4 + 9 thêm 1 nhớ là mấy?',
    replyResponse:
      'Chuẩn luôn! 4 + 9 = 13, thêm 1 nhớ là 14 viết 4 nhớ 1. Kết quả đúng là 54,3!',
    answerText: 'Con trả lời: 4 + 9 + 1 = 14',
  },
};

const GRADE_COLORS: Record<number, { bg: string; text: string }> = {
  1: { bg: '#FEE2E2', text: '#991B1B' },
  2: { bg: '#FEF3C7', text: '#92400E' },
  3: { bg: '#DCFCE7', text: '#166534' },
  4: { bg: '#DBEAFE', text: '#1E40AF' },
  5: { bg: '#EDE9FE', text: '#5B21B6' },
};

export default function PortalScreen() {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const [selectedGrade, setSelectedGrade] = useState<number>(3);
  const [answeredSpeech, setAnsweredSpeech] = useState<boolean>(false);
  const scrollRef = useRef<any>(null);
  const methodLayoutY = useRef<number>(0);

  const currentDemo = DEMO_CALCULATIONS[selectedGrade] || DEMO_CALCULATIONS[3];

  const handleSelectGrade = (grade: number) => {
    setSelectedGrade(grade);
    setAnsweredSpeech(false);
  };

  const handleGoToLogin = () => {
    router.push('/login' as any);
  };

  const handleScrollToMethod = () => {
    if (scrollRef.current && methodLayoutY.current > 0) {
      scrollRef.current.scrollTo({ y: methodLayoutY.current - 20, animated: true });
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      {/* Top Header / App Bar */}
      <View style={styles.header}>
        <View style={styles.headerBrand}>
          <Image
            source={require('../../../assets/illustrations/robot-mascot.png')}
            style={styles.headerMascot}
            resizeMode="contain"
          />
          <View style={styles.headerTitleWrap}>
            <Text style={styles.headerTitle}>
              <Text style={{ color: '#2563EB', fontStyle: 'italic' }}>∑</Text> MathVisionKids
            </Text>
            <View style={styles.headerBadge}>
              <Text style={styles.headerBadgeText}>Tiểu học</Text>
            </View>
          </View>
        </View>

        <Pressable
          style={({ pressed }) => [styles.headerLoginBtn, pressed && styles.btnPressed]}
          onPress={handleGoToLogin}
          accessibilityLabel="Đăng nhập"
          accessibilityRole="button"
        >
          <Text style={styles.headerLoginText}>Đăng nhập</Text>
        </Pressable>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* ========================================================================= */}
        {/* 1. HERO SECTION                                                          */}
        {/* ========================================================================= */}
        <View style={styles.heroSection}>
          {/* New Feature Pill */}
          <View style={styles.heroPill}>
            <View style={styles.heroPillBadge}>
              <Text style={styles.heroPillBadgeText}>Mới</Text>
            </View>
            <Text style={styles.heroPillText}>Gia sư gợi mở cho học sinh lớp 1 đến lớp 5</Text>
          </View>

          {/* Main Headline */}
          <View style={styles.heroHeadlineContainer}>
            <Text style={styles.heroHeadline}>Mở vở ô ly, học toán </Text>
            <View style={styles.heroHighlightBadge}>
              <Text style={styles.heroHighlightText}>từng bước</Text>
            </View>
          </View>

          {/* Subtitle */}
          <Text style={styles.heroSubtitle}>
            Chụp bài toán viết tay và cùng robot MathVisionKids tìm ra lời giải qua từng câu hỏi gợi mở. Bé tự nghĩ, tự làm, tự tin hơn mỗi ngày.
          </Text>

          {/* CTA Buttons */}
          <View style={styles.heroCtaRow}>
            <Pressable
              style={({ pressed }) => [styles.heroPrimaryBtn, pressed && styles.btnPressed]}
              onPress={handleGoToLogin}
              accessibilityLabel="Đăng nhập để bắt đầu"
              accessibilityRole="button"
            >
              <Text style={styles.heroPrimaryBtnText}>Đăng nhập để bắt đầu</Text>
            </Pressable>

            <Pressable
              style={({ pressed }) => [styles.heroSecondaryBtn, pressed && styles.btnPressed]}
              onPress={handleScrollToMethod}
              accessibilityLabel="Xem cách hoạt động"
              accessibilityRole="button"
            >
              <Text style={styles.heroSecondaryBtnText}>Xem cách hoạt động</Text>
            </Pressable>
          </View>

          {/* 4 Feature Tags */}
          <View style={styles.featureTagsWrap}>
            <View style={styles.featureTag}>
              <Text style={styles.featureTagIcon}>📷</Text>
              <Text style={styles.featureTagText}>Nhận diện chữ số ô ly Việt Nam</Text>
            </View>
            <View style={styles.featureTag}>
              <Text style={styles.featureTagIcon}>🛡️</Text>
              <Text style={styles.featureTagText}>Bảo vệ riêng tư học sinh</Text>
            </View>
            <View style={styles.featureTag}>
              <Text style={styles.featureTagIcon}>💡</Text>
              <Text style={styles.featureTagText}>Gợi mở, không làm hộ</Text>
            </View>
            <View style={styles.featureTag}>
              <Text style={styles.featureTagIcon}>📚</Text>
              <Text style={styles.featureTagText}>Chuẩn chương trình Toán 1–5</Text>
            </View>
          </View>

          {/* Interactive Math Notebook Card (tilted -3deg on mobile exactly like web) */}
          <View style={styles.notebookContainerWrapper}>
            {/* Floating Badges */}
            <View style={[styles.floatingBadge, styles.floatingBadgePlus]}>
              <Text style={styles.floatingBadgeText}>+</Text>
            </View>
            <View style={[styles.floatingBadge, styles.floatingBadgeMinus]}>
              <Text style={styles.floatingBadgeText}>−</Text>
            </View>
            <View style={[styles.floatingBadge, styles.floatingBadgeEqual]}>
              <Text style={styles.floatingBadgeEqualText}>=</Text>
            </View>

            {/* Notebook Card */}
            <View style={styles.notebookCard}>
              {/* Card Top Window Bar */}
              <LinearGradient
                colors={['#6366F1', '#3B82F6', '#38BDF8']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.notebookTopBar}
              >
                <View style={styles.notebookTopBarLeft}>
                  <View style={styles.dotGroup}>
                    <View style={styles.topDot} />
                    <View style={styles.topDot} />
                    <View style={styles.topDot} />
                  </View>
                  <Text style={styles.notebookClassText}>
                    Bài của bé · {currentDemo.className}
                  </Text>
                </View>
                <View style={styles.privacyChip}>
                  <Text style={styles.privacyChipText}>Đã che thông tin</Text>
                </View>
              </LinearGradient>

              {/* Notebook Paper Body */}
              <View style={styles.notebookPaper}>
                {/* Red Margin Line */}
                <View style={styles.redMarginLine} />

                {/* Student Name */}
                <Text style={styles.studentNameText}>
                  Họ và tên: {currentDemo.studentName}
                </Text>

                {/* Math Calculation Table */}
                <View style={styles.calculationArea}>
                  {/* Row 1 */}
                  <View style={styles.mathRow}>
                    {currentDemo.row1.map((char, idx) => {
                      const isActive = idx === currentDemo.activeCol;
                      return (
                        <View key={idx} style={[styles.mathCell, isActive && styles.mathCellActive]}>
                          <Text style={styles.mathDigit}>{char}</Text>
                        </View>
                      );
                    })}
                  </View>

                  {/* Row 2 with Operator */}
                  <View style={styles.mathRow}>
                    <Text style={styles.mathOperator}>{currentDemo.operator}</Text>
                    {currentDemo.row2.map((char, idx) => {
                      const isActive = idx === currentDemo.activeCol;
                      return (
                        <View key={idx} style={[styles.mathCell, isActive && styles.mathCellActive]}>
                          <Text style={styles.mathDigit}>{char}</Text>
                        </View>
                      );
                    })}
                  </View>

                  {/* Horizontal Divider Line */}
                  <View style={styles.mathDivider} />

                  {/* Result Row with Error Capsule */}
                  <View style={styles.mathRow}>
                    {currentDemo.resultRow.map((char, idx) => {
                      const isError = idx === currentDemo.errorCol;
                      return (
                        <View key={idx} style={[styles.mathCell, isError && styles.mathCellError]}>
                          <Text style={[styles.mathDigit, isError && styles.mathDigitError]}>
                            {char}
                          </Text>
                        </View>
                      );
                    })}
                  </View>
                </View>

                {/* Robot Speech Bubble */}
                <View style={styles.robotBubble}>
                  <View style={styles.robotBubbleRow}>
                    <Image
                      source={require('../../../assets/illustrations/robot-mascot.png')}
                      style={styles.robotBubbleAvatar}
                      resizeMode="contain"
                    />
                    <Text style={styles.robotBubbleText}>
                      {answeredSpeech ? currentDemo.replyResponse : currentDemo.speechText}
                    </Text>
                  </View>
                </View>

                {/* Child Answer Toggle Button */}
                <View style={styles.replyBtnWrap}>
                  <Pressable
                    style={({ pressed }) => [
                      styles.replyBtn,
                      answeredSpeech ? styles.replyBtnAnswered : styles.replyBtnNormal,
                      pressed && styles.btnPressed,
                    ]}
                    onPress={() => setAnsweredSpeech((prev) => !prev)}
                    accessibilityLabel={answeredSpeech ? 'Đã kiểm tra lại' : currentDemo.answerText}
                    accessibilityRole="button"
                  >
                    <Text
                      style={[
                        styles.replyBtnText,
                        answeredSpeech ? styles.replyBtnTextAnswered : styles.replyBtnTextNormal,
                      ]}
                    >
                      {answeredSpeech ? '✓ Đã kiểm tra lại' : currentDemo.answerText}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>

          {/* 5 Grade Selector Buttons */}
          <View style={styles.gradeButtonsRow}>
            {[1, 2, 3, 4, 5].map((grade) => {
              const isSelected = selectedGrade === grade;
              const colorInfo = GRADE_COLORS[grade] || GRADE_COLORS[3];
              return (
                <Pressable
                  key={grade}
                  style={({ pressed }) => [
                    styles.gradeBtn,
                    { backgroundColor: colorInfo.bg },
                    isSelected && styles.gradeBtnSelected,
                    pressed && styles.btnPressed,
                  ]}
                  onPress={() => handleSelectGrade(grade)}
                  accessibilityLabel={`Lớp ${grade}`}
                  accessibilityRole="button"
                >
                  <Text style={[styles.gradeBtnText, { color: colorInfo.text }]}>Lớp {grade}</Text>
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* ========================================================================= */}
        {/* 2. PHƯƠNG PHÁP SOCRATIC                                                   */}
        {/* ========================================================================= */}
        <View
          style={styles.sectionWhite}
          onLayout={(e) => {
            methodLayoutY.current = e.nativeEvent.layout.y;
          }}
        >
          <View style={styles.sectionHeader}>
            <View style={styles.sectionBadge}>
              <Text style={styles.sectionBadgeText}>Phương pháp Socratic</Text>
            </View>
            <Text style={styles.sectionTitle}>
              Bé hiểu bài thật sâu, thay vì chép bài thụ động
            </Text>
            <Text style={styles.sectionSubtitle}>
              Khác với ứng dụng giải hộ chỉ đưa ra đáp số, MathVisionKids là người gia sư kiên nhẫn: chỉ ra đúng điểm nhầm lẫn và gợi mở để bé tự suy luận.
            </Text>
          </View>

          {/* 3 Step Cards */}
          <View style={styles.stepCardsCol}>
            {/* Step Card 1 */}
            <View style={[styles.stepCard, { backgroundColor: '#FFE4E6' }]}>
              <Text style={styles.stepWatermark}>1</Text>
              <View style={[styles.stepIconWrap, { backgroundColor: 'rgba(244, 63, 94, 0.2)' }]}>
                <Text style={styles.stepIcon}>📸</Text>
              </View>
              <Text style={styles.stepTitle}>Chụp trang vở ô ly</Text>
              <Text style={styles.stepDesc}>
                Bé đặt điện thoại ngay ngắn, chụp trang vở bài làm mà không cần phụ huynh thao tác phức tạp.
              </Text>
              <View style={styles.stepChip}>
                <Text style={styles.stepChipText}>Che thông tin riêng tư</Text>
              </View>
            </View>

            {/* Step Card 2 */}
            <View style={[styles.stepCard, { backgroundColor: '#D1FAE5' }]}>
              <Text style={styles.stepWatermark}>2</Text>
              <View style={[styles.stepIconWrap, { backgroundColor: 'rgba(16, 185, 129, 0.25)' }]}>
                <Text style={styles.stepIcon}>✍️</Text>
              </View>
              <Text style={styles.stepTitle}>Bóc tách nét viết tay</Text>
              <Text style={styles.stepDesc}>
                AI chuyên biệt cho chữ số tiểu học Việt Nam nhận diện từng chữ số, đặt đúng tính thẳng hàng.
              </Text>
              <View style={styles.stepChip}>
                <Text style={styles.stepChipText}>Chuẩn ô ly Việt Nam</Text>
              </View>
            </View>

            {/* Step Card 3 */}
            <View style={[styles.stepCard, { backgroundColor: '#DBEAFE' }]}>
              <Text style={styles.stepWatermark}>3</Text>
              <View style={[styles.stepIconWrap, { backgroundColor: 'rgba(59, 130, 246, 0.25)' }]}>
                <Text style={styles.stepIcon}>💡</Text>
              </View>
              <Text style={styles.stepTitle}>Gợi mở bằng câu hỏi</Text>
              <Text style={styles.stepDesc}>
                Phát hiện ngay vị trí nhầm hoặc quên nhớ, đặt câu hỏi gợi mở thay vì giải hộ.
              </Text>
              <View style={styles.stepChip}>
                <Text style={styles.stepChipText}>Tuyệt đối không giải hộ</Text>
              </View>
            </View>
          </View>

          {/* Full-width Blue Gradient Banner: Bé hiểu sâu, tự tin */}
          <LinearGradient
            colors={['#7040EC', '#46ACFF']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.blueBanner}
          >
            <View style={styles.blueBannerIconWrap}>
              <Text style={styles.blueBannerIcon}>🌟</Text>
            </View>
            <View style={styles.blueBannerContent}>
              <Text style={styles.blueBannerTitle}>Bé hiểu sâu, tự tin</Text>
              <Text style={styles.blueBannerDesc}>
                Bé tự sửa được bài, ghi nhớ phương pháp tư duy bền vững và hào hứng tích lũy sao học tập.
              </Text>
            </View>
          </LinearGradient>

          {/* Yellow Robot Tip Banner */}
          <View style={styles.tipBanner}>
            <Text style={styles.tipBannerIcon}>🔦</Text>
            <Text style={styles.tipBannerText}>
              Mẹo của robot: giữ máy song song với trang vở, trong phòng có đủ ánh sáng để chữ hiện rõ nét nhất nhé!
            </Text>
          </View>
        </View>

        {/* ========================================================================= */}
        {/* 3. SO SÁNH TRIẾT LÝ TIẾP CẬN                                              */}
        {/* ========================================================================= */}
        <View style={styles.sectionLightPurple}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionBadge}>
              <Text style={styles.sectionBadgeText}>So sánh triết lý tiếp cận</Text>
            </View>
            <Text style={styles.sectionTitle}>
              Tại sao gợi mở tư duy tốt hơn đưa sẵn đáp số?
            </Text>
          </View>

          {/* 2 Comparison Cards */}
          <View style={styles.compareCol}>
            {/* Card 1: Giải bài hộ thương mại */}
            <View style={[styles.compareCard, styles.compareCardCommercial]}>
              <View style={styles.compareCardHeader}>
                <Text style={styles.compareCardTitle}>Giải bài hộ thương mại</Text>
                <View style={styles.compareBadgeGray}>
                  <Text style={styles.compareBadgeGrayText}>Ăn xổi, thụ động</Text>
                </View>
              </View>

              <View style={styles.redHighlightBox}>
                <Text style={styles.redHighlightNumber}>423</Text>
                <Text style={styles.redHighlightLabel}>chép vào vở</Text>
              </View>

              <View style={styles.compareList}>
                <View style={styles.compareItem}>
                  <Ionicons name="close-circle-outline" size={24} color="#EF4444" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Đưa ngay đáp án số cuối cùng, bé chỉ việc chép vào vở.
                  </Text>
                </View>
                <View style={styles.compareItem}>
                  <Ionicons name="close-circle-outline" size={24} color="#EF4444" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Bé không hiểu bản chất bước tính hay quy tắc cộng có nhớ.
                  </Text>
                </View>
                <View style={styles.compareItem}>
                  <Ionicons name="close-circle-outline" size={24} color="#EF4444" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Dần mất khả năng suy luận và tự giải quyết vấn đề khi gặp dạng bài mới.
                  </Text>
                </View>
              </View>
            </View>

            {/* Card 2: Đồng hành Socratic */}
            <View style={[styles.compareCard, styles.compareCardSocratic]}>
              <View style={styles.compareCardHeader}>
                <Text style={styles.compareCardTitle}>Đồng hành Socratic</Text>
                <View style={styles.compareBadgeGreen}>
                  <Text style={styles.compareBadgeGreenText}>Chuẩn sư phạm Việt Nam</Text>
                </View>
              </View>

              <View style={styles.yellowHighlightBox}>
                <Text style={styles.yellowHighlightText}>
                  “Số nhớ ở cột đơn vị đang ở đâu nhỉ?”
                </Text>
              </View>

              <View style={styles.compareList}>
                <View style={styles.compareItem}>
                  <Ionicons name="checkmark-circle-outline" size={24} color="#10B981" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Phân tích từng bước đặt tính ở ô ly, khoanh vùng chính xác điểm nhầm lẫn: cột đơn vị, cột chục, số nhớ.
                  </Text>
                </View>
                <View style={styles.compareItem}>
                  <Ionicons name="checkmark-circle-outline" size={24} color="#10B981" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Đặt câu hỏi gợi mở để bé tự nhẩm tính và tìm ra kết quả đúng.
                  </Text>
                </View>
                <View style={styles.compareItem}>
                  <Ionicons name="checkmark-circle-outline" size={24} color="#10B981" style={styles.compareItemIcon} />
                  <Text style={styles.compareItemText}>
                    Trẻ nhớ lâu và hào hứng tự học.
                  </Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* ========================================================================= */}
        {/* 4. TRÁCH NHIỆM VÀ ĐẠO ĐỨC                                                 */}
        {/* ========================================================================= */}
        <View style={styles.sectionWhite}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionBadge}>
              <Text style={styles.sectionBadgeText}>Trách nhiệm và đạo đức</Text>
            </View>
            <Text style={styles.sectionTitle}>
              Cam kết sư phạm và an toàn cho trẻ
            </Text>
            <Text style={styles.sectionSubtitle}>
              Chúng tôi xây dựng MathVisionKids với kim chỉ nam phục vụ giáo dục tiểu học Việt Nam chuẩn mực, nhân văn và an toàn.
            </Text>
          </View>

          {/* 3 Cards with Left-Tilted (-8deg) Squircles */}
          <View style={styles.stepCardsCol}>
            {/* Card 1: Không giải hộ bài tập */}
            <View style={styles.ethicsCard}>
              <View style={[styles.ethicsSquircle, styles.ethicsSquircleYellow]}>
                <Text style={styles.ethicsEmoji}>🧩</Text>
              </View>
              <Text style={styles.ethicsCardTitle}>Không giải hộ bài tập</Text>
              <Text style={styles.ethicsCardDesc}>
                Khác với các ứng dụng chụp ảnh giải bài ăn xổi, MathVisionKids hướng tới bồi dưỡng tư duy toán học độc lập. Trẻ được gợi mở từng bước để tự tìm ra kết quả đúng.
              </Text>
              <View style={styles.ethicsChip}>
                <Text style={styles.ethicsChipText}>Không đưa đáp án sẵn</Text>
              </View>
            </View>

            {/* Card 2: Thầy cô là người định đoạt */}
            <View style={styles.ethicsCard}>
              <View style={[styles.ethicsSquircle, styles.ethicsSquircleGreen]}>
                <Text style={styles.ethicsEmoji}>🧑‍🏫</Text>
              </View>
              <Text style={styles.ethicsCardTitle}>Thầy cô là người định đoạt</Text>
              <Text style={styles.ethicsCardDesc}>
                AI đóng vai trò người trợ giảng chấm sơ bộ. Mọi bài thi hoặc bài tập có độ tin cậy thấp đều được chuyển đến giáo viên để thẩm định và phê duyệt điểm số cuối cùng.
              </Text>
              <View style={styles.ethicsChip}>
                <Text style={styles.ethicsChipText}>Giáo viên phê duyệt 100%</Text>
              </View>
            </View>

            {/* Card 3: Bảo vệ dữ liệu học sinh */}
            <View style={styles.ethicsCard}>
              <View style={[styles.ethicsSquircle, styles.ethicsSquircleBlue]}>
                <Text style={styles.ethicsEmoji}>🛡️</Text>
              </View>
              <Text style={styles.ethicsCardTitle}>Bảo vệ dữ liệu học sinh</Text>
              <Text style={styles.ethicsCardDesc}>
                Thông tin định danh của bé (tên, trường, lớp) được che an toàn trước khi tiếp từ thiết bị. Không chứa quảng cáo, không cơ chế ép streak hay gamification gây nghiện.
              </Text>
              <View style={styles.ethicsChip}>
                <Text style={styles.ethicsChipText}>Xem lại vùng che trước khi gửi</Text>
              </View>
            </View>
          </View>
        </View>

        {/* ========================================================================= */}
        {/* 5. CALL TO ACTION SECTION                                                 */}
        {/* ========================================================================= */}
        <View style={styles.ctaSectionWrapper}>
          <LinearGradient
            colors={['#6366F1', '#3B82F6', '#4F46E5']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.ctaCard}
          >
            {/* Floating Badges inside CTA */}
            <View style={[styles.ctaFloatingBadge, styles.ctaBadgePlus]}>
              <Text style={styles.ctaBadgeText}>+</Text>
            </View>
            <View style={[styles.ctaFloatingBadge, styles.ctaBadgePercent]}>
              <Text style={styles.ctaBadgePercentText}>%</Text>
            </View>
            <View style={[styles.ctaFloatingBadge, styles.ctaBadgeMinus]}>
              <Text style={styles.ctaBadgeText}>−</Text>
            </View>

            <Text style={styles.ctaTitle}>
              Sẵn sàng đồng hành cùng bé chinh phục môn Toán?
            </Text>
            <Text style={styles.ctaSubtitle}>
              Đăng nhập bằng tài khoản Google hoặc Facebook của bạn.
            </Text>

            <View style={styles.ctaButtonsCol}>
              <Pressable
                style={({ pressed }) => [styles.ctaGoogleBtn, pressed && styles.btnPressed]}
                onPress={handleGoToLogin}
                accessibilityLabel="Tiếp tục với Google"
                accessibilityRole="button"
              >
                <Ionicons name="logo-google" size={22} color="#1E1B4B" style={{ marginRight: 10 }} />
                <Text style={styles.ctaGoogleBtnText}>Tiếp tục với Google</Text>
              </Pressable>

              <Pressable
                style={({ pressed }) => [styles.ctaFacebookBtn, pressed && styles.btnPressed]}
                onPress={handleGoToLogin}
                accessibilityLabel="Tiếp tục với Facebook"
                accessibilityRole="button"
              >
                <Ionicons name="logo-facebook" size={22} color="#FFFFFF" style={{ marginRight: 10 }} />
                <Text style={styles.ctaFacebookBtnText}>Tiếp tục với Facebook</Text>
              </Pressable>
            </View>
          </LinearGradient>
        </View>

        {/* ========================================================================= */}
        {/* 6. FOOTER                                                                 */}
        {/* ========================================================================= */}
        <View style={styles.footer}>
          <View style={styles.footerBrand}>
            <Image
              source={require('../../../assets/illustrations/robot-mascot.png')}
              style={styles.footerMascot}
              resizeMode="contain"
            />
            <Text style={styles.footerBrandTitle}>MathVisionKids</Text>
          </View>
          <Text style={styles.footerDesc}>
            Nền tảng học toán sơ học và gợi mở tư duy trên trang vở ô ly, thiết kế chuyên biệt cho học sinh tiểu học Việt Nam từ Lớp 1 đến Lớp 5, đồng hành cùng thầy cô và phụ huynh.
          </Text>
          <Text style={styles.footerCopyright}>
            © 2026 MathVisionKids. Tất cả quyền được bảo lưu.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  btnPressed: {
    opacity: 0.88,
    transform: [{ scale: 0.98 }],
  },

  /* Header */
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 18,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    zIndex: 10,
  },
  headerBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerMascot: {
    width: 34,
    height: 34,
  },
  headerTitleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  headerTitle: {
    fontFamily: FONTS.black,
    fontSize: 18,
    color: '#0F172A',
  },
  headerBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  headerBadgeText: {
    fontFamily: FONTS.bold,
    fontSize: 11,
    color: '#2563EB',
  },
  headerLoginBtn: {
    backgroundColor: '#6366F1',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 999,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  headerLoginText: {
    fontFamily: FONTS.bold,
    fontSize: 13,
    color: '#FFFFFF',
  },

  /* Scroll Body */
  scroll: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    paddingBottom: 40,
  },

  /* Hero Section */
  heroSection: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 36,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  heroPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    marginBottom: 16,
    gap: 8,
  },
  heroPillBadge: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
  },
  heroPillBadgeText: {
    fontFamily: FONTS.black,
    fontSize: 11,
    color: '#FFFFFF',
  },
  heroPillText: {
    fontFamily: FONTS.bold,
    fontSize: 12,
    color: '#92400E',
  },
  heroHeadlineContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
  },
  heroHeadline: {
    fontFamily: FONTS.black,
    fontSize: 30,
    lineHeight: 38,
    color: '#0F172A',
    textAlign: 'center',
  },
  heroHighlightBadge: {
    backgroundColor: '#FBBF24',
    paddingHorizontal: 12,
    paddingVertical: 3,
    borderRadius: 12,
    alignSelf: 'center',
  },
  heroHighlightText: {
    fontFamily: FONTS.black,
    fontSize: 28,
    color: '#1E1B4B',
  },
  heroSubtitle: {
    fontFamily: FONTS.medium,
    fontSize: 15,
    lineHeight: 23,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 24,
    maxWidth: 360,
  },
  heroCtaRow: {
    width: '100%',
    gap: 12,
    marginBottom: 24,
  },
  heroPrimaryBtn: {
    backgroundColor: '#6366F1',
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: 'center',
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4,
  },
  heroPrimaryBtnText: {
    fontFamily: FONTS.extraBold,
    fontSize: 16,
    color: '#FFFFFF',
  },
  heroSecondaryBtn: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: 'center',
  },
  heroSecondaryBtnText: {
    fontFamily: FONTS.bold,
    fontSize: 15,
    color: '#1E1B4B',
  },

  /* Feature Tags */
  featureTagsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 32,
  },
  featureTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  featureTagIcon: {
    fontSize: 14,
  },
  featureTagText: {
    fontFamily: FONTS.bold,
    fontSize: 12,
    color: '#334155',
  },

  /* Notebook Section */
  notebookContainerWrapper: {
    width: '100%',
    position: 'relative',
    marginVertical: 16,
    paddingHorizontal: 8,
  },
  floatingBadge: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 6,
    elevation: 5,
  },
  floatingBadgePlus: {
    top: -12,
    left: -4,
    backgroundColor: '#EF4444',
    transform: [{ rotate: '-12deg' }],
  },
  floatingBadgeMinus: {
    top: -12,
    right: -4,
    backgroundColor: '#10B981',
    transform: [{ rotate: '12deg' }],
  },
  floatingBadgeEqual: {
    bottom: -12,
    left: 12,
    backgroundColor: '#FBBF24',
    borderRadius: 999,
    transform: [{ rotate: '6deg' }],
  },
  floatingBadgeText: {
    fontFamily: FONTS.black,
    fontSize: 24,
    color: '#FFFFFF',
    lineHeight: 28,
  },
  floatingBadgeEqualText: {
    fontFamily: FONTS.black,
    fontSize: 24,
    color: '#1E1B4B',
    lineHeight: 28,
  },

  notebookCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    overflow: 'hidden',
    transform: [{ rotate: '-3deg' }],
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.18,
    shadowRadius: 20,
    elevation: 6,
  },
  notebookTopBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  notebookTopBarLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dotGroup: {
    flexDirection: 'row',
    gap: 4,
  },
  topDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
  },
  notebookClassText: {
    fontFamily: FONTS.bold,
    fontSize: 14,
    color: '#FFFFFF',
  },
  privacyChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  privacyChipText: {
    fontFamily: FONTS.bold,
    fontSize: 11,
    color: '#FFFFFF',
  },

  notebookPaper: {
    backgroundColor: '#FFFFFF',
    paddingTop: 18,
    paddingBottom: 24,
    paddingHorizontal: 16,
    position: 'relative',
    minHeight: 380,
  },
  redMarginLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 28,
    width: 2,
    backgroundColor: 'rgba(239, 68, 68, 0.5)',
  },
  studentNameText: {
    fontFamily: FONTS.bold,
    fontSize: 13,
    color: '#1E1B4B',
    marginLeft: 26,
    marginBottom: 16,
  },

  /* Math Calculation Area */
  calculationArea: {
    alignSelf: 'center',
    alignItems: 'flex-end',
    marginVertical: 12,
  },
  mathRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
  },
  mathOperator: {
    fontFamily: FONTS.black,
    fontSize: 32,
    color: '#1E1B4B',
    marginRight: 10,
  },
  mathCell: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mathCellActive: {
    backgroundColor: '#EEF2F6',
    borderRadius: 14,
  },
  mathCellError: {
    backgroundColor: '#FEE2E2',
    borderBottomWidth: 3,
    borderBottomColor: '#EF4444',
    borderRadius: 14,
  },
  mathDigit: {
    fontFamily: FONTS.black,
    fontSize: 32,
    color: '#1E1B4B',
  },
  mathDigitError: {
    color: '#EF4444',
  },
  mathDivider: {
    width: '120%',
    height: 3,
    backgroundColor: '#4F46E5',
    marginVertical: 6,
    alignSelf: 'flex-end',
  },

  /* Robot Dialogue */
  robotBubble: {
    backgroundColor: '#FEF3C7',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#FDE68A',
    padding: 12,
    marginTop: 18,
  },
  robotBubbleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  robotBubbleAvatar: {
    width: 32,
    height: 32,
    marginTop: 2,
  },
  robotBubbleText: {
    flex: 1,
    fontFamily: FONTS.bold,
    fontSize: 13,
    lineHeight: 19,
    color: '#92400E',
  },

  replyBtnWrap: {
    alignItems: 'flex-end',
    marginTop: 14,
  },
  replyBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1.5,
    borderColor: '#6366F1',
  },
  replyBtnNormal: {
    backgroundColor: '#FFFFFF',
  },
  replyBtnAnswered: {
    backgroundColor: '#6366F1',
  },
  replyBtnText: {
    fontFamily: FONTS.bold,
    fontSize: 13,
  },
  replyBtnTextNormal: {
    color: '#6366F1',
  },
  replyBtnTextAnswered: {
    color: '#FFFFFF',
  },

  /* Grade Selector Buttons */
  gradeButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    flexWrap: 'wrap',
    marginTop: 24,
  },
  gradeBtn: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
  },
  gradeBtnSelected: {
    transform: [{ scale: 1.08 }],
    borderWidth: 2,
    borderColor: '#1E1B4B',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 3,
  },
  gradeBtnText: {
    fontFamily: FONTS.extraBold,
    fontSize: 14,
  },

  /* Section Styling */
  sectionWhite: {
    paddingHorizontal: 20,
    paddingVertical: 36,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  sectionLightPurple: {
    paddingHorizontal: 20,
    paddingVertical: 36,
    backgroundColor: '#FAF8FF',
    borderBottomWidth: 1,
    borderBottomColor: '#F1F0FB',
  },
  sectionHeader: {
    alignItems: 'flex-start',
    marginBottom: 24,
  },
  sectionBadge: {
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 14,
    paddingVertical: 5,
    borderRadius: 999,
    marginBottom: 12,
  },
  sectionBadgeText: {
    fontFamily: FONTS.bold,
    fontSize: 12,
    color: '#6D28D9',
  },
  sectionTitle: {
    fontFamily: FONTS.black,
    fontSize: 24,
    lineHeight: 32,
    color: '#0F172A',
    marginBottom: 10,
  },
  sectionSubtitle: {
    fontFamily: FONTS.medium,
    fontSize: 14,
    lineHeight: 22,
    color: '#64748B',
  },

  /* Step Cards */
  stepCardsCol: {
    gap: 16,
  },
  stepCard: {
    borderRadius: 18,
    padding: 20,
    position: 'relative',
    overflow: 'hidden',
  },
  stepWatermark: {
    position: 'absolute',
    top: 6,
    right: 14,
    fontFamily: FONTS.black,
    fontSize: 76,
    color: 'rgba(255, 255, 255, 0.88)',
  },
  stepIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  stepIcon: {
    fontSize: 28,
  },
  stepTitle: {
    fontFamily: FONTS.black,
    fontSize: 18,
    color: '#1E1B4B',
    marginBottom: 8,
  },
  stepDesc: {
    fontFamily: FONTS.medium,
    fontSize: 14,
    lineHeight: 21,
    color: '#475569',
    marginBottom: 16,
  },
  stepChip: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
  },
  stepChipText: {
    fontFamily: FONTS.bold,
    fontSize: 12,
    color: '#1E1B4B',
  },

  blueBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 18,
    padding: 18,
    marginTop: 20,
    marginBottom: 12,
    gap: 14,
  },
  blueBannerIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  blueBannerIcon: {
    fontSize: 24,
  },
  blueBannerContent: {
    flex: 1,
  },
  blueBannerTitle: {
    fontFamily: FONTS.black,
    fontSize: 16,
    color: '#FFFFFF',
    marginBottom: 4,
  },
  blueBannerDesc: {
    fontFamily: FONTS.medium,
    fontSize: 13,
    lineHeight: 18,
    color: 'rgba(255, 255, 255, 0.95)',
  },

  tipBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    borderRadius: 14,
    padding: 14,
    gap: 12,
  },
  tipBannerIcon: {
    fontSize: 22,
  },
  tipBannerText: {
    flex: 1,
    fontFamily: FONTS.bold,
    fontSize: 13,
    lineHeight: 19,
    color: '#92400E',
  },

  /* Compare Cards */
  compareCol: {
    gap: 16,
  },
  compareCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 20,
  },
  compareCardCommercial: {
    borderWidth: 1.5,
    borderColor: '#FDA4AF',
  },
  compareCardSocratic: {
    borderWidth: 2,
    borderColor: '#10B981',
  },
  compareCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    flexWrap: 'wrap',
    gap: 8,
  },
  compareCardTitle: {
    fontFamily: FONTS.black,
    fontSize: 18,
    color: '#1E1B4B',
  },
  compareBadgeGray: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
  },
  compareBadgeGrayText: {
    fontFamily: FONTS.bold,
    fontSize: 11,
    color: '#64748B',
  },
  compareBadgeGreen: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
  },
  compareBadgeGreenText: {
    fontFamily: FONTS.bold,
    fontSize: 11,
    color: '#166534',
  },

  redHighlightBox: {
    backgroundColor: '#FFF1F2',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  redHighlightNumber: {
    fontFamily: FONTS.black,
    fontSize: 28,
    color: '#EF4444',
  },
  redHighlightLabel: {
    fontFamily: FONTS.bold,
    fontSize: 13,
    color: '#64748B',
  },

  yellowHighlightBox: {
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  yellowHighlightText: {
    fontFamily: FONTS.black,
    fontSize: 15,
    lineHeight: 22,
    color: '#1E1B4B',
  },

  compareList: {
    gap: 12,
  },
  compareItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  compareItemIcon: {
    marginTop: 2,
  },
  compareItemText: {
    flex: 1,
    fontFamily: FONTS.medium,
    fontSize: 13,
    lineHeight: 19,
    color: '#475569',
  },

  /* Ethics Cards with Left-Tilted Squircles */
  ethicsCard: {
    backgroundColor: '#F8FAFC',
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    borderRadius: 18,
    padding: 20,
  },
  ethicsSquircle: {
    width: 66,
    height: 66,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    transform: [{ rotate: '-8deg' }],
  },
  ethicsSquircleYellow: {
    backgroundColor: '#F9C93D',
    shadowColor: '#F9C93D',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4,
  },
  ethicsSquircleGreen: {
    backgroundColor: '#27D69A',
    shadowColor: '#27D69A',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4,
  },
  ethicsSquircleBlue: {
    backgroundColor: '#3DB8FF',
    shadowColor: '#3DB8FF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4,
  },
  ethicsEmoji: {
    fontSize: 32,
  },
  ethicsCardTitle: {
    fontFamily: FONTS.black,
    fontSize: 18,
    color: '#1E1B4B',
    marginBottom: 8,
  },
  ethicsCardDesc: {
    fontFamily: FONTS.medium,
    fontSize: 14,
    lineHeight: 21,
    color: '#475569',
    marginBottom: 16,
  },
  ethicsChip: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
  },
  ethicsChipText: {
    fontFamily: FONTS.bold,
    fontSize: 12,
    color: '#1E1B4B',
  },

  /* CTA Section */
  ctaSectionWrapper: {
    paddingHorizontal: 16,
    paddingVertical: 32,
    backgroundColor: '#FAF8FF',
  },
  ctaCard: {
    borderRadius: 22,
    paddingHorizontal: 20,
    paddingVertical: 36,
    alignItems: 'center',
    position: 'relative',
    overflow: 'hidden',
  },
  ctaFloatingBadge: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  ctaBadgePlus: {
    top: 12,
    left: 12,
    backgroundColor: '#EF4444',
    transform: [{ rotate: '-10deg' }],
  },
  ctaBadgePercent: {
    top: 14,
    right: 14,
    backgroundColor: '#FBBF24',
    borderRadius: 999,
  },
  ctaBadgeMinus: {
    bottom: 14,
    right: 16,
    backgroundColor: '#10B981',
    transform: [{ rotate: '8deg' }],
  },
  ctaBadgeText: {
    fontFamily: FONTS.black,
    fontSize: 24,
    color: '#FFFFFF',
  },
  ctaBadgePercentText: {
    fontFamily: FONTS.black,
    fontSize: 20,
    color: '#1E1B4B',
  },
  ctaTitle: {
    fontFamily: FONTS.black,
    fontSize: 24,
    lineHeight: 32,
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 12,
    marginTop: 18,
  },
  ctaSubtitle: {
    fontFamily: FONTS.medium,
    fontSize: 14,
    lineHeight: 21,
    color: 'rgba(255, 255, 255, 0.95)',
    textAlign: 'center',
    marginBottom: 26,
    maxWidth: 280,
  },
  ctaButtonsCol: {
    width: '100%',
    gap: 12,
  },
  ctaGoogleBtn: {
    backgroundColor: '#FBBF24',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 999,
    shadowColor: '#FBBF24',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    elevation: 3,
  },
  ctaGoogleBtnText: {
    fontFamily: FONTS.extraBold,
    fontSize: 15,
    color: '#1E1B4B',
  },
  ctaFacebookBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.85)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 999,
  },
  ctaFacebookBtnText: {
    fontFamily: FONTS.bold,
    fontSize: 15,
    color: '#FFFFFF',
  },

  /* Footer */
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 28,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    alignItems: 'center',
  },
  footerBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  footerMascot: {
    width: 30,
    height: 30,
  },
  footerBrandTitle: {
    fontFamily: FONTS.black,
    fontSize: 18,
    color: '#1E1B4B',
  },
  footerDesc: {
    fontFamily: FONTS.regular,
    fontSize: 12,
    lineHeight: 18,
    color: '#64748B',
    textAlign: 'center',
    marginBottom: 12,
  },
  footerCopyright: {
    fontFamily: FONTS.bold,
    fontSize: 11,
    color: '#94A3B8',
  },
});
