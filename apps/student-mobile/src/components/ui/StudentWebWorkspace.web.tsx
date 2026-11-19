import React, { useContext, useEffect, useRef, useState } from 'react';
import { Link, usePathname } from 'expo-router';
import type { Href } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppIllustration } from './AppIllustration';
import { AuthContext } from '../../context/AuthContext';
import { getProblemsByGrade } from '../../data/primaryMathCurriculum';
import { STUDENT_WEB } from '../../constants/studentWebDesign';
import { loadLessons } from '../../features/tutoring/learningHistory';
import type { SavedLesson } from '../../features/tutoring/learningHistory';
import { StudentAvatar } from '../../features/student-profile/ProfileCards';
import { profileApi } from '../../features/student-profile/profileApi';
import type { StudentProfile } from '../../features/student-profile/profileApi';
import { studentWorkspaceStyles } from './studentWorkspaceStyles.web';

const destinations = [
  { path: '/', href: '/(tabs)', title: 'Trang chủ', icon: 'home-outline' },
  { path: '/lessons', href: '/(tabs)/lessons', title: 'Bài học', icon: 'book-outline' },
  { path: '/quiz', href: '/quiz', title: 'Câu đố', icon: 'clipboard-outline' },
  { path: '/games', href: '/games', title: 'Trò chơi', icon: 'game-controller-outline' },
  { path: '/achievements', href: '/(tabs)/achievements', title: 'Thành tích', icon: 'trophy-outline' },
  { path: '/saved', href: '/saved', title: 'Bài đã lưu', icon: 'bookmark-outline' },
  { path: '/profile', href: '/(tabs)/profile', title: 'Của em', icon: 'person-outline' },
] as const;
const mascot = require('../../../assets/illustrations/web/robot-mascot.webp');
const workspace = /^\/(?:$|(?:lessons|achievements|profile|account|progress|saved|camera|crop|preview|processing|learning|recognition|results|quiz)(?:\/|$)|games\/?$)/;
const foldSearch = (text: string) => text.toLocaleLowerCase('vi').normalize('NFD').replace(/\p{Diacritic}/gu, '').replace(/đ/g, 'd').trim();

export function StudentWebWorkspace({ children }: React.PropsWithChildren) {
  const pathname = usePathname().replace(/^\/(?:study|learn)(?=\/|$)/, '') || '/';
  const auth = useContext(AuthContext);
  const owner = auth?.isAuthenticated && auth.user?.role === 'STUDENT' && auth.user?.active === true
    ? String(auth.user.id || auth.user.userId || '') : '';
  const enabled = Boolean(owner) && workspace.test(pathname);
  return <div className="student-workspace">
    <style>{studentWorkspaceStyles}</style>
    {enabled && <a className="student-workspace-skip" href="#student-workspace-content">Đến nội dung chính</a>}
    {enabled && <WorkspaceSidebar pathname={pathname} />}
    <div className="student-workspace-main">
      {enabled && <WorkspaceHeader key={owner} owner={owner} pathname={pathname} grade={Number(auth?.user.gradeLevel)} name={auth?.user.name} />}
      <div className="student-workspace-page" id={enabled ? 'student-workspace-content' : undefined}
        role={enabled ? 'main' : undefined} tabIndex={enabled ? -1 : undefined}>{children}</div>
    </div>
  </div>;
}

function WorkspaceSidebar({ pathname }: { pathname: string }) {
  const [collapsed, setCollapsed] = useState(false);
  const links = useRef<HTMLAnchorElement[]>([]);
  const section = '/' + pathname.split('/')[1];
  const activeTab = section === '/progress' ? '/achievements'
    : section === '/account' ? '/profile'
      : section === '/learning' ? '/lessons'
        : ['/camera', '/crop', '/preview', '/processing', '/recognition', '/results'].includes(section) ? '/' : section;
  function moveFocus(event: React.KeyboardEvent, index: number) {
    const count = destinations.length;
    const targets: Record<string, number> = {
      ArrowDown: (index + 1) % count, ArrowUp: (index + count - 1) % count, Home: 0, End: count - 1,
    };
    if (targets[event.key] === undefined) return;
    event.preventDefault();
    links.current[targets[event.key]]?.focus();
  }
  return <aside className={`student-workspace-sidebar${collapsed ? ' is-collapsed' : ''}`}>
    <div className="student-workspace-brand">
      <Ionicons name="planet" size={32} color="#FFE07C" aria-hidden />
      <span>MathVision<span>Kid</span><small>Cùng em học Toán</small></span>
      <button type="button" className="student-workspace-toggle" aria-label={collapsed ? 'Mở rộng menu' : 'Thu gọn menu'}
        aria-controls="student-workspace-nav" aria-expanded={!collapsed} onClick={() => setCollapsed(value => !value)}>
        <Ionicons name={collapsed ? 'chevron-forward' : 'chevron-back'} size={18} color="#E5D9FF" aria-hidden />
      </button>
    </div>
    <nav id="student-workspace-nav" aria-label="Điều hướng học sinh">
        {destinations.map((item, index) => <Link key={item.path} href={item.href as Href} asChild>
          <a ref={element => { if (element) links.current[index] = element; }}
            aria-label={item.title} aria-current={activeTab === item.path ? 'page' : undefined}
            title={collapsed ? item.title : undefined} onKeyDown={event => moveFocus(event, index)}>
            <Ionicons name={item.icon} size={22} color="#FFFFFF" aria-hidden /><span>{item.title}</span>
          </a>
        </Link>)}
    </nav>
    <div className="student-workspace-companion">
      <Link href={{ pathname: '/account', params: { section: 'privacy' } }} asChild><a className="student-workspace-safety">
        <Ionicons name="shield-checkmark-outline" size={23} color={STUDENT_WEB.gold} aria-hidden />
        <span><strong>Học vui, an toàn</strong><small>Bảo vệ thông tin cá nhân của em</small></span>
      </a></Link>
      <div className="student-workspace-sideart"><AppIllustration source={mascot} style={{ width: '100%', height: 220 }} accessible={false} /></div>
    </div>
  </aside>;
}

type Panel = 'search' | 'notifications' | 'account';
function WorkspaceHeader({ owner, pathname, grade, name }: { owner: string; pathname: string; grade: number; name?: string }) {
  const [profile, setProfile] = useState<StudentProfile>();
  const [query, setQuery] = useState('');
  const [panel, setPanel] = useState<Panel | null>(null);
  const [saved, setSaved] = useState<SavedLesson[]>([]);
  const header = useRef<HTMLElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const notification = useRef<HTMLButtonElement>(null);
  const account = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (panel !== 'search') return;
    let active = true;
    void loadLessons(owner).then(rows => { if (active) setSaved(rows); }).catch(() => {});
    return () => { active = false; };
  }, [owner, panel]);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'k' || !search.current?.offsetWidth) return;
      event.preventDefault();
      search.current.focus();
    };
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);
  useEffect(() => {
    const request = new AbortController();
    void profileApi.get(request.signal).then(result => {
      if (!request.signal.aborted) setProfile(result);
    }).catch(() => {});
    return () => request.abort();
  }, [pathname, grade, name]);
  useEffect(() => {
    if (!panel) return;
    const outside = (event: PointerEvent) => {
      if (event.target instanceof Node && !header.current?.contains(event.target)) setPanel(null);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.key !== 'Escape' || !(document.activeElement && header.current?.contains(document.activeElement))) return;
      event.preventDefault();
      setPanel(null);
      ({ search, notifications: notification, account }[panel].current)?.focus();
    };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', outside);
      document.removeEventListener('keydown', escape);
    };
  }, [panel]);
  const keyword = foldSearch(query);
  const currentGrade = profile?.gradeLevel ?? grade;
  const results = keyword && Number.isInteger(currentGrade) && currentGrade >= 1 && currentGrade <= 5
    ? getProblemsByGrade(currentGrade as 1 | 2 | 3 | 4 | 5).filter(problem => foldSearch(`${problem.title} ${problem.topic}`).includes(keyword)).slice(0, 5) : [];
  const savedResults = keyword ? saved.filter(lesson => foldSearch(lesson.problemText).includes(keyword)).slice(0, 3) : [];
  const displayName = profile?.displayName || name || 'Học sinh';
  const searchOpen = panel === 'search' && Boolean(keyword);
  const close = () => setPanel(null);
  const selectResult = () => { close(); setQuery(''); };
  const activate = (next: Panel) => setPanel(value => value === next ? null : next);
  return <header className="student-workspace-topbar" ref={header}
    onBlur={event => { if (event.relatedTarget && !event.currentTarget.contains(event.relatedTarget)) close(); }}>
    <form className="student-workspace-search" role="search" aria-label="Tìm bài học"
      onSubmit={event => { event.preventDefault(); if (keyword) header.current?.querySelector<HTMLAnchorElement>('[data-all-lessons]')?.click(); }}>
      <Ionicons name="search-outline" size={20} color={STUDENT_WEB.primary} aria-hidden />
      <input ref={search} type="search" autoComplete="off" aria-label="Tìm bài học, chủ đề" placeholder="Tìm bài học, chủ đề, bài đã lưu..." aria-keyshortcuts="Control+K Meta+K"
        maxLength={100} value={query} onFocus={() => setPanel('search')} onChange={event => { setQuery(event.target.value); setPanel('search'); }} />
      <kbd aria-hidden>Ctrl + K</kbd>
      {searchOpen && <div className="student-workspace-popover student-workspace-search-results">
        {!results.length && !savedResults.length && <p role="status">Chưa tìm thấy bài học phù hợp.</p>}
        {results.map(problem => <Link key={problem.id} href={{ pathname: '/(tabs)/lessons', params: { q: problem.title } }} asChild>
          <a onClick={selectResult}>{problem.title}</a>
        </Link>)}
        {savedResults.map(lesson => <Link key={lesson.id} href={{ pathname: '/learning/math-guide', params: { lessonId: lesson.id, problemText: lesson.problemText, workText: lesson.workText, reflection: lesson.reflection } }} asChild>
          <a onClick={selectResult}>Đã lưu · {lesson.problemText.slice(0, 90)}</a>
        </Link>)}
        <Link href={{ pathname: '/(tabs)/lessons', params: { q: query.trim() } }} asChild>
          <a data-all-lessons onClick={selectResult}>Xem kết quả trong Bài học</a>
        </Link>
      </div>}
    </form>
    <div className="student-workspace-tools">
      <div className="student-workspace-anchor">
        <button ref={notification} type="button" className="student-workspace-icon" aria-label="Thông báo"
          aria-expanded={panel === 'notifications'} onClick={() => activate('notifications')}>
          <Ionicons name="notifications-outline" size={22} color={STUDENT_WEB.primary} aria-hidden />
        </button>
        {panel === 'notifications' && <div className="student-workspace-popover">
          <strong>Thông báo học tập</strong><p>Chưa có thông báo mới.</p>
          <Link href="/(tabs)/lessons" onPress={close}>Xem bài học</Link>
        </div>}
      </div>
      <Link href="/(tabs)/achievements" asChild><a className="student-workspace-icon" aria-label="Xem thành tích của em">
        <Ionicons name="trophy-outline" size={22} color={STUDENT_WEB.primary} aria-hidden />
      </a></Link>
      {profile && <Link href="/(tabs)/achievements" asChild>
        <a className="student-workspace-stars"><Ionicons name="star" size={18} color="#956300" aria-hidden />{profile.stars} sao</a>
      </Link>}
      <div className="student-workspace-anchor">
        <button ref={account} type="button" className="student-workspace-account" aria-label="Menu tài khoản học sinh"
          aria-expanded={panel === 'account'} onClick={() => activate('account')}>
          <StudentAvatar id={profile?.avatar ?? 'rocket'} photo={profile?.avatarPhoto} size={36} />
          <span>{displayName.includes('@') ? 'Học sinh' : displayName}
            {Number.isInteger(currentGrade) && currentGrade >= 1 && currentGrade <= 5 && <small>Lớp {currentGrade}</small>}
          </span>
          <Ionicons name="chevron-down" size={15} color={STUDENT_WEB.ink} aria-hidden />
        </button>
        {panel === 'account' && <div className="student-workspace-popover">
          <Link href="/account" onPress={close}>Hồ sơ của em</Link>
          <Link href={{ pathname: '/account', params: { section: 'privacy' } }} onPress={close}>Quyền riêng tư</Link>
          <Link href={{ pathname: '/account', params: { section: 'logout' } }} onPress={close}>Đăng xuất</Link>
        </div>}
      </div>
    </div>
  </header>;
}
