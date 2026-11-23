import React, { useEffect, useId, useRef, useState } from 'react';
import {
  ActivityIndicator,
  AppState,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { isAxiosError } from 'axios';
import { AppButton } from '../../components/ui/AppButton';
import { COLORS, FONTS } from '../../constants/theme';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { ParentOverview, formatDailyLimit, formatUsage, useUsageWeek } from './ParentOverview';
import {
  confirmParentPinCode,
  isParentGrantRejected,
  openParentMode,
  parentControlError,
  readParentControlStatus,
  readParentSettings,
  requestParentPinCode,
  type ParentPinPurpose,
  saveParentDailyLimit,
  saveParentGameLimit,
  type ParentSettings,
} from './parentControlApi';
import {
  clearParentModeSession,
  consumeParentModeHandoff,
  readParentModeSession,
  storeParentModeHandoff,
  updateParentModeSession,
} from './parentModeHandoff';

type Section = 'overview' | 'limits';
type LimitKind = 'total' | 'game';
const PIN_LENGTH = 6;
const LIMIT_PRESETS = [15, 30, 45, 60, 90, 120] as const;
const GAME_LIMIT_PRESETS = [5, 10, 15, 20, 30, 45] as const;
// Android's native accessibilityRole enum does not include the web status role.
function statusRole() {
  return Platform.OS === 'web' ? 'status' as const : undefined;
}
type InputInstance = React.ComponentRef<typeof TextInput>;

type ParentWorkspaceProps = { owner: string; onExit: () => void; onChooseLesson?: () => void };

export function ParentModePreview(props: ParentWorkspaceProps) {
  return <ParentWorkspace key={props.owner} {...props} />;
}

function ParentWorkspace({ owner, onExit, onChooseLesson }: ParentWorkspaceProps) {
  const web = Platform.OS === 'web';
  const [section, setSection] = useState<Section>('overview');
  const [settings, setSettings] = useState(() => consumeParentModeHandoff(owner) ?? readParentModeSession(owner));
  const [needsPin, setNeedsPin] = useState(false);
  const [savingLimit, setSavingLimit] = useState(false);
  const [limitKind, setLimitKind] = useState<LimitKind>('total');
  const [uncertainLimits, setUncertainLimits] = useState<Partial<Record<LimitKind, boolean>>>({});
  const scroll = useRef<React.ComponentRef<typeof ScrollView>>(null);
  const { width } = useWindowDimensions();
  const hasSettings = settings !== undefined;
  const grant = settings?.grant;

  useEffect(() => {
    if (!hasSettings && !needsPin) onExit();
  }, [hasSettings, needsPin, onExit]);

  useEffect(() => {
    if (!grant || savingLimit) return;
    const activeGrant = grant;
    const request = new AbortController();
    let fetching = false;
    async function refresh() {
      if (fetching || request.signal.aborted) return;
      if (Platform.OS === 'web' ? document.visibilityState === 'hidden' : AppState.currentState === 'background') return;
      fetching = true;
      try {
        const data = await readParentSettings(activeGrant, request.signal);
        if (request.signal.aborted) return;
        const latest = { ...data, grant };
        setSettings(latest);
        updateParentModeSession(owner, latest);
        setUncertainLimits({});
      } catch (cause) {
        if (!request.signal.aborted && isParentGrantRejected(cause)) {
          clearParentModeSession();
          setNeedsPin(true);
          setSettings(undefined);
        }
      } finally {
        fetching = false;
      }
    }
    void refresh();
    const timer = setInterval(refresh, 5000);
    const listener = AppState.addEventListener('change', state => { if (state === 'active') void refresh(); });
    if (web) document.addEventListener('visibilitychange', refresh);
    return () => {
      request.abort();
      clearInterval(timer);
      listener.remove();
      if (web) document.removeEventListener('visibilitychange', refresh);
    };
  }, [grant, savingLimit, owner, web]);

  function switchSection(next: Section) {
    setSection(next);
    scroll.current?.scrollTo({ y: 0, animated: false });
  }

  function exitWorkspace() {
    clearParentModeSession();
    onExit();
  }

  if (!settings) {
    return (
      <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
        {needsPin ? (
          <ParentProfilePinDialog owner={owner} notice="Phiên phụ huynh đã hết hạn. Nhập lại mã PIN để tiếp tục."
            onExit={exitWorkspace} onOpen={updated => {
              storeParentModeHandoff(owner, updated);
              consumeParentModeHandoff(owner);
              setSettings(updated);
              setNeedsPin(false);
            }} />
        ) : (
          <View style={styles.webRedirectCenter}>
            <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang quay lại hồ sơ" />
          </View>
        )}
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.screen, web && styles.webScreen]} edges={['top', 'bottom']}>
      <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.workspace}>
          <ScrollView
            ref={scroll}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={[
              styles.page,
              width >= 700 && styles.pageWide,
              web && width >= 700 && styles.pageWebWide,
            ]}
          >
            <View style={styles.toolbar}>
              <AppButton
                title="Quay lại"
                variant="secondary"
                style={styles.toolbarAction}
                onPress={exitWorkspace}
                icon={<Ionicons name="arrow-back" size={18} color={COLORS.primaryDark} accessible={false} aria-hidden />}
              />
              <AppButton
                title="Khóa"
                accessibilityLabel="Khóa Góc phụ huynh"
                variant="outlined"
                style={styles.lockAction}
                textStyle={styles.lockActionText}
                onPress={exitWorkspace}
                icon={<Ionicons name="lock-closed-outline" size={17} color={STUDENT_WEB.primary} accessible={false} aria-hidden />}
              />
            </View>

            <View style={[styles.headerRow, width >= 760 && styles.headerRowWide]}>
              <View style={styles.pageHeader}>
                <View style={styles.headerIcon}>
                  <Ionicons name="shield-checkmark-outline" size={24} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
                </View>
                <View style={styles.headerCopy}>
                  <Text accessibilityRole="header" aria-level={1} style={styles.title}>
                    Góc phụ huynh
                  </Text>
                  <Text style={styles.subtitle}>Theo dõi tiến độ học tập và thời gian sử dụng an toàn</Text>
                </View>
              </View>

              <View style={[styles.segment, width >= 760 && styles.segmentWide]}>
                <SelectionButton
                  label="Tổng quan"
                  icon="grid-outline"
                  selected={section === 'overview'}
                  disabled={savingLimit}
                  onPress={() => switchSection('overview')}
                />
                <SelectionButton
                  label="Giới hạn"
                  icon="time-outline"
                  selected={section === 'limits'}
                  disabled={savingLimit}
                  onPress={() => switchSection('limits')}
                />
              </View>
            </View>

            {section === 'overview' ? (
              <ParentOverview
                owner={owner}
                dailyMinutes={settings.dailyMinutes}
                limitUncertain={uncertainLimits.total === true}
                onChooseLesson={onChooseLesson ? () => {
                  clearParentModeSession();
                  onChooseLesson();
                } : undefined}
                onEditLimit={() => {
                  setLimitKind('total');
                  switchSection('limits');
                }}
              />
            ) : (
              <>
                <View style={styles.segment} role="group" accessibilityLabel="Loại thời gian cần giới hạn">
                  <SelectionButton
                    label="Tổng thời gian"
                    icon="time-outline"
                    selected={limitKind === 'total'}
                    disabled={savingLimit}
                    onPress={() => setLimitKind('total')}
                  />
                  <SelectionButton
                    label="Chơi trò chơi"
                    icon="game-controller-outline"
                    selected={limitKind === 'game'}
                    disabled={savingLimit}
                    onPress={() => setLimitKind('game')}
                  />
                </View>
                {limitKind === 'game' && settings.gameMinutes === undefined ? (
                  <View style={styles.surface}>
                    <Text accessibilityRole="alert" style={styles.body}>Chưa tải được cài đặt thời gian chơi trò chơi.</Text>
                  </View>
                ) : (
                  <DailyUsageLimit
                    key={limitKind}
                    kind={limitKind}
                    minutes={limitKind === 'game' ? settings.gameMinutes ?? null : settings.dailyMinutes}
                    limitUncertain={uncertainLimits[limitKind] === true}
                    onSaving={setSavingLimit}
                    onUncertain={() => setUncertainLimits(previous => ({ ...previous, [limitKind]: true }))}
                    onSave={updated => {
                      const confirmed = { ...settings, ...updated };
                      setSettings(confirmed);
                      updateParentModeSession(owner, confirmed);
                      setUncertainLimits(previous => updated.gameMinutes === undefined && previous.game ? { game: true } : {});
                    }}
                  />
                )}
              </>
            )}
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function keepDialogFocus(event: any, onExit?: () => void) {
  const key = event.nativeEvent?.key;
  if (key === 'Escape') {
    onExit?.();
    return;
  }
  if (key !== 'Tab') return;
  const dialog = event.currentTarget.querySelector('[role="dialog"]');
  const controls = dialog?.querySelectorAll(
    'button:not([disabled]), input:not([disabled]), [role="button"]:not([aria-disabled="true"])',
  );
  if (!controls?.length) return;
  const first = controls[0] as HTMLElement;
  const last = controls[controls.length - 1] as HTMLElement;
  if (event.nativeEvent.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.nativeEvent.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function PinModal({ children, title, label = title, onExit, busy = false, embedded = false }: {
  children: React.ReactNode;
  title: string;
  label?: string;
  onExit: () => void;
  busy?: boolean;
  embedded?: boolean;
}) {
  const web = Platform.OS === 'web';
  const dialogRef = useRef<React.ComponentRef<typeof View>>(null);
  const close = () => { if (!busy) onExit(); };
  useEffect(() => {
    if (!web || typeof document === 'undefined') return;
    const previous = document.activeElement as HTMLElement | null;
    const frame = requestAnimationFrame(() => {
      const dialog = dialogRef.current as unknown as HTMLElement | null;
      if (!dialog?.contains(document.activeElement)) dialog?.focus();
    });
    return () => {
      cancelAnimationFrame(frame);
      if (previous?.isConnected && document.activeElement === document.body) previous.focus();
    };
  }, [web]);

  const card = (
    <View ref={dialogRef} tabIndex={web ? -1 : undefined} accessibilityRole={web ? 'dialog' : undefined} accessibilityViewIsModal
      accessibilityLabel={label} aria-modal aria-busy={busy} style={[styles.surface, styles.pinDialog]}>
      <View style={styles.pinDialogHeader}>
        <View style={styles.headerIcon}>
          <Ionicons name="shield-checkmark-outline" size={22} color={COLORS.primaryDark} accessible={false} aria-hidden />
        </View>
        <Text accessibilityRole="header" aria-level={2} style={[styles.heading, styles.headerCopy]}>{title}</Text>
      </View>
      {children}
    </View>
  );
  if (web) {
    const content = (
      <View style={styles.pinScrim} testID="parent-pin-scrim"
        onKeyDown={embedded ? (event: any) => keepDialogFocus(event, close) : undefined}>
        {card}
      </View>
    );
    return embedded ? content : <Modal transparent visible onRequestClose={close}>{content}</Modal>;
  }
  const content = (
    <KeyboardAvoidingView style={styles.nativePinKeyboard} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.nativePinScrim}>
        {card}
      </ScrollView>
    </KeyboardAvoidingView>
  );
  return embedded ? content : <Modal transparent visible onRequestClose={close}>{content}</Modal>;
}

export function ParentProfilePinDialog({
  owner, notice, embedded, cancelLabel = 'Quay lại hồ sơ', onExit, onOpen,
}: {
  owner: string;
  notice?: string;
  embedded?: boolean;
  cancelLabel?: string;
  onExit: () => void;
  onOpen: (settings: ParentSettings) => void;
}) {
  const [recoveryPurpose, setRecoveryPurpose] = useState<ParentPinPurpose>();
  const [pinChanged, setPinChanged] = useState(false);
  const [status, setStatus] = useState<'loading' | 'unavailable' | 'unconfigured' | 'unlock'>('loading');
  const [retry, setRetry] = useState(0);
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const pending = useRef<AbortController | undefined>(undefined);
  const pinInput = useRef<InputInstance>(null);
  const web = Platform.OS === 'web';

  useEffect(() => {
    const request = new AbortController();
    void readParentControlStatus(request.signal)
      .then(value => {
        if (!request.signal.aborted) setStatus(value.pinConfigured ? 'unlock' : 'unconfigured');
      })
      .catch(() => {
        if (!request.signal.aborted) setStatus('unavailable');
      });
    return () => request.abort();
  }, [owner, retry]);
  useEffect(() => () => pending.current?.abort(), [owner]);

  async function submit(candidate = pin) {
    if (pending.current || status !== 'unlock') return;
    if (candidate.length !== PIN_LENGTH) {
      setError('Nhập đủ 6 chữ số của mã PIN.');
      pinInput.current?.focus();
      return;
    }
    const request = new AbortController();
    pending.current = request;
    setError(undefined);
    setBusy(true);
    try {
      const updated = await openParentMode(candidate, false, request.signal);
      if (!request.signal.aborted) onOpen(updated);
    } catch (cause) {
      if (!request.signal.aborted) setError(parentControlError(cause));
    } finally {
      pending.current = undefined;
      if (!request.signal.aborted) {
        setPin('');
        setBusy(false);
      }
    }
  }

  if (recoveryPurpose) {
    return <ParentPinRecovery purpose={recoveryPurpose} embedded={embedded}
      onBack={() => setRecoveryPurpose(undefined)}
      onFinish={() => {
        setRecoveryPurpose(undefined);
        setPinChanged(true);
        setStatus('unlock');
      }} />;
  }

  return (
    <PinModal title={status === 'unlock' ? 'Nhập mã PIN' : 'Góc phụ huynh'} label="Mở Góc phụ huynh" onExit={onExit} busy={busy} embedded={embedded}>
      {(pinChanged || notice) && <Text accessibilityRole={statusRole()} accessibilityLiveRegion="polite" style={styles.body}>
        {pinChanged ? 'Đã lưu mã PIN mới. Nhập PIN mới để mở Góc phụ huynh.' : notice}
      </Text>}
      {status === 'unlock' && (
        <>
          <PinCells label="Mã PIN" inputRef={pinInput} value={pin} disabled={busy} error={error}
            onSubmit={() => void submit()}
            onChange={value => {
              setPin(value);
              setError(undefined);
              if (web && value.length === PIN_LENGTH) void submit(value);
            }} />
          {!web && <AppButton title="Mở Góc phụ huynh" onPress={() => void submit()} loading={busy} />}
          <AppButton title="Quên mã PIN?" variant="ghost" disabled={busy} onPress={() => {
            setPin('');
            setError(undefined);
            setRecoveryPurpose('RESET');
          }} />
        </>
      )}
      {status === 'loading' && <ActivityIndicator accessibilityLabel="Đang kiểm tra mã PIN" />}
      {status === 'unconfigured' && (
        <>
          <Text accessibilityRole={statusRole()} accessibilityLiveRegion="polite" style={styles.body}>
            Tài khoản chưa có mã PIN. Xác nhận email của tài khoản để thiết lập mã PIN cho Góc phụ huynh.
          </Text>
          <AppButton title="Thiết lập mã PIN" onPress={() => setRecoveryPurpose('SETUP')} />
        </>
      )}
      {status === 'unavailable' && (
        <>
          <Text accessibilityRole="alert" style={styles.error}>Chưa kết nối được với tài khoản.</Text>
          <AppButton title="Thử lại" variant="secondary" onPress={() => {
            setStatus('loading');
            setRetry(value => value + 1);
          }} />
        </>
      )}
      <AppButton title={cancelLabel} variant="ghost" disabled={busy} onPress={onExit} />
    </PinModal>
  );
}

function ParentPinRecovery({ purpose, embedded, onBack, onFinish }: {
  purpose: ParentPinPurpose;
  embedded?: boolean;
  onBack: () => void;
  onFinish: () => void;
}) {
  const [maskedEmail, setMaskedEmail] = useState<string>();
  const [code, setCode] = useState('');
  const [pin, setPin] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const request = useRef<AbortController | undefined>(undefined);
  const codeInput = useRef<InputInstance>(null);
  const pinInput = useRef<InputInstance>(null);
  const confirmationInput = useRef<InputInstance>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function perform(action: (signal: AbortSignal) => Promise<void>) {
    if (request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setError('');
    setBusy(true);
    try {
      await action(controller.signal);
    } catch (cause) {
      if (!controller.signal.aborted) setError(parentControlError(cause));
    } finally {
      request.current = undefined;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  function send() {
    void perform(async signal => {
      const result = await requestParentPinCode(purpose, signal);
      if (signal.aborted) return;
      setMaskedEmail(result.maskedEmail);
      setCode('');
    });
  }

  function submit() {
    if (code.length !== PIN_LENGTH || pin.length !== PIN_LENGTH || confirmation.length !== PIN_LENGTH) {
      setError('Nhập đủ 6 chữ số cho mã xác nhận và mỗi ô PIN.');
      return;
    }
    if (pin !== confirmation) {
      setError('Hai mã PIN chưa giống nhau.');
      confirmationInput.current?.focus();
      return;
    }
    void perform(async signal => {
      await confirmParentPinCode(purpose, code, pin, signal);
      if (!signal.aborted) onFinish();
    });
  }

  return (
    <PinModal title={purpose === 'SETUP' ? 'Thiết lập mã PIN' : 'Đặt lại mã PIN'} embedded={embedded} onExit={onBack} busy={busy}>
      {maskedEmail ? (
        <>
          <Text accessibilityLiveRegion="polite" style={styles.body}>
            Mã xác nhận đã được gửi đến {maskedEmail}. Mã có hiệu lực trong 10 phút.
          </Text>
          <PinCells label="Mã xác nhận từ email" inputRef={codeInput} value={code} disabled={busy} onChange={setCode} />
          <PinCells label="Mã PIN mới" inputRef={pinInput} value={pin} disabled={busy} onChange={setPin} />
          <PinCells label="Nhập lại mã PIN mới" inputRef={confirmationInput} value={confirmation}
            disabled={busy} onChange={setConfirmation} onSubmit={submit} />
          <AppButton title="Lưu mã PIN mới" onPress={submit} loading={busy} />
          <AppButton title="Gửi lại mã" variant="ghost" disabled={busy} onPress={send} />
        </>
      ) : (
        <>
          <Text style={styles.body}>Hệ thống sẽ gửi mã xác nhận tới email đã đăng ký của tài khoản này.</Text>
          <AppButton title="Gửi mã xác nhận" onPress={send} loading={busy} />
        </>
      )}
      {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
      <AppButton title="Quay lại" variant="ghost" disabled={busy} onPress={onBack} />
    </PinModal>
  );
}

type IconName = React.ComponentProps<typeof Ionicons>['name'];
function SelectionButton({
  label,
  icon,
  selected,
  onPress,
  choice,
  disabled,
}: {
  label: string;
  icon: IconName;
  selected: boolean;
  onPress: () => void;
  choice?: boolean;
  disabled?: boolean;
}) {
  const color = selected ? STUDENT_WEB.primary : COLORS.textSecondary;
  return (
    <Pressable
      accessibilityLabel={label}
      accessibilityRole="button"
      accessibilityState={{ selected, disabled }}
      aria-pressed={selected}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.selection,
        choice && styles.choice,
        selected && styles.selected,
        pressed && styles.pressed,
      ]}
    >
      <Ionicons name={icon} size={19} color={color} accessible={false} aria-hidden />
      <Text style={[styles.selectionLabel, { color }]}>{label}</Text>
    </Pressable>
  );
}

type FormError = { field: 'pin' | 'duration' | 'request'; message: string };
function PinCells({
  label,
  inputRef,
  value,
  disabled,
  error,
  onChange,
  onSubmit,
}: {
  label: string;
  inputRef: React.Ref<InputInstance>;
  value: string;
  disabled?: boolean;
  error?: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const errorId = useId();
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View testID="pin-cells" style={styles.pinCells}>
        {Array.from({ length: PIN_LENGTH }, (_, index) => (
          <View
            key={index}
            testID="pin-cell"
            style={[
              styles.pinCell,
              focused && index === Math.min(value.length, PIN_LENGTH - 1) && styles.pinCellActive,
              !!error && styles.pinCellError,
            ]}
          >
            <Text style={styles.pinCellText}>{value[index] ? '•' : ''}</Text>
          </View>
        ))}
        <TextInput
          ref={inputRef}
          testID={`pin-input-${label}`}
          accessibilityLabel={label}
          accessibilityHint="Nhập đủ 6 chữ số. Mã PIN sẽ được ẩn."
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          autoCapitalize="none"
          autoCorrect={false}
          autoComplete="off"
          inputMode="numeric"
          maxLength={PIN_LENGTH}
          onSubmitEditing={onSubmit}
          secureTextEntry
          editable={!disabled}
          value={value}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChangeText={text => onChange(text.replace(/[^0-9]/g, '').slice(0, PIN_LENGTH))}
          style={styles.pinCellInput}
        />
      </View>
      {!!error && (
        <Text nativeID={errorId} accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      )}
    </View>
  );
}

function DailyUsageLimit({
  kind,
  minutes,
  limitUncertain,
  onSaving,
  onUncertain,
  onSave,
}: {
  kind: LimitKind;
  minutes: number | null;
  limitUncertain: boolean;
  onSaving: (value: boolean) => void;
  onUncertain: () => void;
  onSave: (value: ParentSettings) => void;
}) {
  const [draft, setDraft] = useState<{ limited: boolean; value: string; base: number | null }>();
  const limited = draft?.limited ?? minutes !== null;
  const value = draft?.value ?? minutes?.toString() ?? '';
  const [pin, setPin] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<{ minutes: number | null }>();
  const [error, setError] = useState<FormError>();
  const pending = useRef<AbortController | undefined>(undefined);
  const durationInput = useRef<InputInstance>(null);
  const pinInput = useRef<InputInstance>(null);
  const usage = useUsageWeek();
  const { width } = useWindowDimensions();
  const desktop = width >= 900;
  const game = kind === 'game';
  const next = limited ? Number(value) : null;
  const changed = next !== minutes;
  useEffect(() => () => pending.current?.abort(), []);

  const todayEntry = usage.week?.days.find(day => day.date === usage.week?.today);
  const elapsedMillis = game ? todayEntry?.gameElapsedMillis : todayEntry?.elapsedMillis;
  const limitMillis = minutes === null ? null : minutes * 60_000;
  const activeProgress = limitMillis !== null && elapsedMillis !== undefined ? Math.min(100, elapsedMillis / limitMillis * 100) : 0;
  const remainingMillis = limitMillis === null || elapsedMillis === undefined ? null : Math.max(0, limitMillis - elapsedMillis);

  function edit() {
    setConfirming(false);
    setPin('');
    setError(undefined);
    setSaved(undefined);
  }

  function applyMinutes(nextMinutes: number) {
    const clamped = Math.max(1, Math.min(1440, nextMinutes));
    setDraft({ limited: true, value: String(clamped), base: minutes });
    edit();
  }

  function adjustMinutes(delta: number) {
    const base = Number(value) || minutes || 30;
    applyMinutes(base + delta);
  }

  function confirm() {
    if (!changed || pending.current) return;
    if (next !== null && (next < 1 || next > 1440)) {
      setError({ field: 'duration', message: 'Nhập từ 1 đến 1.440 phút mỗi ngày.' });
      durationInput.current?.focus();
      return;
    }
    setError(undefined);
    setConfirming(true);
  }

  async function save() {
    if (!confirming || pending.current) return;
    if (pin.length !== PIN_LENGTH) {
      setError({ field: 'pin', message: 'Nhập mã PIN 6 chữ số để lưu giới hạn.' });
      pinInput.current?.focus();
      return;
    }
    const request = new AbortController();
    pending.current = request;
    setBusy(true);
    onSaving(true);
    setError(undefined);
    try {
      const saveLimit = game ? saveParentGameLimit : saveParentDailyLimit;
      const updated = await saveLimit(pin, next, request.signal);
      if (request.signal.aborted) return;
      const savedMinutes = game ? updated.gameMinutes : updated.dailyMinutes;
      if (savedMinutes === undefined) throw new Error('Missing saved limit');
      onSave(updated);
      setDraft(undefined);
      setConfirming(false);
      setSaved({ minutes: savedMinutes });
    } catch (cause) {
      if (!request.signal.aborted) {
        const status = isAxiosError(cause) ? cause.response?.status : undefined;
        const mayHaveSaved = status === undefined || status === 408 || status >= 500;
        if (mayHaveSaved) onUncertain();
        setError({
          field: 'request',
          message: mayHaveSaved
            ? 'Chưa xác nhận được giới hạn mới. Kiểm tra kết nối rồi thử lưu lại.'
            : parentControlError(cause),
        });
      }
    } finally {
      pending.current = undefined;
      if (!request.signal.aborted) {
        setPin('');
        setBusy(false);
        onSaving(false);
      }
    }
  }

  const parsedTarget = changed && next !== null && next >= 1 && next <= 1440 ? next : null;
  const remainingTarget = parsedTarget !== null && elapsedMillis !== undefined ? Math.max(0, parsedTarget * 60_000 - elapsedMillis) : null;

  return (
    <View style={[styles.limitGrid, desktop && styles.limitGridWide]}>
      <View style={[styles.surface, desktop && styles.limitMainColumnWide]} aria-busy={busy}>
        <View style={styles.limitHeaderRow}>
          <View style={styles.limitHeaderIcon}>
            <Ionicons name={game ? 'game-controller-outline' : 'hourglass-outline'} size={24} color="#146448" accessible={false} aria-hidden />
          </View>
          <View style={styles.headerCopy}>
            <Text accessibilityRole="header" aria-level={2} style={styles.heading}>
              {game ? 'Giới hạn chơi trò chơi' : 'Giới hạn thời gian'}
            </Text>
            <Text style={styles.body}>{game
              ? 'Tính thời gian mở màn hình chơi trên web và ứng dụng. Thời gian chơi nằm trong tổng thời gian sử dụng.'
              : 'Tính chung thời gian học, làm Quiz và chơi trên web và ứng dụng.'}</Text>
          </View>
        </View>

        <View style={[styles.current, minutes === null && styles.currentUnlimited]}>
          <View style={styles.headerCopy}>
            <Text style={styles.currentLabel}>{limitUncertain ? 'Giới hạn xác nhận gần nhất' : 'Đang áp dụng'}</Text>
            <Text style={styles.settingValue}>{formatDailyLimit(minutes)}</Text>
          </View>
          <View style={[styles.statusBadge, minutes !== null ? styles.statusBadgeOn : styles.statusBadgeOff]}>
            <Text style={[styles.statusBadgeText, minutes !== null ? styles.statusBadgeTextOn : styles.statusBadgeTextOff]}>
              {limitUncertain ? 'Chưa xác nhận' : minutes !== null ? 'Đang bật' : 'Mở tự do'}
            </Text>
          </View>
        </View>

        <View style={styles.modeRow} role="group" accessibilityLabel="Cách giới hạn thời gian">
          <SelectionButton
            label="Giới hạn mỗi ngày"
            icon={limited ? 'radio-button-on-outline' : 'radio-button-off-outline'}
            choice
            selected={limited}
            disabled={busy}
            onPress={() => {
              setDraft({ limited: true, value, base: minutes });
              edit();
            }}
          />
          <SelectionButton
            label="Không giới hạn"
            icon={!limited ? 'radio-button-on-outline' : 'radio-button-off-outline'}
            choice
            selected={!limited}
            disabled={busy}
            onPress={() => {
              setDraft({ limited: false, value, base: minutes });
              edit();
            }}
          />
        </View>

        {!limited && changed && !confirming && (
          <Text style={styles.body}>Giới hạn hiện tại vẫn áp dụng cho đến khi bạn lưu bằng PIN.</Text>
        )}
        {limited && (
          <View style={styles.durationSection}>
            <View style={styles.durationInputRow}>
              <View style={styles.durationInputCol}>
                <NumericField
                  label={game ? 'Số phút chơi trò chơi mỗi ngày' : 'Số phút dùng app mỗi ngày'}
                  visibleLabel="Thời gian mỗi ngày (phút)"
                  inputRef={durationInput}
                  value={value}
                  disabled={busy}
                  error={error?.field === 'duration' ? error.message : undefined}
                  onChange={nextValue => {
                    setDraft({ limited: true, value: nextValue, base: minutes });
                    edit();
                  }}
                  onSubmit={confirm}
                />
              </View>
              <View style={styles.stepperGroup}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Giảm 5 phút"
                  disabled={busy}
                  onPress={() => adjustMinutes(-5)}
                  style={({ pressed }) => [styles.stepperBtn, pressed && styles.pressed]}
                >
                  <Text style={styles.stepperText}>-5p</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Tăng 5 phút"
                  disabled={busy}
                  onPress={() => adjustMinutes(5)}
                  style={({ pressed }) => [styles.stepperBtn, pressed && styles.pressed]}
                >
                  <Text style={styles.stepperText}>+5p</Text>
                </Pressable>
              </View>
            </View>

            <View style={styles.presetBlock}>
              <Text style={styles.presetHeading}>Chọn nhanh mức phổ biến</Text>
              <View style={styles.presetRow}>
                {(game ? GAME_LIMIT_PRESETS : LIMIT_PRESETS).map(preset => {
                  const selected = Number(value) === preset;
                  return (
                    <Pressable
                      key={preset}
                      accessibilityRole="button"
                      accessibilityLabel={`Chọn ${preset} phút mỗi ngày`}
                      accessibilityState={{ selected, disabled: busy }}
                      disabled={busy}
                      onPress={() => applyMinutes(preset)}
                      style={({ pressed }) => [
                        styles.presetChip,
                        selected && styles.presetChipSelected,
                        pressed && styles.pressed,
                      ]}
                    >
                      <Text style={[styles.presetChipText, selected && styles.presetChipTextSelected]}>
                        {preset} phút
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>

            {remainingTarget !== null && (
              <View
                style={[
                  styles.impactBanner,
                  remainingTarget === 0 ? styles.impactBannerWarn : styles.impactBannerSafe,
                ]}
              >
                <Ionicons
                  name={remainingTarget === 0 ? 'alert-circle-outline' : 'checkmark-circle-outline'}
                  size={18}
                  color={remainingTarget === 0 ? '#92400E' : '#166534'}
                  accessible={false}
                  aria-hidden
                />
                <Text style={[styles.impactText, remainingTarget === 0 ? styles.impactTextWarn : styles.impactTextSafe]}>
                  {remainingTarget === 0
                    ? (game ? 'Với mức này, con đã hết thời gian chơi hôm nay.' : 'Với mức này, con đã hết tổng thời gian hôm nay.')
                    : `Với mức này, còn ${formatUsage(remainingTarget)} ${game ? 'chơi trò chơi' : 'sử dụng'} hôm nay.`}
                </Text>
              </View>
            )}
          </View>
        )}

        {draft && draft.base !== minutes && (
          <Text accessibilityRole={statusRole()} accessibilityLiveRegion="polite" style={styles.body}>
            Giới hạn trên tài khoản vừa thay đổi. Lựa chọn đang chỉnh sửa vẫn được giữ.
          </Text>
        )}
        {saved && saved.minutes === minutes && (
          <View style={styles.successBanner}>
            <Ionicons name="checkmark-circle" size={20} color="#166534" accessible={false} aria-hidden />
            <Text accessibilityRole={statusRole()} accessibilityLiveRegion="polite" style={styles.successText}>
              Đã lưu giới hạn trên tài khoản. Mức mới: {formatDailyLimit(minutes)}.
            </Text>
          </View>
        )}
        {changed && <AppButton title="Xác nhận thay đổi" disabled={busy} onPress={confirm} />}
        {confirming && (
          <PinModal title="Xác nhận bằng mã PIN" onExit={edit} busy={busy}>
            <Text style={styles.body}>{game ? 'Thời gian chơi trò chơi' : 'Tổng thời gian sử dụng'} · {formatDailyLimit(next)}</Text>
            <PinCells label="Mã PIN để lưu" inputRef={pinInput} value={pin} disabled={busy}
              error={error?.field === 'pin' || error?.field === 'request' ? error.message : undefined}
              onSubmit={() => void save()}
              onChange={nextPin => {
                setPin(nextPin);
                setError(undefined);
              }} />
            <AppButton title="Lưu giới hạn" onPress={() => void save()} loading={busy} loadingTitle="Đang lưu giới hạn…" />
            <AppButton title="Hủy xác nhận" variant="ghost" disabled={busy} onPress={edit} />
          </PinModal>
        )}
      </View>

      <View style={[styles.limitSideColumn, desktop && styles.limitSideColumnWide]}>
        <View style={styles.surface}>
          <View style={styles.limitHeaderRow}>
            <View style={[styles.limitHeaderIcon, styles.limitSideIcon]}>
              <Ionicons name="pulse-outline" size={22} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
            </View>
            <View style={styles.headerCopy}>
              <Text accessibilityRole="header" aria-level={3} style={styles.sideHeading}>
                Theo dõi hôm nay
              </Text>
              <Text style={styles.body}>{game ? 'Thời gian chơi trên web và ứng dụng' : 'Tổng thời gian sử dụng'}</Text>
            </View>
          </View>

          {usage.failed || (usage.week && elapsedMillis === undefined) ? (
            <View style={styles.sideNotice}>
              <Text style={styles.body}>Chưa tải được thời gian hôm nay.</Text>
              <AppButton title="Tải lại" variant="secondary" onPress={usage.retry} />
            </View>
          ) : elapsedMillis !== undefined ? (
            <View style={styles.todayMeterCard}>
              <View style={styles.todayMeterTop}>
                <Text style={styles.todayMeterValue}>{formatUsage(elapsedMillis)}</Text>
                {!limitUncertain && <Text style={styles.todayMeterCap}>
                  {minutes !== null ? `/ ${minutes} phút` : 'Không giới hạn'}
                </Text>}
              </View>
              {remainingMillis !== null && !limitUncertain && (
                <>
                  <View style={styles.todayMeterTrack}>
                    <View
                      style={[
                        styles.todayMeterFill,
                        {
                          width: `${Math.max(elapsedMillis > 0 ? 4 : 0, activeProgress)}%`,
                          backgroundColor: activeProgress >= 100 ? COLORS.error : STUDENT_WEB.primary,
                        },
                      ]}
                    />
                  </View>
                  <Text style={styles.todayMeterHint}>
                    {remainingMillis === 0 ? 'Đã đạt giới hạn hôm nay.' : `Còn ${formatUsage(remainingMillis)} hôm nay.`}
                  </Text>
                </>
              )}
            </View>
          ) : (
            <ActivityIndicator color={COLORS.primary} accessibilityLabel="Đang tải thời gian hôm nay" />
          )}
        </View>

        <View style={styles.surface}>
          <Text accessibilityRole="header" aria-level={3} style={styles.sideHeading}>
            Cách giới hạn hoạt động
          </Text>
          <View style={styles.ruleList}>
            <View style={styles.ruleRow}>
              <Ionicons name="sync-outline" size={18} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
              <Text style={styles.ruleText}>Tính tổng thời gian trên cả điện thoại và trình duyệt web.</Text>
            </View>
            <View style={styles.ruleRow}>
              <Ionicons name="moon-outline" size={18} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
              <Text style={styles.ruleText}>{game
                ? 'Khi hết giờ chơi, con vẫn có thể học và làm Quiz nếu còn tổng thời gian sử dụng.'
                : 'Khi hết tổng thời gian, màn hình nghỉ hiện lên. Câu trả lời Quiz chưa gửi được giữ khi màn hình Quiz còn mở.'}</Text>
            </View>
            <View style={styles.ruleRow}>
              <Ionicons name="key-outline" size={18} color={STUDENT_WEB.primary} accessible={false} aria-hidden />
              <Text style={styles.ruleText}>Mọi thay đổi đều yêu cầu xác nhận mã PIN 6 chữ số của phụ huynh.</Text>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
}

function NumericField({
  label,
  visibleLabel,
  inputRef,
  value,
  disabled,
  error,
  onChange,
  onSubmit,
}: {
  label: string;
  visibleLabel?: string;
  inputRef: React.Ref<InputInstance>;
  value: string;
  disabled?: boolean;
  error?: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const errorId = useId();
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{visibleLabel ?? label}</Text>
      <TextInput
        ref={inputRef}
        accessibilityLabel={label}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        autoCapitalize="none"
        autoCorrect={false}
        inputMode="numeric"
        editable={!disabled}
        style={[styles.input, focused && styles.inputFocused, !!error && styles.inputError]}
        value={value}
        returnKeyType="done"
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChangeText={text => onChange(text.replace(/[^0-9]/g, '').slice(0, 4))}
        onSubmitEditing={onSubmit}
      />
      {!!error && (
        <Text nativeID={errorId} accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: COLORS.background },
  webScreen: { backgroundColor: STUDENT_WEB.background },
  webRedirectCenter: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  workspace: { flex: 1 },
  page: { width: '100%', maxWidth: 1120, alignSelf: 'center', padding: 16, paddingBottom: 40, gap: 16 },
  pageWide: { paddingHorizontal: 28, paddingTop: 22, gap: 20 },
  pageWebWide: { maxWidth: 1280, paddingHorizontal: 36, paddingTop: 26, gap: 22 },
  pinScrim: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: 1100,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: 'rgba(27, 19, 56, .48)',
    ...(Platform.OS === 'web' ? ({ backdropFilter: 'blur(5px)' } as object) : {}),
  } as any,
  nativePinKeyboard: { flex: 1, backgroundColor: 'rgba(27, 19, 56, .48)' },
  nativePinScrim: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: 16 },
  pinDialog: {
    width: '100%',
    maxWidth: 480,
    ...(Platform.OS === 'web' ? { maxHeight: 'calc(100vh - 40px)', overflow: 'auto' } : {}),
    padding: 20,
    borderRadius: 26,
    boxShadow: Platform.OS === 'web' ? '0 24px 70px rgba(27, 19, 56, .24)' : undefined,
  } as any,
  pinDialogHeader: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  toolbar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 },
  toolbarAction: { minHeight: 46, paddingHorizontal: 14 },
  lockAction: {
    minHeight: 46,
    paddingHorizontal: 16,
    backgroundColor: STUDENT_WEB.surface,
    borderColor: STUDENT_WEB.border,
    borderWidth: 1.5,
  },
  lockActionText: { color: STUDENT_WEB.primary, fontFamily: FONTS.extraBold },
  headerRow: { gap: 14 },
  headerRowWide: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  pageHeader: { flexDirection: 'row', gap: 12, alignItems: 'center', flex: 1, minWidth: 0 },
  headerIcon: {
    width: 48,
    height: 48,
    borderRadius: 15,
    backgroundColor: STUDENT_WEB.soft,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCopy: { flex: 1, minWidth: 0, gap: 2 },
  title: { fontFamily: FONTS.black, fontSize: 27, lineHeight: 33, color: STUDENT_WEB.ink },
  subtitle: { fontFamily: FONTS.semiBold, fontSize: 14, color: STUDENT_WEB.muted },
  surface: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    borderRadius: 22,
    gap: 16,
    padding: 20,
    ...(Platform.OS === 'web' ? { boxShadow: '0 6px 22px rgba(33, 23, 89, 0.04)' } : {}),
  },
  segment: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 5,
    gap: 6,
    borderRadius: 16,
    backgroundColor: STUDENT_WEB.soft,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
  },
  segmentWide: { minWidth: 300 },
  selection: {
    flexGrow: 1,
    flexBasis: 100,
    minHeight: 46,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 12,
  },
  choice: {
    flexBasis: 'auto',
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    justifyContent: 'flex-start',
    paddingHorizontal: 14,
  },
  selected: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
  },
  selectionLabel: { flexShrink: 1, fontFamily: FONTS.extraBold, fontSize: 15 },
  pressed: { opacity: 0.78 },
  heading: { fontFamily: FONTS.extraBold, fontSize: 21, color: STUDENT_WEB.ink },
  sideHeading: { fontFamily: FONTS.extraBold, fontSize: 18, color: STUDENT_WEB.ink },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 21, color: STUDENT_WEB.muted },
  limitGrid: { gap: 16 },
  limitGridWide: { flexDirection: 'row', alignItems: 'flex-start', gap: 20 },
  limitMainColumnWide: { flex: 1.35, minWidth: 0 },
  limitSideColumn: { gap: 16 },
  limitSideColumnWide: { flex: 1, minWidth: 0 },
  limitHeaderRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  limitHeaderIcon: {
    width: 46,
    height: 46,
    borderRadius: 14,
    backgroundColor: COLORS.pastelGreen,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  limitSideIcon: { backgroundColor: STUDENT_WEB.soft, borderColor: STUDENT_WEB.border },
  current: {
    backgroundColor: COLORS.pastelGreen,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    padding: 15,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  currentUnlimited: { backgroundColor: STUDENT_WEB.soft, borderColor: STUDENT_WEB.border },
  currentLabel: { fontFamily: FONTS.bold, fontSize: 13, color: STUDENT_WEB.muted },
  settingValue: { fontFamily: FONTS.black, fontSize: 22, color: STUDENT_WEB.ink },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 999, borderWidth: 1 },
  statusBadgeOn: { backgroundColor: '#FFFFFF', borderColor: '#86EFAC' },
  statusBadgeOff: { backgroundColor: '#FFFFFF', borderColor: STUDENT_WEB.border },
  statusBadgeText: { fontFamily: FONTS.extraBold, fontSize: 12 },
  statusBadgeTextOn: { color: '#166534' },
  statusBadgeTextOff: { color: STUDENT_WEB.primary },
  modeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  durationSection: { gap: 12 },
  durationInputRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 10, flexWrap: 'wrap' },
  durationInputCol: { flex: 1, minWidth: 170 },
  stepperGroup: { flexDirection: 'row', gap: 8 },
  stepperBtn: {
    minWidth: 52,
    minHeight: 48,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    backgroundColor: STUDENT_WEB.soft,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
  },
  stepperText: { fontFamily: FONTS.extraBold, fontSize: 14, color: STUDENT_WEB.primary },
  presetBlock: { gap: 8 },
  presetHeading: { fontFamily: FONTS.bold, fontSize: 13, color: STUDENT_WEB.muted },
  presetRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  presetChip: {
    minHeight: 44,
    paddingHorizontal: 13,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: STUDENT_WEB.border,
    backgroundColor: '#FAF9FF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  presetChipSelected: { backgroundColor: STUDENT_WEB.soft, borderColor: STUDENT_WEB.primary },
  presetChipText: { fontFamily: FONTS.bold, fontSize: 13, color: STUDENT_WEB.ink },
  presetChipTextSelected: { fontFamily: FONTS.extraBold, color: STUDENT_WEB.primary },
  impactBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
    borderRadius: 14,
    borderWidth: 1,
    padding: 12,
  },
  impactBannerSafe: { backgroundColor: '#F0FDF4', borderColor: '#BBF7D0' },
  impactBannerWarn: { backgroundColor: '#FEFCE8', borderColor: '#FDE68A' },
  impactText: { flex: 1, minWidth: 0, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 19 },
  impactTextSafe: { color: '#166534' },
  impactTextWarn: { color: '#92400E' },
  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: COLORS.pastelGreen,
    borderWidth: 1,
    borderColor: '#86EFAC',
    padding: 13,
    borderRadius: 14,
  },
  successText: { flex: 1, minWidth: 0, fontFamily: FONTS.bold, fontSize: 14, color: '#14532D' },
  sideNotice: { gap: 10 },
  todayMeterCard: {
    backgroundColor: '#FAF9FF',
    borderWidth: 1,
    borderColor: '#EFEBF9',
    borderRadius: 16,
    padding: 14,
    gap: 8,
  },
  todayMeterTop: { flexDirection: 'row', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' },
  todayMeterValue: { fontFamily: FONTS.black, fontSize: 24, color: STUDENT_WEB.ink },
  todayMeterCap: { fontFamily: FONTS.bold, fontSize: 14, color: STUDENT_WEB.muted },
  todayMeterTrack: { height: 9, borderRadius: 6, backgroundColor: '#E4DCFF', overflow: 'hidden' },
  todayMeterFill: { height: 9, borderRadius: 6 },
  todayMeterHint: { fontFamily: FONTS.semiBold, fontSize: 13, color: STUDENT_WEB.muted },
  ruleList: { gap: 12 },
  ruleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  ruleText: { flex: 1, minWidth: 0, fontFamily: FONTS.semiBold, fontSize: 13, lineHeight: 20, color: STUDENT_WEB.muted },
  field: { gap: 6 },
  fieldLabel: { fontFamily: FONTS.bold, fontSize: 15, color: STUDENT_WEB.ink },
  pinCells: { position: 'relative', flexDirection: 'row', gap: 9 },
  pinCell: {
    flex: 1,
    minWidth: 0,
    height: 58,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 13,
  },
  pinCellActive: { borderWidth: 2, borderColor: COLORS.primaryDark, backgroundColor: COLORS.primaryLight },
  pinCellError: { borderColor: COLORS.errorText, backgroundColor: '#FFF5F7' },
  pinCellText: { fontFamily: FONTS.extraBold, fontSize: 26, lineHeight: 32, color: COLORS.textPrimary },
  pinCellInput: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    opacity: 0.01,
    zIndex: 1,
    width: '100%',
    height: '100%',
    color: 'transparent',
    padding: 0,
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: COLORS.textMuted,
    borderRadius: 12,
    paddingHorizontal: 12,
    backgroundColor: COLORS.surface,
    color: COLORS.textPrimary,
    fontFamily: FONTS.bold,
    fontSize: 18,
  },
  inputFocused: { borderWidth: 2, borderColor: COLORS.borderFocus },
  inputError: { borderColor: COLORS.errorText },
  error: { fontFamily: FONTS.bold, fontSize: 14, color: COLORS.errorText },
});
