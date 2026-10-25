/* eslint-disable react-hooks/immutability -- Expo VideoPlayer exposes imperative native time/rate setters, not React state. */
import React, {useEffect, useRef, useState} from 'react';
import {AppState, StyleSheet, Text, View} from 'react-native';
import {useNavigation} from 'expo-router';
import {useEvent} from 'expo';
import {useVideoPlayer, VideoView, type VideoSource} from 'expo-video';
import {COLORS,FONTS} from '../../constants/theme';
import {MediaTimeline} from './MediaTimeline';

export function LessonClip({source,narrated=false}:{source:VideoSource;narrated?:boolean}) {
  const navigation=useNavigation();
  const player=useVideoPlayer(source,item=>{item.loop=false;item.timeUpdateEventInterval=.2;});
  const {isPlaying}=useEvent(player,'playingChange',{isPlaying:player.playing});
  const {status}=useEvent(player,'statusChange',{status:player.status});
  const progress=useEvent(player,'timeUpdate');
  const [rate,setRate]=useState(1);
  const scrubPlaying=useRef<boolean|null>(null);
  useEffect(()=>navigation.addListener('blur',()=>{scrubPlaying.current=null;player.pause();}),[navigation,player]);
  useEffect(()=>{
    const listener=AppState.addEventListener('change',state=>{if(state!=='active'){scrubPlaying.current=null;player.pause();}});
    return()=>listener.remove();
  },[player]);
  return <View style={styles.stack}>
    <VideoView player={player} style={styles.video} contentFit="contain" nativeControls={false} allowsPictureInPicture={false} fullscreenOptions={{enable:false}} accessibilityLabel="Video bài học có chú thích tiếng Việt"/>
    {status==='error'?<Text accessibilityRole="alert" style={styles.body}>Chưa mở được video. Em vẫn có thể đọc từng bước trong bài học.</Text>:<>
      <MediaTimeline title="Video bài học" subtitle={narrated?'Có lời giảng tiếng Việt':'Có chú thích trong video'}
        currentTime={progress?.currentTime??player.currentTime} duration={player.duration} playing={isPlaying} disabled={status!=='readyToPlay'} loading={status!=='readyToPlay'}
        playLabel="Phát video minh họa" pauseLabel="Tạm dừng video" restartLabel="Xem lại từ đầu"
        onToggle={()=>{if(player.playing)player.pause();else{if(player.currentTime>=player.duration)player.currentTime=0;player.play();}}}
        onScrubStart={()=>{scrubPlaying.current=player.playing;player.pause();}}
        onSeek={seconds=>{const resume=scrubPlaying.current??player.playing;scrubPlaying.current=null;player.currentTime=seconds;if(resume)player.play();}}
        onRestart={()=>{player.pause();player.currentTime=0;}}
        rate={rate} onRate={value=>{player.playbackRate=value;setRate(value);}}/>
    </>}
    {!narrated?<Text style={styles.body}>Em có thể dừng ở hình muốn xem kỹ.</Text>:null}
  </View>;
}
const styles=StyleSheet.create({stack:{gap:16},body:{fontFamily:FONTS.regular,fontSize:14,lineHeight:23,color:COLORS.textSecondary},video:{width:'100%' as const,aspectRatio:16/9,borderRadius:21,backgroundColor:'#F0EAFB'}});
