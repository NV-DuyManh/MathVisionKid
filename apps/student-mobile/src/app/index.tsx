import React, { useEffect, useContext } from 'react';
import { View, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../constants/theme';
import { AuthContext } from '../context/AuthContext';
import { BrandLockup } from '../components/ui/BrandLockup';
export default function SplashScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    useEffect(() => {
        if (auth?.isLoading) return;
        router.replace(auth?.isAuthenticated ? '/(tabs)' : '/login');
    }, [router, auth?.isAuthenticated, auth?.isLoading]);
    return (<View style={styles.container}>
      <BrandLockup />
    </View>);
}
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
        alignItems: 'center',
        justifyContent: 'center',
    },

});
