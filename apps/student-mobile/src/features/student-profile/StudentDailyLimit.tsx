import { usePathname, useRouter } from 'expo-router';
import { useContext, useEffect, useState } from 'react';
import { AppState, Modal, ScrollView, StyleSheet, Text, View } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { AppIllustration } from '../../components/ui/AppIllustration';
import { COLORS, FONTS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { readParentControlStatus } from './parentControlApi';

export function StudentDailyLimit() {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  const pathname = usePathname();
  const router = useRouter();
  const inParentMode = pathname === '/parent-mode';
  const [blockedOwner, setBlockedOwner] = useState<string>();

  useEffect(() => {
    if (!auth?.isAuthenticated || !owner) {
      setBlockedOwner(undefined);
      return;
    }
    const lifetime = new AbortController();
    let checking = false;
    async function check() {
      if (checking || lifetime.signal.aborted) return;
      checking = true;
      try {
        const status = await readParentControlStatus(lifetime.signal);
        if (!lifetime.signal.aborted) setBlockedOwner(status.dailyLimitReached ? owner : undefined);
      } catch {
        // Retain the most recent confirmed decision when the network drops.
      } finally {
        checking = false;
      }
    }
    void check();
    const timer = setInterval(() => { if (AppState.currentState !== 'background') void check(); }, 5_000);
    const appState = AppState.addEventListener('change', state => { if (state === 'active') void check(); });
    return () => {
      lifetime.abort();
      clearInterval(timer);
      appState.remove();
    };
  }, [auth?.isAuthenticated, owner, inParentMode]);

  if (!owner || blockedOwner !== owner || inParentMode) return null;
  return <Modal visible animationType="none" onRequestClose={() => {}}>
    <ScrollView style={styles.screen} contentContainerStyle={styles.center}>
      <View style={styles.card} accessibilityViewIsModal>
        <View style={styles.artWell}>
          <AppIllustration source={require('../../../assets/illustrations/robot-mascot.png')} style={styles.art} accessible={false} />
        </View>
        <Text accessibilityRole="header" accessibilityLiveRegion="polite" style={styles.heading}>Đến giờ nghỉ rồi!</Text>
        <Text style={styles.body}>Hôm nay em đã dùng hết thời gian. Ngày mai mình học tiếp nhé.</Text>
        <AppButton title="Góc phụ huynh" onPress={() => router.push('/parent-mode')} />
        <AppButton title="Đăng xuất" variant="ghost" onPress={() => { void auth?.logout(); }} />
      </View>
    </ScrollView>
  </Modal>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  center: { flexGrow: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  card: {
    width: '100%', maxWidth: 432, backgroundColor: COLORS.surface, borderRadius: 28,
    borderWidth: 1, borderColor: COLORS.border, padding: 24, gap: 14,
  },
  artWell: { alignSelf: 'center', backgroundColor: COLORS.primaryLight, borderRadius: 28, padding: 8 },
  art: { width: 112, height: 112 },
  heading: { color: COLORS.primaryDark, fontFamily: FONTS.black, fontSize: 32, lineHeight: 39, textAlign: 'center' },
  body: { color: COLORS.textSecondary, fontFamily: FONTS.semiBold, fontSize: 17, lineHeight: 25, textAlign: 'center' },
});
