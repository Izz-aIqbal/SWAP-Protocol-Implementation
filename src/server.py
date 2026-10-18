# src/server.py - COMPLETE WORKING SERVER
import socket
import threading
import logging
import time
import os
import struct
from datetime import datetime

# ==================== SWAP PROTOCOL CONSTANTS ====================
SWAP_MAGIC = 0xABCD
SWAP_VERSION = 0x01

# Message Types
SWAP_GET = 0x01
SWAP_POST = 0x02
SWAP_OK = 0x80
SWAP_NOT_FOUND = 0x81
SWAP_BAD_REQUEST = 0x82

# Content Type Codes
SWAP_CT_TEXT = 0x0001
SWAP_CT_HTML = 0x0002
SWAP_CT_JPEG = 0x0003
SWAP_CT_PNG = 0x0004
SWAP_CT_JSON = 0x0005
SWAP_CT_BINARY = 0x0006

# Protocol Settings
DEFAULT_PORT = 8080
MAX_PAYLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
HEADER_FORMAT = '!H B B H I H'  # Big-Endian, 12 bytes

# ==================== PROTOCOL FUNCTIONS ====================
def pack_header(msg_type, content_type, payload_len, options=0):
    """Pack SWAP header into 12-byte binary format"""
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
    """Unpack 12-byte binary header into fields"""
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
    """Determine content type from file extension"""
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
    """Convert content type code to string"""
    type_names = {
        SWAP_CT_TEXT: 'text/plain',
        SWAP_CT_HTML: 'text/html',
        SWAP_CT_JPEG: 'image/jpeg',
        SWAP_CT_PNG: 'image/png',
        SWAP_CT_JSON: 'application/json',
        SWAP_CT_BINARY: 'application/octet-stream'
    }
    return type_names.get(content_type, 'unknown')

# ==================== UTILITY FUNCTIONS ====================
def setup_logging():
    """Setup logging configuration"""
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/server.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def recv_exact(socket, n):
    """Receive exactly n bytes from socket"""
    data = b''
    while len(data) < n:
        chunk = socket.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
    return data

def send_all(socket, data):
    """Send all data through socket"""
    total_sent = 0
    while total_sent < len(data):
        sent = socket.send(data[total_sent:])
        if sent == 0:
            raise ConnectionError("Socket connection broken")
        total_sent += sent
    return total_sent

def sanitize_path(requested_path, root_dir):
    """Sanitize file path to prevent directory traversal"""
    # Remove leading slash and normalize
    requested_path = requested_path.lstrip('/')
    if not requested_path:
        requested_path = 'index.html'
    
    # Join with root directory
    full_path = os.path.normpath(os.path.join(root_dir, requested_path))
    
    # Ensure path is within root directory
    root_abs = os.path.abspath(root_dir)
    full_abs = os.path.abspath(full_path)
    
    if not full_abs.startswith(root_abs):
        raise ValueError(f"Security violation: Path traversal attempt")
    
    return full_path

# ==================== SWAP SERVER CLASS ====================
class SWAPServer:
    """SWAP Protocol Server Implementation"""
    
    def __init__(self, host='localhost', port=DEFAULT_PORT, root_dir='resources'):
        self.host = host
        self.port = port
        self.root_dir = root_dir
        self.logger = setup_logging()
        
        # Create directories
        os.makedirs(root_dir, exist_ok=True)
        os.makedirs(os.path.join(root_dir, 'uploads'), exist_ok=True)
        
        # Create sample files
        self._create_sample_files()
    
    def _create_sample_files(self):
        """Create sample files for testing"""
        samples = {
            'index.html': b'''<html>
<head><title>SWAP Server</title></head>
<body>
    <h1>Welcome to SWAP Protocol Server</h1>
    <p>This is a test HTML page served by SWAP protocol.</p>
    <p>Current time: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode() + b'''</p>
    <ul>
        <li><a href="/sample.txt">Sample Text File</a></li>
        <li><a href="/test.json">Sample JSON File</a></li>
    </ul>
</body>
</html>''',
            
            'sample.txt': b'''This is a sample text file for SWAP protocol testing.

SWAP Protocol Features:
- Binary header (12 bytes)
- Big-Endian byte order
- GET and POST methods
- Content type detection
- Persistent connections
- Error handling

File created: ''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode(),
            
            'test.json': b'''{
    "protocol": "SWAP",
    "version": "1.0",
    "status": "running",
    "features": ["GET", "POST", "binary_format", "content_types"],
    "port": 8080,
    "timestamp": "''' + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode() + b'''"
}'''
        }
        
        for filename, content in samples.items():
            filepath = os.path.join(self.root_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'wb') as f:
                    f.write(content)
                self.logger.info(f"Created sample file: {filename}")
    
    def handle_client(self, client_socket, client_address):
        """Handle a client connection"""
        client_ip = client_address[0]
        self.logger.info(f"New connection from {client_ip}")
        
        try:
            # Keep connection open for multiple requests
            while True:
                try:
                    # Read 12-byte header
                    header_data = recv_exact(client_socket, 12)
                except ConnectionError:
                    self.logger.info(f"Connection closed by {client_ip}")
                    break
                
                try:
                    # Parse header
                    header = unpack_header(header_data)
                    
                    # Log request
                    self.logger.info(f"Request from {client_ip}: type={header['type']}, "
                                   f"content_type={header['content_type']}, "
                                   f"payload_len={header['payload_len']}")
                    
                    # Validate payload size
                    if header['payload_len'] > MAX_PAYLOAD_SIZE:
                        raise ValueError(f"Payload too large: {header['payload_len']}")
                    
                    # Read payload
                    payload = recv_exact(client_socket, header['payload_len'])
                    
                except ValueError as e:
                    self.logger.error(f"Invalid request from {client_ip}: {e}")
                    error_msg = str(e).encode('utf-8')
                    response_header = pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg))
                    send_all(client_socket, response_header + error_msg)
                    continue
                
                # Process request
                response = self.process_request(header['type'], payload)
                
                # Send response
                response_data = response['header'] + response['payload']
                send_all(client_socket, response_data)
                
                self.logger.info(f"Sent response to {client_ip}: status={response['status']}, "
                               f"size={len(response['payload'])} bytes")
                
        except Exception as e:
            self.logger.error(f"Error handling client {client_ip}: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"Connection closed for {client_ip}")
    
    def process_request(self, msg_type, payload):
        """Process request and return response"""
        try:
            if msg_type == SWAP_GET:
                return self.handle_get(payload)
            elif msg_type == SWAP_POST:
                return self.handle_post(payload)
            else:
                error_msg = b'Unsupported message type'
                return {
                    'header': pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg)),
                    'payload': error_msg,
                    'status': 'BAD_REQUEST'
                }
                
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            error_msg = str(e).encode('utf-8')
            return {
                'header': pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg)),
                'payload': error_msg,
                'status': 'BAD_REQUEST'
            }
    
    def handle_get(self, payload):
        """Handle GET request"""
        try:
            # Extract requested path
            requested_path = payload.decode('utf-8').strip()
            self.logger.info(f"GET request for: {requested_path}")
            
            # Sanitize path
            full_path = sanitize_path(requested_path, self.root_dir)
            
            # Check if file exists
            if not os.path.exists(full_path):
                error_msg = f'File not found: {requested_path}'.encode('utf-8')
                self.logger.warning(f"File not found: {requested_path}")
                return {
                    'header': pack_header(SWAP_NOT_FOUND, SWAP_CT_TEXT, len(error_msg)),
                    'payload': error_msg,
                    'status': 'NOT_FOUND'
                }
            
            # Read file
            with open(full_path, 'rb') as f:
                file_data = f.read()
            
            # Determine content type
            content_type = get_content_type(full_path)
            
            self.logger.info(f"Serving file: {requested_path} ({len(file_data)} bytes, "
                           f"type: {content_type_to_string(content_type)})")
            
            return {
                'header': pack_header(SWAP_OK, content_type, len(file_data)),
                'payload': file_data,
                'status': 'OK'
            }
            
        except ValueError as e:
            self.logger.error(f"Path validation error: {e}")
            error_msg = str(e).encode('utf-8')
            return {
                'header': pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg)),
                'payload': error_msg,
                'status': 'BAD_REQUEST'
            }
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
            error_msg = str(e).encode('utf-8')
            return {
                'header': pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg)),
                'payload': error_msg,
                'status': 'BAD_REQUEST'
            }
    
    def handle_post(self, payload):
        """Handle POST request"""
        try:
            # Save uploaded data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upload_{timestamp}.dat"
            filepath = os.path.join(self.root_dir, 'uploads', filename)
            
            # Write data to file
            with open(filepath, 'wb') as f:
                f.write(payload)
            
            success_msg = f'Data ({len(payload)} bytes) saved as: {filename}'.encode('utf-8')
            self.logger.info(f"Saved upload: {filename} ({len(payload)} bytes)")
            
            return {
                'header': pack_header(SWAP_OK, SWAP_CT_TEXT, len(success_msg)),
                'payload': success_msg,
                'status': 'OK'
            }
            
        except Exception as e:
            self.logger.error(f"Error saving upload: {e}")
            error_msg = str(e).encode('utf-8')
            return {
                'header': pack_header(SWAP_BAD_REQUEST, SWAP_CT_TEXT, len(error_msg)),
                'payload': error_msg,
                'status': 'BAD_REQUEST'
            }
    
    def start(self):
        """Start the SWAP server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind to port
            server_socket.bind((self.host, self.port))
            server_socket.listen(100)  # Allow 100 queued connections
            server_socket.settimeout(1)  # Timeout for accept()
            
            print("\n" + "="*60)
            print("SWAP SERVER - Simple Web Access Protocol")
            print("="*60)
            print(f"Server running on: {self.host}:{self.port}")
            print(f"Serving files from: {os.path.abspath(self.root_dir)}")
            print(f"Log file: {os.path.abspath('logs/server.log')}")
            print("\nSample files available:")
            print("  GET /index.html    - HTML page")
            print("  GET /sample.txt    - Text file")
            print("  GET /test.json     - JSON data")
            print("\nPress Ctrl+C to stop the server")
            print("="*60 + "\n")
            
            self.logger.info(f"SWAP Server started on {self.host}:{self.port}")
            
            # Main server loop
            while True:
                try:
                    # Accept new connection
                    client_socket, client_address = server_socket.accept()
                    
                    # Handle client in new thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    # Timeout on accept, just continue
                    continue
                    
        except KeyboardInterrupt:
            print("\n" + "="*60)
            print("Server shutdown requested by user")
            print("="*60)
            self.logger.info("Server stopped by user")
            
        except Exception as e:
            print(f"\nServer error: {e}")
            self.logger.error(f"Server error: {e}")
            
        finally:
            server_socket.close()
            print("Server stopped")

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    # Create and start server
    server = SWAPServer(
        host='localhost',     # Listen on localhost
        port=8080,           # SWAP default port
        root_dir='resources' # Directory for files
    )
    server.start()