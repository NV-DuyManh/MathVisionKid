import { initializeApp, getApps } from 'firebase/app';
import { FacebookAuthProvider, getAuth, signInWithPopup, signOut } from 'firebase/auth';

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY?.trim(),
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN?.trim(),
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID?.trim(),
  appId: import.meta.env.VITE_FIREBASE_APP_ID?.trim(),
};

export const facebookConfigured = Object.values(config).every(Boolean);

export async function getFacebookCredential(): Promise<string> {
  if (!facebookConfigured) throw new Error('FACEBOOK_NOT_CONFIGURED');
  const app = getApps()[0] ?? initializeApp(config);
  const result = await signInWithPopup(getAuth(app), new FacebookAuthProvider());
  return result.user.getIdToken();
}

export async function signOutFacebook(): Promise<void> {
  const app = getApps()[0];
  if (app) await signOut(getAuth(app));
}
