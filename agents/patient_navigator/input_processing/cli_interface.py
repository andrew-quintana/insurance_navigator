"""Enhanced CLI Interface for Input Processing Workflow.

This module provides a comprehensive command-line interface for the Input
Processing Workflow with performance monitoring, circuit breaker status,
and end-to-end workflow orchestration.
"""

import asyncio
import logging
import time
import json
import argparse
from typing import Dict, List, Optional, Any
from pathlib import Path

from .handler import DefaultInputHandler
from .router import IntelligentTranslationRouter
from .sanitizer import SanitizationAgent
from .integration import DefaultWorkflowHandoff
from .performance_monitor import get_performance_monitor, track_performance
from .circuit_breaker import CircuitBreaker
from .config import get_config
from .quality_validator import QualityValidator

logger = logging.getLogger(__name__)


class EnhancedCLIInterface:
    """Enhanced CLI interface with performance monitoring and workflow orchestration."""
    
    def __init__(self):
        """Initialize the enhanced CLI interface."""
        self.config = get_config()
        self.performance_monitor = get_performance_monitor()
        
        # Initialize workflow components
        self.input_handler = DefaultInputHandler()
        # Convert config to router-compatible format
        router_config = self.config.to_router_config()
        self.translation_router = IntelligentTranslationRouter(router_config)
        self.sanitization_agent = SanitizationAgent()
        self.integration_layer = DefaultWorkflowHandoff()
        self.quality_validator = QualityValidator()
        
        # Performance tracking
        self.workflow_start_time = None
        self.workflow_metrics = {}
        
        logger.info("Enhanced CLI interface initialized")
    
    @track_performance("cli_workflow")
    async def run_complete_workflow(
        self, 
        input_text: Optional[str] = None,
        input_file: Optional[str] = None,
        voice_input: bool = False,
        source_language: str = "auto",
        target_language: str = "en",
        user_preferences: Optional[Dict[str, Any]] = None,
        show_performance: bool = True,
        export_metrics: bool = False
    ) -> Dict[str, Any]:
        """Run the complete input processing workflow.
        
        Args:
            input_text: Direct text input
            input_file: Path to input file
            voice_input: Whether to use voice input
            source_language: Source language code
            target_language: Target language code
            user_preferences: User preferences for cost/quality trade-offs
            show_performance: Whether to display performance metrics
            export_metrics: Whether to export metrics to file
            
        Returns:
            Complete workflow results
        """
        self.workflow_start_time = time.time()
        
        try:
            print("🚀 Starting Input Processing Workflow...")
            print("=" * 50)
            
            # Step 1: Input Capture
            print("\n📥 Step 1: Input Capture")
            input_result = await self._capture_input(
                input_text, input_file, voice_input
            )
            
            if not input_result["success"]:
                return self._create_error_result("Input capture failed", input_result["error"])
            
            captured_text = input_result["text"]
            print(f"✅ Captured text: {captured_text[:100]}{'...' if len(captured_text) > 100 else ''}")
            
            # Step 2: Translation with Fallback
            print("\n🌐 Step 2: Translation with Intelligent Fallback")
            translation_result = await self._translate_with_fallback(
                captured_text, source_language, target_language, user_preferences
            )
            
            if not translation_result["success"]:
                return self._create_error_result("Translation failed", translation_result["error"])
            
            translated_text = translation_result["translated_text"]
            print(f"✅ Translation successful: {translated_text[:100]}{'...' if len(translated_text) > 100 else ''}")
            print(f"   Provider: {translation_result['provider']}")
            print(f"   Confidence: {translation_result['confidence']:.2f}")
            print(f"   Cost: ${translation_result['cost_estimate']:.6f}")
            
            # Step 3: Sanitization
            print("\n🧹 Step 3: Insurance Domain Sanitization")
            sanitization_result = await self._sanitize_content(translated_text)
            
            if not sanitization_result["success"]:
                return self._create_error_result("Sanitization failed", sanitization_result["error"])
            
            sanitized_text = sanitization_result["sanitized_text"]
            print(f"✅ Sanitization successful: {sanitized_text[:100]}{'...' if len(sanitized_text) > 100 else ''}")
            print(f"   Issues found: {sanitization_result['issues_count']}")
            print(f"   Confidence: {sanitization_result['confidence']:.2f}")
            
            # Step 3.5: Quality Validation
            print("\n🔍 Step 3.5: Quality Validation & Assessment")
            quality_result = await self._validate_quality(
                original_text=captured_text,
                translated_text=translated_text,
                sanitized_text=sanitized_text,
                source_language=source_language,
                target_language=target_language
            )
            
            if not quality_result["success"]:
                print(f"⚠️  Quality validation warning: {quality_result['warning']}")
            else:
                print(f"✅ Quality validation passed")
                print(f"   Overall score: {quality_result['overall_score']:.1f}/100")
                print(f"✅ Translation quality: {quality_result['translation_score']:.1f}/100")
                print(f"   Sanitization quality: {quality_result['sanitization_score']:.1f}/100")
                print(f"   Intent preservation: {quality_result['intent_score']:.1f}/100")
            
            # Step 4: Integration Layer
            print("\n🔗 Step 4: Integration Layer Processing")
            integration_result = await self._process_integration(
                sanitized_text, source_language, target_language
            )
            
            if not integration_result["success"]:
                return self._create_error_result("Integration failed", integration_result["error"])
            
            final_output = integration_result["output"]
            print(f"✅ Integration successful")
            print(f"   Output format: {integration_result['output_format']}")
            print(f"   Metadata fields: {len(integration_result['metadata'])}")
            
            # Step 5: Performance Summary
            if show_performance:
                print("\n📊 Step 5: Performance Summary")
                await self._display_performance_summary()
            
            # Step 6: Export Metrics (if requested)
            if export_metrics:
                print("\n💾 Step 6: Exporting Metrics")
                export_path = await self._export_workflow_metrics()
                print(f"✅ Metrics exported to: {export_path}")
            
            # Calculate total workflow time
            total_time = time.time() - self.workflow_start_time
            
            # Create final result
            result = {
                "success": True,
                "workflow_time": total_time,
                "input": {
                    "original_text": captured_text,
                    "source_language": source_language,
                    "target_language": target_language
                },
                "translation": {
                    "translated_text": translated_text,
                    "provider": translation_result["provider"],
                    "confidence": translation_result["confidence"],
                    "cost_estimate": translation_result["cost_estimate"]
                },
                "sanitization": {
                    "sanitized_text": sanitized_text,
                    "issues_count": sanitization_result["issues_count"],
                    "confidence": sanitization_result["confidence"]
                },
                "quality_validation": {
                    "overall_score": quality_result.get("overall_score", 0),
                    "translation_score": quality_result.get("translation_score", 0),
                    "sanitization_score": quality_result.get("sanitization_score", 0),
                    "intent_score": quality_result.get("intent_score", 0),
                    "warnings": quality_result.get("warnings", [])
                },
                "integration": {
                    "output": final_output,
                    "output_format": integration_result["output_format"],
                    "metadata": integration_result["metadata"]
                },
                "performance": {
                    "total_time": total_time,
                    "performance_metrics": self.workflow_metrics
                }
            }
            
            print("\n🎉 Workflow completed successfully!")
            print(f"⏱️  Total time: {total_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result("Workflow execution failed", error_msg)
    
    async def _capture_input(
        self, 
        input_text: Optional[str], 
        input_file: Optional[str], 
        voice_input: bool
    ) -> Dict[str, Any]:
        """Capture input from various sources."""
        try:
            if input_text:
                return {"success": True, "text": input_text, "source": "direct_input"}
            
            elif input_file:
                file_path = Path(input_file)
                if not file_path.exists():
                    return {"success": False, "error": f"Input file not found: {input_file}"}
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if not content:
                    return {"success": False, "error": "Input file is empty"}
                
                return {"success": True, "text": content, "source": "file_input"}
            
            elif voice_input:
                # Use voice input handler
                voice_result = await self.input_handler.capture_voice_input()
                if voice_result["success"]:
                    return {"success": True, "text": voice_result["text"], "source": "voice_input"}
                else:
                    return {"success": False, "error": voice_result["error"]}
            
            else:
                # Interactive input
                print("Enter text to process (press Enter twice to finish):")
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                
                text = "\n".join(lines[:-1]).strip()  # Remove last empty line
                if not text:
                    return {"success": False, "error": "No input text provided"}
                
                return {"success": True, "text": text, "source": "interactive_input"}
                
        except Exception as e:
            return {"success": False, "error": f"Input capture error: {str(e)}"}
    
    async def _translate_with_fallback(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Translate text with intelligent fallback."""
        try:
            result = await self.translation_router.translate_with_fallback(
                text, source_lang, target_lang, user_preferences
            )
            
            return {
                "success": True,
                "translated_text": result.text,
                "provider": result.provider,
                "confidence": result.confidence,
                "cost_estimate": result.cost_estimate
            }
            
        except Exception as e:
            return {"success": False, "error": f"Translation error: {str(e)}"}
    
    async def _sanitize_content(self, text: str) -> Dict[str, Any]:
        """Sanitize content for insurance domain."""
        try:
            # Create a default user context for sanitization
            from .types import UserContext
            context = UserContext(
                user_id="test_user",
                language_preference="en",
                domain_context="insurance",
                conversation_history=[],
                session_metadata={"test_session": True}
            )
            
            result = await self.sanitization_agent.sanitize(text, context)
            
            return {
                "success": True,
                "sanitized_text": result.structured_prompt,
                "issues_count": len(result.modifications),
                "confidence": result.confidence
            }
            
        except Exception as e:
            return {"success": False, "error": f"Sanitization error: {str(e)}"}
    
    async def _process_integration(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Dict[str, Any]:
        """Process content through integration layer."""
        try:
            # Create a sanitized output object for the integration layer
            from .types import SanitizedOutput
            sanitized_output = SanitizedOutput(
                cleaned_text=text,
                structured_prompt=text,
                confidence=0.9,
                modifications=[],
                metadata={"source_language": source_lang, "target_language": target_lang},
                original_text=text
            )
            
            # Create user context
            from .types import UserContext
            user_context = UserContext(
                user_id="test_user",
                language_preference=source_lang,
                domain_context="insurance",
                conversation_history=[],
                session_metadata={"test_session": True}
            )
            
            result = await self.integration_layer.format_for_downstream(
                sanitized_output, user_context
            )
            
            return {
                "success": True,
                "output": result.prompt_text,
                "output_format": "agent_prompt",
                "metadata": result.metadata
            }
            
        except Exception as e:
            return {"success": False, "error": f"Integration error: {str(e)}"}
    
    async def _validate_quality(
        self,
        original_text: str,
        translated_text: str,
        sanitized_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """Validate quality of translation and sanitization."""
        try:
            # Perform comprehensive quality validation
            validation_result = await self.quality_validator.validate_workflow_quality(
                original_text=original_text,
                translated_text=translated_text,
                sanitized_text=sanitized_text,
                source_language=source_language,
                target_language=target_language
            )
            
            return validation_result
            
        except Exception as e:
            return {
                "success": False,
                "warning": f"Quality validation failed: {str(e)}",
                "overall_score": 0,
                "translation_score": 0,
                "sanitization_score": 0,
                "intent_score": 0
            }
    
    async def _display_performance_summary(self) -> None:
        """Display comprehensive performance summary."""
        try:
            # Get performance summary
            summary = self.performance_monitor.get_performance_summary()
            
            # Display overall performance
            print(f"   Overall Performance:")
            if "overall" in summary:
                overall = summary["overall"]
                print(f"     Average duration: {overall['avg_duration']:.3f}s")
                print(f"     Median duration: {overall['median_duration']:.3f}s")
                print(f"     Min duration: {overall['min_duration']:.3f}s")
                print(f"     Max duration: {overall['max_duration']:.3f}s")
            
            # Display operation-specific performance
            print(f"   Operation Performance:")
            for op_name, op_stats in summary["operations"].items():
                print(f"     {op_name}:")
                print(f"       Total calls: {op_stats['total_calls']}")
                print(f"       Success rate: {op_stats['success_rate']:.1%}")
                print(f"       Avg duration: {op_stats['avg_duration']:.3f}s")
                print(f"       Min/Max: {op_stats['min_duration']:.3f}s / {op_stats['max_duration']:.3f}s")
            
            # Display system metrics
            system_metrics = summary.get("system", {})
            if system_metrics:
                print(f"   System Metrics:")
                print(f"     CPU usage: {system_metrics.get('cpu_percent', 0):.1f}%")
                print(f"     Memory usage: {system_metrics.get('memory_percent', 0):.1f}%")
                print(f"     Available memory: {system_metrics.get('memory_available_gb', 0):.1f} GB")
            
            # Display router statistics
            router_stats = self.translation_router.get_router_stats()
            print(f"   Router Statistics:")
            print(f"     Total translations: {router_stats['total_translations']}")
            print(f"     Fallback usage: {router_stats['fallback_usage']}")
            print(f"     Total cost tracked: ${router_stats['cost_tracking']['total_cost']:.6f}")
            print(f"     Circuit breaker state: {router_stats['circuit_breaker_status']['router_state']}")
            
        except Exception as e:
            print(f"   ⚠️  Performance display error: {e}")
    
    async def _export_workflow_metrics(self) -> str:
        """Export workflow metrics to file."""
        try:
            # Get current timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Export performance metrics
            performance_data = self.performance_monitor.export_metrics("json")
            
            # Get router statistics
            router_stats = self.translation_router.get_router_stats()
            
            # Combine all metrics
            export_data = {
                "timestamp": timestamp,
                "workflow_duration": time.time() - self.workflow_start_time,
                "performance_metrics": json.loads(performance_data),
                "router_statistics": router_stats,
                "workflow_metrics": self.workflow_metrics
            }
            
            # Create export directory if it doesn't exist
            export_dir = Path("logs/metrics_exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            export_path = export_dir / f"workflow_metrics_{timestamp}.json"
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return "export_failed"
    
    def _create_error_result(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "success": False,
            "error_type": error_type,
            "error_message": error_message,
            "workflow_time": time.time() - self.workflow_start_time if self.workflow_start_time else 0
        }
    
    async def show_system_status(self) -> None:
        """Display comprehensive system status."""
        print("\n🔍 System Status Report")
        print("=" * 50)
        
        try:
            # Provider health status
            print("\n📡 Provider Health Status:")
            provider_health = await self.translation_router._get_provider_health()
            for provider_name, is_healthy in provider_health.items():
                status_icon = "✅" if is_healthy else "❌"
                print(f"   {status_icon} {provider_name}: {'Healthy' if is_healthy else 'Unhealthy'}")
            
            # Circuit breaker status
            print("\n⚡ Circuit Breaker Status:")
            router_cb = self.translation_router.router_circuit_breaker
            print(f"   Router: {router_cb.state.value} (failures: {router_cb.failure_count})")
            
            for name, config in self.translation_router.providers.items():
                if hasattr(config.provider, 'circuit_breaker'):
                    cb = config.provider.circuit_breaker
                    print(f"   {name}: {cb.state.value} (failures: {cb.failure_count})")
            
            # Performance overview
            print("\n📊 Performance Overview:")
            summary = self.performance_monitor.get_performance_summary()
            print(f"   Monitor uptime: {summary['monitor_uptime']:.1f}s")
            print(f"   Total operations: {summary['total_operations']}")
            
            # Recent errors
            print("\n⚠️  Recent Errors:")
            error_summary = self.performance_monitor.get_error_summary()
            if error_summary:
                for operation, errors in error_summary.items():
                    print(f"   {operation}: {len(errors)} errors")
                    for error in errors[:3]:  # Show first 3 errors
                        print(f"     - {error[:100]}{'...' if len(error) > 100 else ''}")
            else:
                print("   No recent errors")
            
            # Cost summary
            print("\n💰 Cost Summary:")
            router_stats = self.translation_router.get_router_stats()
            cost_tracking = router_stats["cost_tracking"]
            print(f"   Total cost tracked: ${cost_tracking['total_cost']:.6f}")
            for provider, cost in cost_tracking['cost_by_provider'].items():
                print(f"   {provider}: ${cost:.6f}")
            
        except Exception as e:
            print(f"   ⚠️  Status report error: {e}")
    
    async def run_performance_test(self, test_text: str, iterations: int = 5) -> None:
        """Run performance test with multiple iterations."""
        print(f"\n🧪 Performance Test: {iterations} iterations")
        print("=" * 50)
        
        test_results = []
        
        for i in range(iterations):
            print(f"\nIteration {i + 1}/{iterations}")
            
            try:
                start_time = time.time()
                
                result = await self.run_complete_workflow(
                    input_text=test_text,
                    source_language="en",
                    target_language="es",
                    show_performance=False,
                    export_metrics=False
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if result["success"]:
                    test_results.append({
                        "iteration": i + 1,
                        "duration": duration,
                        "success": True
                    })
                    print(f"   ✅ Success in {duration:.3f}s")
                else:
                    test_results.append({
                        "iteration": i + 1,
                        "duration": duration,
                        "success": False,
                        "error": result.get("error_message", "Unknown error")
                    })
                    print(f"   ❌ Failed in {duration:.3f}s: {result.get('error_message', 'Unknown error')}")
                
            except Exception as e:
                test_results.append({
                    "iteration": i + 1,
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                })
                print(f"   ❌ Exception in {duration:.3f}s: {e}")
        
        # Calculate statistics
        successful_results = [r for r in test_results if r["success"]]
        if successful_results:
            durations = [r["duration"] for r in successful_results]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            print(f"\n📊 Test Results Summary:")
            print(f"   Successful iterations: {len(successful_results)}/{iterations}")
            print(f"   Average duration: {avg_duration:.3f}s")
            print(f"   Min duration: {min_duration:.3f}s")
            print(f"   Max duration: {max_duration:.3f}s")
            
            # Check performance targets
            if avg_duration < 5.0:
                print(f"   🎯 Performance target met: <5s latency")
            else:
                print(f"   ⚠️  Performance target missed: {avg_duration:.3f}s >= 5s")
        else:
            print(f"\n❌ All test iterations failed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Input Processing Workflow CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow with text input
  python -m agents.patient_navigator.input_processing.cli_interface --text "Hello world" --source-lang en --target-lang es
  
  # Run workflow with file input
  python -m agents.patient_navigator.input_processing.cli_interface --file input.txt --source-lang auto --target-lang en
  
  # Run workflow with voice input
  python -m agents.patient_navigator.input_processing.cli_interface --voice --source-lang auto --target-lang en
  
  # Show system status
  python -m agents.patient_navigator.input_processing.cli_interface --status
  
  # Run performance test
  python -m agents.patient_navigator.input_processing.cli_interface --performance-test --iterations 10
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument("--text", help="Direct text input")
    input_group.add_argument("--file", help="Input file path")
    input_group.add_argument("--voice", action="store_true", help="Use voice input")
    input_group.add_argument("--interactive", action="store_true", help="Interactive input mode")
    
    # Language options
    parser.add_argument("--source-lang", default="auto", help="Source language code (default: auto)")
    parser.add_argument("--target-lang", default="en", help="Target language code (default: en)")
    
    # Workflow options
    parser.add_argument("--user-preferences", help="JSON string of user preferences")
    parser.add_argument("--no-performance", action="store_true", help="Hide performance metrics")
    parser.add_argument("--export-metrics", action="store_true", help="Export metrics to file")
    
    # System commands
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--performance-test", action="store_true", help="Run performance test")
    parser.add_argument("--iterations", type=int, default=5, help="Number of test iterations")
    
    args = parser.parse_args()
    
    # Initialize CLI interface
    cli = EnhancedCLIInterface()
    
    async def run_cli():
        try:
            if args.status:
                await cli.show_system_status()
                return
            
            if args.performance_test:
                test_text = args.text or "This is a test message for performance testing of the input processing workflow."
                await cli.run_performance_test(test_text, args.iterations)
                return
            
            # Check if any input method is specified
            if not any([args.text, args.file, args.voice, args.interactive]):
                parser.print_help()
                return
            
            # Parse user preferences
            user_preferences = None
            if args.user_preferences:
                try:
                    user_preferences = json.loads(args.user_preferences)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON in user preferences")
                    return
            
            # Run workflow
            result = await cli.run_complete_workflow(
                input_text=args.text,
                input_file=args.file,
                voice_input=args.voice,
                source_language=args.source_lang,
                target_language=args.target_lang,
                user_preferences=user_preferences,
                show_performance=not args.no_performance,
                export_metrics=args.export_metrics
            )
            
            if not result["success"]:
                print(f"\n❌ Workflow failed: {result['error_message']}")
                return 1
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Workflow interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            logger.error(f"CLI error: {e}", exc_info=True)
            return 1
    
    # Run CLI
    exit_code = asyncio.run(run_cli())
    exit(exit_code)


if __name__ == "__main__":
    main()