import React, { useRef } from 'react';
import { Platform, Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, FONTS } from '../../constants/theme';
import { VOICE_CHOICES, type NarrationChoice } from './narrationVoices';

export function VoicePicker({ value, onChange, disabled = false }: { value: NarrationChoice | null; onChange: (value: NarrationChoice) => void; disabled?: boolean }) {
  const buttons = useRef<(React.ElementRef<typeof View> | null)[]>([]);
  const { width, fontScale } = useWindowDimensions();
  const stacked = width < 350 || fontScale > 1.3;
  return <View style={styles.stack}>
    <View style={styles.heading}><View style={styles.headingMark} accessible={false}/><Text style={styles.eyebrow}>GIỌNG ĐỒNG HÀNH</Text></View>
    <View accessibilityRole="radiogroup" accessibilityLabel="Chọn giọng đọc" style={styles.options}>
      {VOICE_CHOICES.map((option,index) => <Pressable key={option.id} ref={node => { buttons.current[index]=node; }}
        accessibilityRole="radio" accessibilityLabel={option.name} accessibilityState={{ checked:value===option.id, disabled:disabled||!value }}
        aria-checked={value===option.id} disabled={disabled||!value}
        {...(Platform.OS==='web' ? { tabIndex:value===option.id?0:-1, onKeyDown:(event: any)=>{
          const key=event.nativeEvent.key;
          if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(key))return;
          event.preventDefault();
          const next=key==='Home'?0:key==='End'?2:(index+(['ArrowLeft','ArrowUp'].includes(key)?-1:1)+3)%3;
          onChange(VOICE_CHOICES[next].id);buttons.current[next]?.focus();
        }}:{})}
        onPress={()=>onChange(option.id)} style={({pressed})=>[styles.option,stacked&&styles.fullWidth,option.id==='device'&&styles.device,value===option.id&&styles.selected,(disabled||!value)&&styles.disabled,pressed&&{opacity:.7}]}>
        <View style={[styles.icon,option.id===VOICE_CHOICES[1].id&&styles.female,option.id==='device'&&styles.deviceIcon]} accessible={false}>
          <Ionicons name={option.id==='device'?'flash-outline':'volume-medium-outline'} size={20} color={option.id==='device'?'#286B57':COLORS.primaryDark}/>
        </View>
        <View style={styles.words}><Text style={styles.name}>{option.name}</Text>{option.id==='device'?<Text style={styles.caption}>Đọc bằng giọng của máy</Text>:null}</View>
        <Ionicons name={value===option.id?'checkmark-circle':'ellipse-outline'} size={18} color={value===option.id?COLORS.primaryDark:COLORS.textMuted} accessible={false}/>
      </Pressable>)}
    </View>
  </View>;
}
const styles=StyleSheet.create({
  stack:{gap:12},heading:{flexDirection:'row',alignItems:'center',gap:7,paddingHorizontal:2},headingMark:{width:5,height:14,borderRadius:3,backgroundColor:COLORS.primary},
  eyebrow:{fontFamily:FONTS.extraBold,fontSize:10,lineHeight:16,letterSpacing:1.1,color:COLORS.primaryDark},
  options:{flexDirection:'row',flexWrap:'wrap',gap:8},option:{flexBasis:'47%',flexGrow:1,minWidth:0,minHeight:64,borderWidth:1.5,borderColor:COLORS.border,borderRadius:18,paddingHorizontal:10,paddingVertical:12,flexDirection:'row',alignItems:'center',gap:7,backgroundColor:COLORS.surface},
  fullWidth:{flexBasis:'100%'},device:{flexBasis:'100%',minHeight:60,backgroundColor:'#F7FBF9'},selected:{backgroundColor:COLORS.primaryLight,borderColor:COLORS.primaryDark},disabled:{opacity:.5},
  icon:{width:30,height:34,borderRadius:12,alignItems:'center',justifyContent:'center',backgroundColor:COLORS.surfaceSubdued},female:{backgroundColor:'#FCEDEF'},deviceIcon:{backgroundColor:'#E3F2EB'},
  words:{flex:1,minWidth:0},name:{fontFamily:FONTS.extraBold,fontSize:13,lineHeight:20,color:COLORS.textPrimary},caption:{fontFamily:FONTS.regular,fontSize:12,lineHeight:18,color:COLORS.textSecondary,marginTop:1},
});
