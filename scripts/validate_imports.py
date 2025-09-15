#!/usr/bin/env python3
"""
Import Validation Script - Phase 1 Import Management Resolution

This script validates that all imports are properly resolved and there are no
circular dependencies, implementing CI/CD import validation as part of Phase 1
of the Agent Integration Infrastructure Refactor.

Usage:
    python scripts/validate_imports.py [--check-circular] [--check-psycopg2] [--verbose]
"""

import os
import sys
import ast
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any
import importlib.util
import traceback

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class ImportValidator:
    """Validates imports and detects circular dependencies."""
    
    def __init__(self):
        self.project_root = project_root
        self.import_graph: Dict[str, Set[str]] = {}
        self.import_errors: List[Dict[str, Any]] = []
        self.circular_dependencies: List[List[str]] = []
        self.psycopg2_usage: List[Dict[str, Any]] = []
    
    def validate_all_imports(self, check_circular: bool = True, check_psycopg2: bool = True) -> Dict[str, Any]:
        """Validate all imports in the project."""
        logger.info("Starting import validation")
        
        # Find all Python files
        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files to validate")
        
        # Validate each file
        for file_path in python_files:
            self._validate_file_imports(file_path)
        
        # Check for circular dependencies
        if check_circular:
            self._detect_circular_dependencies()
        
        # Check for psycopg2 usage
        if check_psycopg2:
            self._check_psycopg2_usage()
        
        return {
            "total_files": len(python_files),
            "import_errors": self.import_errors,
            "circular_dependencies": self.circular_dependencies,
            "psycopg2_usage": self.psycopg2_usage,
            "validation_passed": len(self.import_errors) == 0 and len(self.circular_dependencies) == 0
        }
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        
        # Directories to scan
        scan_dirs = [
            self.project_root / "agents",
            self.project_root / "core",
            self.project_root / "api",
            self.project_root / "backend",
            self.project_root / "db",
            self.project_root / "utils"
        ]
        
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                for root, dirs, files in os.walk(scan_dir):
                    # Skip __pycache__ directories
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    
                    for file in files:
                        if file.endswith(".py") and file != "__init__.py":
                            python_files.append(Path(root) / file)
        
        return python_files
    
    def _validate_file_imports(self, file_path: Path) -> None:
        """Validate imports in a single file."""
        try:
            # Read and parse the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract imports
            imports = self._extract_imports(tree)
            
            # Build import graph
            module_name = self._get_module_name(file_path)
            self.import_graph[module_name] = set()
            
            for import_name in imports:
                self.import_graph[module_name].add(import_name)
                
                # Try to resolve the import
                if not self._can_resolve_import(import_name, file_path):
                    self.import_errors.append({
                        "file": str(file_path),
                        "import": import_name,
                        "error": "Cannot resolve import",
                        "type": "import_error"
                    })
            
        except SyntaxError as e:
            self.import_errors.append({
                "file": str(file_path),
                "import": None,
                "error": f"Syntax error: {e}",
                "type": "syntax_error"
            })
        except Exception as e:
            self.import_errors.append({
                "file": str(file_path),
                "import": None,
                "error": f"Parse error: {e}",
                "type": "parse_error"
            })
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements from an AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return imports
    
    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        relative_path = file_path.relative_to(self.project_root)
        module_parts = relative_path.parts[:-1] + (relative_path.stem,)
        return ".".join(module_parts)
    
    def _can_resolve_import(self, import_name: str, file_path: Path) -> bool:
        """Check if an import can be resolved."""
        try:
            # Try to import the module
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                return True
            
            # Check if it's a relative import
            if import_name.startswith('.'):
                return True
            
            # Check if it's a local module
            if import_name.startswith(('agents.', 'core.', 'api.', 'backend.', 'db.', 'utils.')):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _detect_circular_dependencies(self) -> None:
        """Detect circular dependencies in the import graph."""
        logger.info("Detecting circular dependencies")
        
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                self.circular_dependencies.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.import_graph.get(node, set()):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])
    
    def _check_psycopg2_usage(self) -> None:
        """Check for psycopg2 usage that should be migrated to asyncpg."""
        logger.info("Checking for psycopg2 usage")
        
        python_files = self._find_python_files()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'psycopg2' in content:
                    # Find specific psycopg2 usage
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'psycopg2' in line:
                            self.psycopg2_usage.append({
                                "file": str(file_path),
                                "line": i,
                                "content": line.strip(),
                                "suggestion": "Consider migrating to asyncpg for async operations"
                            })
            
            except Exception as e:
                logger.warning(f"Could not check psycopg2 usage in {file_path}: {e}")


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate imports and detect circular dependencies")
    parser.add_argument("--check-circular", action="store_true", default=True, help="Check for circular dependencies")
    parser.add_argument("--check-psycopg2", action="store_true", default=True, help="Check for psycopg2 usage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create validator
    validator = ImportValidator()
    
    try:
        result = validator.validate_all_imports(
            check_circular=args.check_circular,
            check_psycopg2=args.check_psycopg2
        )
        
        # Print results
        print(f"\n{'='*60}")
        print(f"Import Validation Results")
        print(f"{'='*60}")
        print(f"Total files checked: {result['total_files']}")
        print(f"Import errors: {len(result['import_errors'])}")
        print(f"Circular dependencies: {len(result['circular_dependencies'])}")
        print(f"psycopg2 usage found: {len(result['psycopg2_usage'])}")
        print(f"Validation passed: {result['validation_passed']}")
        
        if result['import_errors']:
            print(f"\nImport Errors:")
            for error in result['import_errors']:
                print(f"  ❌ {error['file']}:{error.get('line', '?')} - {error['error']}")
        
        if result['circular_dependencies']:
            print(f"\nCircular Dependencies:")
            for cycle in result['circular_dependencies']:
                print(f"  🔄 {' -> '.join(cycle)}")
        
        if result['psycopg2_usage']:
            print(f"\npsycopg2 Usage (consider migrating to asyncpg):")
            for usage in result['psycopg2_usage']:
                print(f"  ⚠️  {usage['file']}:{usage['line']} - {usage['content']}")
        
        print(f"\n{'='*60}")
        
        return 0 if result['validation_passed'] else 1
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
