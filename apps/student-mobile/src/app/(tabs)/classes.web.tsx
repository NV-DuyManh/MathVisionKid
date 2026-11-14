import { useContext, useEffect, useRef, useState } from 'react';
import { ScrollView, Text, TextInput, View, Pressable, StyleSheet } from 'react-native';
import { FONTS, WEB_DESIGN } from '../../constants/theme';
import apiClient from '../../services/api/apiClient';
import { AuthContext } from '../../context/AuthContext';

type Preview = { classId: string; name: string; gradeLevel: number; generation: string };
type Entry = Omit<Preview, 'generation'> & { status: 'JOINED' | 'PENDING' | 'DECLINED' | 'REMOVED' };
const labels = { JOINED: 'Đã vào lớp', PENDING: 'Đang chờ cô/thầy duyệt', DECLINED: 'Cô/thầy chưa đồng ý', REMOVED: 'Em không còn trong lớp' };

export default function StudentClasses() {
  const auth = useContext(AuthContext);
  const [code, setCode] = useState('');
  const [token, setToken] = useState('');
  const [preview, setPreview] = useState<Preview>();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const credential = token || code;
  const loadVersion = useRef(0);
  const load = async (signal?: AbortSignal) => {
    const version = ++loadVersion.current;
    const { data } = await apiClient.get<Entry[]>('/student/classes', { signal });
    if (!signal?.aborted && version === loadVersion.current) setEntries(data);
  };
  useEffect(() => {
    const controller = new AbortController();
    const value = new URLSearchParams(window.location.hash.slice(1)).get('classroom');
    if (value && /^[a-f0-9]{64}$/.test(value)) {
      setToken(value);
    }
    void load(controller.signal).catch(() => {
      if (!controller.signal.aborted) setError('Chưa xem được lớp. Em thử tải lại nhé.');
    });
    return () => controller.abort();
  }, []);
  const submit = async () => {
    if (pending.current || !credential) return;
    pending.current = true;
    setBusy(true); setError(''); setNotice('');
    try {
      if (!preview) {
        const { data } = await apiClient.post<Preview>('/student/classes/invitation-preview', { credential });
        setPreview(data);
      } else {
        const { data } = await apiClient.post<Entry>('/student/classes/join', {
          credential, classId: preview.classId, generation: preview.generation,
        });
        loadVersion.current++;
        setEntries(current => [...current.filter(entry => entry.classId !== data.classId), data]);
        setNotice(labels[data.status]); setPreview(undefined); setToken(''); setCode('');
        clearInvite();
      }
    } catch (failure: unknown) {
      const status = (failure as { response?: { status?: number } })?.response?.status;
      setError(status === 404 ? 'Mã hoặc link này không dùng được. Em xin cô hoặc thầy mã mới nhé.'
        : status === 429 ? 'Em chờ một chút rồi thử lại nhé.' : 'Chưa xong rồi. Em thử lại nhé.');
      if (status === 404) { setPreview(undefined); setToken(''); clearInvite(); }
    } finally { pending.current = false; setBusy(false); }
  };
  return <ScrollView contentContainerStyle={styles.container}>
    <Text accessibilityRole="header" style={styles.heading}>Lớp của em</Text>
    <View style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Tham gia lớp</Text>
      {preview ? <>
        <Text style={styles.title}>{preview.name}</Text>
        <Text style={styles.text}>Khối {preview.gradeLevel} · {auth?.user?.name || 'Học sinh'}</Text>
        <Text style={styles.text}>Đúng lớp của em chứ?</Text>
      </> : token ? <Text style={styles.text}>Em mở lớp từ lời mời của cô hoặc thầy.</Text> :
        <TextInput accessibilityLabel="Mã lớp sáu số" placeholder="Nhập mã lớp" keyboardType="number-pad"
          style={styles.input} value={code} editable={!busy} maxLength={6}
          onChangeText={value => setCode(value.replace(/[^0-9]/g, ''))} />}
      <Pressable accessibilityRole="button" disabled={busy || (!token && code.length !== 6)}
        onPress={() => void submit()} style={[styles.button, (busy || (!token && code.length !== 6)) && styles.disabled]}>
        <Text style={styles.buttonText}>{busy ? 'Em chờ một chút…' : preview ? 'Xác nhận tham gia' : 'Xem lớp'}</Text>
      </Pressable>
      {(preview || token) && <Pressable accessibilityRole="button" onPress={() => { setPreview(undefined); setToken(''); clearInvite(); }} disabled={busy}>
        <Text style={styles.link}>Dùng mã khác</Text></Pressable>}
      {preview && token && <Pressable accessibilityRole="button" disabled={busy}
        onPress={() => window.location.replace('/login#classroom=' + token + '&switch=1')}>
        <Text style={styles.link}>Đổi tài khoản</Text>
      </Pressable>}
      {!!error && <Text accessibilityRole="alert" style={styles.text}>{error}</Text>}
      {!!notice && <Text accessibilityLiveRegion="polite" style={styles.text}>{notice}</Text>}
    </View>
    <View style={styles.card}>
      <Text accessibilityRole="header" style={styles.title}>Lớp và yêu cầu của em</Text>
      <Pressable accessibilityRole="button" onPress={() => void load().catch(() => setError('Chưa xem được lớp. Em thử lại nhé.'))}>
        <Text style={styles.link}>Cập nhật danh sách</Text>
      </Pressable>
      {entries.length === 0 && <Text style={styles.text}>Các lớp em tham gia sẽ hiện ở đây.</Text>}
      {entries.map(entry => <View key={entry.classId} style={{ paddingVertical: 8 }}>
        <Text style={styles.title}>{entry.name}</Text>
        <Text style={styles.text}>{labels[entry.status]}</Text>
      </View>)}
    </View>
  </ScrollView>;
}

function clearInvite() {
  if (window.location.hash) window.history.replaceState(window.history.state, '', window.location.pathname + window.location.search);
}

const styles = StyleSheet.create({
  container: { width: '100%', maxWidth: 640, alignSelf: 'center', padding: 20, paddingBottom: 110, gap: 16 },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: WEB_DESIGN.colors.paperLine, borderRadius: 18, padding: 18, gap: 12 },
  heading: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.black, fontSize: 28 },
  title: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.bold, fontSize: 20 },
  text: { color: WEB_DESIGN.colors.ink, fontFamily: FONTS.regular, fontSize: 17 },
  input: { minHeight: 52, borderWidth: 1, borderColor: WEB_DESIGN.colors.ink, borderRadius: 12, padding: 12, fontSize: 20, color: WEB_DESIGN.colors.ink },
  button: { minHeight: 50, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: WEB_DESIGN.colors.blue },
  disabled: { opacity: .6 },
  buttonText: { color: '#fff', fontFamily: FONTS.bold, fontSize: 17 },
  link: { color: WEB_DESIGN.colors.blue, minHeight: 44, paddingTop: 10, fontFamily: FONTS.bold, fontSize: 16 },
});
