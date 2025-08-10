"""CLI interface for the Input Processing Workflow."""

import asyncio
import argparse
import logging
import sys
from typing import Optional
import json

from .types import InputType, UserContext, ProcessingError
from .handler import DefaultInputHandler
from .router import TranslationRouter
from .sanitizer import SanitizationAgent
from .integration import DefaultWorkflowHandoff
from .config import get_config

logger = logging.getLogger(__name__)


class InputProcessingCLI:
    """Command-line interface for input processing workflow."""
    
    def __init__(self):
        """Initialize the CLI with all pipeline components."""
        try:
            self.config = get_config()
            self.input_handler = DefaultInputHandler()
            self.translation_router = TranslationRouter()
            self.sanitizer = SanitizationAgent()
            self.integration = DefaultWorkflowHandoff({})
            
            logger.info("Input processing CLI initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize CLI: {e}")
            raise
    
    async def process_voice_input(self) -> str:
        """Process voice input through full pipeline.
        
        Returns:
            Structured prompt for downstream agents
        """
        logger.info("Starting voice input processing")
        
        try:
            # Step 1: Capture voice input
            print("🎤 Listening for voice input... (Press Ctrl+C to cancel)")
            audio_data = await self.input_handler.capture_voice_input(
                timeout=self.config.voice_timeout
            )
            
            # Validate audio quality
            quality = self.input_handler.validate_input_quality(audio_data)
            print(f"🔍 Audio quality score: {quality.score:.2f}")
            
            if quality.score < self.config.min_audio_quality_score:
                print(f"⚠️  Audio quality too low (issues: {', '.join(quality.issues)})")
                return "Audio quality insufficient for processing"
            
            # For Phase 1, audio processing is not implemented
            print("⚠️  Voice processing not yet implemented. Please use text input mode.")
            return "Voice processing not available in Phase 1"
            
        except KeyboardInterrupt:
            print("\n👋 Voice input cancelled by user")
            return "Input cancelled"
        except Exception as e:
            logger.error(f"Voice input processing failed: {e}")
            return f"Error: {e}"
    
    async def process_text_input(self, text: Optional[str] = None) -> str:
        """Process text input through full pipeline.
        
        Args:
            text: Text to process (if None, will prompt user)
            
        Returns:
            Structured prompt for downstream agents
        """
        logger.info("Starting text input processing")
        
        try:
            # Step 1: Capture text input
            if text is None:
                print("📝 Text Input Mode")
                input_text = await self.input_handler.capture_text_input(
                    "Enter your message (in Spanish): "
                )
            else:
                input_text = text
            
            if not input_text.strip():
                print("❌ Empty input provided")
                return "Empty input"
            
            # Validate text quality
            quality = self.input_handler.validate_input_quality(input_text)
            print(f"🔍 Text quality score: {quality.score:.2f}")
            
            if quality.issues:
                print(f"⚠️  Quality issues: {', '.join(quality.issues)}")
            
            # Create user context
            user_context = UserContext(
                user_id="cli_user",
                conversation_history=[],
                language_preference=self.config.default_language,
                domain_context=self.config.domain_context
            )
            
            # Step 2: Translation
            print(f"🌍 Translating from {self.config.default_language} to {self.config.target_language}...")
            translation_result = await self.translation_router.route(
                input_text, 
                self.config.default_language
            )
            
            print(f"✅ Translation complete (confidence: {translation_result.confidence:.2f}, provider: {translation_result.provider})")
            print(f"📄 Translated text: {translation_result.text}")
            
            # Step 3: Sanitization
            print("🧹 Sanitizing and structuring text...")
            sanitized_output = await self.sanitizer.sanitize(
                translation_result.text,
                user_context
            )
            
            print(f"✅ Sanitization complete (confidence: {sanitized_output.confidence:.2f})")
            print(f"🔧 Modifications applied: {len(sanitized_output.modifications)}")
            for mod in sanitized_output.modifications:
                print(f"   - {mod}")
            
            # Step 4: Integration
            print("🔗 Formatting for downstream workflow...")
            agent_prompt = await self.integration.format_for_downstream(
                sanitized_output,
                user_context
            )
            
            print("✅ Processing complete!")
            print(f"📋 Final structured prompt: {agent_prompt.prompt_text}")
            print(f"🎯 Overall confidence: {agent_prompt.confidence:.2f}")
            
            return agent_prompt.prompt_text
            
        except KeyboardInterrupt:
            print("\n👋 Text input cancelled by user")
            return "Input cancelled"
        except Exception as e:
            logger.error(f"Text input processing failed: {e}")
            print(f"❌ Error: {e}")
            return f"Error: {e}"
    
    async def run_interactive_mode(self):
        """Run interactive CLI mode for testing."""
        print("🚀 Input Processing Workflow - Interactive Mode")
        print("=" * 50)
        
        # Display configuration
        print(f"🔧 Configuration:")
        print(f"   Source language: {self.config.default_language}")
        print(f"   Target language: {self.config.target_language}")
        print(f"   Available providers: {list(self.translation_router.get_available_providers().keys())}")
        print(f"   Voice timeout: {self.config.voice_timeout}s")
        print()
        
        while True:
            try:
                print("Select input mode:")
                print("1. Text input")
                print("2. Voice input (placeholder)")
                print("3. Exit")
                
                choice = input("Enter choice (1-3): ").strip()
                
                if choice == "1":
                    result = await self.process_text_input()
                    print(f"\n🏁 Result: {result}\n")
                    
                elif choice == "2":
                    result = await self.process_voice_input()
                    print(f"\n🏁 Result: {result}\n")
                    
                elif choice == "3":
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.\n")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Interactive mode error: {e}")
                print(f"❌ Unexpected error: {e}")
                print("Continuing...\n")
    
    def get_status(self) -> dict:
        """Get status of all pipeline components."""
        return {
            "config_valid": True,
            "input_handler_ready": True,
            "translation_providers": self.translation_router.get_available_providers(),
            "sanitizer_ready": True,
            "integration_ready": True,
            "supported_input_types": [t.value for t in self.input_handler.get_supported_input_types()]
        }


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Input Processing Workflow CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python -m agents.patient_navigator.input_processing.cli_interface

  # Process text directly
  python -m agents.patient_navigator.input_processing.cli_interface --text "Necesito ayuda con mi seguro"

  # Check status
  python -m agents.patient_navigator.input_processing.cli_interface --status
        """
    )
    
    parser.add_argument(
        "--text",
        type=str,
        help="Text to process directly (skips interactive input)"
    )
    
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Use voice input mode"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status and exit"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        cli = InputProcessingCLI()
        
        if args.status:
            # Show status and exit
            status = cli.get_status()
            print("🔍 System Status:")
            print(json.dumps(status, indent=2))
            return
        
        if args.text:
            # Process provided text
            result = await cli.process_text_input(args.text)
            print(f"Result: {result}")
            
        elif args.voice:
            # Process voice input
            result = await cli.process_voice_input()
            print(f"Result: {result}")
            
        else:
            # Interactive mode
            await cli.run_interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())