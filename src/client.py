# src/client.py - COMPLETE WORKING CLIENT
import socket
import struct
import argparse
import os

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
    
    return struct.unpack(HEADER_FORMAT, header_bytes)

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

# ==================== SWAP CLIENT CLASS ====================
class SWAPClient:
    """SWAP Protocol Client Implementation"""
    
    def __init__(self, server_host='localhost', server_port=DEFAULT_PORT):
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
    
    def connect(self):
        """Connect to SWAP server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            self.socket.connect((self.server_host, self.server_port))
            print(f"✅ Connected to SWAP server at {self.server_host}:{self.server_port}")
            return True
        except socket.timeout:
            print(f"❌ Connection timeout to {self.server_host}:{self.server_port}")
            return False
        except ConnectionRefusedError:
            print(f"❌ Connection refused. Make sure server is running on port {self.server_port}")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
            self.socket = None
            print("✅ Disconnected from server")
    
    def send_request(self, msg_type, payload, content_type=SWAP_CT_BINARY):
        """Send request and receive response"""
        try:
            # Pack and send header
            header = pack_header(msg_type, content_type, len(payload))
            send_all(self.socket, header)
            
            # Send payload
            if payload:
                send_all(self.socket, payload)
            
            # Receive response header
            response_header = recv_exact(self.socket, 12)
            magic, version, resp_type, resp_content_type, payload_len, options = unpack_header(response_header)
            
            # Validate magic and version
            if magic != SWAP_MAGIC:
                print(f"❌ Invalid magic number in response: 0x{magic:04X}")
                return None
            
            if version != SWAP_VERSION:
                print(f"❌ Unsupported protocol version: {version}")
                return None
            
            # Receive payload
            response_payload = recv_exact(self.socket, payload_len) if payload_len > 0 else b''
            
            return {
                'type': resp_type,
                'content_type': resp_content_type,
                'payload': response_payload,
                'options': options
            }
            
        except socket.timeout:
            print("❌ Request timeout")
            return None
        except ConnectionError as e:
            print(f"❌ Connection error: {e}")
            return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def get_file(self, resource_path, save_as=None):
        """GET a file from server"""
        print(f"\n📥 GET Request: {resource_path}")
        
        # Send GET request
        response = self.send_request(
            SWAP_GET,
            resource_path.encode('utf-8'),
            get_content_type(resource_path)
        )
        
        if not response:
            return False
        
        # Handle response
        if response['type'] == SWAP_OK:
            print(f"✅ Success! Received {len(response['payload'])} bytes")
            print(f"   Content Type: {content_type_to_string(response['content_type'])}")
            
            # Save file if requested
            if save_as:
                os.makedirs(os.path.dirname(save_as) if os.path.dirname(save_as) else '.', exist_ok=True)
                with open(save_as, 'wb') as f:
                    f.write(response['payload'])
                print(f"✅ File saved as: {save_as}")
            
            # Display text content
            if response['content_type'] in [SWAP_CT_TEXT, SWAP_CT_HTML, SWAP_CT_JSON]:
                try:
                    content = response['payload'].decode('utf-8')
                    print("\n📄 Content:")
                    print("-" * 40)
                    print(content[:1000])
                    if len(content) > 1000:
                        print("... [truncated]")
                    print("-" * 40)
                except:
                    print("   (Binary content)")
            
            return True
            
        elif response['type'] == SWAP_NOT_FOUND:
            error_msg = response['payload'].decode('utf-8', errors='ignore')
            print(f"❌ File not found: {resource_path}")
            print(f"   Server: {error_msg}")
            return False
            
        elif response['type'] == SWAP_BAD_REQUEST:
            error_msg = response['payload'].decode('utf-8', errors='ignore')
            print(f"❌ Bad request: {error_msg}")
            return False
            
        else:
            print(f"❌ Unexpected response type: 0x{response['type']:02X}")
            return False
    
    def post_data(self, data, description="data"):
        """POST data to server"""
        print(f"\n📤 POST Request: {len(data)} bytes of {description}")
        
        response = self.send_request(
            SWAP_POST,
            data,
            SWAP_CT_BINARY
        )
        
        if not response:
            return False
        
        if response['type'] == SWAP_OK:
            success_msg = response['payload'].decode('utf-8', errors='ignore')
            print(f"✅ POST successful: {success_msg}")
            return True
        else:
            error_msg = response['payload'].decode('utf-8', errors='ignore')
            print(f"❌ POST failed: {error_msg}")
            return False
    
    def test_connection(self):
        """Test connection to server"""
        print("\n🔍 Testing connection to server...")
        if self.connect():
            print("✅ Connection test passed")
            self.disconnect()
            return True
        else:
            print("❌ Connection test failed")
            return False

# ==================== COMMAND LINE INTERFACE ====================
def print_banner():
    print("\n" + "="*60)
    print("SWAP CLIENT - Simple Web Access Protocol")
    print("="*60)

def print_help():
    print("\nAvailable commands:")
    print("  get <path> [save_as]  - GET a file (optional save)")
    print("  post <text>           - POST text data")
    print("  file <filename>       - POST file content")
    print("  test                  - Test connection")
    print("  help                  - Show this help")
    print("  quit                  - Exit client")
    print("\nExamples:")
    print("  get /index.html")
    print("  get /sample.txt saved.txt")
    print("  post Hello from SWAP client")
    print("  file mydata.txt")
    print("="*60)

def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description='SWAP Protocol Client')
    parser.add_argument('--server', default='localhost', help='Server hostname (default: localhost)')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'Server port (default: {DEFAULT_PORT})')
    parser.add_argument('--get', help='GET a resource (e.g., /index.html)')
    parser.add_argument('--save', help='Save GET response to file')
    parser.add_argument('--post', help='POST text data')
    parser.add_argument('--file', help='POST data from file')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    
    args = parser.parse_args()
    
    # Create client
    client = SWAPClient(args.server, args.port)
    
    # If test mode
    if args.test:
        client.test_connection()
        return
    
    # If command-line arguments provided
    if args.get:
        if client.connect():
            client.get_file(args.get, args.save)
            client.disconnect()
        return
    
    if args.post:
        if client.connect():
            client.post_data(args.post.encode('utf-8'), "text")
            client.disconnect()
        return
    
    if args.file:
        try:
            with open(args.file, 'rb') as f:
                data = f.read()
            if client.connect():
                client.post_data(data, f"file '{args.file}'")
                client.disconnect()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
        return
    
    # Interactive mode
    print_banner()
    print_help()
    
    if not client.connect():
        print("\n❌ Cannot connect to server. Exiting.")
        return
    
    try:
        while True:
            try:
                cmd = input("\nswap> ").strip()
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == 'quit' or command == 'exit':
                    print("Goodbye!")
                    break
                
                elif command == 'help':
                    print_help()
                
                elif command == 'test':
                    client.test_connection()
                
                elif command == 'get' and len(parts) > 1:
                    save_as = parts[2] if len(parts) > 2 else None
                    client.get_file(parts[1], save_as)
                
                elif command == 'post' and len(parts) > 1:
                    text_data = ' '.join(parts[1:])
                    client.post_data(text_data.encode('utf-8'), "text")
                
                elif command == 'file' and len(parts) > 1:
                    try:
                        with open(parts[1], 'rb') as f:
                            data = f.read()
                        client.post_data(data, f"file '{parts[1]}'")
                    except FileNotFoundError:
                        print(f"❌ File not found: {parts[1]}")
                
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    finally:
        client.disconnect()

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    main()