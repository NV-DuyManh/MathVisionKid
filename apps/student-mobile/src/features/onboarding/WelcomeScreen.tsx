import React, { useContext, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { NativeScrollEvent, NativeSyntheticEvent, ScrollViewInstance } from 'react-native';
import { useRouter } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../../context/AuthContext';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';
import { loadLearningProgress } from '../tutoring/learningProgress';
import { completeOnboarding } from './onboardingStorage';

const WELCOME_CARDS = [
  {
    title: 'Học Toán thông minh cùng AI',
    description: 'Khám phá, luyện tập và chinh phục kiến thức Toán học thật thú vị!',
    action: 'Bắt đầu',
  },
  {
    title: 'Ôn tập, luyện tập và khám phá',
    description: 'Chọn bài theo chương trình của em. Tập giải từng bước với gợi ý và giải thích dễ hiểu.',
    action: 'Tiếp theo',
    image: require('../../../assets/illustrations/approved/practice.webp'),
  },
  {
    title: 'Theo dõi tiến bộ và nhận thưởng',
    description: 'Xem lại những bài em đã làm, tích sao và mở khóa danh hiệu khi tiến bộ.',
    action: 'Bắt đầu học ngay',
    image: require('../../../assets/illustrations/achievement-trophy.png'),
  },
];

export default function WelcomeScreen() {
  const auth = useContext(AuthContext);
  const currentAuth = useRef(auth);
  useLayoutEffect(() => { currentAuth.current = auth; }, [auth]);
  const router = useRouter();
  const { width, height, fontScale } = useWindowDimensions();
  const pager = useRef<ScrollViewInstance>(null);
  const [pageWidth, setPageWidth] = useState(width);
  const [page, setPage] = useState(0);
  const scrollTarget = useRef<number | null>(null);
  const reduceMotion = useRef(false);
  const navigating = useRef(false);
  const [leaving, setLeaving] = useState(false);
  const imageHeight = Math.min(300, Math.max(154, Math.min(width * .65, height * .33)));
  const lastPage = page === WELCOME_CARDS.length - 1;
  const resumeLabel = auth?.isAuthenticated ? 'Tiếp tục học' : 'Đăng nhập';
  const finish = async (resume = false) => {
    if (!auth || auth.isLoading || navigating.current) return;
    navigating.current = true;
    setLeaving(true);
    await completeOnboarding();
    if (currentAuth.current?.isAuthenticated) {
      const owner = currentAuth.current.user?.id || currentAuth.current.user?.userId;
      const saved = resume && owner ? await loadLearningProgress(owner) : null;
      const verified = currentAuth.current;
      if (verified?.isAuthenticated) {
        if (saved && (verified.user?.id || verified.user?.userId) === owner) {
          router.replace({ pathname: '/learning/math-guide', params: {
            problemText: saved.problemText, workText: saved.workText, lessonId: saved.lessonId,
          } });
        } else router.replace('/(tabs)');
        return;
      }
    }
    router.replace('/login');
  };
  const goToCard = (index: number) => {
    scrollTarget.current = index;
    setPage(index);
    pager.current?.scrollTo({ x: index * pageWidth, animated: !reduceMotion.current });
  };
  const updatePage = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const offset = event.nativeEvent.contentOffset.x;
    if (scrollTarget.current !== null) {
      if (Math.abs(offset - scrollTarget.current * pageWidth) > 1) return;
      scrollTarget.current = null;
    }
    setPage(Math.max(0, Math.min(WELCOME_CARDS.length - 1, Math.round(offset / pageWidth))));
  };

  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then(enabled => {
      if (mounted) reduceMotion.current = enabled;
    }).catch(() => {});
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', enabled => {
      reduceMotion.current = enabled;
    });
    return () => {
      mounted = false;
      subscription.remove();
    };
  }, []);

  if (!auth || auth.isLoading) return <View style={styles.loading}><ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang xác minh tài khoản" /></View>;

  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <StatusBar style="light" />
    <LinearGradient colors={['#322594', '#7552D1', '#E4D7FA', '#F8F7FE']} locations={[0, .27, .54, .74]} style={StyleSheet.absoluteFill} pointerEvents="none" />
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.brand}>
        <Ionicons name="planet-outline" size={28} color="#FFDB55" accessible={false} />
        <Text style={[styles.wordmark, width <= 390 && { fontSize: 21 }]} numberOfLines={1}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Bỏ qua giới thiệu" disabled={leaving} onPress={() => { void finish(); }} style={styles.skip}><Text style={styles.skipLabel}>Bỏ qua</Text></Pressable>
      </View>
      <View style={styles.pagerShell} onLayout={event => {
        const nextWidth = event.nativeEvent.layout.width;
        if (nextWidth <= 0) return;
        scrollTarget.current = page;
        setPageWidth(nextWidth);
        pager.current?.scrollTo({ x: page * nextWidth, animated: false });
      }}>
        <ScrollView ref={pager} horizontal pagingEnabled showsHorizontalScrollIndicator={false}
          testID="welcome-pager" onMomentumScrollEnd={updatePage}
          onTouchStart={() => { scrollTarget.current = null; }}>
          {WELCOME_CARDS.map((card, index) => <View key={card.title} style={[styles.slide, { width: pageWidth }]} testID={`welcome-card-${index + 1}`}
            accessibilityElementsHidden={page !== index} importantForAccessibility={page === index ? 'auto' : 'no-hide-descendants'} aria-hidden={page !== index}>
            <View style={[styles.art, { height: imageHeight + 20 }]} accessible={false} importantForAccessibility="no-hide-descendants">
              <View style={[styles.artGlow, { width: imageHeight, height: imageHeight }]} />
              {'image' in card ? <AppIllustration source={card.image} style={[styles.artObject, { width: imageHeight * .38 }]} accessible={false} />
                : <View style={styles.mathCard}><Ionicons name="shapes-outline" size={26} color="#E2F7FF" /><Text style={styles.mathLabel}>8 + 5</Text></View>}
              <AppIllustration highResolution source={require('../../../assets/illustrations/robot-mascot.png')} style={{ width: imageHeight * .88, height: imageHeight }} accessible={false} />
              <Ionicons name="sparkles" size={28} color="#FFDA63" style={styles.sparkle} accessible={false} />
            </View>
            <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={[styles.title, pageWidth >= 600 && styles.titleWide]}>{card.title}</Text>
            <Text style={[styles.description, fontScale > 1.3 && styles.descriptionLarge]}>{card.description}</Text>
          </View>)}
        </ScrollView>
      </View>
      <View style={styles.pagerControls}>
        <View style={styles.dots} accessibilityRole="tablist" accessibilityLabel="Các trang giới thiệu">
          {WELCOME_CARDS.map((card, index) => <Pressable key={card.title} accessibilityRole="tab" accessibilityLabel={`Trang giới thiệu ${index + 1}`}
            accessibilityState={{ selected: index === page }} aria-selected={index === page} disabled={leaving} onPress={() => goToCard(index)} style={styles.dotButton}>
            <View style={[styles.dot, index === page && styles.dotActive]} />
          </Pressable>)}
        </View>
      </View>
      <View style={styles.actions}>
        <Pressable accessibilityRole="button" accessibilityLabel={WELCOME_CARDS[page].action} disabled={leaving}
          onPress={() => { if (lastPage) void finish(); else goToCard(page + 1); }} style={({ pressed }) => [styles.start, pressed && styles.pressed]}>
          <LinearGradient colors={['#5637C9', '#7950E8']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.startFill}>
            <Text style={styles.startLabel}>{WELCOME_CARDS[page].action}</Text>
            <Ionicons name={lastPage ? 'rocket-outline' : 'arrow-forward'} size={22} color="#FFFFFF" accessible={false} />
          </LinearGradient>
        </Pressable>
        {page === 0 && <Pressable accessibilityRole="button" accessibilityLabel={resumeLabel} disabled={leaving} onPress={() => { void finish(true); }}
          style={({ pressed }) => [styles.continueAction, pressed && styles.pressed]}>
          <Text style={styles.continuePrompt}>{auth.isAuthenticated ? 'Sẵn sàng học tiếp?' : 'Đã có tài khoản?'} <Text style={styles.continueLabel}>{resumeLabel}</Text></Text>
        </Pressable>}
      </View>
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F8F7FE' }, loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.background },
  content: { flexGrow: 1, width: '100%', maxWidth: 820, alignSelf: 'center', paddingBottom: 24 },
  brand: { minHeight: 64, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 24, paddingTop: 8 },
  skip: { marginLeft: 'auto', minHeight: 44, paddingHorizontal: 6, justifyContent: 'center' }, skipLabel: { fontFamily: FONTS.bold, color: '#FFFFFF', fontSize: 14 },
  wordmark: { flexShrink: 1, minWidth: 0, fontFamily: FONTS.black, fontSize: 27, letterSpacing: -.6, color: '#FFFFFF' }, brandAccent: { color: '#FFDA55' },
  pagerShell: { width: '100%' }, slide: { alignItems: 'center', paddingHorizontal: 24, paddingBottom: 8 },
  art: { width: '100%', alignItems: 'center', justifyContent: 'center', marginTop: 8, marginBottom: 12 },
  artGlow: { position: 'absolute', borderRadius: 200, backgroundColor: '#FFFFFF20' },
  artObject: { position: 'absolute', left: '12%', bottom: '14%', aspectRatio: 1 },
  mathCard: { position: 'absolute', left: '12%', top: '19%', alignItems: 'center', gap: 3, padding: 10, borderRadius: 14, borderWidth: 1, borderColor: '#B7EDFF', backgroundColor: '#373C9A', transform: [{ rotate: '-12deg' }] },
  mathLabel: { fontFamily: FONTS.extraBold, fontSize: 15, color: '#E2F7FF' },
  sparkle: { position: 'absolute', right: '12%', top: '13%' },
  title: { maxWidth: 530, fontFamily: FONTS.black, fontSize: 27, lineHeight: 34, textAlign: 'center', color: '#18164C', marginBottom: 12 },
  titleWide: { fontSize: 38, lineHeight: 48, maxWidth: 650 }, description: { maxWidth: 530, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, textAlign: 'center', color: '#514A68' },
  descriptionLarge: { marginBottom: 8 }, pagerControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 4 },
  dots: { flexDirection: 'row', alignItems: 'center' }, dotButton: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center' }, dot: { width: 8, height: 8, borderRadius: 6, backgroundColor: '#CCBEDF' }, dotActive: { width: 20, backgroundColor: '#6040CF' },
  actions: { width: '100%', maxWidth: 570, alignSelf: 'center', paddingHorizontal: 24, gap: 5 },
  start: { borderRadius: 30, overflow: 'hidden' }, startFill: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, paddingHorizontal: 20, paddingVertical: 10 },
  startLabel: { fontFamily: FONTS.extraBold, fontSize: 20, color: '#FFFFFF' }, pressed: { opacity: .76 },
  continueAction: { alignSelf: 'center', minHeight: 44, justifyContent: 'center', paddingHorizontal: 12 },
  continuePrompt: { textAlign: 'center', fontFamily: FONTS.regular, color: '#5B526B', fontSize: 14, lineHeight: 22 },
  continueLabel: { fontFamily: FONTS.extraBold, color: '#5637C9' },
});
