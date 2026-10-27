import React, {useEffect, useState} from 'react';
import {AppState, StyleSheet, Text, View} from 'react-native';
import {Ionicons} from '@expo/vector-icons';
import {AppButton} from '../../components/ui/AppButton';
import {COLORS,FONTS} from '../../constants/theme';
import type {LessonResponse} from './api/TutorService';
import {lessonVideoApi, PersonalVideo} from './lessonVideoApi';
import {saveLessonMovie} from './lessonVideoFile';
import {LessonClip} from './LessonClip';
import {TaskProgress} from '../../components/ui/TaskProgress';

const VIDEO_STEPS=['Dựng hình và lời giảng','Tải video về','Mở trình phát'] as const;

function wait(signal: AbortSignal) {
  return new Promise<void>((resolve,reject)=>{
    const abort=()=>{clearTimeout(timer);signal.removeEventListener('abort',abort);reject(new Error('Stopped'));};
    const timer=setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},1000);
    signal.addEventListener('abort',abort,{once:true});if(signal.aborted)abort();
  });
}
export function PersonalLessonVideo({scope,lesson}:{scope:string;lesson:LessonResponse}) {
  return <Movie key={JSON.stringify([scope,lesson.sessionId,lesson.revision])} lesson={lesson}/>;
}
function Movie({lesson}:{lesson:LessonResponse}) {
  const [attempt,setAttempt]=useState(0), [progress,setProgress]=useState(0), [error,setError]=useState(false);
  const [ready,setReady]=useState<{uri:string;video:PersonalVideo}|null>(null);
  const [stage,setStage]=useState(0);
  useEffect(()=>{
    let alive=true, complete=false, asset:ReturnType<typeof saveLessonMovie>|undefined;
    const controller=new AbortController();
    const listener=AppState.addEventListener('change',state=>{
      if(state!=='active'&&!complete){controller.abort();if(alive)setError(true);}
    });
    void (async()=>{
      try{
        let video=await lessonVideoApi.prepare({sessionId:lesson.sessionId,revision:lesson.revision},controller.signal);
        const deadline=Date.now()+115000;
        while(video.status==='RENDERING'){
          if(!alive||controller.signal.aborted) return;
          setProgress(video.progress);
          if(Date.now()>deadline)throw new Error('Video wait expired');
          await wait(controller.signal);video=await lessonVideoApi.status(video.videoId,controller.signal);
        }
        if(!alive||controller.signal.aborted)return;
        if(video.status!=='READY'||!video.hasAudio)throw new Error('Voiced video unavailable');
        setStage(1);
        const bytes=await lessonVideoApi.download(video.videoId,controller.signal);
        if(!alive||controller.signal.aborted)return;
        asset=saveLessonMovie(bytes);complete=true;setReady({uri:asset.uri,video});
      }catch{if(alive)setError(true);}
    })();
    return()=>{alive=false;controller.abort();listener.remove();asset?.dispose();};
  },[lesson.sessionId,lesson.revision,attempt]);
  if(error)return <View style={styles.panel} accessibilityLiveRegion="polite"><Ionicons name="videocam-outline" size={35} color={COLORS.primaryDark}/>
    <Text style={styles.heading}>Mình chưa mở được video</Text><Text style={styles.body}>Bài học của em vẫn ở đây. Em có thể thử lại hoặc đọc từng bước đang học.</Text>
    <AppButton title="Thử tạo video lại" onPress={()=>{setError(false);setProgress(0);setStage(0);setAttempt(value=>value+1);}}/></View>;
  if(!ready)return <View style={styles.panel} accessibilityLiveRegion="polite" aria-busy>
    <Ionicons name="sparkles-outline" size={36} color={COLORS.primaryDark}/><Text style={styles.heading}>{stage===0?'Đang dựng video bài của em':'Đang mở video bài của em'}</Text>
    <Text style={styles.body}>Mình chuẩn bị hình minh họa và lời giảng tiếng Việt theo các bước của bài này.</Text>
    <TaskProgress steps={VIDEO_STEPS} activeStep={stage}/>
    {stage===0&&progress>0?<Text style={styles.small}>Phần dựng video: {progress}%</Text>:null}</View>;
  return <View style={styles.stack}>
    <Text style={styles.eyebrow}>VIDEO BÀI CỦA EM</Text>
    <Text style={styles.heading}>{ready.video.title}</Text>
    <Text style={styles.body}>{lesson.status==='COMPLETE'?'Cùng xem lại cách làm qua từng bước em đã hoàn thành.':'Video giải thích bước đang học. Các bước em chưa làm vẫn để em tự thử nhé.'}</Text>
    <LessonClip source={ready.uri} narrated preparationSteps={VIDEO_STEPS}/>
  </View>;
}
const styles=StyleSheet.create({
 stack:{gap:12},panel:{padding:21,paddingVertical:28,borderRadius:24,backgroundColor:'#FCFAFF',borderWidth:1,borderColor:'#EAE3F2',gap:17},
 heading:{fontFamily:FONTS.extraBold,fontSize:19,lineHeight:28,color:COLORS.textPrimary},body:{fontFamily:FONTS.regular,fontSize:14,lineHeight:23,color:COLORS.textSecondary},
 small:{fontFamily:FONTS.bold,fontSize:13,color:COLORS.primaryDark},eyebrow:{fontFamily:FONTS.extraBold,fontSize:11,lineHeight:18,letterSpacing:.8,color:'#80629F'},
});
