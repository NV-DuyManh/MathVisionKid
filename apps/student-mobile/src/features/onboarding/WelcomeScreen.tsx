import React, { useContext, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { KeyDownEvent, NativeScrollEvent, NativeSyntheticEvent, ScrollViewInstance } from 'react-native';
import { useRouter } from 'expo-router';
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
    image: require('../../../assets/illustrations/robot-mascot.png'),
  },
  {
    title: 'Hiểu bài qua từng bước nhỏ',
    description: 'Chụp bài toán, đọc đề và thử cách làm. Cùng tìm lời giải nhé!',
    image: require('../../../assets/illustrations/approved/practice.webp'),
  },
  {
    title: 'Mỗi ngày tiến bộ một chút',
    description: 'Luyện tập theo chương trình của em, nhận sao và lưu lại những điều đã học.',
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
  const tabButtons = useRef<(React.ElementRef<typeof View> | null)[]>([]);
  const [pageWidth, setPageWidth] = useState(width);
  const [page, setPage] = useState(0);
  const scrollTarget = useRef<number | null>(null);
  const reduceMotion = useRef(false);
  const navigating = useRef(false);
  const [leaving, setLeaving] = useState(false);
  const imageHeight = Math.min(330, Math.max(150, height * (height > 740 ? .36 : .29)));
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
    if (Platform.OS === 'web' && typeof window !== 'undefined' && /^\/(?:study|learn)(?:\/|$)/.test(window.location.pathname)) window.location.replace('/login');
    else router.replace('/login');
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
    <LinearGradient colors={['#3930A9', '#8863DE', '#E6DCF9', '#F8F7FE']} locations={[0, .36, .67, .86]} style={StyleSheet.absoluteFill} pointerEvents="none" />
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
          onTouchStart={() => { scrollTarget.current = null; }}
          {...(Platform.OS === 'web' ? { onWheel: () => { scrollTarget.current = null; } } : {})}
          onScroll={Platform.OS === 'web' ? updatePage : undefined} scrollEventThrottle={Platform.OS === 'web' ? 16 : undefined}>
          {WELCOME_CARDS.map((card, index) => <View key={card.title} style={[styles.slide, { width: pageWidth }]} testID={`welcome-card-${index + 1}`}
            accessibilityElementsHidden={page !== index} importantForAccessibility={page === index ? 'auto' : 'no-hide-descendants'} aria-hidden={page !== index}>
            <View style={[styles.art, { height: imageHeight + 36 }]}>
              <View style={[styles.artGlow, { width: imageHeight, height: imageHeight }]} />
              <AppIllustration highResolution source={card.image} style={{ width: Math.min(pageWidth - 48, imageHeight + 40), height: imageHeight }} accessible={false} />
              <Ionicons name="sparkles" size={28} color="#FFDA63" style={styles.sparkle} accessible={false} />
            </View>
            <Text accessibilityRole="header" style={[styles.title, pageWidth >= 600 && styles.titleWide]}>{card.title}</Text>
            <Text style={[styles.description, fontScale > 1.3 && styles.descriptionLarge]}>{card.description}</Text>
          </View>)}
        </ScrollView>
      </View>
      <View style={styles.pagerControls}>
        <View style={styles.dots} accessibilityRole="tablist" accessibilityLabel="Các trang giới thiệu">
          {WELCOME_CARDS.map((card, index) => <Pressable key={card.title} ref={node => { tabButtons.current[index] = node; }} accessibilityRole="tab" accessibilityLabel={`Trang giới thiệu ${index + 1}`}
            accessibilityState={{ selected: index === page }} aria-selected={index === page} onPress={() => goToCard(index)} style={styles.dotButton}
            {...(Platform.OS === 'web' ? { tabIndex: index === page ? 0 : -1, onKeyDown: (event: React.KeyboardEvent | KeyDownEvent) => {
              const key = 'key' in event ? event.key : event.nativeEvent.key;
              if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(key)) return;
              event.preventDefault();
              const nextPage = key === 'Home' ? 0 : key === 'End' ? WELCOME_CARDS.length - 1
                : (index + (key === 'ArrowRight' ? 1 : -1) + WELCOME_CARDS.length) % WELCOME_CARDS.length;
              goToCard(nextPage);
              tabButtons.current[nextPage]?.focus();
            } } : {})}>
            <View style={[styles.dot, index === page && styles.dotActive]} />
          </Pressable>)}
        </View>
      </View>
      <View style={styles.actions}>
        <Pressable accessibilityRole="button" accessibilityLabel="Bắt đầu" disabled={leaving} onPress={() => { void finish(); }} style={({ pressed }) => [styles.start, pressed && styles.pressed]}>
          <LinearGradient colors={['#5637C9', '#7950E8']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.startFill}>
            <Text style={styles.startLabel}>Bắt đầu</Text><Ionicons name="arrow-forward" size={25} color="#FFFFFF" accessible={false} />
          </LinearGradient>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Tiếp tục học" disabled={leaving} onPress={() => { void finish(true); }}
          style={({ pressed }) => [styles.continueAction, pressed && styles.pressed]}>
          <Text style={styles.continuePrompt}>Sẵn sàng học tiếp? <Text style={styles.continueLabel}>Tiếp tục học</Text></Text>
        </Pressable>
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
  artGlow: { position: 'absolute', borderRadius: 200, backgroundColor: '#FFFFFF12' }, sparkle: { position: 'absolute', right: '12%', top: '12%' },
  title: { maxWidth: 530, fontFamily: FONTS.black, fontSize: 29, lineHeight: 37, textAlign: 'center', color: '#18164C', marginBottom: 16 },
  titleWide: { fontSize: 38, lineHeight: 48, maxWidth: 650 }, description: { maxWidth: 530, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, textAlign: 'center', color: '#514A68' },
  descriptionLarge: { marginBottom: 8 }, pagerControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 14, marginTop: 12 },
  dots: { flexDirection: 'row', alignItems: 'center' }, dotButton: { width: 42, height: 48, alignItems: 'center', justifyContent: 'center' }, dot: { width: 7, height: 7, borderRadius: 6, backgroundColor: '#CCBEDF' }, dotActive: { width: 20, backgroundColor: '#6040CF' },
  actions: { width: '100%', maxWidth: 570, alignSelf: 'center', paddingHorizontal: 24, marginTop: 18, gap: 5 },
  start: { borderRadius: 30, overflow: 'hidden' }, startFill: { minHeight: 58, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 18, paddingHorizontal: 24, paddingVertical: 12 },
  startLabel: { fontFamily: FONTS.extraBold, fontSize: 20, color: '#FFFFFF' }, pressed: { opacity: .76 },
  continueAction: { alignSelf: 'center', minHeight: 44, justifyContent: 'center', paddingHorizontal: 12 },
  continuePrompt: { textAlign: 'center', fontFamily: FONTS.regular, color: '#5B526B', fontSize: 14, lineHeight: 22 },
  continueLabel: { fontFamily: FONTS.extraBold, color: '#5637C9' },
});
