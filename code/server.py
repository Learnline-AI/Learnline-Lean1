# server.py - Simplified Transcription Server
# Optimized for real-time Hindi/English transcription with language switching
from queue import Queue, Empty
import logging
from logsetup import setup_logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logger.info("🖥️👋 Welcome to real-time transcription server")

from datetime import datetime
from colors import Colors
import uvicorn
import asyncio
import struct
import json
import time
import threading
import sys
import os
from pathlib import Path

from typing import Any, Dict, Optional, Callable, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, Response, FileResponse

USE_SSL = False

# Railway memory monitoring
try:
    import psutil
    MEMORY_MONITORING = True
    logger.info("🖥️💾 Memory monitoring enabled for Railway")
except ImportError:
    MEMORY_MONITORING = False
    logger.warning("🖥️⚠️ psutil not available - memory monitoring disabled")

def check_memory_usage():
    """Check current memory usage for Railway optimization."""
    if not MEMORY_MONITORING:
        return None
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        return memory_mb
    except Exception:
        return None

def log_memory_usage(context: str = ""):
    """Log memory usage with context."""
    if not MEMORY_MONITORING:
        return
    memory_mb = check_memory_usage()
    if memory_mb:
        context_str = f" [{context}]" if context else ""
        if memory_mb > 400:  # Warning threshold for Railway (512MB limit)
            logger.warning(f"🖥️💾⚠️ HIGH MEMORY{context_str}: {memory_mb:.1f}MB")
        else:
            logger.info(f"🖥️💾{context_str}: {memory_mb:.1f}MB")

# Transcription configuration
DEFAULT_LANGUAGE = "en"  # Default to English
SUPPORTED_LANGUAGES = ["en", "hi", "hi-en"]  # English, Hindi, Hindi-English code-switching

# Railway-optimized configuration for memory constraints
try:
    # Reduced queue size for Railway's memory limits (512MB typical)
    default_queue_size = 30 if os.getenv("RAILWAY_DEPLOYMENT") else 100
    MAX_AUDIO_QUEUE_SIZE = int(os.getenv("MAX_AUDIO_QUEUE_SIZE", default_queue_size))
    if __name__ == "__main__":
        logger.info(f"🖥️⚙️ {Colors.apply('[RAILWAY-OPTIMIZED]').blue} Audio queue size: {Colors.apply(str(MAX_AUDIO_QUEUE_SIZE)).blue}")
except ValueError:
    MAX_AUDIO_QUEUE_SIZE = 30 if os.getenv("RAILWAY_DEPLOYMENT") else 100
    if __name__ == "__main__":
        logger.warning(f"🖥️⚠️ Invalid MAX_AUDIO_QUEUE_SIZE env var. Using Railway default: {MAX_AUDIO_QUEUE_SIZE}")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from audio_in import AudioInputProcessor
from colors import Colors

# Railway monitoring integration
try:
    from railway_monitor import init_railway_monitor, get_monitor
    RAILWAY_MONITOR_AVAILABLE = True
except ImportError:
    RAILWAY_MONITOR_AVAILABLE = False
    logger.warning("Railway monitor not available")

# Transcription history storage
class TranscriptionHistory:
    """Manages transcription history with export functionality."""
    def __init__(self):
        self.transcriptions: List[Dict[str, Any]] = []
        self.current_session_start = datetime.now()
    
    def add_transcription(self, text: str, language: str, timestamp: float, is_final: bool = True):
        """Add a transcription to the history."""
        entry = {
            "text": text,
            "language": language,
            "timestamp": timestamp,
            "formatted_time": format_timestamp_ns(int(timestamp * 1_000_000_000)),
            "is_final": is_final,
            "session_start": self.current_session_start.isoformat()
        }
        self.transcriptions.append(entry)
    
    def export_to_json(self) -> str:
        """Export transcriptions as JSON string."""
        return json.dumps({
            "session_start": self.current_session_start.isoformat(),
            "export_time": datetime.now().isoformat(),
            "transcriptions": self.transcriptions
        }, indent=2)
    
    def export_to_text(self) -> str:
        """Export transcriptions as plain text."""
        lines = [f"Transcription Session - {self.current_session_start.strftime('%Y-%m-%d %H:%M:%S')}\n"]
        for entry in self.transcriptions:
            if entry["is_final"]:
                lines.append(f"[{entry['formatted_time']}] ({entry['language']}) {entry['text']}")
        return "\n".join(lines)
    
    def clear(self):
        """Clear all transcriptions and reset session."""
        self.transcriptions.clear()
        self.current_session_start = datetime.now()
    
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transcriptions."""
        return self.transcriptions[-limit:] if len(self.transcriptions) > limit else self.transcriptions

# --------------------------------------------------------------------
# Custom no-cache StaticFiles
# --------------------------------------------------------------------
class NoCacheStaticFiles(StaticFiles):
    """
    Serves static files without allowing client-side caching.

    Overrides the default Starlette StaticFiles to add 'Cache-Control' headers
    that prevent browsers from caching static assets. Useful for development.
    """
    async def get_response(self, path: str, scope: Dict[str, Any]) -> Response:
        """
        Gets the response for a requested path, adding no-cache headers.

        Args:
            path: The path to the static file requested.
            scope: The ASGI scope dictionary for the request.

        Returns:
            A Starlette Response object with cache-control headers modified.
        """
        response: Response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        # These might not be strictly necessary with no-store, but belt and suspenders
        if "etag" in response.headers:
             response.headers.__delitem__("etag")
        if "last-modified" in response.headers:
             response.headers.__delitem__("last-modified")
        return response

# --------------------------------------------------------------------
# Lifespan management
# --------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan, initializing and shutting down resources.

    Initializes global components for transcription processing and stores them in 
    `app.state`. Handles cleanup on shutdown.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("🖥️▶️ Transcription server starting up")
    log_memory_usage("startup")
    
    # Initialize Railway monitoring if available
    if RAILWAY_MONITOR_AVAILABLE:
        app.state.railway_monitor = init_railway_monitor()
        if app.state.railway_monitor:
            # Start monitoring task
            asyncio.create_task(app.state.railway_monitor.start_monitoring())
    
    # Initialize transcription history
    app.state.TranscriptionHistory = TranscriptionHistory()
    
    # Initialize audio input processor with Railway-optimized settings
    railway_latency = 0.5 if os.getenv("RAILWAY_DEPLOYMENT") else 0.3
    app.state.AudioInputProcessor = AudioInputProcessor(
        DEFAULT_LANGUAGE,
        is_orpheus=False,  # No TTS engine needed
        pipeline_latency=railway_latency,  # Higher latency for Railway stability
    )
    
    # Current language state (can be changed via WebSocket)
    app.state.current_language = DEFAULT_LANGUAGE
    
    log_memory_usage("ready")
    yield

    logger.info("🖥️⏹️ Transcription server shutting down")
    log_memory_usage("shutdown")
    app.state.AudioInputProcessor.shutdown()

# --------------------------------------------------------------------
# FastAPI app instance
# --------------------------------------------------------------------
app = FastAPI(lifespan=lifespan)

# Enable CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files with no cache
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

@app.get("/favicon.ico")
async def favicon():
    """
    Serves the favicon.ico file.

    Returns:
        A FileResponse containing the favicon.
    """
    return FileResponse("static/favicon.ico")

@app.get("/")
async def get_index() -> HTMLResponse:
    """
    Serves the main index.html page.

    Reads the content of static/index.html and returns it as an HTML response.

    Returns:
        An HTMLResponse containing the content of index.html.
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# --------------------------------------------------------------------
# HTTP API Endpoints for transcription management
# --------------------------------------------------------------------

@app.get("/api/status")
async def get_status():
    """
    Returns the current server status and configuration.
    """
    status = {
        "status": "running",
        "server_type": "transcription_only",
        "supported_languages": SUPPORTED_LANGUAGES,
        "default_language": DEFAULT_LANGUAGE,
        "max_audio_queue_size": MAX_AUDIO_QUEUE_SIZE,
        "version": "2.0-transcription-railway",
        "railway_deployment": os.getenv("RAILWAY_DEPLOYMENT", "false") == "true"
    }
    
    # Add Railway monitoring stats if available
    if RAILWAY_MONITOR_AVAILABLE and hasattr(app.state, 'railway_monitor') and app.state.railway_monitor:
        try:
            monitor_stats = app.state.railway_monitor.get_summary_stats()
            status["performance"] = monitor_stats
        except Exception as e:
            logger.debug(f"Error getting monitor stats: {e}")
    
    return status

@app.get("/api/languages")
async def get_supported_languages():
    """
    Returns the list of supported languages for transcription.
    """
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "language_info": {
            "en": {"name": "English", "code": "en"},
            "hi": {"name": "Hindi", "code": "hi"},
            "hi-en": {"name": "Hindi-English (Code-switching)", "code": "hi-en"}
        }
    }

@app.post("/api/export/{format}")
async def export_transcriptions(format: str):
    """
    Exports transcription history in the specified format.
    
    Args:
        format: Export format ('json' or 'text')
    """
    if not hasattr(app.state, 'TranscriptionHistory'):
        return {"error": "No transcription history available"}
    
    history = app.state.TranscriptionHistory
    
    if format.lower() == "json":
        content = history.export_to_json()
        media_type = "application/json"
        filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    elif format.lower() == "text":
        content = history.export_to_text()
        media_type = "text/plain"
        filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    else:
        return {"error": "Unsupported format. Use 'json' or 'text'"}
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/history")
async def get_transcription_history(limit: int = 50):
    """
    Returns recent transcription history.
    
    Args:
        limit: Maximum number of transcriptions to return (default: 50)
    """
    if not hasattr(app.state, 'TranscriptionHistory'):
        return {"error": "No transcription history available"}
    
    recent = app.state.TranscriptionHistory.get_recent(limit)
    return {
        "count": len(recent),
        "limit": limit,
        "transcriptions": recent
    }

@app.delete("/api/history")
async def clear_transcription_history():
    """
    Clears all transcription history.
    """
    if hasattr(app.state, 'TranscriptionHistory'):
        app.state.TranscriptionHistory.clear()
        return {"message": "Transcription history cleared successfully"}
    return {"error": "No transcription history available"}

# --------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------
def parse_json_message(text: str) -> dict:
    """
    Safely parses a JSON string into a dictionary.

    Logs a warning if the JSON is invalid and returns an empty dictionary.

    Args:
        text: The JSON string to parse.

    Returns:
        A dictionary representing the parsed JSON, or an empty dictionary on error.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("🖥️⚠️ Ignoring client message with invalid JSON")
        return {}

def format_timestamp_ns(timestamp_ns: int) -> str:
    """
    Formats a nanosecond timestamp into a human-readable HH:MM:SS.fff string.

    Args:
        timestamp_ns: The timestamp in nanoseconds since the epoch.

    Returns:
        A string formatted as hours:minutes:seconds.milliseconds.
    """
    # Split into whole seconds and the nanosecond remainder
    seconds = timestamp_ns // 1_000_000_000
    remainder_ns = timestamp_ns % 1_000_000_000

    # Convert seconds part into a datetime object (local time)
    dt = datetime.fromtimestamp(seconds)

    # Format the main time as HH:MM:SS
    time_str = dt.strftime("%H:%M:%S")

    # For instance, if you want milliseconds, divide the remainder by 1e6 and format as 3-digit
    milliseconds = remainder_ns // 1_000_000
    formatted_timestamp = f"{time_str}.{milliseconds:03d}"

    return formatted_timestamp

# --------------------------------------------------------------------
# WebSocket data processing
# --------------------------------------------------------------------

async def process_incoming_data(ws: WebSocket, app: FastAPI, incoming_chunks: asyncio.Queue, callbacks: 'TranscriptionCallbacks') -> None:
    """
    Receives messages via WebSocket, processes audio and text messages.

    Handles binary audio chunks, extracting metadata (timestamp, flags) and
    putting the audio PCM data with metadata into the `incoming_chunks` queue.
    Applies back-pressure if the queue is full.
    Parses text messages (assumed JSON) and triggers actions based on message type
    (e.g., updates client TTS state via `callbacks`, clears history, sets speed).

    Args:
        ws: The WebSocket connection instance.
        app: The FastAPI application instance (for accessing global state if needed).
        incoming_chunks: An asyncio queue to put processed audio metadata dictionaries into.
        callbacks: The TranscriptionCallbacks instance for this connection to manage state.
    """
    try:
        while True:
            msg = await ws.receive()
            if "bytes" in msg and msg["bytes"]:
                raw = msg["bytes"]

                # Ensure we have at least an 8‑byte header: 4 bytes timestamp_ms + 4 bytes flags
                if len(raw) < 8:
                    logger.warning("🖥️⚠️ Received packet too short for 8‑byte header.")
                    continue

                # Unpack big‑endian uint32 timestamp (ms) and uint32 flags
                timestamp_ms, flags = struct.unpack("!II", raw[:8])
                client_sent_ns = timestamp_ms * 1_000_000

                # Build metadata using fixed fields
                metadata = {
                    "client_sent_ms":           timestamp_ms,
                    "client_sent":              client_sent_ns,
                    "client_sent_formatted":    format_timestamp_ns(client_sent_ns),
                    "isTTSPlaying":             bool(flags & 1),
                }

                # Record server receive time
                server_ns = time.time_ns()
                metadata["server_received"] = server_ns
                metadata["server_received_formatted"] = format_timestamp_ns(server_ns)

                # The rest of the payload is raw PCM bytes
                metadata["pcm"] = raw[8:]

                # Check queue size before putting data
                current_qsize = incoming_chunks.qsize()
                if current_qsize < MAX_AUDIO_QUEUE_SIZE:
                    # Now put only the metadata dict (containing PCM audio) into the processing queue.
                    await incoming_chunks.put(metadata)
                else:
                    # Queue is full, drop the chunk and log a warning
                    logger.warning(
                        f"🖥️⚠️ Audio queue full ({current_qsize}/{MAX_AUDIO_QUEUE_SIZE}); dropping chunk. Possible lag."
                    )

            elif "text" in msg and msg["text"]:
                # Text-based message: parse JSON
                data = parse_json_message(msg["text"])
                msg_type = data.get("type")
                logger.info(Colors.apply(f"🖥️📥 ←←Client: {data}").orange)


                if msg_type == "clear_history":
                    logger.info("🖥️ℹ️ Received clear_history from client.")
                    app.state.TranscriptionHistory.clear()
                    # Send confirmation to client
                    callbacks.message_queue.put_nowait({
                        "type": "history_cleared",
                        "content": "Transcription history cleared successfully"
                    })
                elif msg_type == "change_language":
                    new_language = data.get("language", DEFAULT_LANGUAGE)
                    if new_language in SUPPORTED_LANGUAGES:
                        logger.info(f"🖥️🌐 Changing language to: {new_language}")
                        app.state.current_language = new_language
                        # Restart audio processor with new language (Railway-optimized)
                        app.state.AudioInputProcessor.shutdown()
                        railway_latency = 0.5 if os.getenv("RAILWAY_DEPLOYMENT") else 0.3
                        app.state.AudioInputProcessor = AudioInputProcessor(
                            new_language,
                            is_orpheus=False,
                            pipeline_latency=railway_latency,
                        )
                        # Reassign callbacks
                        setup_audio_callbacks(app, callbacks)
                        # Confirm language change to client
                        callbacks.message_queue.put_nowait({
                            "type": "language_changed",
                            "content": new_language
                        })
                    else:
                        logger.warning(f"🖥️⚠️ Unsupported language: {new_language}")
                elif msg_type == "export_request":
                    export_format = data.get("format", "json").lower()
                    logger.info(f"🖥️📤 Export request received: {export_format}")
                    if export_format == "json":
                        export_data = app.state.TranscriptionHistory.export_to_json()
                    elif export_format == "text":
                        export_data = app.state.TranscriptionHistory.export_to_text()
                    else:
                        export_data = app.state.TranscriptionHistory.export_to_json()
                    
                    callbacks.message_queue.put_nowait({
                        "type": "export_data",
                        "format": export_format,
                        "content": export_data,
                        "filename": f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
                    })
                elif msg_type == "get_recent_transcriptions":
                    limit = data.get("limit", 50)
                    recent = app.state.TranscriptionHistory.get_recent(limit)
                    callbacks.message_queue.put_nowait({
                        "type": "recent_transcriptions",
                        "content": recent
                    })
                elif msg_type == "set_speed":
                    speed_value = data.get("speed", 0)
                    speed_factor = speed_value / 100.0  # Convert 0-100 to 0.0-1.0
                    turn_detection = app.state.AudioInputProcessor.transcriber.turn_detection
                    if turn_detection:
                        turn_detection.update_settings(speed_factor)
                        logger.info(f"🖥️⚙️ Updated turn detection settings to factor: {speed_factor:.2f}")


    except asyncio.CancelledError:
        pass # Task cancellation is expected on disconnect
    except WebSocketDisconnect as e:
        logger.warning(f"🖥️⚠️ {Colors.apply('WARNING').red} disconnect in process_incoming_data: {repr(e)}")
    except RuntimeError as e:  # Often raised on closed transports
        logger.error(f"🖥️💥 {Colors.apply('RUNTIME_ERROR').red} in process_incoming_data: {repr(e)}")
    except Exception as e:
        logger.exception(f"🖥️💥 {Colors.apply('EXCEPTION').red} in process_incoming_data: {repr(e)}")

async def send_text_messages(ws: WebSocket, message_queue: asyncio.Queue) -> None:
    """
    Continuously sends text messages from a queue to the client via WebSocket.

    Waits for messages on the `message_queue`, formats them as JSON, and sends
    them to the connected WebSocket client. Optimized for transcription messages.

    Args:
        ws: The WebSocket connection instance.
        message_queue: An asyncio queue yielding dictionaries to be sent as JSON.
    """
    try:
        while True:
            await asyncio.sleep(0.001) # Yield control
            data = await message_queue.get()
            msg_type = data.get("type")
            # Log transcription-related messages with optimization for high frequency messages
            if msg_type in ["partial_transcription"]:
                # Reduce logging for frequent partial transcriptions to avoid performance impact
                logger.debug(Colors.apply(f"🖥️📤 →→Client: {msg_type} - {str(data.get('content', ''))[:30]}...").orange)
            elif msg_type in ["final_transcription", "language_changed", "export_data"]:
                content_preview = str(data.get('content', ''))[:50] if len(str(data.get('content', ''))) > 50 else str(data.get('content', ''))
                logger.info(Colors.apply(f"🖥️📤 →→Client: {msg_type} - {content_preview}...").orange)
            else:
                logger.debug(Colors.apply(f"🖥️📤 →→Client: {data}").orange)
            await ws.send_json(data)
    except asyncio.CancelledError:
        pass # Task cancellation is expected on disconnect
    except WebSocketDisconnect as e:
        logger.warning(f"🖥️⚠️ {Colors.apply('WARNING').red} disconnect in send_text_messages: {repr(e)}")
    except RuntimeError as e:  # Often raised on closed transports
        logger.error(f"🖥️💥 {Colors.apply('RUNTIME_ERROR').red} in send_text_messages: {repr(e)}")
    except Exception as e:
        logger.exception(f"🖥️💥 {Colors.apply('EXCEPTION').red} in send_text_messages: {repr(e)}")

# TTS-related functions removed - not needed for transcription-only server

async def send_transcription_status(app: FastAPI, message_queue: asyncio.Queue, callbacks: 'TranscriptionCallbacks') -> None:
    """
    Continuously monitors transcription status and sends status updates to the client.

    Provides periodic status updates about the transcription process, 
    language detection, and system health to keep the client informed.

    Args:
        app: The FastAPI application instance (to access global components).
        message_queue: An asyncio queue to put status messages onto.
        callbacks: The TranscriptionCallbacks instance managing this connection's state.
    """
    try:
        logger.info("🖥️📊 Starting transcription status monitor")
        last_status_time = 0
        status_interval = 5.0  # Send status every 5 seconds

        while True:
            await asyncio.sleep(1.0)  # Check status every second (reduced frequency)

            current_time = time.time()
            if current_time - last_status_time > status_interval:
                # Send status update
                status_data = {
                    "type": "transcription_status",
                    "content": {
                        "language": app.state.current_language,
                        "is_recording": not callbacks.silence_active,
                        "transcription_count": len(app.state.TranscriptionHistory.transcriptions),
                        "session_duration": current_time - app.state.TranscriptionHistory.current_session_start.timestamp(),
                        "audio_queue_size": callbacks.audio_queue_size if hasattr(callbacks, 'audio_queue_size') else 0
                    }
                }
                message_queue.put_nowait(status_data)
                last_status_time = current_time

    except asyncio.CancelledError:
        pass # Task cancellation is expected on disconnect
    except WebSocketDisconnect as e:
        logger.warning(f"🖥️⚠️ {Colors.apply('WARNING').red} disconnect in send_transcription_status: {repr(e)}")
    except RuntimeError as e:
        logger.error(f"🖥️💥 {Colors.apply('RUNTIME_ERROR').red} in send_transcription_status: {repr(e)}")
    except Exception as e:
        logger.exception(f"🖥️💥 {Colors.apply('EXCEPTION').red} in send_transcription_status: {repr(e)}")


# --------------------------------------------------------------------
# Callback class to handle transcription events
# --------------------------------------------------------------------
class TranscriptionCallbacks:
    """
    Manages state and callbacks for a single WebSocket connection's transcription lifecycle.

    This class holds connection-specific state flags and implements callback methods 
    triggered by the `AudioInputProcessor`. It sends transcription messages back to 
    the client via the provided `message_queue` and manages transcription history.
    Simplified for transcription-only functionality.
    """
    def __init__(self, app: FastAPI, message_queue: asyncio.Queue):
        """
        Initializes the TranscriptionCallbacks instance for a WebSocket connection.

        Args:
            app: The FastAPI application instance (to access global components).
            message_queue: An asyncio queue for sending messages back to the client.
        """
        self.app = app
        self.message_queue = message_queue
        self.final_transcription = ""
        self.partial_transcription = ""
        self.last_partial_text = ""

        # Initialize connection-specific state flags
        self.silence_active: bool = True
        self.is_recording: bool = False
        self.last_transcription_time: float = 0.0
        self.audio_queue_size: int = 0

        self.reset_state() # Call reset to ensure consistency
        logger.info("🖥️🎯 TranscriptionCallbacks initialized for new connection")


    def reset_state(self):
        """Resets connection-specific state flags and variables to their initial values."""
        # Reset transcription state
        self.silence_active = True
        self.is_recording = False
        self.last_transcription_time = 0.0
        self.partial_transcription = ""
        self.final_transcription = ""
        self.last_partial_text = ""
        self.audio_queue_size = 0
        logger.debug("🖥️🔄 Transcription state reset")


    # Abort worker not needed for transcription-only server

    def on_partial(self, txt: str):
        """
        Callback invoked when a partial transcription result is available.

        Updates internal state, sends the partial result to the client,
        and manages transcription history.

        Args:
            txt: The partial transcription text.
        """
        if txt and txt != self.last_partial_text:
            self.partial_transcription = txt
            self.last_partial_text = txt
            self.last_transcription_time = time.time()
            
            # Add to history as partial (non-final)
            self.app.state.TranscriptionHistory.add_transcription(
                text=txt,
                language=self.app.state.current_language,
                timestamp=self.last_transcription_time,
                is_final=False
            )
            
            # Send to client
            self.message_queue.put_nowait({
                "type": "partial_transcription", 
                "content": txt,
                "language": self.app.state.current_language,
                "timestamp": self.last_transcription_time
            })
            logger.debug(f"🖥️🎯 Partial transcription ({self.app.state.current_language}): {txt[:50]}...")

    def on_potential_sentence(self, txt: str):
        """
        Callback invoked when a potentially complete sentence is detected by the STT.
        For transcription-only, we just log this for debugging.

        Args:
            txt: The potential sentence text.
        """
        logger.debug(f"🖥️🎯 Potential sentence detected: '{txt}'")

    def on_potential_final(self, txt: str):
        """
        Callback invoked when a potential *final* transcription is detected.
        This indicates high confidence in the transcription.

        Args:
            txt: The potential final transcription text.
        """
        logger.info(f"{Colors.apply('🖥️🎯 High confidence transcription: ').green}{txt}")
        # Could be used for confidence scoring in the future

    def on_before_final(self, audio: bytes, txt: str):
        """
        Callback invoked just before the final STT result for a user turn is confirmed.
        In transcription-only mode, this prepares for the final transcription result.

        Args:
            audio: The raw audio bytes corresponding to the final transcription. (Currently unused)
            txt: The transcription text (might be slightly refined in on_final).
        """
        logger.info(Colors.apply('🖥️🎯 =================== TRANSCRIPTION TURN END ===================').light_gray)
        
        # Use the most reliable transcription text available
        transcription_content = self.final_transcription if self.final_transcription else self.partial_transcription or txt
        
        if transcription_content:
            # Update transcription time
            self.last_transcription_time = time.time()
            
            logger.info(f"🖥️📝 Preparing final transcription: '{transcription_content}'")

    def on_final(self, txt: str):
        """
        Callback invoked when the final transcription result for a user turn is available.

        Stores the final transcription and sends it to the client with history management.

        Args:
            txt: The final transcription text.
        """
        if txt and txt.strip():
            self.final_transcription = txt
            self.last_transcription_time = time.time()
            
            logger.info(f"\n{Colors.apply('🖥️✅ FINAL TRANSCRIPTION: ').green}{txt}")
            
            # Add to history as final transcription
            self.app.state.TranscriptionHistory.add_transcription(
                text=txt,
                language=self.app.state.current_language,
                timestamp=self.last_transcription_time,
                is_final=True
            )
            
            # Send final transcription to client
            self.message_queue.put_nowait({
                "type": "final_transcription",
                "content": txt,
                "language": self.app.state.current_language,
                "timestamp": self.last_transcription_time,
                "confidence": "high"  # Placeholder for future confidence scoring
            })

    # Abort functionality not needed for transcription-only server

    def on_silence_active(self, silence_active: bool):
        """
        Callback invoked when the silence detection state changes.

        Updates the internal silence_active flag and notifies client of recording state.

        Args:
            silence_active: True if silence is currently detected, False otherwise.
        """
        if self.silence_active != silence_active:
            self.silence_active = silence_active
            self.is_recording = not silence_active
            
            # Notify client of recording state change
            self.message_queue.put_nowait({
                "type": "recording_state",
                "content": {
                    "is_recording": self.is_recording,
                    "silence_active": silence_active
                }
            })
            
            logger.debug(f"🖥️🎙️ Recording state: {'ACTIVE' if self.is_recording else 'SILENT'}")

    # Assistant text callbacks not needed for transcription-only server

    def on_recording_start(self):
        """
        Callback invoked when the audio input processor starts recording user speech.
        In transcription-only mode, this simply indicates the start of audio capture.
        """
        self.is_recording = True
        logger.info(f"{Colors.ORANGE}🖥️🎙️ Recording started for transcription.{Colors.RESET}")
        
        # Notify client that recording has started
        self.message_queue.put_nowait({
            "type": "recording_started",
            "content": {
                "timestamp": time.time(),
                "language": self.app.state.current_language
            }
        })

    # Assistant answer functionality not needed for transcription-only server


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def setup_audio_callbacks(app: FastAPI, callbacks: 'TranscriptionCallbacks'):
    """
    Sets up audio input processor callbacks for a connection.
    
    Args:
        app: The FastAPI application instance.
        callbacks: The TranscriptionCallbacks instance for this connection.
    """
    app.state.AudioInputProcessor.realtime_callback = callbacks.on_partial
    app.state.AudioInputProcessor.transcriber.potential_sentence_end = callbacks.on_potential_sentence
    app.state.AudioInputProcessor.transcriber.potential_full_transcription_callback = callbacks.on_potential_final
    app.state.AudioInputProcessor.transcriber.full_transcription_callback = callbacks.on_final
    app.state.AudioInputProcessor.transcriber.before_final_sentence = callbacks.on_before_final
    app.state.AudioInputProcessor.recording_start_callback = callbacks.on_recording_start
    app.state.AudioInputProcessor.silence_active_callback = callbacks.on_silence_active
    
    # Remove TTS-related callbacks that are no longer needed
    if hasattr(app.state.AudioInputProcessor.transcriber, 'on_tts_allowed_to_synthesize'):
        app.state.AudioInputProcessor.transcriber.on_tts_allowed_to_synthesize = None
    if hasattr(app.state.AudioInputProcessor.transcriber, 'potential_full_transcription_abort_callback'):
        app.state.AudioInputProcessor.transcriber.potential_full_transcription_abort_callback = None


# --------------------------------------------------------------------
# Main WebSocket endpoint
# --------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Handles the main WebSocket connection for real-time voice chat.

    Accepts a connection, sets up connection-specific state via `TranscriptionCallbacks`,
    initializes audio/message queues, and creates asyncio tasks for handling
    incoming data, audio processing, outgoing text messages, and outgoing TTS chunks.
    Manages the lifecycle of these tasks and cleans up on disconnect.

    Args:
        ws: The WebSocket connection instance provided by FastAPI.
    """
    await ws.accept()
    logger.info("🖥️✅ Client connected via WebSocket.")
    
    # Track connection in Railway monitor
    if RAILWAY_MONITOR_AVAILABLE and hasattr(app.state, 'railway_monitor') and app.state.railway_monitor:
        app.state.railway_monitor.add_connection()

    message_queue = asyncio.Queue()
    audio_chunks = asyncio.Queue()

    # Set up callback manager for connection-specific state
    callbacks = TranscriptionCallbacks(app, message_queue)

    # Assign callbacks to the AudioInputProcessor (global component)
    setup_audio_callbacks(app, callbacks)

    # Create tasks for handling transcription responsibilities
    tasks = [
        asyncio.create_task(process_incoming_data(ws, app, audio_chunks, callbacks)),
        asyncio.create_task(app.state.AudioInputProcessor.process_chunk_queue(audio_chunks)),
        asyncio.create_task(send_text_messages(ws, message_queue)),
        asyncio.create_task(send_transcription_status(app, message_queue, callbacks)),
    ]

    try:
        # Wait for any task to complete (e.g., client disconnect)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            if not task.done():
                task.cancel()
        # Await cancelled tasks to let them clean up if needed
        await asyncio.gather(*pending, return_exceptions=True)
    except Exception as e:
        logger.error(f"🖥️💥 {Colors.apply('ERROR').red} in WebSocket session: {repr(e)}")
    finally:
        logger.info("🖥️🧹 Cleaning up WebSocket tasks...")
        for task in tasks:
            if not task.done():
                task.cancel()
        # Ensure all tasks are awaited after cancellation
        # Use return_exceptions=True to prevent gather from stopping on first error during cleanup
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Remove connection from Railway monitor
        if RAILWAY_MONITOR_AVAILABLE and hasattr(app.state, 'railway_monitor') and app.state.railway_monitor:
            app.state.railway_monitor.remove_connection()
        
        logger.info("🖥️❌ WebSocket session ended.")

# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------
if __name__ == "__main__":

    # Run the server without SSL
    if not USE_SSL:
        logger.info("🖥️▶️ Starting server without SSL.")
        uvicorn.run("server:app", host="0.0.0.0", port=8000, log_config=None)

    else:
        logger.info("🖥️🔒 Attempting to start server with SSL.")
        # Check if cert files exist
        cert_file = "127.0.0.1+1.pem"
        key_file = "127.0.0.1+1-key.pem"
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
             logger.error(f"🖥️💥 SSL cert file ({cert_file}) or key file ({key_file}) not found.")
             logger.error("🖥️💥 Please generate them using mkcert:")
             logger.error("🖥️💥   choco install mkcert") # Assuming Windows based on earlier check, adjust if needed
             logger.error("🖥️💥   mkcert -install")
             logger.error("🖥️💥   mkcert 127.0.0.1 YOUR_LOCAL_IP") # Remind user to replace with actual IP if needed
             logger.error("🖥️💥 Exiting.")
             sys.exit(1)

        # Run the server with SSL
        logger.info(f"🖥️▶️ Starting server with SSL (cert: {cert_file}, key: {key_file}).")
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            log_config=None,
            ssl_certfile=cert_file,
            ssl_keyfile=key_file,
        )
