"""Paragraph boundaries in standard PCM WAV cue points; no estimated speech times."""
import io
import struct
import wave


def read_cues(data: bytes) -> list[int]:
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        return []
    offset = 12
    while offset + 8 <= len(data):
        size = struct.unpack_from('<I', data, offset + 4)[0]
        if offset + 8 + size > len(data):
            return []
        if data[offset:offset+4] == b'cue ' and size >= 4:
            count = struct.unpack_from('<I', data, offset + 8)[0]
            if not 1 <= count <= 80 or size != 4 + count * 24:
                return []
            rows = [struct.unpack_from('<II4sIII', data, offset+12+i*24) for i in range(count)]
            points = [row[5] for row in rows]
            if any(row[0] != i or row[2] != b'data' for i,row in enumerate(rows)) or points != sorted(set(points)) or points[0] != 0:
                return []
            return points
        offset += 8 + size + size % 2
    return []


def add_cues(data: bytes, frames: list[int]) -> bytes:
    if not 1 <= len(frames) <= 80 or frames[0] != 0 or frames != sorted(set(frames)):
        raise ValueError('Invalid audio boundaries')
    with wave.open(io.BytesIO(data), 'rb') as source:
        if frames[-1] >= source.getnframes():
            raise ValueError('Boundary outside audio')
    payload = struct.pack('<I', len(frames)) + b''.join(struct.pack('<II4sIII', index, position, b'data', 0, 0, position) for index,position in enumerate(frames))
    result = bytearray(data + b'cue ' + struct.pack('<I', len(payload)) + payload)
    struct.pack_into('<I', result, 4, len(result)-8)
    return bytes(result)


def join_pcm(chunks: list[bytes], paragraph_indexes: list[int]) -> bytes:
    if not chunks or len(chunks) != len(paragraph_indexes):
        raise ValueError('Invalid audio parts')
    output = io.BytesIO()
    starts = []
    frames = 0
    with wave.open(output, 'wb') as joined:
        joined.setnchannels(1); joined.setsampwidth(2); joined.setframerate(16000)
        previous = -1
        for data,index in zip(chunks, paragraph_indexes):
            if index != previous:
                if index != previous+1:
                    raise ValueError('Invalid paragraph order')
                starts.append(frames); previous = index
            if not data or len(data) % 2:
                raise ValueError('Incomplete PCM')
            joined.writeframes(data); frames += len(data)//2
    return add_cues(output.getvalue(), starts)
