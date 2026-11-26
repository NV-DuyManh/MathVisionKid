import { getApps, initializeApp } from '@firebase/app';
import { GoogleAuthProvider, browserPopupRedirectResolver, getAuth,
  initializeAuth, inMemoryPersistence, signInWithPopup, signOut } from '@firebase/auth';
import { firebaseConfig } from '../config/runtime';

export type GoogleCredential = { idToken: string; profileAccessToken?: string };

export async function getGoogleCredential(): Promise<GoogleCredential> {
  const existing = getApps().find(app => app.name === 'mathvision-social');
  const auth = existing ? getAuth(existing) : initializeAuth(initializeApp(firebaseConfig, 'mathvision-social'), {
    persistence: inMemoryPersistence, popupRedirectResolver: browserPopupRedirectResolver,
  });
  const result = await signInWithPopup(auth, new GoogleAuthProvider());
  try {
    const credential = GoogleAuthProvider.credentialFromResult(result);
    if (!credential?.idToken) throw new Error('Missing Google ID token');
    return { idToken: credential.idToken, profileAccessToken: credential.accessToken };
  } finally {
    await signOut(auth).catch(() => {});
  }
}
