"""离线Wwise Vorbis转换：复用本机OWLib源码/码本，编译隔离CLI，不初始化CASC或下载。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path.home()/'.universal-modder/toolchains/OWLib-source/DataTool/ConvertLogic'
RELEASE=Path.home()/'.universal-modder/toolchains/owlib/2.25.0.0-1151'
CODEBOOKS=RELEASE/'Third Party/packed_codebooks_aoTuV_603.bin'
BUILD=ROOT/'research/voice-20261027-feedback6/wem-decoder'
FILES=['WEM/WwiseRIFFVorbis.cs','WEM/CodebookLibrary.cs','WEM/BitOggStream.cs',
       'BitStream.cs','BitUint.cs','WEM/Packet.cs','WEM/VorbisPacketHeader.cs','SoundUtils.cs']


def build():
    BUILD.mkdir(parents=True,exist_ok=True);hashes={};paths=[]
    for name in FILES:
        source=SOURCE/name;text=source.read_text(encoding='utf-8-sig');hashes[name]=hashlib.sha256(source.read_bytes()).hexdigest()
        # 本机仅有Framework编译器；只改等价语法，不改变ww2ogg算法。
        text=text.replace('using static DataTool.ConvertLogic.SoundUtils;','')
        if name!='SoundUtils.cs':text=text.replace('SwapBytes(', 'SoundUtils.SwapBytes(').replace('ArraysEqual(', 'SoundUtils.ArraysEqual(')
        text=text.replace('nameof(data)','"data"').replace('_reader?.Dispose();','if (_reader != null) _reader.Dispose();')
        text=text.replace('_stream?.Dispose();','if (_stream != null) _stream.Dispose();').replace('(_loopStart, _loopEnd) = (_loopEnd, _loopStart);','var loopSwap = _loopStart; _loopStart = _loopEnd; _loopEnd = loopSwap;')
        if 'namespace DataTool.ConvertLogic;' in text:text=text.replace('namespace DataTool.ConvertLogic;','namespace DataTool.ConvertLogic {')+'\n}\n'
        text=text.replace('$"LoopStart={_loopStart}"','"LoopStart=" + _loopStart').replace('$"LoopEnd={_loopEnd}"','"LoopEnd=" + _loopEnd')
        text=text.replace('$"{cbSize}, {bis.TotalBitsRead / 8 + 1}"','cbSize + ", " + (bis.TotalBitsRead / 8 + 1)')
        if name.endswith('WwiseRIFFVorbis.cs'):
            a='ushort Read16() => _littleEndian ? _reader.ReadUInt16() : SoundUtils.SwapBytes(_reader.ReadUInt16());'
            b='uint Read32() => _littleEndian ? _reader.ReadUInt32() : SoundUtils.SwapBytes(_reader.ReadUInt32());'
            if a not in text or b not in text:raise ValueError('Local OWLib constructor changed')
            text=text.replace(a,'').replace(b,'')
            text=text.replace('public class WwiseRIFFVorbis : IDisposable {',
                'public class WwiseRIFFVorbis : IDisposable {\nprivate ushort Read16() { return _littleEndian ? _reader.ReadUInt16() : SoundUtils.SwapBytes(_reader.ReadUInt16()); }\nprivate uint Read32() { return _littleEndian ? _reader.ReadUInt32() : SoundUtils.SwapBytes(_reader.ReadUInt32()); }')
        if name=='SoundUtils.cs':text=text.replace('internal static ushort SwapBytes(ushort x) => (ushort) SwapBytes((uint) x);','internal static ushort SwapBytes(ushort x) { return (ushort) SwapBytes((uint) x); }')
        target=BUILD/Path(name).name;target.write_text(text,encoding='utf-8');paths.append(target)
    cli=BUILD/'VoiceWemCli.cs'
    cli.write_text('using System; using System.IO; using DataTool.ConvertLogic.WEM; class VoiceWemCli { static int Main(string[] args) { try { if(args.Length!=3)return 2; using(var input=File.OpenRead(args[0])) using(var output=File.Create(args[1])) using(var decoder=new WwiseRIFFVorbis(input,args[2])) { decoder.ConvertToOgg(output); } return 0; } catch(Exception e) { Console.Error.WriteLine(e.ToString());return 1; } } }',encoding='utf-8');paths.append(cli)
    exe=BUILD/'voice-wem-decode.exe';compiler=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    run=subprocess.run([str(compiler),'/nologo','/target:exe','/out:'+str(exe),*map(str,paths)],capture_output=True,text=True,errors='replace')
    if run.returncode:raise RuntimeError(run.stdout[-3500:]+run.stderr[-1000:])
    proof=dict(source=str(SOURCE),sourceSha256=hashes,syntaxOnlyCompatibility=True,codebooksSha256=hashlib.sha256(CODEBOOKS.read_bytes()).hexdigest())
    (BUILD/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');return exe


def decode(wem,ogg,exe=None):
    exe=exe or build();ogg=Path(ogg)
    if ogg.exists():raise ValueError('Preserve existing decoder output: '+str(ogg))
    result=subprocess.run([str(exe),str(Path(wem).resolve()),str(ogg.resolve()),str(CODEBOOKS)],capture_output=True,timeout=30)
    if result.returncode:raise ValueError(result.stderr.decode(errors='replace')[-2000:])
    if ogg.read_bytes()[:4]!=b'OggS':raise ValueError('Decoder did not produce OGG')
    return ogg


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('wem',type=Path);p.add_argument('ogg',type=Path);a=p.parse_args()
    print(decode(a.wem,a.ogg))
