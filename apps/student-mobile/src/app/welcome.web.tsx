import { useContext } from 'react';
import { Redirect } from 'expo-router';
import { AuthContext } from '../context/AuthContext';

export default function WebWelcomeRedirect() {
  const auth = useContext(AuthContext);
  if (!auth || auth.isLoading) return null;
  return <Redirect href={auth.isAuthenticated ? '/(tabs)' : '/login'} />;
}
