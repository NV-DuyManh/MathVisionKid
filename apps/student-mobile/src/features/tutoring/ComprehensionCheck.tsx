import React,{useEffect,useRef,useState} from 'react';
import {ActivityIndicator,StyleSheet,Text,TextInput,View} from 'react-native';
import {AppButton} from '../../components/ui/AppButton';
import {RecoveryNotice} from '../../components/ui/RecoveryNotice';
import {MathText} from '../../components/domain/MathText';
import {COLORS,FONTS} from '../../constants/theme';
import {TutorService,type LearningCheck} from './api/TutorService';

export function ComprehensionCheck({sessionId,revision}:{sessionId:string;revision:number}){
  const [check,setCheck]=useState<LearningCheck|null>(null),[value,setValue]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(false);
  const [focused,setFocused]=useState(false);
  const pending=useRef<AbortController|null>(null);
  useEffect(()=>()=>pending.current?.abort(),[]);
  const send=async(answer='')=>{
    if(pending.current)return;const control=new AbortController();pending.current=control;setBusy(true);setError(false);
    try{const result=await TutorService.checkUnderstanding({sessionId,revision},answer,control.signal);if(!control.signal.aborted)setCheck(result);}
    catch{if(!control.signal.aborted)setError(true);}
    finally{if(!control.signal.aborted){pending.current=null;setBusy(false);}}
  };
  return <View style={styles.card}>
    {!check&&!busy&&!error?<AppButton title="Thử nhanh để nhớ cách làm" variant="secondary" onPress={()=>{void send();}}/>:null}
    {busy?<View style={styles.waiting} accessibilityLiveRegion="polite" aria-busy><ActivityIndicator color={COLORS.primaryDark}/><Text style={styles.body}>{check?'Đang kiểm tra kết quả…':'Đang mở câu thử nhanh…'}</Text></View>:null}
    {check?<><Text style={styles.label}>THỬ VỚI SỐ KHÁC</Text><Text style={styles.body}>{check.question}</Text><MathText style={styles.expression}>{check.expression+' = ?'}</MathText>
      <Text style={styles.caption}>Câu luyện nhỏ này tách riêng với đề bài phía trên.</Text>
      <TextInput accessibilityLabel="Kết quả câu thử nhanh" style={[styles.input,focused&&{borderColor:COLORS.primaryDark}]} onFocus={()=>setFocused(true)} onBlur={()=>setFocused(false)} value={value} maxLength={30} onChangeText={setValue} keyboardType="numbers-and-punctuation" editable={!busy&&!check.correct} placeholder="Nhập số hoặc phân số"/>
      {check.checked?<Text accessibilityRole="alert" style={[styles.body,{color:check.correct?'#236747':'#9A4935'}]}>{check.feedback}</Text>:null}
      {!check.correct?<AppButton title="Kiểm tra câu thử nhanh" disabled={!value.trim()||busy} onPress={()=>{void send(value);}}/>:null}
    </>:null}
    {error?<RecoveryNotice title="Chưa mở được câu thử nhanh" message="Em vẫn có thể tiếp tục bài học." actions={[{label:'Thử lại',onPress:()=>{void send(check?value:'');}}]}/>:null}
  </View>;
}
const styles=StyleSheet.create({card:{gap:10,borderRadius:18,backgroundColor:'#F6F2FF',padding:12},label:{fontFamily:FONTS.extraBold,fontSize:10,letterSpacing:1,color:'#7658A1'},body:{fontFamily:FONTS.regular,fontSize:14,lineHeight:22,color:COLORS.textPrimary},caption:{fontFamily:FONTS.regular,fontSize:12,lineHeight:18,color:COLORS.textSecondary},expression:{fontFamily:FONTS.bold,fontSize:20,lineHeight:30,color:COLORS.primaryDark},input:{minHeight:48,padding:12,borderRadius:12,borderWidth:1,borderColor:'#CFC1E9',backgroundColor:'#FFF',fontSize:16,color:COLORS.textPrimary},waiting:{flexDirection:'row',gap:10,alignItems:'center'}});
