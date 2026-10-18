# tests/test_protocol.py - SWAP Protocol Unit Tests
import unittest
import sys
import os
import socket
import threading
import time

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import from our project
from src.protocol import *

class TestProtocolConstants(unittest.TestCase):
    """Test protocol constants and basic values"""
    
    def test_constants(self):
        """Test that all constants are defined correctly"""
        print("📊 Testing protocol constants...")
        
        # Magic number
        self.assertEqual(SWAP_MAGIC, 0xABCD, "Magic number should be 0xABCD")
        
        # Version
        self.assertEqual(SWAP_VERSION, 0x01, "Version should be 0x01")
        
        # Message types
        self.assertEqual(SWAP_GET, 0x01, "SWAP_GET should be 0x01")
        self.assertEqual(SWAP_POST, 0x02, "SWAP_POST should be 0x02")
        self.assertEqual(SWAP_OK, 0x80, "SWAP_OK should be 0x80")
        self.assertEqual(SWAP_NOT_FOUND, 0x81, "SWAP_NOT_FOUND should be 0x81")
        self.assertEqual(SWAP_BAD_REQUEST, 0x82, "SWAP_BAD_REQUEST should be 0x82")
        
        # Content types
        self.assertEqual(SWAP_CT_TEXT, 0x0001, "SWAP_CT_TEXT should be 0x0001")
        self.assertEqual(SWAP_CT_HTML, 0x0002, "SWAP_CT_HTML should be 0x0002")
        self.assertEqual(SWAP_CT_JSON, 0x0005, "SWAP_CT_JSON should be 0x0005")
        self.assertEqual(SWAP_CT_BINARY, 0x0006, "SWAP_CT_BINARY should be 0x0006")
        
        # Port
        self.assertEqual(DEFAULT_PORT, 8080, "Default port should be 8080")
        
        print("✅ All constants are correct!")

class TestHeaderPacking(unittest.TestCase):
    """Test header packing and unpacking"""
    
    def test_pack_header_basic(self):
        """Test basic header packing"""
        print("\n📦 Testing basic header packing...")
        
        # Pack a simple GET header
        header = pack_header(SWAP_GET, SWAP_CT_HTML, 100)
        
        # Check length (should be 12 bytes)
        self.assertEqual(len(header), 12, "Header should be 12 bytes")
        
        print("✅ Basic header packing test passed")
    
    def test_unpack_header_basic(self):
        """Test header unpacking"""
        print("\n📦 Testing header unpacking...")
        
        # Pack then unpack
        header = pack_header(SWAP_POST, SWAP_CT_JSON, 500, 0x0001)
        unpacked = unpack_header(header)
        
        # Verify values
        self.assertEqual(unpacked['magic'], SWAP_MAGIC)
        self.assertEqual(unpacked['version'], SWAP_VERSION)
        self.assertEqual(unpacked['type'], SWAP_POST)
        self.assertEqual(unpacked['content_type'], SWAP_CT_JSON)
        self.assertEqual(unpacked['payload_len'], 500)
        self.assertEqual(unpacked['options'], 0x0001)
        
        print("✅ Header unpacking test passed")
    
    def test_header_roundtrip(self):
        """Test pack -> unpack -> same values"""
        print("\n🔄 Testing header roundtrip...")
        
        test_cases = [
            (SWAP_GET, SWAP_CT_HTML, 0, 0x0000),
            (SWAP_POST, SWAP_CT_JSON, 1024, 0x0001),
            (SWAP_OK, SWAP_CT_TEXT, 65535, 0xFFFF),
            (SWAP_NOT_FOUND, SWAP_CT_BINARY, 1, 0x0101),
        ]
        
        for msg_type, content_type, payload_len, options in test_cases:
            header = pack_header(msg_type, content_type, payload_len, options)
            unpacked = unpack_header(header)
            
            self.assertEqual(unpacked['type'], msg_type)
            self.assertEqual(unpacked['content_type'], content_type)
            self.assertEqual(unpacked['payload_len'], payload_len)
            self.assertEqual(unpacked['options'], options)
        
        print("✅ Header roundtrip tests passed")
    
    def test_invalid_header_length(self):
        """Test error for invalid header length"""
        print("\n⚠️ Testing invalid header length error...")
        
        with self.assertRaises(ValueError):
            unpack_header(b'too short')
        
        with self.assertRaises(ValueError):
            unpack_header(b'too' * 10)  # Too long
            
        print("✅ Invalid header length error handling works")
    
    def test_invalid_magic(self):
        """Test error for wrong magic number"""
        print("\n⚠️ Testing invalid magic number error...")
        
        # Create header with wrong magic
        wrong_header = struct.pack('!H B B H I H', 
                                  0x1234,  # Wrong magic
                                  SWAP_VERSION,
                                  SWAP_GET,
                                  SWAP_CT_HTML,
                                  100,
                                  0)
        
        with self.assertRaises(ValueError) as context:
            unpack_header(wrong_header)
        
        self.assertIn("Invalid magic number", str(context.exception))
        print("✅ Invalid magic number detection works")
    
    def test_invalid_version(self):
        """Test error for wrong version"""
        print("\n⚠️ Testing invalid version error...")
        
        # Create header with wrong version
        wrong_header = struct.pack('!H B B H I H',
                                  SWAP_MAGIC,
                                  0x99,  # Wrong version
                                  SWAP_GET,
                                  SWAP_CT_HTML,
                                  100,
                                  0)
        
        with self.assertRaises(ValueError) as context:
            unpack_header(wrong_header)
        
        self.assertIn("Unsupported version", str(context.exception))
        print("✅ Invalid version detection works")

class TestContentTypeDetection(unittest.TestCase):
    """Test content type detection from filenames"""
    
    def test_get_content_type(self):
        """Test content type detection"""
        print("\n📁 Testing content type detection...")
        
        test_cases = [
            ('index.html', SWAP_CT_HTML),
            ('page.htm', SWAP_CT_HTML),
            ('document.txt', SWAP_CT_TEXT),
            ('data.json', SWAP_CT_JSON),
            ('image.jpg', SWAP_CT_JPEG),
            ('picture.jpeg', SWAP_CT_JPEG),
            ('graphic.png', SWAP_CT_PNG),
            ('unknown.xyz', SWAP_CT_BINARY),
            ('noextension', SWAP_CT_BINARY),
            ('', SWAP_CT_BINARY),
        ]
        
        for filename, expected_type in test_cases:
            detected = get_content_type(filename)
            self.assertEqual(detected, expected_type, 
                           f"Filename '{filename}' should be {hex(expected_type)}")
        
        print("✅ Content type detection works correctly")

class TestSWAPMessageClass(unittest.TestCase):
    """Test SWAPMessage class"""
    
    def test_message_creation(self):
        """Test creating SWAPMessage objects"""
        print("\n📨 Testing SWAPMessage creation...")
        
        # Create message
        message = SWAPMessage(SWAP_OK, SWAP_CT_TEXT, b'Hello World', 0x0001)
        
        # Check attributes
        self.assertEqual(message.type, SWAP_OK)
        self.assertEqual(message.content_type, SWAP_CT_TEXT)
        self.assertEqual(message.payload, b'Hello World')
        self.assertEqual(message.options, 0x0001)
        self.assertEqual(message.payload_len, 11)  # len('Hello World')
        
        print("✅ Message creation works")
    
    def test_message_packing(self):
        """Test message packing"""
        print("\n📨 Testing message packing...")
        
        # Create and pack message
        message = SWAPMessage(SWAP_POST, SWAP_CT_JSON, b'{"test": true}')
        packed = message.pack()
        
        # Should be header (12 bytes) + payload
        expected_len = 12 + len(b'{"test": true}')
        self.assertEqual(len(packed), expected_len)
        
        print("✅ Message packing works")
    
    def test_message_unpacking(self):
        """Test message unpacking"""
        print("\n📨 Testing message unpacking...")
        
        # Create original message
        original = SWAPMessage(SWAP_GET, SWAP_CT_HTML, b'/index.html', 0x0000)
        packed = original.pack()
        
        # Unpack
        unpacked = SWAPMessage.unpack(packed)
        
        # Should be identical
        self.assertEqual(unpacked.type, original.type)
        self.assertEqual(unpacked.content_type, original.content_type)
        self.assertEqual(unpacked.payload, original.payload)
        self.assertEqual(unpacked.options, original.options)
        self.assertEqual(unpacked.payload_len, original.payload_len)
        
        print("✅ Message unpacking works")
    
    def test_message_roundtrip(self):
        """Test pack -> unpack roundtrip"""
        print("\n🔄 Testing message roundtrip...")
        
        test_messages = [
            SWAPMessage(SWAP_GET, SWAP_CT_HTML, b'/index.html'),
            SWAPMessage(SWAP_POST, SWAP_CT_JSON, b'{"data": "test"}', 0x0001),
            SWAPMessage(SWAP_OK, SWAP_CT_TEXT, b'Success!'),
            SWAPMessage(SWAP_NOT_FOUND, SWAP_CT_TEXT, b'File not found'),
            SWAPMessage(SWAP_BAD_REQUEST, SWAP_CT_TEXT, b'Invalid request'),
        ]
        
        for original in test_messages:
            packed = original.pack()
            unpacked = SWAPMessage.unpack(packed)
            
            self.assertEqual(unpacked.type, original.type)
            self.assertEqual(unpacked.content_type, original.content_type)
            self.assertEqual(unpacked.payload, original.payload)
            self.assertEqual(unpacked.options, original.options)
        
        print("✅ Message roundtrip tests passed")
    
    def test_string_representation(self):
        """Test __str__ method"""
        print("\n📝 Testing string representation...")
        
        message = SWAPMessage(SWAP_GET, SWAP_CT_HTML, b'test')
        str_repr = str(message)
        
        # Should contain type name
        self.assertIn('GET', str_repr)
        self.assertIn('content_type', str_repr)
        self.assertIn('payload_len', str_repr)
        
        print("✅ String representation works")

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_content_type_to_string(self):
        """Test content type code to string conversion"""
        print("\n🔤 Testing content type to string...")
        
        test_cases = [
            (SWAP_CT_TEXT, 'text/plain'),
            (SWAP_CT_HTML, 'text/html'),
            (SWAP_CT_JSON, 'application/json'),
            (SWAP_CT_BINARY, 'application/octet-stream'),
            (0x9999, 'unknown'),  # Unknown code
        ]
        
        for code, expected_string in test_cases:
            result = content_type_to_string(code)
            self.assertEqual(result, expected_string)
        
        print("✅ Content type to string conversion works")

class TestNetworkFunctions(unittest.TestCase):
    """Test network-related functions (requires server running)"""
    
    @classmethod
    def setUpClass(cls):
        """Start a test server"""
        print("\n🌐 Setting up test server...")
        
        from src.server import SWAPServer
        
        # Create test server on different port
        cls.test_server = SWAPServer(host='localhost', port=8888, root_dir='test_resources')
        
        # Start server in background thread
        cls.server_thread = threading.Thread(target=cls.test_server.start, daemon=True)
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        print("✅ Test server started on port 8888")
    
    def test_basic_connection(self):
        """Test basic TCP connection to server"""
        print("\n🔌 Testing basic connection...")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(('localhost', 8888))
            sock.close()
            print("✅ Basic connection test passed")
        except Exception as e:
            self.fail(f"Connection failed: {e}")
    
    def test_protocol_communication(self):
        """Test actual protocol communication"""
        print("\n📡 Testing protocol communication...")
        
        try:
            # Connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(('localhost', 8888))
            
            # Send GET request for index.html
            header = pack_header(SWAP_GET, SWAP_CT_HTML, 11)  # 11 bytes for "/index.html"
            payload = b'/index.html'
            
            sock.sendall(header + payload)
            
            # Receive response header
            response_header = sock.recv(12)
            self.assertEqual(len(response_header), 12, "Should receive 12-byte header")
            
            # Parse header
            parsed = unpack_header(response_header)
            
            # Check it's a valid response
            self.assertEqual(parsed['magic'], SWAP_MAGIC)
            self.assertEqual(parsed['version'], SWAP_VERSION)
            
            # Receive payload
            if parsed['payload_len'] > 0:
                payload = sock.recv(parsed['payload_len'])
                self.assertEqual(len(payload), parsed['payload_len'])
            
            sock.close()
            print("✅ Protocol communication test passed")
            
        except Exception as e:
            self.fail(f"Protocol communication failed: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup after tests"""
        print("\n🧹 Cleaning up test resources...")
        
        # Remove test directory if it exists
        import shutil
        if os.path.exists('test_resources'):
            shutil.rmtree('test_resources')
        
        print("✅ Cleanup complete")

def run_all_tests():
    """Run all tests with nice formatting"""
    print("\n" + "="*70)
    print("              SWAP PROTOCOL - UNIT TESTS")
    print("="*70)
    print(f"Python: {sys.version}")
    print(f"Directory: {os.getcwd()}")
    print("="*70)
    
    # Create test suite
    loader = unittest.TestLoader()
    
    # Add test classes
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestProtocolConstants))
    suite.addTests(loader.loadTestsFromTestCase(TestHeaderPacking))
    suite.addTests(loader.loadTestsFromTestCase(TestContentTypeDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestSWAPMessageClass))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilityFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, descriptions=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("                  TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}")
    
    if result.errors:
        print("\n⚠️ ERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! ✅")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    print("="*70)
    
    return result.wasSuccessful()

def quick_test():
    """Run quick basic tests only"""
    print("\n⚡ QUICK TESTS - Basic functionality only")
    
    # Run basic tests without network tests
    basic_tests = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    basic_tests.addTests(loader.loadTestsFromTestCase(TestProtocolConstants))
    basic_tests.addTests(loader.loadTestsFromTestCase(TestHeaderPacking))
    basic_tests.addTests(loader.loadTestsFromTestCase(TestContentTypeDetection))
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(basic_tests)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='SWAP Protocol Unit Tests')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--list', action='store_true', help='List all tests')
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 Available Tests:")
        print("-" * 40)
        for test_class in [TestProtocolConstants, TestHeaderPacking, 
                          TestContentTypeDetection, TestSWAPMessageClass,
                          TestUtilityFunctions, TestNetworkFunctions]:
            print(f"\n{test_class.__name__}:")
            loader = unittest.TestLoader()
            tests = loader.getTestCaseNames(test_class)
            for test in tests:
                print(f"  • {test}")
        print("-" * 40)
        sys.exit(0)
    
    if args.quick:
        success = quick_test()
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)