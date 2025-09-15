#!/usr/bin/env python3
"""
Agent Migration Script - Phase 1 Import Management Resolution

This script migrates existing agents to use the new dependency injection pattern,
resolving import management issues as part of Phase 1 of the Agent Integration
Infrastructure Refactor.

Usage:
    python scripts/migrate_agents_to_di.py [--dry-run] [--agent-name AGENT_NAME]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class AgentMigrator:
    """Migrates agents to use dependency injection pattern."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.agents_dir = project_root / "agents"
        self.migrations_applied = []
        self.errors = []
    
    def migrate_all_agents(self) -> Dict[str, Any]:
        """Migrate all agents in the agents directory."""
        logger.info("Starting agent migration to dependency injection pattern")
        
        # Find all agent files
        agent_files = self._find_agent_files()
        logger.info(f"Found {len(agent_files)} agent files to migrate")
        
        for agent_file in agent_files:
            try:
                self._migrate_agent_file(agent_file)
            except Exception as e:
                error_msg = f"Failed to migrate {agent_file}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        return {
            "migrations_applied": self.migrations_applied,
            "errors": self.errors,
            "total_files": len(agent_files),
            "successful_migrations": len(self.migrations_applied)
        }
    
    def migrate_specific_agent(self, agent_name: str) -> Dict[str, Any]:
        """Migrate a specific agent by name."""
        logger.info(f"Migrating specific agent: {agent_name}")
        
        agent_files = self._find_agent_files()
        matching_files = [f for f in agent_files if agent_name in str(f)]
        
        if not matching_files:
            error_msg = f"No agent files found matching: {agent_name}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        for agent_file in matching_files:
            try:
                self._migrate_agent_file(agent_file)
            except Exception as e:
                error_msg = f"Failed to migrate {agent_file}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        return {
            "migrations_applied": self.migrations_applied,
            "errors": self.errors,
            "total_files": len(matching_files),
            "successful_migrations": len(self.migrations_applied)
        }
    
    def _find_agent_files(self) -> List[Path]:
        """Find all Python files in the agents directory."""
        agent_files = []
        
        for root, dirs, files in os.walk(self.agents_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    agent_files.append(Path(root) / file)
        
        return agent_files
    
    def _migrate_agent_file(self, agent_file: Path) -> None:
        """Migrate a single agent file to use dependency injection."""
        logger.info(f"Migrating agent file: {agent_file}")
        
        # Read the file
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply migrations
        original_content = content
        
        # Migration 1: Add core imports
        content = self._add_core_imports(content)
        
        # Migration 2: Update BaseAgent subclasses
        content = self._update_base_agent_subclasses(content)
        
        # Migration 3: Add dependency injection to constructors
        content = self._add_dependency_injection(content)
        
        # Migration 4: Add health check and initialization methods
        content = self._add_lifecycle_methods(content)
        
        # Migration 5: Update import statements
        content = self._update_import_statements(content)
        
        # Check if changes were made
        if content != original_content:
            if not self.dry_run:
                # Write the updated content
                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Successfully migrated: {agent_file}")
            else:
                logger.info(f"Would migrate: {agent_file} (dry run)")
            
            self.migrations_applied.append(str(agent_file))
        else:
            logger.info(f"No changes needed for: {agent_file}")
    
    def _add_core_imports(self, content: str) -> str:
        """Add core module imports if not present."""
        if "from core.database import" not in content and "from core.agent_integration import" not in content:
            # Add imports after existing imports
            lines = content.split('\n')
            import_end = 0
            
            for i, line in enumerate(lines):
                if line.startswith(('import ', 'from ')):
                    import_end = i + 1
                elif line.strip() == '' and import_end > 0:
                    break
            
            # Insert core imports
            core_imports = [
                "",
                "# Core dependency injection imports",
                "from core.database import DatabaseManager",
                "from core.agent_integration import AgentIntegrationManager",
                ""
            ]
            
            lines[import_end:import_end] = core_imports
            content = '\n'.join(lines)
        
        return content
    
    def _update_base_agent_subclasses(self, content: str) -> str:
        """Update BaseAgent subclasses to support dependency injection."""
        # This is a simplified migration - in practice, you'd need more sophisticated parsing
        if "class " in content and "BaseAgent" in content:
            # Add dependency injection parameters to constructors
            content = content.replace(
                "def __init__(self,",
                "def __init__(self, db_manager: Optional[DatabaseManager] = None, config: Optional[Dict[str, Any]] = None,"
            )
        
        return content
    
    def _add_dependency_injection(self, content: str) -> str:
        """Add dependency injection support to agent constructors."""
        # Store injected dependencies
        if "def __init__" in content and "self.db_manager = db_manager" not in content:
            # Find the end of __init__ method and add dependency storage
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def __init__" in line:
                    # Find the end of the method (look for next method or class)
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith(('    def ', '    async def ', 'class ')) or (lines[j].strip() and not lines[j].startswith('    ')):
                            # Insert dependency storage before the next method
                            dependency_lines = [
                                "        # Store injected dependencies",
                                "        self.db_manager = db_manager",
                                "        self.config = config or {}",
                                ""
                            ]
                            lines[j:j] = dependency_lines
                            break
                    break
            
            content = '\n'.join(lines)
        
        return content
    
    def _add_lifecycle_methods(self, content: str) -> str:
        """Add health check and initialization methods if not present."""
        if "async def health_check" not in content:
            # Add lifecycle methods at the end of the class
            lines = content.split('\n')
            class_end = 0
            
            for i, line in enumerate(lines):
                if line.startswith('class '):
                    # Find the end of the class
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith(('    ', '    async def ', '    def ')):
                            class_end = j
                            break
            
            lifecycle_methods = [
                "",
                "    async def initialize(self) -> None:",
                "        \"\"\"Initialize the agent with injected dependencies.\"\"\"",
                "        self.logger.info(f\"Initializing agent: {self.name}\")",
                "        # Override in subclasses for custom initialization",
                "        pass",
                "",
                "    async def health_check(self) -> Dict[str, Any]:",
                "        \"\"\"Perform health check on the agent.\"\"\"",
                "        try:",
                "            return {",
                "                \"status\": \"healthy\",",
                "                \"agent_name\": self.name,",
                "                \"mock_mode\": getattr(self, 'mock', False),",
                "                \"has_db_manager\": self.db_manager is not None",
                "            }",
                "        except Exception as e:",
                "            return {",
                "                \"status\": \"unhealthy\",",
                "                \"agent_name\": self.name,",
                "                \"error\": str(e)",
                "            }",
                "",
                "    async def shutdown(self) -> None:",
                "        \"\"\"Shutdown the agent and cleanup resources.\"\"\"",
                "        self.logger.info(f\"Shutting down agent: {self.name}\")",
                "        # Override in subclasses for custom shutdown logic",
                "        pass"
            ]
            
            lines[class_end:class_end] = lifecycle_methods
            content = '\n'.join(lines)
        
        return content
    
    def _update_import_statements(self, content: str) -> str:
        """Update import statements to use new core modules."""
        # Replace old database imports with core imports
        content = content.replace(
            "from backend.shared.db.connection import",
            "from core.database import"
        )
        content = content.replace(
            "from api.upload_pipeline.database import",
            "from core.database import"
        )
        
        return content


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate agents to dependency injection pattern")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    parser.add_argument("--agent-name", type=str, help="Migrate specific agent by name")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create migrator
    migrator = AgentMigrator(dry_run=args.dry_run)
    
    try:
        if args.agent_name:
            result = migrator.migrate_specific_agent(args.agent_name)
        else:
            result = migrator.migrate_all_agents()
        
        # Print results
        print(f"\n{'='*60}")
        print(f"Agent Migration Results")
        print(f"{'='*60}")
        print(f"Total files processed: {result['total_files']}")
        print(f"Successful migrations: {result['successful_migrations']}")
        print(f"Errors: {len(result['errors'])}")
        
        if result['migrations_applied']:
            print(f"\nMigrated files:")
            for file in result['migrations_applied']:
                print(f"  ✅ {file}")
        
        if result['errors']:
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  ❌ {error}")
        
        if args.dry_run:
            print(f"\n⚠️  This was a dry run - no files were actually modified")
        
        print(f"\n{'='*60}")
        
        return 0 if not result['errors'] else 1
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
