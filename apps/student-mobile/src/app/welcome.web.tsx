import { useContext } from 'react';
import { Redirect } from 'expo-router';
import { AuthContext } from '../context/AuthContext';
import { useIsCompactStudentWeb } from '../components/ui/useIsCompactStudentWeb';
import WelcomeScreen from '../features/onboarding/WelcomeScreen';

export default function WebWelcomeRedirect() {
  const auth = useContext(AuthContext);
  const compactWeb = useIsCompactStudentWeb();
  if (compactWeb) return <WelcomeScreen />;
  if (!auth || auth.isLoading) return null;
  return <Redirect href={auth.isAuthenticated ? '/(tabs)' : '/login'} />;
}
