import React, { useContext, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Pressable,
  useWindowDimensions,
} from 'react-native';
import { FONTS, COLORS, SIZES, SHADOWS } from '../constants/theme';
import { AppButton } from '../components/ui/AppButton';
import { AuthContext } from '../context/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { BrandLockup } from '../components/ui/BrandLockup';
import { authApi } from '../services/api/authApi';

type Gender = 'MALE' | 'FEMALE' | 'OTHER' | 'PREFER_NOT_TO_SAY';
type AuthView = 'login' | 'register' | 'request-reset' | 'confirm-reset';

const genders: { value: Gender; label: string }[] = [
  { value: 'MALE', label: 'Nam' },
  { value: 'FEMALE', label: 'Nữ' },
  { value: 'OTHER', label: 'Khác' },
  { value: 'PREFER_NOT_TO_SAY', label: 'Không tiết lộ' },
];

export default function LoginScreen() {
  const { width } = useWindowDimensions();
  const wide = width >= 1000;
  const [authView, setAuthView] = useState<AuthView>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [gender, setGender] = useState<Gender>('PREFER_NOT_TO_SAY');
  const [gradeLevel, setGradeLevel] = useState(1);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const auth = useContext(AuthContext);
  const clearMessages = () => {
    setErrorMessage('');
    setSuccessMessage('');
  };

  const openView = (view: AuthView) => {
    setAuthView(view);
    clearMessages();
  };

  const handleLogin = async () => {
    if (!auth) return;
    if (!email.trim() || !password) {
      setErrorMessage('Vui lòng nhập đầy đủ email và mật khẩu.');
      return;
    }
    clearMessages();
    setLoading(true);
    try {
      await auth.login({ email: email.trim(), password });
    } catch (e: any) {
      let message = 'Lỗi kết nối máy chủ. Vui lòng kiểm tra và thử lại.';
      if (e.response?.status === 401) {
        message = 'Tài khoản hoặc mật khẩu không đúng. Vui lòng kiểm tra lại.';
      } else if (e.response?.status === 403) {
        message = 'Tài khoản chưa được phép đăng nhập. Vui lòng liên hệ thầy cô.';
      }
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    const cleanEmail = email.trim();
    const cleanName = displayName.trim();
    const cleanPhone = phoneNumber.trim();

    if (!cleanName || !cleanEmail || !registerPassword || !confirmPassword || !cleanPhone) {
      setErrorMessage('Vui lòng điền đầy đủ thông tin.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setErrorMessage('Email chưa đúng định dạng.');
      return;
    }
    if (registerPassword.length < 8 || registerPassword.length > 72) {
      setErrorMessage('Mật khẩu cần có từ 8 đến 72 ký tự.');
      return;
    }
    if (registerPassword !== confirmPassword) {
      setErrorMessage('Mật khẩu xác nhận chưa khớp.');
      return;
    }
    if (!/^[+0-9() .-]{7,32}$/.test(cleanPhone)) {
      setErrorMessage('Số điện thoại chưa đúng định dạng.');
      return;
    }

    clearMessages();
    setLoading(true);
    try {
      await authApi.register({
        email: cleanEmail,
        displayName: cleanName,
        password: registerPassword,
        role: 'STUDENT',
        gender,
        phoneNumber: cleanPhone,
        gradeLevel,
      });
      setPassword('');
      setRegisterPassword('');
      setConfirmPassword('');
      setAuthView('login');
      setSuccessMessage('Tạo tài khoản thành công. Em có thể đăng nhập ngay.');
    } catch (e: any) {
      if (e.response?.status === 409) {
        setErrorMessage('Email này đã được đăng ký. Hãy đăng nhập hoặc dùng email khác.');
      } else if (e.response?.status === 400) {
        setErrorMessage('Thông tin chưa hợp lệ. Hãy kiểm tra lại các mục đã nhập.');
      } else {
        setErrorMessage('Chưa tạo được tài khoản. Vui lòng thử lại sau.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRequestPasswordReset = async () => {
    const cleanEmail = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setErrorMessage('Vui lòng nhập email đã đăng ký hợp lệ.');
      return;
    }
    clearMessages();
    setLoading(true);
    try {
      await authApi.requestPasswordReset(cleanEmail);
      setAuthView('confirm-reset');
      setSuccessMessage('Nếu email đã đăng ký, mã xác nhận 6 số sẽ được gửi đến hộp thư đó.');
    } catch (error: any) {
      const errorCode = error.response?.data?.error?.code;
      setErrorMessage(errorCode === 'EMAIL_DELIVERY_FAILED'
        ? 'Dịch vụ email đang từ chối thông tin SMTP. Quản trị viên cần kiểm tra cấu hình gửi email.'
        : error.response?.status === 503
          ? 'Dịch vụ gửi email chưa được cấu hình đầy đủ. Hãy liên hệ quản trị viên.'
          : 'Chưa gửi được mã xác nhận. Hãy kiểm tra kết nối rồi thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmPasswordReset = async () => {
    if (!/^\d{6}$/.test(resetCode)) {
      setErrorMessage('Mã xác nhận phải gồm đúng 6 chữ số.');
      return;
    }
    if (newPassword.length < 8 || newPassword.length > 72) {
      setErrorMessage('Mật khẩu mới cần có từ 8 đến 72 ký tự.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setErrorMessage('Mật khẩu xác nhận chưa khớp.');
      return;
    }
    clearMessages();
    setLoading(true);
    try {
      await authApi.confirmPasswordReset(email.trim(), resetCode, newPassword);
      setAuthView('login');
      setPassword('');
      setResetCode('');
      setNewPassword('');
      setConfirmNewPassword('');
      setSuccessMessage('Đổi mật khẩu thành công. Hãy đăng nhập bằng mật khẩu mới.');
    } catch (error: any) {
      setErrorMessage(error.response?.status === 400
        ? 'Mã không đúng, đã hết hạn hoặc đã vượt số lần thử. Hãy yêu cầu mã mới.'
        : 'Chưa đổi được mật khẩu. Hãy thử lại sau.');
    } finally {
      setLoading(false);
    }
  };

  const field = (
    label: string,
    value: string,
    onChangeText: (text: string) => void,
    options: {
      placeholder: string;
      keyboardType?: 'default' | 'email-address' | 'phone-pad' | 'number-pad';
      secureTextEntry?: boolean;
      autoComplete?: 'name' | 'email' | 'tel' | 'new-password' | 'username' | 'password';
      autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
      maxLength?: number;
    },
  ) => (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={(text) => { onChangeText(text); if (errorMessage) setErrorMessage(''); }}
          placeholder={options.placeholder}
          placeholderTextColor={COLORS.textMuted}
          keyboardType={options.keyboardType || 'default'}
          secureTextEntry={options.secureTextEntry}
          autoCapitalize={options.autoCapitalize || (options.keyboardType === 'email-address' || options.secureTextEntry ? 'none' : 'words')}
          autoComplete={options.autoComplete}
          maxLength={options.maxLength}
          accessibilityLabel={label}
          accessibilityHint="Trường bắt buộc"
        />
      </View>
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={[styles.scrollContent, wide && styles.scrollWide]} keyboardShouldPersistTaps="handled">
        <View style={[styles.brandSection, wide && styles.brandWide]}>
          <BrandLockup compact />
          {wide ? <>
            <Text style={styles.welcomeTitle}>Mỗi bài toán,<Text style={{ color: '#7548EA' }}> một khám phá.</Text></Text>
            <Text style={styles.welcomeCopy}>Cùng Sao nhỏ hiểu đề, thử cách làm và tự tin tìm lời giải.</Text>
          </> : null}
        </View>
        <View style={styles.formColumn}>
          <View style={[styles.card, SHADOWS.small]}>
            <Text style={styles.title} accessibilityRole="header">
              {authView === 'login' ? 'Đăng nhập' : authView === 'register' ? 'Tạo tài khoản học sinh' : 'Khôi phục mật khẩu'}
            </Text>
            <Text style={styles.subtitle}>
              {authView === 'login' ? 'Cùng giải và kiểm tra bài toán hôm nay nhé!'
                : authView === 'register' ? 'Điền thông tin để bắt đầu hành trình học toán.'
                  : authView === 'request-reset' ? 'Nhận mã xác nhận 6 số qua email đã đăng ký.'
                    : 'Nhập mã trong email và đặt mật khẩu mới.'}
            </Text>

            {errorMessage ? (
              <View style={styles.errorBanner} accessible accessibilityRole="alert" accessibilityLiveRegion="assertive">
                <Ionicons name="alert-circle" size={20} color={COLORS.error} />
                <Text style={styles.errorText}>{errorMessage}</Text>
              </View>
            ) : null}
            {successMessage ? (
              <View style={styles.successBanner} accessible accessibilityRole="alert" accessibilityLiveRegion="polite">
                <Ionicons name="checkmark-circle" size={20} color={COLORS.success} />
                <Text style={styles.successText}>{successMessage}</Text>
              </View>
            ) : null}

            <View style={styles.form} accessibilityState={{ busy: loading }}>
              {authView === 'login' ? <>
                {field('Email', email, setEmail, { placeholder: 'Nhập email của em', keyboardType: 'email-address', autoComplete: 'username', maxLength: 255 })}
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Mật khẩu</Text>
                  <View style={styles.inputWrapper}>
                    <TextInput
                      style={[styles.input, styles.passwordInput]}
                      value={password}
                      onChangeText={(text) => { setPassword(text); if (errorMessage) setErrorMessage(''); }}
                      placeholder="Nhập mật khẩu của em"
                      placeholderTextColor={COLORS.textMuted}
                      secureTextEntry={!showPassword}
                      autoCapitalize="none"
                      autoComplete="password"
                      textContentType="password"
                      accessibilityLabel="Mật khẩu"
                    />
                    <TouchableOpacity style={styles.eyeButton} onPress={() => setShowPassword(!showPassword)} accessibilityRole="button" accessibilityLabel={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                      <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={22} color={COLORS.textSecondary} />
                    </TouchableOpacity>
                  </View>
                </View>
                <Pressable style={styles.forgotButton} onPress={() => openView('request-reset')} accessibilityRole="button">
                  <Text style={styles.switchText}>Quên mật khẩu?</Text>
                </Pressable>
                <AppButton title="Đăng nhập" onPress={handleLogin} loading={loading} disabled={loading} variant="primary" />
                <Pressable style={styles.switchButton} onPress={() => openView('register')} accessibilityRole="button">
                  <Text style={styles.switchText}>Chưa có tài khoản? Đăng ký</Text>
                </Pressable>
              </> : authView === 'register' ? <>
                {field('Họ và tên', displayName, setDisplayName, { placeholder: 'Tên của em', autoComplete: 'name', maxLength: 255 })}
                {field('Email đăng nhập', email, setEmail, { placeholder: 'ten@example.com', keyboardType: 'email-address', autoComplete: 'email', maxLength: 255 })}
                {field('Số điện thoại', phoneNumber, setPhoneNumber, { placeholder: 'Nhập số điện thoại', keyboardType: 'phone-pad', autoComplete: 'tel', maxLength: 32 })}

                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Vai trò</Text>
                  <View style={styles.readOnlyField} accessibilityLabel="Vai trò: Học sinh">
                    <Ionicons name="school-outline" size={20} color={COLORS.textSecondary} />
                    <Text style={styles.readOnlyText}>Học sinh</Text>
                  </View>
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.label} accessibilityRole="text">Khối lớp</Text>
                  <View style={styles.choiceRow} accessibilityLabel="Chọn khối lớp">
                    {[1, 2, 3, 4, 5].map((grade) => (
                      <Pressable key={grade} style={[styles.choice, gradeLevel === grade && styles.choiceSelected]} onPress={() => setGradeLevel(grade)} accessibilityRole="button" accessibilityLabel={`Lớp ${grade}`} accessibilityState={{ selected: gradeLevel === grade }}>
                        <Text style={[styles.choiceText, gradeLevel === grade && styles.choiceTextSelected]}>Lớp {grade}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.label} accessibilityRole="text">Giới tính</Text>
                  <View style={styles.choiceRow} accessibilityLabel="Chọn giới tính">
                    {genders.map((option) => (
                      <Pressable key={option.value} style={[styles.choice, gender === option.value && styles.choiceSelected]} onPress={() => setGender(option.value)} accessibilityRole="button" accessibilityLabel={option.label} accessibilityState={{ selected: gender === option.value }}>
                        <Text style={[styles.choiceText, gender === option.value && styles.choiceTextSelected]}>{option.label}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                {field('Mật khẩu', registerPassword, setRegisterPassword, { placeholder: 'Từ 8 đến 72 ký tự', secureTextEntry: true, autoComplete: 'new-password', maxLength: 72 })}
                {field('Nhập lại mật khẩu', confirmPassword, setConfirmPassword, { placeholder: 'Nhập lại mật khẩu', secureTextEntry: true, autoComplete: 'new-password', maxLength: 72 })}
                <Text style={styles.helperText}>Mật khẩu cần có ít nhất 8 ký tự.</Text>
                <AppButton title="Tạo tài khoản" onPress={handleRegister} loading={loading} disabled={loading} variant="primary" />
                <Pressable style={styles.switchButton} onPress={() => openView('login')} accessibilityRole="button">
                  <Text style={styles.switchText}>Đã có tài khoản? Đăng nhập</Text>
                </Pressable>
              </> : authView === 'request-reset' ? <>
                <Text style={styles.helperText}>Nhập email dùng để tạo tài khoản. Mã có hiệu lực trong 10 phút.</Text>
                {field('Email đăng ký', email, setEmail, { placeholder: 'ten@example.com', keyboardType: 'email-address', autoComplete: 'email', maxLength: 255 })}
                <AppButton title="Gửi mã xác nhận" onPress={handleRequestPasswordReset} loading={loading} disabled={loading} variant="primary" />
                <Pressable style={styles.switchButton} onPress={() => openView('login')} accessibilityRole="button">
                  <Text style={styles.switchText}>Quay lại đăng nhập</Text>
                </Pressable>
              </> : <>
                {field('Mã xác nhận 6 số', resetCode, setResetCode, { placeholder: '000000', keyboardType: 'number-pad', autoCapitalize: 'none', maxLength: 6 })}
                {field('Mật khẩu mới', newPassword, setNewPassword, { placeholder: 'Từ 8 đến 72 ký tự', secureTextEntry: true, autoComplete: 'new-password', maxLength: 72 })}
                {field('Nhập lại mật khẩu mới', confirmNewPassword, setConfirmNewPassword, { placeholder: 'Nhập lại mật khẩu mới', secureTextEntry: true, autoComplete: 'new-password', maxLength: 72 })}
                <AppButton title="Xác nhận và đổi mật khẩu" onPress={handleConfirmPasswordReset} loading={loading} disabled={loading} variant="primary" />
                <Pressable style={styles.switchButton} onPress={() => openView('request-reset')} accessibilityRole="button">
                  <Text style={styles.switchText}>Gửi lại mã</Text>
                </Pressable>
                <Pressable style={styles.switchButton} onPress={() => openView('login')} accessibilityRole="button">
                  <Text style={styles.switchText}>Quay lại đăng nhập</Text>
                </Pressable>
              </>}
            </View>
          </View>
          <View style={styles.footerNote}>
            <Text style={styles.footerText}>{authView === 'register' ? 'Thông tin của em được dùng để tạo tài khoản học tập.' : 'Tài khoản được xác minh bằng email và mã bảo mật.'}</Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { flexGrow: 1, padding: SIZES.large, justifyContent: 'center', maxWidth: 480, width: '100%', alignSelf: 'center' },
  scrollWide: { maxWidth: 1140, flexDirection: 'row', gap: 60, alignItems: 'center', padding: 44 },
  brandWide: { flex: 1, padding: 35, paddingVertical: 55, borderRadius: 35, backgroundColor: '#EEE7FC', minHeight: 530, justifyContent: 'center' },
  formColumn: { flex: 1, width: '100%', maxWidth: 460, alignSelf: 'center' },
  welcomeTitle: { fontFamily: FONTS.black, fontSize: 35, lineHeight: 45, color: COLORS.textPrimary, textAlign: 'center', marginTop: 35 },
  welcomeCopy: { fontFamily: FONTS.regular, fontSize: 17, lineHeight: 28, color: '#73618D', textAlign: 'center', marginTop: 18 },
  brandSection: { alignItems: 'center', marginBottom: SIZES.xlarge },
  card: { backgroundColor: COLORS.surface, borderRadius: SIZES.cardRadius, padding: SIZES.xlarge, borderWidth: 1, borderColor: COLORS.border },
  title: { fontSize: 22, fontFamily: FONTS.extraBold, color: COLORS.textPrimary, marginBottom: 4 },
  subtitle: { fontFamily: FONTS.regular, fontSize: 14, color: COLORS.textSecondary, marginBottom: SIZES.large },
  errorBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FEF2F2', borderColor: '#FECACA', borderWidth: 1, borderRadius: SIZES.inputRadius, padding: SIZES.medium, marginBottom: SIZES.large, gap: SIZES.small },
  errorText: { color: COLORS.errorText, fontSize: 14, fontFamily: FONTS.semiBold, flex: 1 },
  successBanner: { flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.successLight, borderColor: '#86EFAC', borderWidth: 1, borderRadius: SIZES.inputRadius, padding: SIZES.medium, marginBottom: SIZES.large, gap: SIZES.small },
  successText: { color: COLORS.success, fontSize: 14, fontFamily: FONTS.semiBold, flex: 1 },
  form: { width: '100%' },
  inputGroup: { marginBottom: SIZES.large },
  label: { fontSize: 14, fontFamily: FONTS.bold, color: COLORS.textPrimary, marginBottom: 8 },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F8FAFC', borderWidth: 1.5, borderColor: COLORS.border, borderRadius: SIZES.inputRadius, paddingHorizontal: SIZES.medium, minHeight: 52 },
  input: { flex: 1, minWidth: 0, fontFamily: FONTS.regular, fontSize: 16, color: COLORS.textPrimary, minHeight: 52 },
  passwordInput: { paddingRight: SIZES.small },
  eyeButton: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center' },
  readOnlyField: { minHeight: 52, borderRadius: SIZES.inputRadius, borderWidth: 1.5, borderColor: COLORS.border, backgroundColor: '#F8FAFC', paddingHorizontal: SIZES.medium, flexDirection: 'row', alignItems: 'center', gap: SIZES.small },
  readOnlyText: { fontFamily: FONTS.regular, fontSize: 16, color: COLORS.textSecondary },
  choiceRow: { flexDirection: 'row', flexWrap: 'wrap', gap: SIZES.small },
  choice: { minHeight: 44, minWidth: 62, paddingHorizontal: SIZES.medium, borderWidth: 1, borderColor: COLORS.border, borderRadius: SIZES.pillRadius, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surface },
  choiceSelected: { borderColor: COLORS.primary, backgroundColor: COLORS.primaryLight },
  choiceText: { fontFamily: FONTS.semiBold, color: COLORS.textSecondary, fontSize: 13 },
  choiceTextSelected: { color: COLORS.primaryDark },
  helperText: { fontFamily: FONTS.regular, fontSize: 12, color: COLORS.textSecondary, marginTop: -SIZES.medium, marginBottom: SIZES.large },
  switchButton: { minHeight: 48, alignItems: 'center', justifyContent: 'center', marginTop: SIZES.small },
  forgotButton: { minHeight: 44, alignItems: 'flex-end', justifyContent: 'center', marginBottom: SIZES.small },
  switchText: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark, textAlign: 'center' },
  footerNote: { marginTop: SIZES.xlarge, alignItems: 'center' },
  footerText: { fontFamily: FONTS.regular, fontSize: 13, color: COLORS.textSecondary, textAlign: 'center' },
});
