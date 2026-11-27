import React, { useCallback, useContext, useId, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { RecoveryNotice } from '../../components/ui/RecoveryNotice';
import { StudentPageHeader } from '../../components/ui/StudentPageHeader';
import { useIsCompactStudentWeb } from '../../components/ui/useIsCompactStudentWeb';
import { COLORS, FONTS } from '../../constants/theme';
import { AuthContext } from '../../context/AuthContext';
import { foldLessonSearch, getPrimaryChapters, matchesPrimaryLesson, primaryGrade } from '../../data/primaryMathLessons';
import type { PrimaryChapter, PrimaryGrade, PrimaryLesson } from '../../data/primaryMathLessons';
import { getLessonArtwork } from '../lesson-artwork/lessonArtwork';
import { logFlowDomain, recognitionDraftStore } from '../recognition/state/recognitionDraftStore';
import { useStudentProfile } from '../student-profile/useStudentProfile';
import { getCurriculumProblem } from '../../data/primaryMathCurriculum';
import { getPrimaryMathExample } from '../../data/primaryMathExampleSteps';
import { loadLessons } from '../tutoring/learningHistory';
import { CorrectAnswerFeedback } from '../tutoring/CorrectAnswerFeedback';

import { PRIMARY_CATALOG_ARTWORK } from './primaryCatalogArtwork';
import { checkPracticeAnswer, practiceHint, PRIMARY_PRACTICE_ANSWERS } from './practiceAnswer';

export function PrimaryLessonsWeb() {
  const auth = useContext(AuthContext);
  const owner = auth?.isAuthenticated ? auth.user?.id || auth.user?.userId : undefined;
  const { value, failed, retry } = useStudentProfile(owner);
  const grade = primaryGrade(value?.gradeLevel);
  const compact = useIsCompactStudentWeb();
  const router = useRouter();
  const { q, lesson, section } = useLocalSearchParams<{ q?: string; lesson?: string; section?: string }>();
  const query = typeof q === 'string' ? q : '';
  const requestedLesson = typeof lesson === 'string' ? lesson : '';

  return <ScrollView contentContainerStyle={styles.screen}>
    {compact && <StudentPageHeader compact title="Bài học" onBack={() => router.replace('/(tabs)')} onAvatar={() => router.push('/account')} />}
    {owner && grade && !failed ? <LessonCatalog key={JSON.stringify([owner, grade, query, requestedLesson, section])}
      owner={owner} grade={grade} initialQuery={query} requestedLesson={requestedLesson}
      requestedSection={typeof section === 'string' ? section : ''} /> :
      owner && !failed && !value ? <Text accessibilityRole="status" style={styles.copy}>Đang mở chương trình học của em…</Text> :
        <RecoveryNotice title="Chưa tải được lớp của em" message="Em tải lại hồ sơ để mở đúng chương trình học nhé."
          actions={[{ label: 'Tải lại hồ sơ', onPress: retry }]} />}
  </ScrollView>;
}

function LessonCatalog({ owner, grade, initialQuery, requestedLesson, requestedSection }: {
  owner: string; grade: PrimaryGrade; initialQuery: string; requestedLesson: string; requestedSection: string;
}) {
  const chapters = getPrimaryChapters(grade);
  const section = chapters.some(chapter => chapter.lessons.some(lesson =>
    lesson.practice.some(problem => problem.section === requestedSection))) ? requestedSection : '';
  const target = requestedLesson ? chapters.find(chapter => chapter.lessons.some(lesson => lesson.id === requestedLesson)) : undefined;
  const [query, setQuery] = useState(initialQuery);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [openedLesson, setOpenedLesson] = useState(target ? requestedLesson : undefined);
  const [saved, setSaved] = useState<Set<string>>();
  const [savedUnavailable, setSavedUnavailable] = useState(false);
  const router = useRouter();
  useFocusEffect(useCallback(() => {
    let active = true;
    setSavedUnavailable(false);
    void loadLessons(owner).then(lessons => {
      if (active) setSaved(new Set(lessons.flatMap(lesson => {
        const problem = getCurriculumProblem(lesson.problemText);
        return problem ? [problem.id] : [];
      })));
    }).catch(() => {
      if (active) {
        setSaved(undefined);
        setSavedUnavailable(true);
      }
    });
    return () => { active = false; };
  }, [owner]));
  const keyword = foldLessonSearch(query);
  const visible = chapters.map(chapter => ({
    chapter,
    lessons: chapter.lessons.filter(lesson => (!section || lesson.practice.some(problem => problem.section === section))
      && matchesPrimaryLesson(chapter, lesson, keyword)),
  })).filter(group => group.lessons.length);
  const total = visible.reduce((sum, group) => sum + group.lessons.length, 0);
  const quickPractice = visible.flatMap(group => group.lessons).find(lesson => lesson.practice.length)?.practice[0];
  const changeQuery = (value: string) => {
    setQuery(value);
    setExpanded({});
    setOpenedLesson(undefined);
  };

  return <>
    <View style={styles.banner}>
      <Text accessibilityRole="header" style={styles.title}>Toán lớp {grade}</Text>
      <Text style={styles.copy}>{chapters.length} chương · {chapters.reduce((sum, chapter) => sum + chapter.lessons.length, 0)} bài học</Text>
      {saved && <Text style={styles.copy}>{chapters.flatMap(chapter => chapter.lessons)
        .filter(lesson => lesson.practice.some(problem => saved.has(problem.id))).length} bài học có bài làm đã lưu</Text>}
      {savedUnavailable && <Text role="status" style={styles.copy}>Chưa tải được bài đã lưu. Em mở lại trang để thử nhé.</Text>}
    </View>
    <View style={styles.search}>
      <Ionicons name="search-outline" size={21} color={COLORS.primaryDark} accessible={false} />
      <TextInput accessibilityLabel="Tìm bài học trong lớp" placeholder="Tìm chương hoặc bài học…" placeholderTextColor={COLORS.textMuted}
        maxLength={120} value={query} style={styles.input} onChangeText={changeQuery} />
      {query.length > 0 && <Pressable accessibilityRole="button" accessibilityLabel="Xóa tìm kiếm bài học"
        style={styles.clear} onPress={() => changeQuery('')}>
        <Ionicons name="close" size={18} color={COLORS.primaryDark} accessible={false} />
      </Pressable>}
    </View>
    {requestedLesson && !target && <Text accessibilityRole="status" style={styles.copy}>Bài em mở không có trong chương trình lớp {grade}.</Text>}
    {section && <AppButton title={`Bỏ lọc: ${section}`} variant="secondary" onPress={() => router.replace('/(tabs)/lessons')} />}
    {keyword && <Text accessibilityLiveRegion="polite" style={styles.copy}>{total} bài học phù hợp</Text>}
    {quickPractice && <AppButton title="Bắt đầu học ngay" onPress={() => router.push({
      pathname: '/learning/math-guide', params: { problemText: quickPractice.problemText },
    })} />}
    {visible.map(({ chapter, lessons }) => {
      const isExpanded = expanded[chapter.id] ?? (Boolean(keyword || section) || target?.id === chapter.id);
      const chapterContent = `content-${chapter.id}`;
      return <View key={chapter.id} style={styles.chapter}>
        <Pressable accessibilityRole="button" accessibilityLabel={`Chương ${chapters.indexOf(chapter) + 1}: ${chapter.title}`}
          aria-expanded={isExpanded} aria-controls={isExpanded ? chapterContent : undefined}
          onPress={() => setExpanded(previous => ({ ...previous, [chapter.id]: !isExpanded }))} style={styles.chapterButton}>
          <LessonPicture id={chapter.id} />
          <View style={styles.flex}>
            <Text style={styles.chapterTitle}>{chapters.indexOf(chapter) + 1}. {chapter.title}</Text>
            <Text style={styles.copy}>{lessons.length} bài học</Text>
          </View>
          <Ionicons name={isExpanded ? 'chevron-up' : 'chevron-down'} size={22} color={COLORS.primaryDark} accessible={false} />
        </Pressable>
        {isExpanded && <View nativeID={chapterContent} style={styles.lessons}>
          {lessons.map(lesson => {
            const open = openedLesson === lesson.id;
            return <View key={lesson.id} style={styles.lesson}>
              <Pressable accessibilityRole="button" accessibilityLabel={`Mở bài: ${lesson.title}`} aria-expanded={open}
                aria-controls={open ? `content-${lesson.id}` : undefined} style={styles.lessonButton}
                onPress={() => setOpenedLesson(open ? undefined : lesson.id)}>
                <LessonPicture id={lesson.id} />
                <Text style={[styles.lessonTitle, styles.flex]}>{chapter.lessons.indexOf(lesson) + 1}. {lesson.title}</Text>
                <Ionicons name={open ? 'chevron-up' : 'chevron-forward'} size={19} color={COLORS.primaryDark} accessible={false} />
              </Pressable>
              {open && <LessonDetails key={lesson.id} lesson={lesson} saved={saved} />}
            </View>;
          })}
        </View>}
      </View>;
    })}
    {total === 0 && <Text style={styles.copy}>Chưa tìm thấy bài phù hợp. Em thử tìm bằng từ khác nhé.</Text>}
  </>;
}

function LessonPicture({ id }: { id: string }) {
  return <Image source={PRIMARY_CATALOG_ARTWORK[id]} style={styles.picture} resizeMode="cover" accessible={false} />;
}

function LessonDetails({ lesson, saved }: { lesson: PrimaryLesson; saved?: Set<string> }) {
  const router = useRouter();
  const [example, setExample] = useState<'easy' | 'advanced'>();
  const [exampleHint, setExampleHint] = useState(false);
  const answerKeys = PRIMARY_PRACTICE_ANSWERS[lesson.id];
  return <View nativeID={`content-${lesson.id}`} style={styles.detail}>
    <MathText style={styles.copy}>{lesson.explanation}</MathText>
    <AreaDiagram lessonId={lesson.id} />
    {(['easy', 'advanced'] as const).map((level, index) => {
      const title = level === 'easy' ? 'Ví dụ dễ' : 'Ví dụ nâng cao';
      const open = example === level;
      const detailId = `example-${lesson.id}-${level}`;
      const hintId = `${detailId}-hint`;
      return <View key={level} style={styles.example}>
        <Pressable accessibilityRole="button" accessibilityLabel={title} aria-expanded={open}
          aria-controls={open ? detailId : undefined} style={styles.lessonButton}
          onPress={() => { setExample(open ? undefined : level); setExampleHint(false); }}>
          <Text style={[styles.lessonTitle, styles.flex]}>{title}</Text>
          <Ionicons name={open ? 'chevron-up' : 'chevron-down'} size={19} color={COLORS.primaryDark} accessible={false} />
        </Pressable>
        {open && <View nativeID={detailId} style={styles.detail}>
          <MathText style={styles.copy}>{lesson.examples[index][0]}</MathText>
          <Pressable accessibilityRole="button" aria-expanded={exampleHint}
            aria-controls={exampleHint ? hintId : undefined} onPress={() => setExampleHint(value => !value)} style={styles.action}>
            <Text style={styles.link}>{exampleHint ? 'Ẩn gợi ý cách giải' : 'Xem gợi ý cách giải'}</Text>
          </Pressable>
          {exampleHint && <View nativeID={hintId}><MathText style={styles.copy}>
            {getPrimaryMathExample(lesson.id, level)?.steps[0].question ?? lesson.explanation}
          </MathText></View>}
          <AppButton title="Học từng bước" accessibilityLabel={`Học từng bước: ${title}`}
            onPress={() => router.push({ pathname: '/learning/math-guide', params: { exampleId: lesson.id, exampleLevel: level } })} />
        </View>}
      </View>;
    })}
    <Text accessibilityRole="header" style={styles.lessonTitle}>Luyện tập ({lesson.practice.length + lesson.selfPractice.length} bài)</Text>
    {lesson.practice.map((problem, index) => <View key={problem.id} style={styles.practice}>
      <View style={styles.practiceHeading}>
        <Image source={getLessonArtwork(problem.id).source} style={styles.image} resizeMode="contain" accessible={false} />
        <Text accessibilityRole="header" style={[styles.lessonTitle, styles.flex]}>Bài {index + 1} · {problem.title}</Text>
      </View>
      {saved?.has(problem.id) && <Text style={styles.copy}>Đã lưu bài làm</Text>}
      <MathText style={styles.copy}>{problem.problemText}</MathText>
      <PracticeResponse title={`Bài ${index + 1}`} question={problem.problemText}
        answerKey={answerKeys?.[index] ?? ''} hint={problem.guidance} />
      <View style={styles.actions}>
        <AppButton title="Học từng bước" accessibilityLabel={`Học từng bước: ${problem.title}`}
          onPress={() => router.push({ pathname: '/learning/math-guide', params: { problemText: problem.problemText } })} />
        <AppButton title="Chụp bài làm của em" variant="secondary" accessibilityLabel={`Chụp bài làm: ${problem.title}`} onPress={() => {
          recognitionDraftStore.clearDraft();
          logFlowDomain('ACQUIRE', 'MATH_TUTOR');
          router.push({ pathname: '/camera', params: { mode: 'MATH_TUTOR', problemText: problem.problemText } });
        }} />
      </View>
    </View>)}
    {lesson.selfPractice.map(([question], index) => {
      const position = lesson.practice.length + index;
      const title = `Bài ${position + 1}`;
      return <View key={question} style={styles.practice}>
        <Text accessibilityRole="header" style={styles.lessonTitle}>{title}</Text>
        <MathText style={styles.copy}>{question}</MathText>
        <PracticeResponse title={title} question={question} answerKey={answerKeys?.[position] ?? ''}
          hint={practiceHint(lesson.id, position, lesson.explanation)} />
      </View>;
    })}
  </View>;
}

function PracticeResponse({ title, question, answerKey, hint }: { title: string; question: string; answerKey: string; hint: string }) {
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<'correct' | 'incorrect'>();
  const [hintVisible, setHintVisible] = useState(false);
  const responseId = useId();
  const correct = result === 'correct';
  const disabled = !answer.trim() || correct;
  const check = () => {
    if (disabled) return;
    const matches = checkPracticeAnswer(answer, answerKey, question);
    setResult(matches ? 'correct' : 'incorrect');
    setHintVisible(!matches);
  };
  return <View style={styles.practiceResponse}>
    <TextInput accessibilityLabel={`Đáp án: ${title}`} aria-invalid={result === 'incorrect'}
      aria-describedby={hintVisible ? responseId : undefined}
      placeholder="Nhập đáp án" placeholderTextColor={COLORS.textSecondary}
      autoCapitalize="none" autoCorrect={false} maxLength={160} editable={!correct}
      style={[styles.input, styles.practiceInput]} value={answer}
      onChangeText={value => { setAnswer(value); setResult(undefined); }} onSubmitEditing={check} />
    <AppButton title="Kiểm tra đáp án" accessibilityLabel={`Kiểm tra đáp án: ${title}`} disabled={disabled} onPress={check} />
    {correct ? <CorrectAnswerFeedback message="Em làm đúng rồi!" /> : hintVisible && <View
      accessibilityLiveRegion={result === 'incorrect' ? 'polite' : undefined} style={styles.practiceHint}>
      {result === 'incorrect' && <Text style={styles.lessonTitle}>Chưa đúng. Em thử lại nhé!</Text>}
      <Text style={styles.lessonTitle}>Gợi ý cách giải</Text>
      <View nativeID={responseId}><MathText style={styles.copy}>{hint}</MathText></View>
    </View>}
  </View>;
}

const areaDimensions: Record<string, [columns: number, rows: number] | undefined> = {
  'grade-3-area-square-unit': [3, 3],
  'grade-3-area-rectangle': [6, 3],
  'grade-3-area-square': [4, 4],
};

function AreaDiagram({ lessonId }: { lessonId: string }) {
  const sides = areaDimensions[lessonId];
  if (!sides) return null;
  const [columns, rows] = sides;
  const caption = `${rows} hàng, mỗi hàng ${columns} ô vuông cạnh 1 cm`;
  return <View accessible accessibilityRole="image" accessibilityLabel={caption} style={styles.areaDiagram}>
    {Array.from({ length: rows }, (_, row) => <View key={row} style={styles.areaRow}>
      {Array.from({ length: columns }, (_, column) => <View key={column} style={styles.areaCell} />)}
    </View>)}
    <Text style={styles.copy}>{caption}</Text>
  </View>;
}

const styles = StyleSheet.create({
  screen: { width: '100%', maxWidth: 1100, alignSelf: 'center', padding: 16, paddingBottom: 96, gap: 14 },
  banner: { backgroundColor: '#EEE7FF', borderRadius: 22, gap: 4, padding: 18 },
  title: { fontFamily: FONTS.bold, fontSize: 30, color: COLORS.textPrimary },
  copy: { fontFamily: FONTS.regular, color: COLORS.textSecondary, fontSize: 16, lineHeight: 24 },
  search: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#FFFFFF', borderColor: '#DED1FF', borderWidth: 1, borderRadius: 16, paddingHorizontal: 14 },
  input: { flex: 1, minWidth: 0, minHeight: 48, color: COLORS.textPrimary, fontFamily: FONTS.regular, fontSize: 16 },
  clear: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  chapter: { backgroundColor: '#FFFFFF', borderColor: '#DED1FF', borderWidth: 1, borderRadius: 18 },
  chapterButton: { flexDirection: 'row', alignItems: 'center', padding: 12, gap: 12, minHeight: 70 },
  chapterTitle: { fontFamily: FONTS.bold, fontSize: 20, color: COLORS.textPrimary },
  flex: { flex: 1, minWidth: 0 },
  picture: { width: 48, height: 48, backgroundColor: '#EEE7FF', borderRadius: 12 },
  image: { width: 44, height: 44 },
  lessons: { padding: 10, gap: 8 },
  lesson: { backgroundColor: '#F7F3FF', borderRadius: 14 },
  lessonButton: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, minHeight: 64 },
  lessonTitle: { fontFamily: FONTS.bold, color: COLORS.textPrimary, fontSize: 17 },
  detail: { padding: 14, paddingTop: 4, gap: 12 },
  example: { padding: 12, gap: 6, borderRadius: 12, backgroundColor: '#FFFFFF' },
  practice: { padding: 12, gap: 6, borderRadius: 12, backgroundColor: '#FFFFFF' },
  practiceHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  practiceResponse: { gap: 8, marginVertical: 6 },
  practiceInput: { flex: 0, borderWidth: 1, borderColor: '#B6A6DD', borderRadius: 12, paddingHorizontal: 12 },
  practiceHint: { gap: 4, backgroundColor: '#F3EDFF', padding: 12, borderRadius: 12 },
  action: { minHeight: 44, alignSelf: 'flex-start', justifyContent: 'center' },
  link: { fontFamily: FONTS.bold, color: COLORS.primaryDark, fontSize: 16 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  areaDiagram: { alignSelf: 'flex-start', gap: 2 },
  areaRow: { flexDirection: 'row', gap: 2 },
  areaCell: { width: 24, height: 24, borderWidth: 1, borderColor: '#7653BC', backgroundColor: '#DED1FF', borderRadius: 3 },
});
