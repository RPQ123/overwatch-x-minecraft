"""Prepare one explicitly selected cold native map on the original Present owner."""
import ctypes,struct
from observe_overwatch import ROOT,PoseReader
from provided_plugin_symbols import provided_plugin,PeImage
from native_bootstrap_maps import VERSION,MAPS

def prepare(process,pid,creation,map_id=0x08000000000002af):
    if map_id not in MAPS.values():raise ValueError("Unverified native bootstrap map")
    module,image,pdb=provided_plugin(process);reader=PoseReader(process)
    demo=image.symbol_rva(pdb.exact('?isDemo@globals@@3_NA'))
    if process.read(module+demo,1)!=b'\0':raise ValueError('Bootstrap only applies to a fresh pre-Demo client')
    # This supplied executable decrypts .text at runtime. Its on-disk bytes at
    # this RVA are ciphertext, so use the measured unpacked build signature.
    load=0xc7f090;prefix=bytes.fromhex('4c8bdc5341564883ec58488b058fc3a8004833c44889442440418b40704d8bf0')
    if process.read(process.base+load,32)!=prefix:raise ValueError('Unpacked original data-pack loader differs')
    admin=reader.pointer(process.base+0x17b7f90)
    if reader.unpack('<I',admin+0x220)[0]!=0:raise ValueError('Preserve the existing original hero')
    data=struct.pack('<8sIIIIQQIIII32sQ',b'OWBOOT01',VERSION,96,pid,0,creation,module,image.image_size,image.timestamp,demo,load,prefix,map_id)
    if len(data)!=96:raise AssertionError('Bootstrap request ABI')
    path=ROOT/f'native-host/build/session-bootstrap-request-{pid}.bin';path.write_bytes(data);return path
