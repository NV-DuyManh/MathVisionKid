"""Parse supplied bounded ZIP range bytes only. No network or payload reads.

CLI: tail -> central directory range; directory -> metadata-member local header
ranges; local header -> compressed metadata range; decode -> bounded JSON.
Range evidence never claims a fresh SHA256 check of the full archive.
"""
import argparse
import binascii
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zlib


def eocd(tail, start, full_size):
    position = tail.rfind(b'PK\x05\x06')
    if position < 0 or len(tail)-position < 22:
        raise ValueError('EOCD not found in supplied tail')
    sig,disk,cd_disk,on_disk,total,size,offset,comment = struct.unpack_from('<4s4H2IH',tail,position)
    if start+position+22+comment != full_size:
        raise ValueError('EOCD/comment does not end at exact remote size')
    if disk or cd_disk or on_disk != total:
        raise ValueError('multi-disk archive unsupported')
    if total==65535 or size==4294967295 or offset==4294967295:
        raise ValueError('ZIP64 requires explicit ZIP64 metadata discovery')
    if offset+size > start+position:
        raise ValueError('directory outside archive')
    return {'full_size':full_size,'member_count':total,'directory_offset':offset,'directory_bytes':size,
            'next_range':f'bytes={offset}-{offset+size-1}',
            'directory_contained_in_supplied_tail':offset>=start and offset+size<=start+len(tail),
            'full_archive_hash_verified_by_range':False}


def central_directory(data, expected_count=None):
    entries=[]; cursor=0
    while cursor<len(data):
        if len(data)-cursor<46 or data[cursor:cursor+4]!=b'PK\x01\x02':
            raise ValueError('incomplete/invalid central directory')
        row=struct.unpack_from('<4s6H3I5H2I',data,cursor)
        flags,method,crc,compressed,uncompressed=row[3],row[4],row[7],row[8],row[9]
        nlen,xlen,clen,disk,local=row[10],row[11],row[12],row[13],row[16]
        end=cursor+46+nlen+xlen+clen
        if end>len(data) or disk or flags&1 or compressed==4294967295 or local==4294967295:
            raise ValueError('unsupported/encrypted/ZIP64/truncated member')
        name=data[cursor+46:cursor+46+nlen].decode('utf8' if flags&2048 else 'cp437')
        if '\\' in name or name.startswith('/') or '..' in PurePosixPath(name).parts:
            raise ValueError('unsafe archive member path')
        entries.append({'name':name,'compressed_bytes':compressed,'uncompressed_bytes':uncompressed,
                        'method':method,'crc32':crc,'local_header_offset':local,
                        'local_header_range':f'bytes={local}-{local+29}'})
        cursor=end
    if len({x['name'] for x in entries})!=len(entries) or expected_count is not None and expected_count!=len(entries):
        raise ValueError('duplicate directory member/count mismatch')
    return entries


def metadata_permitted(name):
    lower=name.casefold()
    if any(word in lower for word in ('sealed','pilot','concept_challenge','holdout','evaluation')):
        return False
    base=PurePosixPath(lower).name
    return base.endswith('.json') and any(word in base for word in ('manifest','index','parts'))


def local_payload_range(header, entry):
    if not metadata_permitted(entry['name']):
        raise ValueError('member is not an allowed metadata manifest/index')
    if len(header)<30 or header[:4]!=b'PK\x03\x04':
        raise ValueError('invalid local header')
    sig,version,flags,method,tm,dt,crc,compressed,uncompressed,nlen,xlen=struct.unpack_from('<4s5H3I2H',header)
    if flags&1 or method!=entry['method']:
        raise ValueError('local/directory mismatch')
    offset=entry['local_header_offset']+30+nlen+xlen
    return {'name':entry['name'],'offset':offset,'bytes':entry['compressed_bytes'],
            'next_range':f"bytes={offset}-{offset+entry['compressed_bytes']-1}",
            'full_archive_hash_verified_by_range':False}


def decode_metadata(compressed,entry,limit=8*1024*1024):
    if not metadata_permitted(entry['name']) or entry['uncompressed_bytes']>limit:
        raise ValueError('metadata allowlist/size bound rejected')
    if len(compressed)!=entry['compressed_bytes']:
        raise ValueError('compressed bytecount mismatch')
    if entry['method']==0:
        raw=compressed
    elif entry['method']==8:
        decompressor=zlib.decompressobj(-15)
        raw=decompressor.decompress(compressed,limit+1)
        if len(raw)>limit or not decompressor.eof or decompressor.unused_data:
            raise ValueError('deflate metadata stream exceeds bound/incomplete')
    else:
        raise ValueError('unsupported ZIP metadata compression')
    if len(raw)!=entry['uncompressed_bytes'] or binascii.crc32(raw)&0xffffffff!=entry['crc32']:
        raise ValueError('metadata size/CRC mismatch')
    return {'name':entry['name'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
            'document':json.loads(raw),'full_archive_hash_verified_by_range':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    t=sub.add_parser('tail');t.add_argument('--input',required=True);t.add_argument('--start',required=True,type=int);t.add_argument('--full-size',required=True,type=int)
    d=sub.add_parser('directory');d.add_argument('--input',required=True);d.add_argument('--count',type=int)
    h=sub.add_parser('header');h.add_argument('--input',required=True);h.add_argument('--entry',required=True)
    m=sub.add_parser('decode');m.add_argument('--input',required=True);m.add_argument('--entry',required=True)
    for parser in (t,d,h,m):parser.add_argument('--output',required=True)
    args=p.parse_args();data=Path(args.input).read_bytes()
    if args.action=='tail':
        result=eocd(data,args.start,args.full_size)
        if result['directory_contained_in_supplied_tail']:
            offset=result['directory_offset']-args.start
            result['entries']=central_directory(data[offset:offset+result['directory_bytes']],result['member_count'])
            result['allowed_metadata_entries']=[x for x in result['entries'] if metadata_permitted(x['name'])]
    elif args.action=='directory':
        result={'entries':central_directory(data,args.count),'full_archive_hash_verified_by_range':False}
        result['allowed_metadata_entries']=[x for x in result['entries'] if metadata_permitted(x['name'])]
    elif args.action=='header':result=local_payload_range(data,json.loads(Path(args.entry).read_text('utf8')))
    else:result=decode_metadata(data,json.loads(Path(args.entry).read_text('utf8')))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('entries','document','allowed_metadata_entries')}))


if __name__=='__main__':main()
