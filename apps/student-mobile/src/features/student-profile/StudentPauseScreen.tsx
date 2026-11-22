import { Ionicons } from '@expo/vector-icons';
import { Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS, SHADOWS } from '../../constants/theme';

type PauseScreenProps = {
  reason: 'daily-limit' | 'game-limit' | 'connection';
  onContinue: () => void;
  onLeave: () => void;
  working?: boolean;
  checking?: boolean;
  retryFailed?: boolean;
  catalogDialog?: boolean;
};

export function StudentPauseScreen({ reason, onContinue, onLeave, working, checking, retryFailed, catalogDialog }: PauseScreenProps) {
  const isRest = reason === 'daily-limit';
  const gameLimit = reason === 'game-limit';
  const scrimId = catalogDialog ? 'student-game-catalog-scrim' : isRest ? 'student-rest-scrim' : undefined;
  return <View style={scrimId ? styles.scrim : styles.screen} nativeID={scrimId}>
    {scrimId && Platform.OS === 'web' && <style>{`#${scrimId} { backdrop-filter: blur(3px); }`}</style>}
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.center}>
        <View style={[styles.card, !!scrimId && SHADOWS.medium]} accessibilityViewIsModal={!!scrimId}>
          <View style={styles.intro}>
            <View style={[styles.icon, !isRest && styles.connectionIcon]}>
              <Ionicons name={gameLimit ? 'hourglass-outline' : isRest ? 'moon-outline' : 'cloud-offline-outline'} size={28} color={isRest ? COLORS.primaryDark : COLORS.textPrimary} accessibilityElementsHidden importantForAccessibility="no" aria-hidden />
            </View>
            <Text nativeID={catalogDialog ? 'student-game-catalog-heading' : isRest ? 'student-rest-heading' : undefined} accessibilityRole="header" accessibilityLiveRegion="polite" style={styles.heading}>
              {gameLimit ? 'Đã hết giờ chơi hôm nay' : isRest ? 'Đến giờ nghỉ rồi!' : 'Chưa xác minh được thời gian sử dụng'}
            </Text>
            <Text style={styles.body}>{gameLimit
              ? 'Em vẫn có thể học hoặc làm Quiz nếu còn thời gian sử dụng hôm nay.'
              : isRest
              ? 'Hôm nay em đã dùng hết thời gian. Ngày mai mình học tiếp nhé.'
              : 'Trò chơi đang tạm dừng. Em kiểm tra kết nối mạng rồi thử lại nhé.'}</Text>
          </View>
          {isRest && working && <View style={styles.note}>
            <Text style={styles.noteTitle}>Nếu em đang làm bài</Text>
            <Text style={styles.body}>Hãy giữ màn hình này mở và nhờ người lớn. Phần chưa gửi có thể mất nếu em tải lại, đóng ứng dụng hoặc đăng xuất.</Text>
          </View>}
          {!isRest && retryFailed && <Text accessibilityRole="alert" style={styles.body}>Vẫn chưa xác minh được. Em có thể thử lại hoặc về danh sách trò chơi.</Text>}
          <View style={styles.actions}>
            {catalogDialog ? <AppButton title="Đóng" onPress={onLeave} /> : gameLimit ? <>
              <AppButton title="Trở về danh sách trò chơi" onPress={onLeave} />
              <AppButton title="Kiểm tra lại" onPress={onContinue} variant="ghost" />
            </> : <>
              <AppButton title={isRest ? 'Góc phụ huynh' : 'Kiểm tra lại'} onPress={onContinue} loading={!isRest && checking} loadingTitle="Đang kiểm tra…" />
              <AppButton title={isRest ? 'Đăng xuất' : 'Trở về danh sách trò chơi'} variant="ghost" onPress={onLeave} />
            </>}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  safeArea: { flex: 1 },
  scrim: { flex: 1, backgroundColor: 'rgba(27, 19, 56, 0.55)' },
  center: { flexGrow: 1, justifyContent: 'center', alignItems: 'center', padding: 16 },
  card: { width: '100%', maxWidth: 500, backgroundColor: COLORS.surface, borderRadius: 24, borderWidth: 1, borderColor: COLORS.border, padding: 24, gap: 20 },
  intro: { gap: 10, alignItems: 'flex-start' },
  icon: { alignItems: 'center', justifyContent: 'center', width: 54, height: 54, backgroundColor: COLORS.primaryLight, borderRadius: 16 },
  connectionIcon: { backgroundColor: COLORS.surfaceSubdued },
  heading: { color: COLORS.textPrimary, fontFamily: FONTS.black, fontSize: 28, lineHeight: 34 },
  body: { color: COLORS.textSecondary, fontFamily: FONTS.semiBold, fontSize: 16, lineHeight: 24 },
  note: { gap: 4, padding: 14, borderRadius: 14, backgroundColor: COLORS.surfaceSubdued },
  noteTitle: { color: COLORS.textPrimary, fontFamily: FONTS.bold, fontSize: 16, lineHeight: 23 },
  actions: { gap: 6 },
});
