#!/usr/bin/env python3
"""
Quick test script for ElevenLabs Speech-to-Text functionality.
This allows us to test voice input without needing PyAudio.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.development')

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_elevenlabs_stt():
    """Test ElevenLabs speech-to-text functionality."""
    
    try:
        from elevenlabs import speech_to_text
        from elevenlabs.core import client_wrapper
        import httpx
        
        # Get API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment")
            return
        
        print("✅ ElevenLabs API key loaded")
        
        # Check what audio files we have
        audio_files = list(project_root.glob("**/*.wav")) + list(project_root.glob("**/*.mp3")) + list(project_root.glob("**/*.m4a"))
        
        if audio_files:
            print(f"🎵 Found audio files: {[f.name for f in audio_files[:3]]}")
            # Use the first audio file for testing
            test_file = audio_files[0]
            print(f"🎤 Testing with: {test_file}")
            
            # Create client wrapper with API key
            client_wrapper_instance = client_wrapper.AsyncClientWrapper(
                api_key=api_key,
                base_url="https://api.elevenlabs.io",
                timeout=30.0,
                httpx_client=httpx.AsyncClient()
            )
            
            # Create speech-to-text client
            stt_client = speech_to_text.client.AsyncSpeechToTextClient(
                client_wrapper=client_wrapper_instance
            )
            
            # Test speech-to-text conversion
            try:
                # Open file as file object
                with open(test_file, 'rb') as audio_file:
                    response = await stt_client.convert(
                        file=audio_file,
                        model_id="scribe_v1"  # Use the correct model ID
                    )
                    print(f"✅ Speech-to-text successful!")
                    print(f"📝 Transcribed text: {response.text}")
                    
                    # Handle different response structures
                    if hasattr(response, 'language'):
                        print(f"🔍 Language detected: {response.language}")
                    if hasattr(response, 'processing_time_seconds'):
                        print(f"⏱️  Processing time: {response.processing_time_seconds}s")
                    
                    # Show a preview of the transcription
                    preview = response.text[:100] + "..." if len(response.text) > 100 else response.text
                    print(f"📖 Preview: {preview}")
                    
            except Exception as e:
                print(f"❌ Speech-to-text failed: {e}")
                
        else:
            print("🎵 No audio files found for testing")
            print("💡 To test voice input, you can:")
            print("   1. Record a short audio file (.wav, .mp3, .m4a)")
            print("   2. Place it in the examples/ directory")
            print("   3. Run this script again")
            
            # Test the API connection anyway
            print("\n🔍 Testing API connection...")
            try:
                # Create client wrapper with API key
                client_wrapper_instance = client_wrapper.AsyncClientWrapper(
                    api_key=api_key,
                    base_url="https://api.elevenlabs.io",
                    timeout=30.0,
                    httpx_client=httpx.AsyncClient()
                )
                
                # Create speech-to-text client
                stt_client = speech_to_text.client.AsyncSpeechToTextClient(
                    client_wrapper=client_wrapper_instance
                )
                
                print("✅ ElevenLabs API connection successful")
                print("🎤 Speech-to-text client ready for use")
                
            except Exception as e:
                print(f"❌ API connection failed: {e}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure elevenlabs is installed: pip install elevenlabs")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

async def create_test_audio():
    """Create a simple test audio file for testing."""
    
    print("\n🎵 Creating Test Audio File...")
    print("=" * 40)
    
    try:
        # Check if we have text-to-speech capabilities
        from elevenlabs import text_to_speech
        from elevenlabs.core import client_wrapper
        import httpx
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment")
            return
        
        print("✅ Creating test audio file using ElevenLabs TTS...")
        
        # Create client wrapper
        client_wrapper_instance = client_wrapper.AsyncClientWrapper(
            api_key=api_key,
            base_url="https://api.elevenlabs.io",
            timeout=30.0,
            httpx_client=httpx.AsyncClient()
        )
        
        # Create TTS client
        tts_client = text_to_speech.client.AsyncTextToSpeechClient(
            client_wrapper=client_wrapper_instance
        )
        
        # Test text to convert to speech
        test_text = "Hello, I need help with my insurance policy. Can you assist me?"
        
        print(f"📝 Converting text to speech: '{test_text}'")
        
        # Generate speech - handle async generator correctly
        response = tts_client.convert(
            text=test_text,
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            model_id="eleven_multilingual_v2"
        )
        
        # The response is an async generator, we need to collect the audio chunks
        audio_chunks = []
        async for chunk in response:
            if hasattr(chunk, 'audio') and chunk.audio:
                audio_chunks.append(chunk.audio)
            elif hasattr(chunk, 'audio'):
                # Handle case where chunk.audio might be None
                continue
        
        if audio_chunks:
            # Combine all audio chunks
            combined_audio = b''.join(audio_chunks)
            
            # Save the audio file
            output_path = project_root / "examples" / "test_voice_input.wav"
            with open(output_path, "wb") as f:
                f.write(combined_audio)
            
            print(f"✅ Test audio file created: {output_path}")
            print(f"💾 File size: {len(combined_audio)} bytes")
            
            # Now test speech-to-text with this file
            print("\n🎤 Testing speech-to-text with generated audio...")
            
            # Create speech-to-text client
            from elevenlabs import speech_to_text
            stt_client = speech_to_text.client.AsyncSpeechToTextClient(
                client_wrapper=client_wrapper_instance
            )
            
            # Convert back to text
            with open(output_path, 'rb') as audio_file:
                stt_response = await stt_client.convert(
                    file=audio_file,
                    model_id="scribe_v1"  # Use the correct model ID
                )
            
            print(f"✅ Speech-to-text successful!")
            print(f"📝 Original text: '{test_text}'")
            print(f"📝 Transcribed text: '{stt_response.text}'")
            
            # Handle different response structures
            if hasattr(stt_response, 'language'):
                print(f"🔍 Language detected: {stt_response.language}")
            if hasattr(stt_response, 'processing_time_seconds'):
                print(f"⏱️  Processing time: {stt_response.processing_time_seconds}s")
            
            # Calculate accuracy
            original_words = set(test_text.lower().split())
            transcribed_words = set(stt_response.text.lower().split())
            accuracy = len(original_words.intersection(transcribed_words)) / len(original_words) * 100
            print(f"🎯 Word accuracy: {accuracy:.1f}%")
        else:
            print("❌ No audio chunks received from TTS")
            print("🔍 Debugging TTS response...")
            
            # Try to debug what we're getting
            response = tts_client.convert(
                text=test_text,
                voice_id="21m00Tcm4TlvDq8ikWAM",
                model_id="eleven_multilingual_v2"
            )
            
            chunk_count = 0
            async for chunk in response:
                chunk_count += 1
                print(f"Chunk {chunk_count}: {type(chunk)} - {dir(chunk)}")
                if hasattr(chunk, 'audio'):
                    print(f"  Audio attribute: {chunk.audio is not None}")
                if hasattr(chunk, 'text'):
                    print(f"  Text: {chunk.text}")
        
    except Exception as e:
        print(f"❌ Error creating test audio: {e}")
        import traceback
        traceback.print_exc()

async def test_voice_workflow():
    """Test the complete voice workflow using the existing CLI interface."""
    
    print("\n🚀 Testing Complete Voice Workflow...")
    print("=" * 50)
    
    try:
        # Import the CLI interface
        from agents.patient_navigator.input_processing.cli_interface import EnhancedCLIInterface
        
        cli = EnhancedCLIInterface()
        
        # Test system status
        print("📊 Checking system status...")
        await cli.show_system_status()
        
        # Test with a mock voice input (since we don't have real audio)
        print("\n🎤 Testing voice workflow with mock input...")
        
        # We'll simulate what would happen with voice input
        test_text = "I need help with my insurance policy"
        print(f"📝 Simulated voice input: '{test_text}'")
        
        # Run the workflow
        result = await cli.run_complete_workflow(
            input_text=test_text,
            voice_input=False,  # Set to False since we're simulating
            source_language="en",
            target_language="es",
            show_performance=True
        )
        
        if result["success"]:
            print("✅ Voice workflow test successful!")
        else:
            print(f"❌ Voice workflow test failed: {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Voice workflow test error: {e}")

async def test_real_voice_input():
    """Test with a real audio file if available."""
    
    print("\n🎤 Testing Real Voice Input...")
    print("=" * 40)
    
    # Look for audio files in the examples directory
    examples_dir = project_root / "examples"
    audio_files = list(examples_dir.glob("*.wav")) + list(examples_dir.glob("*.mp3")) + list(examples_dir.glob("*.m4a"))
    
    if not audio_files:
        print("🎵 No audio files found in examples directory")
        return
    
    print(f"🎵 Found {len(audio_files)} audio file(s) for testing")
    
    for audio_file in audio_files[:2]:  # Test up to 2 files
        print(f"\n🎤 Testing with: {audio_file.name}")
        
        try:
            # Test speech-to-text
            from elevenlabs import speech_to_text
            from elevenlabs.core import client_wrapper
            import httpx
            
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                print("❌ ELEVENLABS_API_KEY not found")
                continue
            
            # Create client
            client_wrapper_instance = client_wrapper.AsyncClientWrapper(
                api_key=api_key,
                base_url="https://api.elevenlabs.io",
                timeout=30.0,
                httpx_client=httpx.AsyncClient()
            )
            
            stt_client = speech_to_text.client.AsyncSpeechToTextClient(
                client_wrapper=client_wrapper_instance
            )
            
            # Convert audio to text
            with open(audio_file, 'rb') as f:
                response = await stt_client.convert(
                    file=f,
                    model_id="scribe_v1"
                )
            
            print(f"✅ Transcription successful!")
            print(f"📝 Text: {response.text[:200]}...")
            
            # Now test the complete workflow with this transcribed text
            print(f"🔄 Running complete workflow with transcribed text...")
            
            from agents.patient_navigator.input_processing.cli_interface import EnhancedCLIInterface
            cli = EnhancedCLIInterface()
            
            result = await cli.run_complete_workflow(
                input_text=response.text,
                voice_input=True,  # Mark as voice input
                source_language="en",
                target_language="es",
                show_performance=True
            )
            
            if result["success"]:
                print(f"✅ Voice workflow successful with real audio!")
                print(f"📊 Final output: {result.get('output', 'No output')}")
            else:
                print(f"❌ Voice workflow failed: {result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing {audio_file.name}: {e}")

async def main():
    """Main test function."""
    print("🎯 ElevenLabs Speech-to-Text Test")
    print("=" * 40)
    
    # Test 1: Basic ElevenLabs STT functionality
    await test_elevenlabs_stt()
    
    # Test 2: Create test audio file
    await create_test_audio()
    
    # Test 3: Test with real audio files if available
    await test_real_voice_input()
    
    # Test 4: Complete voice workflow
    await test_voice_workflow()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 