# src/protocol.py (if you don't have it)
import struct

# Constants (same as in server.py)
SWAP_MAGIC = 0xABCD
SWAP_VERSION = 0x01
SWAP_GET = 0x01
SWAP_POST = 0x02
SWAP_OK = 0x80
SWAP_NOT_FOUND = 0x81
SWAP_BAD_REQUEST = 0x82

SWAP_CT_TEXT = 0x0001
SWAP_CT_HTML = 0x0002
SWAP_CT_JPEG = 0x0003
SWAP_CT_PNG = 0x0004
SWAP_CT_JSON = 0x0005
SWAP_CT_BINARY = 0x0006

DEFAULT_PORT = 8080
HEADER_FORMAT = '!H B B H I H'

def pack_header(msg_type, content_type, payload_len, options=0):
    return struct.pack(
        HEADER_FORMAT,
        SWAP_MAGIC,
        SWAP_VERSION,
        msg_type,
        content_type,
        payload_len,
        options
    )

def unpack_header(header_bytes):
    if len(header_bytes) != 12:
        raise ValueError(f"Header must be 12 bytes, got {len(header_bytes)}")
    
    magic, version, msg_type, content_type, payload_len, options = struct.unpack(
        HEADER_FORMAT, header_bytes
    )
    
    if magic != SWAP_MAGIC:
        raise ValueError(f"Invalid magic number: 0x{magic:04X}")
    
    if version != SWAP_VERSION:
        raise ValueError(f"Unsupported version: {version}")
    
    return {
        'magic': magic,
        'version': version,
        'type': msg_type,
        'content_type': content_type,
        'payload_len': payload_len,
        'options': options
    }

def get_content_type(filename):
    if not filename or '.' not in filename:
        return SWAP_CT_BINARY
    
    ext = filename.lower().split('.')[-1]
    
    type_map = {
        'txt': SWAP_CT_TEXT,
        'html': SWAP_CT_HTML,
        'htm': SWAP_CT_HTML,
        'jpg': SWAP_CT_JPEG,
        'jpeg': SWAP_CT_JPEG,
        'png': SWAP_CT_PNG,
        'json': SWAP_CT_JSON,
    }
    
    return type_map.get(ext, SWAP_CT_BINARY)

def content_type_to_string(content_type):
    type_names = {
        SWAP_CT_TEXT: 'text/plain',
        SWAP_CT_HTML: 'text/html',
        SWAP_CT_JPEG: 'image/jpeg',
        SWAP_CT_PNG: 'image/png',
        SWAP_CT_JSON: 'application/json',
        SWAP_CT_BINARY: 'application/octet-stream'
    }
    return type_names.get(content_type, 'unknown')

class SWAPMessage:
    def __init__(self, msg_type, content_type, payload=b'', options=0):
        self.type = msg_type
        self.content_type = content_type
        self.payload = payload
        self.options = options
        self.payload_len = len(payload)
    
    def pack(self):
        header = pack_header(self.type, self.content_type, self.payload_len, self.options)
        return header + self.payload
    
    @classmethod
    def unpack(cls, data):
        if len(data) < 12:
            raise ValueError("Data too short for SWAP header")
        
        header = unpack_header(data[:12])
        payload = data[12:12+header['payload_len']]
        
        if len(payload) != header['payload_len']:
            raise ValueError(f"Payload length mismatch")
        
        return cls(
            header['type'],
            header['content_type'],
            payload,
            header['options']
        )
    
    def __str__(self):
        type_names = {
            SWAP_GET: 'GET',
            SWAP_POST: 'POST',
            SWAP_OK: 'OK',
            SWAP_NOT_FOUND: 'NOT_FOUND',
            SWAP_BAD_REQUEST: 'BAD_REQUEST'
        }
        return (f"SWAPMessage(type={type_names.get(self.type, 'UNKNOWN')}, "
                f"content_type=0x{self.content_type:04X}, "
                f"payload_len={self.payload_len}, options=0x{self.options:04X})")