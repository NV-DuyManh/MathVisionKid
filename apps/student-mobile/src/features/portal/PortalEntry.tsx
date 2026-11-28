import React, { useContext, useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { BrandLockup } from '../../components/ui/BrandLockup';
import { COLORS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import PortalScreen from './PortalScreen';

export default function PortalEntry() {
  const router = useRouter();
  const auth = useContext(AuthContext);
  const isLoading = auth?.isLoading;
  const isAuthenticated = auth?.isAuthenticated;

  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace('/(tabs)');
  }, [router, isAuthenticated, isLoading]);

  if (!isLoading && !isAuthenticated) return <PortalScreen />;

  return (
    <View style={styles.container}>
      <BrandLockup />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
