import { getApps, initializeApp } from '@firebase/app';
import { GoogleAuthProvider, browserPopupRedirectResolver, getAuth,
  initializeAuth, inMemoryPersistence, signInWithPopup, signOut } from '@firebase/auth';
import { firebaseConfig } from '../config/runtime';

export async function getGoogleCredential(): Promise<string> {
  const existing = getApps().find(app => app.name === 'mathvision-social');
  const auth = existing ? getAuth(existing) : initializeAuth(initializeApp(firebaseConfig, 'mathvision-social'), {
    persistence: inMemoryPersistence, popupRedirectResolver: browserPopupRedirectResolver,
  });
  const result = await signInWithPopup(auth, new GoogleAuthProvider());
  try {
    const credential = GoogleAuthProvider.credentialFromResult(result)?.idToken;
    if (!credential) throw new Error('Missing Google ID token');
    return credential;
  } finally {
    await signOut(auth).catch(() => {});
  }
}
