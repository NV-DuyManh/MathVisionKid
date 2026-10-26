export function saveSpeechAudio(bytes: Uint8Array): { uri: string; dispose: () => void } {
  const uri = URL.createObjectURL(new Blob([new Uint8Array(bytes).buffer], { type: 'audio/mpeg' }));
  return { uri, dispose: () => URL.revokeObjectURL(uri) };
}
