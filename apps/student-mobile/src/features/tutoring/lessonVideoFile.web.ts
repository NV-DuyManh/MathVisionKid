export function saveLessonMovie(bytes: Uint8Array): {uri: string; dispose: () => void} {
  const uri=URL.createObjectURL(new Blob([new Uint8Array(bytes).buffer],{type:'video/mp4'}));
  return {uri,dispose:()=>URL.revokeObjectURL(uri)};
}
