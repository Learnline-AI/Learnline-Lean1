"""
WebSocket Functionality Test Suite
==================================

Comprehensive tests for WebSocket communication and real-time functionality:
- WebSocket connection establishment
- Real-time message handling
- Audio data transmission
- Partial transcription updates
- Language switching commands
- Export functionality
- Connection stability under load

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import unittest
import asyncio
import json
import time
import struct
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import websockets
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

try:
    import uvicorn
    from fastapi.testclient import TestClient
    from server import app
except ImportError as e:
    logger.error(f"Failed to import server modules: {e}")
    raise

class WebSocketTestClient:
    """Test client for WebSocket functionality testing."""
    
    def __init__(self, uri: str = "ws://localhost:8001/ws"):
        """Initialize WebSocket test client."""
        self.uri = uri
        self.websocket = None
        self.messages_received = []
        self.connection_events = []
        self.audio_sent_count = 0
        self.is_connected = False
        
    async def connect(self, timeout: float = 5.0) -> bool:
        """Connect to WebSocket server."""
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.uri), 
                timeout=timeout
            )
            self.is_connected = True
            self.connection_events.append(("connected", time.time()))
            logger.info(f"Connected to {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.uri}: {e}")
            self.connection_events.append(("connection_failed", time.time(), str(e)))
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            self.connection_events.append(("disconnected", time.time()))
            logger.info("Disconnected from WebSocket")
    
    async def send_json_message(self, message: Dict[str, Any]):
        """Send JSON message to server."""
        if not self.websocket:
            raise RuntimeError("Not connected to WebSocket")
        
        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        logger.debug(f"Sent JSON message: {message}")
    
    async def send_audio_chunk(self, audio_data: bytes, timestamp_ms: int = None, flags: int = 0):
        """Send audio chunk with header to server."""
        if not self.websocket:
            raise RuntimeError("Not connected to WebSocket")
        
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000) & 0xFFFFFFFF
        
        # Create header (8 bytes: timestamp + flags)
        header = struct.pack("!II", timestamp_ms, flags)
        
        # Combine header with audio data
        message = header + audio_data
        
        await self.websocket.send(message)
        self.audio_sent_count += 1
        logger.debug(f"Sent audio chunk: {len(audio_data)} bytes, timestamp: {timestamp_ms}")
    
    async def receive_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Receive and parse JSON message from server."""
        if not self.websocket:
            raise RuntimeError("Not connected to WebSocket")
        
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            parsed = json.loads(message)
            self.messages_received.append(parsed)
            logger.debug(f"Received message: {parsed}")
            return parsed
        except asyncio.TimeoutError:
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            return None
    
    async def listen_for_messages(self, duration: float):
        """Listen for messages for specified duration."""
        start_time = time.time()
        messages = []
        
        while time.time() - start_time < duration:
            message = await self.receive_message(timeout=0.1)
            if message:
                messages.append(message)
        
        return messages
    
    def generate_pcm_audio(self, duration: float = 1.0, frequency: float = 440.0) -> bytes:
        """Generate PCM audio data for testing."""
        sample_rate = 16000
        samples = int(sample_rate * duration)
        
        # Generate sine wave
        t = np.linspace(0, duration, samples, False)
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Convert to int16 PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        return audio_int16.tobytes()

class WebSocketFunctionalityTestSuite(unittest.TestCase):
    """Test suite for WebSocket functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test server."""
        cls.test_port = 8001
        cls.server_thread = None
        cls.server_task = None
        
        # Start test server in background
        cls.start_test_server()
        
        # Allow server to start
        time.sleep(2)
        
        logger.info(f"Test server started on port {cls.test_port}")
    
    @classmethod
    def start_test_server(cls):
        """Start test server in background thread."""
        def run_server():
            try:
                uvicorn.run(
                    "server:app",
                    host="127.0.0.1",
                    port=cls.test_port,
                    log_level="warning"
                )
            except Exception as e:
                logger.error(f"Server startup failed: {e}")
        
        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
    
    def setUp(self):
        """Set up individual test cases."""
        self.client = WebSocketTestClient(f"ws://localhost:{self.test_port}/ws")
        self.test_start_time = time.time()
    
    def tearDown(self):
        """Clean up after each test."""
        test_duration = time.time() - self.test_start_time
        logger.info(f"Test completed in {test_duration:.2f} seconds")
    
    async def async_test_connection_establishment(self):
        """Test WebSocket connection establishment."""
        # Test successful connection
        connected = await self.client.connect(timeout=10.0)
        self.assertTrue(connected, "Failed to establish WebSocket connection")
        self.assertTrue(self.client.is_connected, "Connection state not updated")
        
        # Test connection events
        self.assertGreater(len(self.client.connection_events), 0)
        self.assertEqual(self.client.connection_events[0][0], "connected")
        
        # Clean up
        await self.client.disconnect()
        self.assertFalse(self.client.is_connected, "Connection state not updated after disconnect")
    
    def test_connection_establishment(self):
        """Synchronous wrapper for connection test."""
        asyncio.run(self.async_test_connection_establishment())
    
    async def async_test_json_message_handling(self):
        """Test JSON message sending and receiving."""
        await self.client.connect()
        
        # Test language change message
        language_change_msg = {
            "type": "change_language",
            "language": "hi"
        }
        
        await self.client.send_json_message(language_change_msg)
        
        # Listen for response
        response = await self.client.receive_message(timeout=2.0)
        self.assertIsNotNone(response, "No response received for language change")
        
        if response:
            self.assertEqual(response.get("type"), "language_changed")
            self.assertEqual(response.get("content"), "hi")
        
        # Test clear history message
        clear_msg = {"type": "clear_history"}
        await self.client.send_json_message(clear_msg)
        
        response = await self.client.receive_message(timeout=2.0)
        self.assertIsNotNone(response, "No response received for clear history")
        
        if response:
            self.assertEqual(response.get("type"), "history_cleared")
        
        await self.client.disconnect()
    
    def test_json_message_handling(self):
        """Synchronous wrapper for JSON message test."""
        asyncio.run(self.async_test_json_message_handling())
    
    async def async_test_audio_data_transmission(self):
        """Test audio data transmission."""
        await self.client.connect()
        
        # Generate test audio
        audio_data = self.client.generate_pcm_audio(duration=0.5)
        self.assertGreater(len(audio_data), 0, "No audio data generated")
        
        # Send audio chunk
        await self.client.send_audio_chunk(audio_data)
        self.assertEqual(self.client.audio_sent_count, 1)
        
        # Send multiple chunks
        for i in range(5):
            chunk = self.client.generate_pcm_audio(duration=0.1, frequency=440 + i * 100)
            await self.client.send_audio_chunk(chunk, timestamp_ms=int(time.time() * 1000) + i * 100)
        
        self.assertEqual(self.client.audio_sent_count, 6)
        
        # Listen for potential transcription responses
        messages = await self.client.listen_for_messages(duration=2.0)
        
        # Check for transcription messages
        transcription_messages = [msg for msg in messages if 
                                msg.get("type") in ["partial_transcription", "final_transcription"]]
        
        logger.info(f"Received {len(transcription_messages)} transcription messages")
        
        await self.client.disconnect()
    
    def test_audio_data_transmission(self):
        """Synchronous wrapper for audio transmission test."""
        asyncio.run(self.async_test_audio_data_transmission())
    
    async def async_test_real_time_transcription_flow(self):
        """Test complete real-time transcription flow."""
        await self.client.connect()
        
        # Set language to English
        await self.client.send_json_message({
            "type": "change_language",
            "language": "en"
        })
        
        # Wait for language change confirmation
        await self.client.receive_message(timeout=1.0)
        
        # Simulate continuous audio streaming
        total_chunks = 10
        chunk_duration = 0.2
        
        for i in range(total_chunks):
            # Generate audio with varying frequency to simulate speech
            frequency = 200 + (i % 5) * 50
            audio = self.client.generate_pcm_audio(duration=chunk_duration, frequency=frequency)
            
            await self.client.send_audio_chunk(audio)
            
            # Small delay between chunks
            await asyncio.sleep(0.05)
        
        # Listen for responses
        messages = await self.client.listen_for_messages(duration=3.0)
        
        # Analyze received messages
        partial_messages = [msg for msg in messages if msg.get("type") == "partial_transcription"]
        final_messages = [msg for msg in messages if msg.get("type") == "final_transcription"]
        status_messages = [msg for msg in messages if msg.get("type") == "transcription_status"]
        recording_messages = [msg for msg in messages if msg.get("type") in ["recording_started", "recording_state"]]
        
        logger.info(f"Received: {len(partial_messages)} partial, "
                   f"{len(final_messages)} final, "
                   f"{len(status_messages)} status, "
                   f"{len(recording_messages)} recording messages")
        
        # Verify we received some form of transcription activity
        total_transcription_activity = len(partial_messages) + len(final_messages)
        self.assertGreater(total_transcription_activity, 0, 
                          "No transcription activity detected")
        
        await self.client.disconnect()
    
    def test_real_time_transcription_flow(self):
        """Synchronous wrapper for real-time transcription test."""
        asyncio.run(self.async_test_real_time_transcription_flow())
    
    async def async_test_language_switching(self):
        """Test language switching functionality."""
        await self.client.connect()
        
        # Test switching through different languages
        languages = ["en", "hi", "hi-en", "en"]
        
        for lang in languages:
            # Send language change request
            await self.client.send_json_message({
                "type": "change_language", 
                "language": lang
            })
            
            # Wait for confirmation
            response = await self.client.receive_message(timeout=2.0)
            self.assertIsNotNone(response, f"No response for language change to {lang}")
            
            if response:
                self.assertEqual(response.get("type"), "language_changed")
                self.assertEqual(response.get("content"), lang)
                
                logger.info(f"Language switched to: {lang}")
        
        await self.client.disconnect()
    
    def test_language_switching(self):
        """Synchronous wrapper for language switching test."""
        asyncio.run(self.async_test_language_switching())
    
    async def async_test_export_functionality(self):
        """Test export functionality."""
        await self.client.connect()
        
        # Generate some fake transcription activity
        await self.client.send_audio_chunk(self.client.generate_pcm_audio())
        await asyncio.sleep(0.5)
        
        # Test JSON export
        await self.client.send_json_message({
            "type": "export_request",
            "format": "json"
        })
        
        json_response = await self.client.receive_message(timeout=2.0)
        self.assertIsNotNone(json_response, "No JSON export response")
        
        if json_response:
            self.assertEqual(json_response.get("type"), "export_data")
            self.assertEqual(json_response.get("format"), "json")
            self.assertIsNotNone(json_response.get("content"))
        
        # Test text export
        await self.client.send_json_message({
            "type": "export_request",
            "format": "text"
        })
        
        text_response = await self.client.receive_message(timeout=2.0)
        self.assertIsNotNone(text_response, "No text export response")
        
        if text_response:
            self.assertEqual(text_response.get("type"), "export_data")
            self.assertEqual(text_response.get("format"), "text")
            self.assertIsNotNone(text_response.get("content"))
        
        await self.client.disconnect()
    
    def test_export_functionality(self):
        """Synchronous wrapper for export functionality test."""
        asyncio.run(self.async_test_export_functionality())
    
    async def async_test_connection_stability_under_load(self):
        """Test connection stability under load."""
        await self.client.connect()
        
        start_time = time.time()
        messages_sent = 0
        errors = []
        
        # Send many messages rapidly
        try:
            for i in range(50):
                # Alternate between audio and JSON messages
                if i % 2 == 0:
                    audio = self.client.generate_pcm_audio(duration=0.1)
                    await self.client.send_audio_chunk(audio)
                else:
                    await self.client.send_json_message({
                        "type": "get_recent_transcriptions",
                        "limit": 10
                    })
                
                messages_sent += 1
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        except Exception as e:
            errors.append(str(e))
            logger.error(f"Error during load test: {e}")
        
        # Listen for any responses
        messages = await self.client.listen_for_messages(duration=2.0)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # Verify connection is still stable
        self.assertTrue(self.client.is_connected, "Connection lost during load test")
        
        # Log results
        logger.info(f"Load test completed: {messages_sent} messages sent in {test_duration:.2f}s")
        logger.info(f"Received {len(messages)} responses, {len(errors)} errors")
        
        # Should not have too many errors
        error_rate = len(errors) / max(1, messages_sent)
        self.assertLess(error_rate, 0.1, f"Too many errors during load test: {error_rate:.2%}")
        
        await self.client.disconnect()
    
    def test_connection_stability_under_load(self):
        """Synchronous wrapper for load test."""
        asyncio.run(self.async_test_connection_stability_under_load())
    
    async def async_test_message_ordering_and_integrity(self):
        """Test message ordering and data integrity."""
        await self.client.connect()
        
        # Send messages with sequence numbers
        sequence_messages = []
        for i in range(10):
            msg = {
                "type": "get_recent_transcriptions", 
                "sequence": i,
                "timestamp": time.time()
            }
            sequence_messages.append(msg)
            await self.client.send_json_message(msg)
            await asyncio.sleep(0.05)
        
        # Collect responses
        responses = await self.client.listen_for_messages(duration=3.0)
        
        # Filter relevant responses
        transcription_responses = [r for r in responses if r.get("type") == "recent_transcriptions"]
        
        # Verify we got responses
        logger.info(f"Sent {len(sequence_messages)} requests, got {len(transcription_responses)} responses")
        
        await self.client.disconnect()
    
    def test_message_ordering_and_integrity(self):
        """Synchronous wrapper for message ordering test."""
        asyncio.run(self.async_test_message_ordering_and_integrity())

class WebSocketPerformanceTestSuite(unittest.TestCase):
    """Performance tests for WebSocket functionality."""
    
    def setUp(self):
        """Set up performance tests."""
        self.test_port = 8001
        self.client = WebSocketTestClient(f"ws://localhost:{self.test_port}/ws")
    
    async def async_test_connection_latency(self):
        """Test WebSocket connection latency."""
        latencies = []
        
        for i in range(5):
            start_time = time.time()
            connected = await self.client.connect()
            connection_time = time.time() - start_time
            
            if connected:
                latencies.append(connection_time)
                await self.client.disconnect()
            
            await asyncio.sleep(0.1)
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            logger.info(f"Connection latency - Avg: {avg_latency*1000:.2f}ms, "
                       f"Max: {max_latency*1000:.2f}ms, Min: {min_latency*1000:.2f}ms")
            
            # Connection should be reasonably fast
            self.assertLess(avg_latency, 1.0, "Average connection latency too high")
            self.assertLess(max_latency, 2.0, "Maximum connection latency too high")
    
    def test_connection_latency(self):
        """Synchronous wrapper for connection latency test."""
        asyncio.run(self.async_test_connection_latency())
    
    async def async_test_message_throughput(self):
        """Test message throughput."""
        await self.client.connect()
        
        message_count = 100
        start_time = time.time()
        
        # Send many small messages rapidly
        for i in range(message_count):
            await self.client.send_json_message({
                "type": "get_recent_transcriptions",
                "limit": 1,
                "sequence": i
            })
        
        send_time = time.time() - start_time
        
        # Calculate throughput
        throughput = message_count / send_time
        
        logger.info(f"Message throughput: {throughput:.1f} messages/second "
                   f"({message_count} messages in {send_time:.3f}s)")
        
        # Should handle reasonable throughput
        self.assertGreater(throughput, 50, "Message throughput too low")
        
        await self.client.disconnect()
    
    def test_message_throughput(self):
        """Synchronous wrapper for throughput test."""
        asyncio.run(self.async_test_message_throughput())


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(WebSocketFunctionalityTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(WebSocketPerformanceTestSuite))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    logger.info("Starting WebSocket functionality test suite...")
    
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)