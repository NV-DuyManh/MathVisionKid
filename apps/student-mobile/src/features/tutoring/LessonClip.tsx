import React, {useEffect} from 'react';
import {AppState, StyleSheet, Text, View} from 'react-native';
import {useNavigation} from 'expo-router';
import {useEvent} from 'expo';
import {useVideoPlayer, VideoView, type VideoSource} from 'expo-video';
import {AppButton} from '../../components/ui/AppButton';
import {COLORS,FONTS} from '../../constants/theme';

export function LessonClip({source,narrated=false}:{source:VideoSource;narrated?:boolean}) {
  const navigation=useNavigation();
  const player=useVideoPlayer(source,item=>{item.loop=false;});
  const {isPlaying}=useEvent(player,'playingChange',{isPlaying:player.playing});
  const {status}=useEvent(player,'statusChange',{status:player.status});
  useEffect(()=>navigation.addListener('blur',()=>{player.pause();}),[navigation,player]);
  useEffect(()=>{
    const listener=AppState.addEventListener('change',state=>{if(state!=='active')player.pause();});
    return()=>listener.remove();
  },[player]);
  return <View style={styles.stack}>
    <VideoView player={player} style={styles.video} contentFit="contain" nativeControls={false} allowsPictureInPicture={false} fullscreenOptions={{enable:false}} accessibilityLabel="Video bài học có chú thích tiếng Việt"/>
    {status==='error'?<Text accessibilityRole="alert" style={styles.body}>Chưa mở được video. Em vẫn có thể đọc từng bước trong bài học.</Text>:<>
      <AppButton title={isPlaying?'Tạm dừng video':'Phát video minh họa'} onPress={()=>{if(isPlaying)player.pause();else player.play();}}/>
      <AppButton title="Xem lại từ đầu" variant="secondary" onPress={()=>{player.pause();player.seekBy(-player.currentTime);}}/>
    </>}
    <Text style={styles.body}>{narrated?'Video có lời giảng tiếng Việt và chữ hướng dẫn. Em có thể dừng để xem kỹ.':'Video có chữ hướng dẫn, không tự phát âm thanh. Em có thể dừng để xem kỹ.'}</Text>
  </View>;
}
const styles=StyleSheet.create({stack:{gap:16},body:{fontFamily:FONTS.regular,fontSize:14,lineHeight:23,color:COLORS.textSecondary},video:{width:'100%',aspectRatio:16/9,borderRadius:21,backgroundColor:'#F0EAFB'}});
