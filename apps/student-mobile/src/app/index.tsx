import React, { useEffect, useContext } from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS, FONTS } from '../constants/theme';
import { AuthContext } from '../context/AuthContext';
import { getAppBranding } from '../config/appConfig';
export default function SplashScreen() {
    const router = useRouter();
    const auth = useContext(AuthContext);
    const branding = getAppBranding();
    useEffect(() => {
        if (auth?.isLoading) return;
        router.replace(auth?.isAuthenticated ? '/(tabs)' : '/login');
    }, [router, auth?.isAuthenticated, auth?.isLoading]);
    return (<View style={styles.container}>
      <Image source={require('../../assets/illustrations/mathvision-star.png')} style={styles.icon} resizeMode="contain" accessible={false}/>
      <Text style={styles.title}>{branding.name}</Text>
      <Text style={styles.subtitle}>{branding.subtitle}</Text>

      {<Text style={styles.tagline}>{branding.tagline}</Text>}
    </View>);
}
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
        alignItems: 'center',
        justifyContent: 'center',
    },
    icon: {
        width: 160,
        height: 160,
        marginBottom: 16,
    },
    title: {
        fontSize: 32,
        fontFamily: FONTS.extraBold,
        color: COLORS.primaryDark,
        marginBottom: 8,
    },
    tagline: {
        fontSize: 16,
        color: COLORS.textSecondary,
        fontFamily: FONTS.medium,
    },
    subtitle: {
        fontSize: 16,
        color: COLORS.textPrimary,
        fontFamily: FONTS.semiBold,
        textAlign: 'center',
        marginBottom: 8,
        paddingHorizontal: 24,
    },
});
