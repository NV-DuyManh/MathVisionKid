export type AudioCue = { index: number; start: number; end: number };
/** Standard RIFF cue points are decoded sample offsets, not text-length estimates. */
export function audioCues(bytes: Uint8Array): AudioCue[] {
  if (bytes.length < 44) return [];
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const tag = (offset: number) => String.fromCharCode(...bytes.subarray(offset, offset+4));
  if (tag(0) !== 'RIFF' || tag(8) !== 'WAVE' || view.getUint32(4,true)+8 !== bytes.length) return [];
  let rate = 0, frameBytes = 0, frames = 0, positions: number[] = [];
  for (let offset=12; offset+8<=bytes.length;) {
    const size = view.getUint32(offset+4,true), start = offset+8;
    if (start+size>bytes.length) return [];
    if (tag(offset)==='fmt ' && size>=16 && view.getUint16(start,true)===1) {
      rate=view.getUint32(start+4,true);frameBytes=view.getUint16(start+12,true);
    } else if (tag(offset)==='data' && frameBytes) frames=size/frameBytes;
    else if (tag(offset)==='cue ' && size>=4) {
      const count=view.getUint32(start,true);
      if (!count || count>80 || size!==4+24*count || positions.length) return [];
      for(let i=0;i<count;i++) {
        const row=start+4+24*i;
        if(view.getUint32(row,true)!==i || tag(row+8)!=='data') return [];
        positions.push(view.getUint32(row+20,true));
      }
    }
    offset=start+size+size%2;
  }
  if (!rate || !frames || !Number.isInteger(frames) || positions[0]!==0 || positions.some((point,i)=>point>=frames || i>0 && point<=positions[i-1])) return [];
  return positions.map((point,index)=>({index,start:point/rate,end:(positions[index+1]??frames)/rate}));
}
