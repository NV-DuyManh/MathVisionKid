import React, { useRef, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import type { KeyDownEvent, ViewInstance } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { AppButton } from '../../components/ui/AppButton';
import { MathText } from '../../components/domain/MathText';
import { COLORS, FONTS } from '../../constants/theme';
import type { NotebookQuestion } from './api/TutorService';

export function QuestionPicker({ questions, onChoose, onCrop }: {
  questions: NotebookQuestion[]; onChoose: (question: NotebookQuestion) => void; onCrop: () => void;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const cards = useRef(new Map<number, ViewInstance>());
  return <View style={s.stack}>
    <Text style={s.title} accessibilityRole="header">Em muốn học câu nào?</Text>
    <Text style={s.caption}>Đã đọc {questions.length} câu. Chọn một câu rồi kiểm tra lại đề trước khi học nhé.</Text>
    <View style={s.stack} accessibilityRole="radiogroup" accessibilityLabel="Các câu trong ảnh">
      {questions.map((question, index) => <Pressable key={index} accessibilityRole="radio" accessibilityLabel={question.label}
        accessibilityState={{ checked: selected === index }} aria-checked={selected === index} onPress={() => setSelected(index)}
        ref={node => { if (node) cards.current.set(index, node); else cards.current.delete(index); }}
        tabIndex={(selected ?? 0) === index ? 0 : -1}
        {...(Platform.OS === 'web' ? { onKeyDown: (event: KeyDownEvent) => {
          const { key } = event.nativeEvent;
          if ([' ', 'Enter', 'ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(key)) {
            event.preventDefault();
            const direction = ['ArrowRight','ArrowDown'].includes(key) ? 1 : ['ArrowLeft','ArrowUp'].includes(key) ? -1 : 0;
            const next = key === 'Home' ? 0 : key === 'End' ? questions.length-1 : (index+direction+questions.length)%questions.length;
            setSelected(next); cards.current.get(next)?.focus();
          }
        } } : {})}
        style={({ pressed }) => [s.item, selected === index && s.selected, pressed && { opacity: .8 }]}>
        <View style={s.row}><Text style={s.label}>{question.label}</Text><Ionicons accessible={false} name={selected === index ? 'radio-button-on' : 'radio-button-off'} size={22} color={COLORS.primaryDark}/></View>
        <MathText style={s.body}>{question.problemText}</MathText>
        {question.uncertain ? <Text style={s.warning}>Có chỗ cần em kiểm tra lại với ảnh.</Text> : null}
      </Pressable>)}
    </View>
    <AppButton title="Học câu đã chọn" disabled={selected === null} onPress={() => { if (selected !== null) onChoose(questions[selected]); }}/>
    <AppButton title="Chọn vùng khác trong ảnh" variant="ghost" onPress={onCrop}/>
  </View>;
}
const s = StyleSheet.create({
  stack: { gap: 12 }, title: { fontFamily: FONTS.extraBold, fontSize: 21, lineHeight: 29, color: COLORS.textPrimary },
  caption: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 22, color: COLORS.textSecondary },
  item: { gap: 8, padding: 14, borderRadius: 18, borderWidth: 1.5, borderColor: '#E6DFF2', backgroundColor: '#FFF' },
  selected: { borderColor: COLORS.primary, backgroundColor: '#F4EEFF' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 }, label: { flex: 1, fontFamily: FONTS.bold, fontSize: 14, color: COLORS.primaryDark },
  body: { fontFamily: FONTS.regular, fontSize: 14, lineHeight: 23, color: COLORS.textSecondary },
  warning: { fontFamily: FONTS.semiBold, fontSize: 12, lineHeight: 19, color: '#966013' },
});
