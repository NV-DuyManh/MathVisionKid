import React,{useCallback,useState} from 'react';
import {Platform,Pressable,StyleSheet,Text,View} from 'react-native';
import {useFocusEffect,useRouter} from 'expo-router';
import {Ionicons} from '@expo/vector-icons';
import {COLORS,FONTS} from '../../constants/theme';
import {loadLearningProgress,type LearningProgress} from './learningProgress';

export function ResumeLessonCard({owner}:{owner?:string}){
  const router=useRouter(),[saved,setSaved]=useState<LearningProgress|null>(null);
  const [focused,setFocused]=useState(false);
  useFocusEffect(useCallback(()=>{let live=true;setSaved(null);void loadLearningProgress(owner).then(row=>{if(live)setSaved(row);});return()=>{live=false;};},[owner]));
  if(!saved)return null;
  return <Pressable accessibilityRole="button" accessibilityLabel="Tiếp tục bài đang học" accessibilityHint={saved.problemText.slice(0,180)} style={({pressed})=>[styles.card,focused&&styles.focus,pressed&&{opacity:.75}]}
    onFocus={event=>{const target=event.currentTarget as unknown as {matches?:(selector:string)=>boolean};if(Platform.OS!=='web'||target.matches?.(':focus-visible'))setFocused(true);}} onBlur={()=>setFocused(false)} onPointerDown={()=>setFocused(false)}
    onPress={()=>router.push({pathname:'/learning/math-guide',params:{problemText:saved.problemText,workText:saved.workText,lessonId:saved.lessonId}})}>
    <View style={styles.badge}><Ionicons name="play-outline" size={23} color={COLORS.primaryDark} accessible={false}/></View>
    <View style={styles.words}><Text style={styles.title}>Bài học gần nhất của em</Text><Text style={styles.preview} numberOfLines={1}>{saved.problemText}</Text><Text style={styles.link}>Mở lại để học tiếp</Text></View>
    <Ionicons name="chevron-forward" size={19} color={COLORS.primaryDark} accessible={false}/>
  </Pressable>;
}
const styles=StyleSheet.create({focus:{outlineWidth:2,outlineOffset:3,outlineStyle:'solid',outlineColor:'#6C43C4'},card:{marginTop:16,backgroundColor:'#FFF',padding:14,borderRadius:19,borderWidth:1,borderColor:'#DFD1F8',flexDirection:'row',alignItems:'center',gap:11,minHeight:88},badge:{width:42,height:46,borderRadius:14,backgroundColor:'#EEE5FF',alignItems:'center',justifyContent:'center'},words:{flex:1,minWidth:0,gap:3},title:{fontFamily:FONTS.bold,fontSize:14,color:COLORS.textPrimary},preview:{fontFamily:FONTS.regular,fontSize:12,color:COLORS.textSecondary},link:{fontFamily:FONTS.bold,fontSize:12,color:COLORS.primaryDark}});
