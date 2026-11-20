import { usePathname, useRouter } from 'expo-router';
import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState, type ComponentRef, type PropsWithChildren } from 'react';
import { AppState, Keyboard, Modal, Platform, View } from 'react-native';
import { AuthContext } from '../../context/AuthContext';
import { readParentControlStatus } from './parentControlApi';
import { ParentProfilePinDialog } from './ParentModePreview';
import { clearParentModeSession, storeParentModeHandoff } from './parentModeHandoff';
import { StudentPauseScreen } from './StudentPauseScreen';

export const StudentGameAccess = createContext(true);
export const VerifyStudentGameAccess = createContext<() => Promise<boolean>>(async () => false);

const activityPath = /^\/(?:lessons|quiz\/[^/]+|learning\/[^/]+|camera|crop|preview|processing|recognition\/[^/]+|results\/[^/]+)(?:\/|$)/;
const keepRestOpen = () => {};

export function StudentDailyLimit({ children }: PropsWithChildren) {
  const auth = useContext(AuthContext);
  const owner = auth?.user?.id ?? auth?.user?.userId;
  const pathname = usePathname();
  const router = useRouter();
  const inParentMode = pathname === '/parent-mode';
  const activeOwner = auth?.isAuthenticated ? owner : undefined;
  const previousParentContext = useRef({ activeOwner, inParentMode });
  const [decision, setDecision] = useState<{ owner: string; blocked: boolean; verified: boolean }>();
  if (decision && decision.owner !== activeOwner) setDecision(undefined);
  const [showWebPin, setShowWebPin] = useState(false);
  const requestCurrentStatus = useRef<(() => Promise<boolean>) | undefined>(undefined);
  const content = useRef<ComponentRef<typeof View>>(null);
  const verify = useCallback(async () => requestCurrentStatus.current?.() ?? false, []);

  useLayoutEffect(() => {
    const previous = previousParentContext.current;
    if (Platform.OS === 'web' && (previous.activeOwner !== activeOwner || (previous.inParentMode && !inParentMode))) {
      clearParentModeSession();
    }
    previousParentContext.current = { activeOwner, inParentMode };
  }, [activeOwner, inParentMode]);

  useEffect(() => {
    if (!auth?.isAuthenticated || !owner) return;
    const lifetime = new AbortController();
    let pending: { version: number; result: Promise<boolean> } | undefined;
    let offlineVersion = 0;
    function markUnverified() {
      setDecision(previous => ({
        owner, blocked: previous !== undefined && previous.owner === owner && previous.blocked, verified: false,
      }));
    }
    function onOffline() {
      offlineVersion++;
      markUnverified();
    }
    async function read(version: number) {
      try {
        const status = await readParentControlStatus(lifetime.signal);
        if (lifetime.signal.aborted || version !== offlineVersion) return false;
        if (Platform.OS === 'web' && !navigator.onLine) {
          markUnverified();
          return false;
        }
        setDecision({ owner, blocked: status.dailyLimitReached, verified: status.activityVerified });
        return status.activityVerified && !status.dailyLimitReached;
      } catch {
        if (!lifetime.signal.aborted && version === offlineVersion) markUnverified();
        return false;
      }
    }
    function check() {
      if (lifetime.signal.aborted) return Promise.resolve(false);
      if (pending?.version === offlineVersion) return pending.result;
      const version = offlineVersion;
      const result = read(version).finally(() => {
        if (pending?.version === version) pending = undefined;
      });
      pending = { version, result };
      return result;
    }
    requestCurrentStatus.current = check;
    void check();
    const timer = setInterval(() => { if (AppState.currentState !== 'background') void check(); }, 5_000);
    const appState = AppState.addEventListener('change', state => { if (state === 'active') void check(); });
    if (Platform.OS === 'web') {
      window.addEventListener('offline', onOffline);
      window.addEventListener('online', check);
    }
    return () => {
      lifetime.abort();
      requestCurrentStatus.current = undefined;
      clearInterval(timer);
      appState.remove();
      if (Platform.OS === 'web') {
        window.removeEventListener('offline', onOffline);
        window.removeEventListener('online', check);
      }
    };
  }, [auth?.isAuthenticated, owner, inParentMode]);

  const current = owner && decision?.owner === owner ? decision : undefined;
  const blocked = auth?.isAuthenticated === true && current?.blocked === true;
  const mayPlay = !auth?.isAuthenticated || (current?.verified === true && !blocked);
  const showRest = blocked && !inParentMode;
  // Keep the route tree mounted so a pending answer remains in the current screen.
  // React Native Modal traps focus on web; inert also removes the backdrop from tab order.
  useLayoutEffect(() => {
    if (Platform.OS === 'web') {
      const backdrop = content.current as unknown as HTMLElement | null;
      if (backdrop) backdrop.inert = showRest;
    } else if (showRest) Keyboard.dismiss();
  }, [showRest]);

  return <StudentGameAccess.Provider value={mayPlay}>
    <VerifyStudentGameAccess.Provider value={verify}>
      <View ref={content} style={{ flex: 1, minHeight: 0 }} pointerEvents={showRest ? 'none' : 'auto'}
        aria-hidden={showRest || undefined} accessibilityElementsHidden={showRest}
        importantForAccessibility={showRest ? 'no-hide-descendants' : 'auto'}>
        {children}
      </View>
      {showRest && <Modal visible transparent animationType="none" onRequestClose={keepRestOpen} aria-labelledby="student-rest-heading">
        {Platform.OS === 'web' && showWebPin && owner ? (
          <ParentProfilePinDialog
            owner={owner}
            cancelLabel="Quay lại"
            onExit={() => setShowWebPin(false)}
            onOpen={settings => {
              storeParentModeHandoff(owner, settings);
              setShowWebPin(false);
              router.push('/parent-mode');
            }}
          />
        ) : (
          <StudentPauseScreen reason="daily-limit" working={activityPath.test(pathname)}
            onContinue={() => {
              if (Platform.OS === 'web') setShowWebPin(true);
              else router.push('/parent-mode');
            }}
            onLeave={() => { setShowWebPin(false); void auth?.logout(); }} />
        )}
      </Modal>}
    </VerifyStudentGameAccess.Provider>
  </StudentGameAccess.Provider>;
}
