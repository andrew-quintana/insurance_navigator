"""Input Handler implementation for voice and text input capture."""

import asyncio
import logging
from typing import Union, List
import sys
import io
import wave
import threading
import time

# Audio processing imports
try:
    import pyaudio
    import speech_recognition as sr
    import scipy.io.wavfile as wavfile
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError as e:
    AUDIO_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Audio processing libraries not available: {e}")

from .types import InputHandler, QualityScore, InputType, InputCaptureError
from .config import get_input_config

logger = logging.getLogger(__name__)


class DefaultInputHandler(InputHandler):
    """Default implementation of the InputHandler protocol."""
    
    def __init__(self):
        """Initialize the input handler."""
        self.config = get_input_config()
        
        # Audio configuration
        self.sample_rate = 44100
        self.channels = 1
        self.chunk_size = 1024
        self.format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        
        # Initialize PyAudio if available
        self.audio = None
        if AUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
                logger.info("PyAudio initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PyAudio: {e}")
                self.audio = None
        
        # Speech recognition
        self.recognizer = sr.Recognizer() if AUDIO_AVAILABLE else None
        if self.recognizer:
            # Adjust for ambient noise
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.energy_threshold = 4000
            self.recognizer.pause_threshold = 0.8
        
        logger.info("Input handler initialized")
    
    async def capture_voice_input(self, timeout: float = 30.0) -> bytes:
        """Capture audio from microphone and return raw audio bytes.
        
        Args:
            timeout: Maximum time to wait for input in seconds
            
        Returns:
            Raw audio bytes
            
        Raises:
            TimeoutError: If no input received within timeout
            RuntimeError: If microphone access fails
        """
        if not AUDIO_AVAILABLE or not self.audio:
            logger.error("Audio capture not available - missing dependencies or initialization failed")
            raise RuntimeError("Audio capture not available")
        
        logger.info(f"Starting voice capture with {timeout}s timeout")
        
        try:
            # Use asyncio to run audio capture in executor
            # Addresses: FM-043 - Replace deprecated get_event_loop() with get_running_loop()
            loop = asyncio.get_running_loop()
            audio_data = await loop.run_in_executor(
                None, 
                self._capture_audio_sync, 
                timeout
            )
            
            if len(audio_data) == 0:
                raise TimeoutError("No audio captured within timeout period")
            
            logger.info(f"Voice capture completed: {len(audio_data)} bytes")
            return audio_data
            
        except TimeoutError:
            logger.warning(f"Voice capture timed out after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"Voice capture failed: {e}")
            raise RuntimeError(f"Voice capture failed: {e}")
    
    def _capture_audio_sync(self, timeout: float) -> bytes:
        """Synchronous audio capture implementation.
        
        Args:
            timeout: Maximum time to wait for input
            
        Returns:
            Raw audio bytes
        """
        if not self.audio:
            raise RuntimeError("PyAudio not initialized")
        
        # Open audio stream
        stream = None
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.debug("Audio stream opened, starting recording...")
            
            frames = []
            start_time = time.time()
            silence_threshold = 500  # Adjust based on testing
            silence_duration = 0
            max_silence = 3.0  # Stop after 3 seconds of silence
            
            # Record audio with timeout and silence detection
            while time.time() - start_time < timeout:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Check for silence
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    volume = np.sqrt(np.mean(audio_array**2))
                    
                    if volume < silence_threshold:
                        silence_duration += self.chunk_size / self.sample_rate
                        if silence_duration > max_silence and len(frames) > 10:
                            logger.debug("Detected end of speech, stopping recording")
                            break
                    else:
                        silence_duration = 0
                        
                except Exception as e:
                    logger.error(f"Error reading audio chunk: {e}")
                    break
            
            if not frames:
                logger.warning("No audio frames captured")
                return b""
            
            # Combine all frames
            audio_data = b''.join(frames)
            logger.debug(f"Captured {len(frames)} audio chunks, {len(audio_data)} total bytes")
            
            return audio_data
            
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    logger.error(f"Error closing audio stream: {e}")
    
    def convert_speech_to_text(self, audio_data: bytes) -> str:
        """Convert audio bytes to text using speech recognition.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Transcribed text
            
        Raises:
            InputCaptureError: If speech recognition fails
        """
        if not AUDIO_AVAILABLE or not self.recognizer:
            raise InputCaptureError("Speech recognition not available")
        
        if len(audio_data) == 0:
            raise InputCaptureError("No audio data provided")
        
        try:
            # Convert raw audio bytes to AudioData
            audio_buffer = io.BytesIO()
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            audio_buffer.seek(0)
            
            # Use speech recognition
            with sr.AudioFile(audio_buffer) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                # Record the audio
                audio = self.recognizer.record(source)
            
            logger.debug("Attempting speech recognition...")
            
            # Try Google Speech Recognition (free tier)
            try:
                text = self.recognizer.recognize_google(audio, language='es-ES')
                logger.info(f"Speech recognition successful: '{text}'")
                return text
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                raise InputCaptureError("Could not understand audio")
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                # Fallback to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Offline speech recognition successful: '{text}'")
                    return text
                except Exception:
                    raise InputCaptureError(f"Speech recognition failed: {e}")
                
        except Exception as e:
            logger.error(f"Speech to text conversion failed: {e}")
            raise InputCaptureError(f"Speech to text conversion failed: {e}")
    
    async def capture_text_input(self, prompt: str = "Enter your message: ") -> str:
        """Capture text input from CLI.
        
        Args:
            prompt: Prompt to display to user
            
        Returns:
            User input text
            
        Raises:
            KeyboardInterrupt: If user cancels input
        """
        try:
            logger.debug(f"Capturing text input with prompt: {prompt}")
            
            # Use asyncio to make this non-blocking
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, input, prompt)
            
            # Validate input length
            max_length = self.config["max_text_length"]
            if len(user_input) > max_length:
                logger.warning(f"Input truncated from {len(user_input)} to {max_length} characters")
                user_input = user_input[:max_length]
            
            logger.info(f"Captured text input: {len(user_input)} characters")
            return user_input.strip()
            
        except KeyboardInterrupt:
            logger.info("Text input cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Error capturing text input: {e}")
            raise InputCaptureError(f"Failed to capture text input: {e}")
    
    def validate_input_quality(self, input_data: Union[bytes, str]) -> QualityScore:
        """Validate quality of input data.
        
        Args:
            input_data: Raw input data (audio bytes or text string)
            
        Returns:
            QualityScore with assessment and issues
        """
        issues = []
        
        if isinstance(input_data, bytes):
            # Audio quality validation
            if len(input_data) == 0:
                issues.append("No audio data captured")
                return QualityScore(score=0.0, confidence=1.0, issues=issues)
            
            # Real audio quality analysis
            if AUDIO_AVAILABLE:
                try:
                    # Convert bytes to numpy array for analysis
                    audio_array = np.frombuffer(input_data, dtype=np.int16)
                    
                    # Check audio length
                    duration = len(audio_array) / self.sample_rate
                    if duration < 0.5:
                        issues.append("Audio too short (less than 0.5 seconds)")
                    elif duration > 30:
                        issues.append("Audio too long (more than 30 seconds)")
                    
                    # Analyze audio levels
                    rms = np.sqrt(np.mean(audio_array**2))
                    max_amplitude = np.max(np.abs(audio_array))
                    
                    # Check for silence
                    if rms < 100:
                        issues.append("Audio level too low - possible silence")
                    elif rms > 8000:
                        issues.append("Audio level too high - possible clipping")
                    
                    # Check for clipping
                    if max_amplitude >= 32767 * 0.95:  # Near max for 16-bit
                        issues.append("Audio clipping detected")
                    
                    # Calculate signal-to-noise ratio estimate
                    if len(audio_array) > 0:
                        noise_floor = np.percentile(np.abs(audio_array), 10)
                        snr_estimate = rms / max(noise_floor, 1)
                        if snr_estimate < 3:
                            issues.append("Low signal-to-noise ratio")
                    
                    # Calculate quality score
                    score = 1.0
                    if duration < 0.5 or duration > 30:
                        score -= 0.3
                    if rms < 100 or rms > 8000:
                        score -= 0.2
                    if max_amplitude >= 32767 * 0.95:
                        score -= 0.3
                    if len(issues) > 0:
                        score -= len(issues) * 0.1
                    
                    score = max(0.0, score)
                    confidence = 0.8
                    
                except Exception as e:
                    logger.warning(f"Audio quality analysis failed: {e}")
                    issues.append("Audio quality analysis failed")
                    score = 0.5
                    confidence = 0.5
            else:
                # Fallback for when audio libraries not available
                score = 0.6  # Moderate quality assumption
                confidence = 0.5
                issues.append("Audio quality analysis unavailable")
            
        else:  # text input
            # Text quality validation
            text = input_data.strip()
            
            if len(text) == 0:
                issues.append("Empty text input")
                return QualityScore(score=0.0, confidence=1.0, issues=issues)
            
            if len(text) < 3:
                issues.append("Text input too short")
            
            if len(text) > self.config["max_text_length"]:
                issues.append(f"Text input exceeds maximum length ({self.config['max_text_length']} characters)")
            
            # Check for suspicious patterns
            if text.count(' ') == 0 and len(text) > 10:
                issues.append("No spaces detected - possible input error")
            
            # Check for non-printable characters
            if any(ord(char) < 32 or ord(char) > 126 for char in text if char not in '\n\r\t'):
                non_printable_count = sum(1 for char in text if ord(char) < 32 or ord(char) > 126)
                if non_printable_count > len(text) * 0.1:  # More than 10% non-printable
                    issues.append("High number of non-printable characters")
            
            # Calculate quality score based on issues
            score = max(0.1, 1.0 - (len(issues) * 0.2))
            confidence = 0.8 if issues else 0.95
        
        logger.debug(f"Input quality validation: score={score}, confidence={confidence}, issues={issues}")
        return QualityScore(score=score, confidence=confidence, issues=issues)
    
    def get_supported_input_types(self) -> List[InputType]:
        """Get list of supported input types."""
        # For Phase 1, support both text and voice (voice is placeholder)
        return [InputType.TEXT, InputType.VOICE]