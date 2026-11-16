import React, { useContext, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { ScrollViewInstance } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AuthContext } from '../context/AuthContext';
import { AppIllustration } from '../components/ui/AppIllustration';
import { COLORS, FONTS } from '../constants/theme';

const WELCOME_CARDS = [
  {
    title: 'Học Toán thông minh cùng AI',
    description: 'Khám phá, luyện tập và chinh phục kiến thức Toán học thật thú vị!',
    image: require('../../assets/illustrations/robot-mascot.png'),
  },
  {
    title: 'Hiểu bài qua từng bước nhỏ',
    description: 'Chụp bài toán, đọc đề và thử cách làm. Cùng tìm lời giải nhé!',
    image: require('../../assets/illustrations/approved/practice.webp'),
  },
  {
    title: 'Mỗi ngày tiến bộ một chút',
    description: 'Luyện tập theo chương trình của em, nhận sao và lưu lại những điều đã học.',
    image: require('../../assets/illustrations/achievement-trophy.png'),
  },
];

export default function WelcomeScreen() {
  const auth = useContext(AuthContext);
  const router = useRouter();
  const { width, height, fontScale } = useWindowDimensions();
  const pager = useRef<ScrollViewInstance>(null);
  const [pageWidth, setPageWidth] = useState(width);
  const [page, setPage] = useState(0);
  const imageHeight = Math.min(340, Math.max(190, height * .34));
  const goToCard = (index: number) => {
    setPage(index);
    pager.current?.scrollTo({ x: index * pageWidth, animated: true });
  };

  useEffect(() => {
    if (!auth?.isLoading && auth?.isAuthenticated) router.replace('/(tabs)');
  }, [auth?.isLoading, auth?.isAuthenticated, router]);

  if (!auth || auth.isLoading) return <View style={styles.loading}><ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang xác minh tài khoản" /></View>;
  if (auth.isAuthenticated) return null;

  return <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
    <LinearGradient colors={['#3930A9', '#8863DE', '#E6DCF9', '#F8F7FE']} locations={[0, .36, .67, .86]} style={StyleSheet.absoluteFill} pointerEvents="none" />
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.brand} accessibilityLabel="MathVisionKid">
        <Ionicons name="planet-outline" size={28} color="#FFDB55" accessible={false} />
        <Text style={styles.wordmark}>MathVision<Text style={styles.brandAccent}>Kid</Text></Text>
      </View>
      <View style={styles.pagerShell} onLayout={event => {
        const nextWidth = event.nativeEvent.layout.width;
        if (nextWidth <= 0) return;
        setPageWidth(nextWidth);
        pager.current?.scrollTo({ x: page * nextWidth, animated: false });
      }}>
        <ScrollView ref={pager} horizontal pagingEnabled showsHorizontalScrollIndicator={false}
          testID="welcome-pager" onMomentumScrollEnd={event => {
            setPage(Math.max(0, Math.min(WELCOME_CARDS.length - 1, Math.round(event.nativeEvent.contentOffset.x / pageWidth))));
          }}>
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
        <Pressable accessibilityRole="button" accessibilityLabel="Trang giới thiệu trước" accessibilityState={{ disabled: page === 0 }} disabled={page === 0}
          onPress={() => goToCard(page - 1)} style={({ pressed }) => [styles.arrow, page === 0 && styles.arrowDisabled, pressed && styles.pressed]}>
          <Ionicons name="chevron-back" size={22} color={page === 0 ? '#AAA0BC' : '#5637C9'} accessible={false} />
        </Pressable>
        <View style={styles.dots} accessibilityRole="tablist" accessibilityLabel="Các trang giới thiệu">
          {WELCOME_CARDS.map((card, index) => <Pressable key={card.title} accessibilityRole="tab" accessibilityLabel={`Trang giới thiệu ${index + 1}`}
            accessibilityState={{ selected: index === page }} aria-selected={index === page} onPress={() => goToCard(index)} style={styles.dotButton}>
            <View style={[styles.dot, index === page && styles.dotActive]} />
          </Pressable>)}
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel="Trang giới thiệu tiếp theo" accessibilityState={{ disabled: page === WELCOME_CARDS.length - 1 }} disabled={page === WELCOME_CARDS.length - 1}
          onPress={() => goToCard(page + 1)} style={({ pressed }) => [styles.arrow, page === WELCOME_CARDS.length - 1 && styles.arrowDisabled, pressed && styles.pressed]}>
          <Ionicons name="chevron-forward" size={22} color={page === WELCOME_CARDS.length - 1 ? '#AAA0BC' : '#5637C9'} accessible={false} />
        </Pressable>
      </View>
      <Text accessibilityLiveRegion="polite" style={styles.pageLabel}>Trang {page + 1} trên {WELCOME_CARDS.length}</Text>
      <View style={styles.actions}>
        <Pressable accessibilityRole="button" accessibilityLabel="Bắt đầu" onPress={() => router.push('/login')} style={({ pressed }) => [styles.start, pressed && styles.pressed]}>
          <LinearGradient colors={['#5637C9', '#7950E8']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.startFill}>
            <Text style={styles.startLabel}>Bắt đầu</Text><Ionicons name="arrow-forward" size={25} color="#FFFFFF" accessible={false} />
          </LinearGradient>
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel="Tiếp tục học" onPress={() => router.push('/login')} style={({ pressed }) => [styles.continue, pressed && styles.pressed]}>
          <Text style={styles.continuePrompt}>Sẵn sàng học tiếp? <Text style={styles.continueLabel}>Tiếp tục học</Text></Text>
        </Pressable>
      </View>
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#F8F7FE' }, loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.background },
  content: { flexGrow: 1, width: '100%', maxWidth: 820, alignSelf: 'center', paddingBottom: 12 },
  brand: { minHeight: 68, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 24, paddingTop: 12 },
  wordmark: { fontFamily: FONTS.black, fontSize: 27, letterSpacing: -.6, color: '#FFFFFF' }, brandAccent: { color: '#FFDA55' },
  pagerShell: { width: '100%' }, slide: { alignItems: 'center', paddingHorizontal: 24, paddingBottom: 8 },
  art: { width: '100%', alignItems: 'center', justifyContent: 'center', marginTop: 8, marginBottom: 12 },
  artGlow: { position: 'absolute', borderRadius: 200, backgroundColor: '#FFFFFF12' }, sparkle: { position: 'absolute', right: '12%', top: '12%' },
  title: { maxWidth: 530, fontFamily: FONTS.black, fontSize: 29, lineHeight: 37, textAlign: 'center', color: '#18164C', marginBottom: 16 },
  titleWide: { fontSize: 38, lineHeight: 48 }, description: { maxWidth: 530, fontFamily: FONTS.regular, fontSize: 16, lineHeight: 25, textAlign: 'center', color: '#514A68' },
  descriptionLarge: { marginBottom: 8 }, pagerControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 14, marginTop: 12 },
  arrow: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFFFFF7A', alignItems: 'center', justifyContent: 'center' }, arrowDisabled: { backgroundColor: '#FFFFFF38' },
  dots: { flexDirection: 'row', alignItems: 'center' }, dotButton: { width: 42, height: 48, alignItems: 'center', justifyContent: 'center' }, dot: { width: 10, height: 10, borderRadius: 6, backgroundColor: '#CCBEDF' }, dotActive: { width: 26, backgroundColor: '#6040CF' },
  pageLabel: { fontFamily: FONTS.semiBold, fontSize: 12, color: '#75688A', textAlign: 'center', marginBottom: 16 },
  actions: { width: '100%', maxWidth: 570, alignSelf: 'center', paddingHorizontal: 24, paddingTop: 16, marginTop: 'auto' },
  start: { borderRadius: 30, overflow: 'hidden' }, startFill: { minHeight: 58, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 18, paddingHorizontal: 24, paddingVertical: 12 },
  startLabel: { fontFamily: FONTS.extraBold, fontSize: 20, color: '#FFFFFF' }, continue: { minHeight: 56, alignItems: 'center', justifyContent: 'center', marginTop: 8 },
  continuePrompt: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 22, textAlign: 'center', color: '#756A86' }, continueLabel: { fontFamily: FONTS.extraBold, color: '#5637C9' }, pressed: { opacity: .76 },
});
