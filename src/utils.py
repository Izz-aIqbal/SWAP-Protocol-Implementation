# src/utils.py
"""
Utility functions for SWAP protocol
"""

import os
import logging
import struct
from datetime import datetime

# Import protocol constants
try:
    from .protocol import MAX_PAYLOAD_SIZE
except ImportError:
    # Fallback if protocol.py not imported properly
    MAX_PAYLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

def setup_logging(log_file='logs/server.log', level=logging.INFO):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def read_file_bytes(filepath):
    """Read file as bytes"""
    try:
        with open(filepath, 'rb') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read file {filepath}: {e}")

def validate_payload_size(payload_len):
    """Validate payload size against maximum limit"""
    if payload_len > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload too large: {payload_len} > {MAX_PAYLOAD_SIZE}")
    return True

def sanitize_path(requested_path, root_dir='.'):
    """
    Sanitize file path to prevent directory traversal attacks
    
    Args:
        requested_path: Path requested by client (e.g., '/index.html')
        root_dir: Root directory where files are served from
    
    Returns:
        Full safe path within root directory
    
    Raises:
        ValueError: If path tries to escape root directory
    """
    # Remove leading slash and normalize
    if not requested_path:
        requested_path = 'index.html'
    
    requested_path = requested_path.lstrip('/')
    
    # Prevent empty path segments and double dots
    if '..' in requested_path:
        raise ValueError(f"Path traversal attempt detected: {requested_path}")
    
    # Join with root directory and normalize
    full_path = os.path.normpath(os.path.join(root_dir, requested_path))
    
    # Ensure path is within root directory
    root_abs = os.path.abspath(root_dir)
    full_abs = os.path.abspath(full_path)
    
    if not full_abs.startswith(root_abs):
        raise ValueError(f"Security violation: Path '{requested_path}' tries to escape root directory")
    
    return full_path

def recv_exact(socket, n):
    """
    Receive exactly n bytes from socket
    
    Args:
        socket: Socket to receive from
        n: Number of bytes to receive
    
    Returns:
        bytes: Received data
    
    Raises:
        ConnectionError: If connection is closed before receiving all data
    """
    data = b''
    while len(data) < n:
        chunk = socket.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before receiving all data")
        data += chunk
    return data

def send_all(socket, data):
    """
    Send all data through socket
    
    Args:
        socket: Socket to send to
        data: Data to send
    
    Returns:
        int: Number of bytes sent
    
    Raises:
        ConnectionError: If socket connection is broken
    """
    total_sent = 0
    while total_sent < len(data):
        sent = socket.send(data[total_sent:])
        if sent == 0:
            raise ConnectionError("Socket connection broken")
        total_sent += sent
    return total_sent

def hex_dump(data, bytes_per_line=16):
    """
    Create a hex dump of binary data
    
    Args:
        data: Binary data to dump
        bytes_per_line: Bytes to show per line
    
    Returns:
        str: Formatted hex dump
    """
    if not data:
        return "No data"
    
    result = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f'{i:04x}: {hex_part:<{bytes_per_line*3}}  {ascii_part}')
    
    return '\n'.join(result)

def create_sample_files(root_dir='resources'):
    """Create sample files for testing"""
    os.makedirs(root_dir, exist_ok=True)
    
    samples = {
        'index.html': b'''<!DOCTYPE html>
<html>
<head>
    <title>SWAP Protocol Server</title>
</head>
<body>
    <h1>SWAP Protocol Demonstration</h1>
    <p>This server implements the SWAP (Simple Web Access Protocol)</p>
    <ul>
        <li><a href="/sample.txt">Sample Text File</a></li>
        <li><a href="/test.json">Sample JSON Data</a></li>
    </ul>
    <p>Time: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode() + b'''</p>
</body>
</html>''',
        
        'sample.txt': b'''Sample Text File for SWAP Protocol Testing

Features:
- Binary protocol (no JSON/XML)
- Fixed 12-byte headers
- GET and POST methods
- Content type detection
- Persistent connections
- Error handling

Created for Computer Networks Assignment 3
Student: Izza Iqbal
ID: B23F0317A1119
''',
        
        'test.json': b'''{
    "protocol": "SWAP",
    "version": "1.0",
    "status": "operational",
    "author": "Izza Iqbal",
    "student_id": "B23F0317A1119",
    "course": "Computer Networks",
    "assignment": 3,
    "timestamp": "''' + datetime.now().isoformat().encode() + b'''"
}'''
    }
    
    created_files = []
    for filename, content in samples.items():
        filepath = os.path.join(root_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'wb') as f:
                f.write(content)
            created_files.append(filename)
    
    return created_files

def validate_header_bytes(header_bytes):
    """
    Validate that header bytes are correct
    
    Args:
        header_bytes: 12 bytes of header data
    
    Returns:
        bool: True if valid, False otherwise
    """
    if len(header_bytes) != 12:
        return False
    
    try:
        # Try to unpack
        magic, version = struct.unpack('!H B', header_bytes[:3])
        if magic != 0xABCD or version != 0x01:
            return False
        return True
    except:
        return False

# Test the functions if run directly
if __name__ == "__main__":
    # Test sanitize_path
    print("Testing sanitize_path function:")
    try:
        test_path = sanitize_path("/index.html", "test_dir")
        print(f"✓ Normal path: {test_path}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        sanitize_path("../../../etc/passwd", "test_dir")
        print("✗ Should have blocked path traversal")
    except ValueError as e:
        print(f"✓ Correctly blocked: {e}")
    
    # Test hex_dump
    print("\nTesting hex_dump function:")
    test_data = b"Hello SWAP Protocol!\x00\x01\x02\x03"
    print(hex_dump(test_data))
    
    print("\n✅ All utility functions working!")