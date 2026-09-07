import React, { useState, useContext } from 'react';
import { View, Text, StyleSheet, TextInput, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { COLORS, SIZES } from '../constants/theme';
import { AppButton } from '../components/ui/AppButton';
import { AuthContext } from '../context/AuthContext';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const auth = useContext(AuthContext);

  const handleDemoLogin = async () => {
    if (!auth) return;
    try {
      await auth.login({ email, password });
    } catch (e: any) {
      console.log('Login error', e.response?.data || e.message);
      // MathVision uses friendly Vietnamese copy
      const message = e.response?.data?.message || "Lỗi kết nối máy chủ. Vui lòng thử lại.";
      Alert.alert("Không thể đăng nhập", message);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>Đăng nhập</Text>
          <Text style={styles.subtitle}>Cùng làm bài tập với MathVision nhé!</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email / Tài khoản</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="Nhập email của em"
              autoCapitalize="none"
              keyboardType="email-address"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Mật khẩu</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="Nhập mật khẩu"
              secureTextEntry
            />
          </View>

          <Text style={styles.forgotPassword}>Quên mật khẩu?</Text>
          
          <View style={styles.spacer} />
          
          <AppButton 
            title="Đăng nhập" 
            onPress={handleDemoLogin} 
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    padding: SIZES.large,
    justifyContent: 'center',
  },
  header: {
    marginBottom: SIZES.xxlarge,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: COLORS.primaryDark,
    marginBottom: SIZES.small,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  form: {
    width: '100%',
  },
  inputGroup: {
    marginBottom: SIZES.large,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  input: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: SIZES.medium,
    fontSize: 16,
    color: COLORS.textPrimary,
  },
  forgotPassword: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
    alignSelf: 'flex-end',
    marginTop: -8,
  },
  spacer: {
    height: SIZES.xlarge,
  },
  spacerSmall: {
    height: SIZES.medium,
  }
});
