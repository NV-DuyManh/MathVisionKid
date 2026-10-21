import {File, Paths} from 'expo-file-system';

export function saveLessonMovie(bytes: Uint8Array): {uri: string; dispose: () => void} {
  const file=new File(Paths.cache,`lesson-${Date.now()}-${Math.random().toString(36).slice(2)}.mp4`);
  file.create();file.write(bytes);
  return {uri:file.uri,dispose:()=>{try{file.delete();}catch{/* The private cache may already have been removed. */}}};
}
