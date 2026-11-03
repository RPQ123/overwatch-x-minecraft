"""Disassemble one SHA/CKey-verified local24919 shader to private audit storage."""
import ctypes as C
import hashlib
import struct
import zlib


def disassemble(bytecode):
    library = C.WinDLL('d3dcompiler_47.dll')
    fn = library.D3DDisassemble
    fn.argtypes = [C.c_void_p, C.c_size_t, C.c_uint, C.c_char_p, C.POINTER(C.c_void_p)]
    fn.restype = C.c_long
    data = C.create_string_buffer(bytecode)
    blob = C.c_void_p()
    result = fn(data, len(bytecode), 0, None, C.byref(blob))
    if result < 0:
        raise ValueError(f'D3DDisassemble HRESULT {result:x}')
    table = C.cast(blob, C.POINTER(C.POINTER(C.c_void_p))).contents
    pointer = C.WINFUNCTYPE(C.c_void_p, C.c_void_p)(table[3])
    size = C.WINFUNCTYPE(C.c_size_t, C.c_void_p)(table[4])
    release = C.WINFUNCTYPE(C.c_uint, C.c_void_p)(table[2])
    try:
        return C.string_at(pointer(blob), size(blob)).decode('utf-8').rstrip('\0')
    finally:
        release(blob)


def extract_code(archive, guid):
    row = archive.records[guid]
    raw = archive.fetch(row['ckey'], guid+'.raw')
    if len(raw) != row['bytes'] or hashlib.md5(raw).hexdigest() != row['ckey']:
        raise ValueError('Shader code archive CKey mismatch')
    start = struct.unpack_from('<Q', raw)[0]
    size, compressed = struct.unpack_from('<2I', raw, 28)
    code = zlib.decompress(raw[start:start+compressed], 31)
    if len(code) != size or not code.startswith(b'DXBC'):
        raise ValueError('Shader bytecode size/signature')
    return code
