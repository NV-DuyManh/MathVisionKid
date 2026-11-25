import React, { useContext, useRef, useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { LessonSheet } from '../tutoring/LessonSheet';

export function LogoutSheet({ onClose }: { onClose: () => void }) {
  const auth = useContext(AuthContext);
  const lock = useRef(false);
  const [leaving, setLeaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const close = () => {
    if (!lock.current) onClose();
  };

  const logout = async () => {
    if (!auth || lock.current) return;
    lock.current = true;
    setLeaving(true);
    setFailed(false);
    try {
      await auth.logout();
    } catch {
      setFailed(true);
    } finally {
      lock.current = false;
      setLeaving(false);
    }
  };

  return <LessonSheet title="Đăng xuất" compact onClose={close}>
    <Text style={styles.body}>Em có muốn đăng xuất khỏi tài khoản này?</Text>
    {failed && <Text accessibilityRole="alert" style={styles.error}>Chưa đăng xuất được. Em thử lại nhé.</Text>}
    <AppButton title="Xác nhận đăng xuất" variant="danger" loading={leaving} loadingTitle="Đang đăng xuất…" onPress={() => { void logout(); }} />
    <AppButton title="Ở lại" variant="secondary" disabled={leaving} onPress={close} />
  </LessonSheet>;
}

const styles = StyleSheet.create({
  body: { fontFamily: FONTS.regular, fontSize: 15, lineHeight: 23, color: COLORS.textSecondary },
  error: { fontFamily: FONTS.semiBold, fontSize: 14, lineHeight: 21, color: COLORS.errorText },
});
