#!/usr/bin/env python3
"""
validate_docs.py - Documentation contract validation tool

Validates that documentation follows the adjacent-first contract system:
- Checks initiative file completeness
- Validates adjacency freshness
- Ensures token budget compliance
- Verifies readiness gate criteria

Usage:
    python tools/validate_docs.py [initiative_serial]
    python tools/validate_docs.py 001  # Validate specific initiative
    python tools/validate_docs.py      # Validate all initiatives
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DocsValidator:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.docs_dir = self.repo_root / "docs"
        self.meta_dir = self.docs_dir / "meta"
        self.initiatives_dir = self.docs_dir / "initiatives"
        self.knowledge_dir = self.docs_dir / "knowledge"
        
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")
        
    def log_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def log_info(self, message: str):
        self.info.append(f"ℹ️  INFO: {message}")

    def validate_structure(self) -> bool:
        """Validate basic directory structure exists."""
        required_dirs = [
            self.docs_dir,
            self.initiatives_dir,
            self.knowledge_dir,
            self.docs_dir / "summaries" / "rollups",
            self.meta_dir,
        ]
        
        required_files = [
            self.docs_dir / "README.md",
            self.docs_dir / "DOCS_POLICY.md",
            self.docs_dir / "DOCS_READINESS_CHECKLIST.md",
            self.knowledge_dir / "ADJACENT_INDEX.md",
            self.meta_dir / "adjacency.json",
            self.meta_dir / "search_config.json",
            self.meta_dir / "CLAUDE_CODE_SYSTEM_PROMPT.md",
        ]
        
        all_good = True
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                self.log_error(f"Missing directory: {dir_path.relative_to(self.repo_root)}")
                all_good = False
                
        for file_path in required_files:
            if not file_path.exists():
                self.log_error(f"Missing file: {file_path.relative_to(self.repo_root)}")
                all_good = False
                
        if all_good:
            self.log_info("Documentation structure validation passed")
            
        return all_good

    def load_adjacency_json(self) -> Optional[Dict]:
        """Load and validate adjacency.json."""
        adjacency_file = self.meta_dir / "adjacency.json"
        
        if not adjacency_file.exists():
            self.log_error("Missing adjacency.json file")
            return None
            
        try:
            with open(adjacency_file) as f:
                data = json.load(f)
                
            # Validate structure
            if "components" not in data:
                self.log_error("adjacency.json missing 'components' key")
                return None
                
            return data
            
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in adjacency.json: {e}")
            return None

    def validate_initiative_files(self, serial: str) -> bool:
        """Validate that all required files exist for an initiative."""
        required_files = [
            f"CONTEXT{serial}.md",
            f"PRD{serial}.md", 
            f"RFC{serial}.md",
            f"TODO{serial}.md",
        ]
        
        missing_files = []
        for filename in required_files:
            filepath = self.initiatives_dir / filename
            if not filepath.exists():
                missing_files.append(filename)
                
        if missing_files:
            self.log_error(f"Initiative {serial} missing files: {', '.join(missing_files)}")
            return False
            
        return True

    def validate_context_file(self, serial: str, adjacency_data: Dict) -> Tuple[bool, List[str]]:
        """Validate CONTEXT file and extract adjacent components."""
        context_file = self.initiatives_dir / f"CONTEXT{serial}.md"
        
        if not context_file.exists():
            self.log_error(f"Missing CONTEXT{serial}.md")
            return False, []
            
        try:
            with open(context_file) as f:
                content = f.read()
        except Exception as e:
            self.log_error(f"Cannot read CONTEXT{serial}.md: {e}")
            return False, []
            
        # Check for isolation flag
        if "Isolation: true" in content:
            self.log_info(f"Initiative {serial} marked as isolated - skipping adjacency checks")
            return True, []
            
        # Extract adjacent components mentioned
        adjacent_components = []
        for line in content.split('\n'):
            if '/summaries/rollups/' in line and '_rollup.md' in line:
                # Extract component name from rollup link
                import re
                match = re.search(r'/summaries/rollups/(\w+)_rollup\.md', line)
                if match:
                    adjacent_components.append(match.group(1))
                    
        if len(adjacent_components) < 3:
            self.log_warning(f"Initiative {serial} lists {len(adjacent_components)} adjacent components (recommended: 3-7)")
        elif len(adjacent_components) > 7:
            self.log_warning(f"Initiative {serial} lists {len(adjacent_components)} adjacent components (recommended: 3-7)")
        else:
            self.log_info(f"Initiative {serial} lists {len(adjacent_components)} adjacent components")
            
        # Check if token budget is mentioned
        if "20k tokens" not in content and "20000" not in content:
            self.log_warning(f"Initiative {serial} doesn't mention token budget")
            
        return True, adjacent_components

    def validate_adjacent_index(self, components: List[str]) -> bool:
        """Validate that adjacent components appear in ADJACENT_INDEX.md."""
        index_file = self.knowledge_dir / "ADJACENT_INDEX.md"
        
        if not index_file.exists():
            self.log_error("Missing ADJACENT_INDEX.md")
            return False
            
        try:
            with open(index_file) as f:
                content = f.read()
        except Exception as e:
            self.log_error(f"Cannot read ADJACENT_INDEX.md: {e}")
            return False
            
        missing_components = []
        stale_components = []
        
        for component in components:
            if component not in content:
                missing_components.append(component)
            else:
                # Check for date freshness (basic check for YYYY-MM-DD pattern)
                import re
                # Look for the component line and extract date
                for line in content.split('\n'):
                    if component in line and '|' in line:
                        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', line)
                        if date_match:
                            try:
                                component_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                days_old = (datetime.now() - component_date).days
                                if days_old > 90:
                                    stale_components.append(f"{component} ({days_old} days old)")
                                elif days_old > 60:
                                    self.log_warning(f"Component {component} is {days_old} days old (consider refresh)")
                            except ValueError:
                                pass
                        break
                        
        if missing_components:
            self.log_error(f"Components missing from ADJACENT_INDEX.md: {', '.join(missing_components)}")
            
        if stale_components:
            self.log_warning(f"Stale components (>90 days): {', '.join(stale_components)}")
            
        return len(missing_components) == 0

    def validate_rfc_interfaces(self, serial: str) -> bool:
        """Validate that RFC includes verbatim interface contracts."""
        rfc_file = self.initiatives_dir / f"RFC{serial}.md"
        
        if not rfc_file.exists():
            return True  # RFC validation is only relevant if file exists
            
        try:
            with open(rfc_file) as f:
                content = f.read()
        except Exception as e:
            self.log_error(f"Cannot read RFC{serial}.md: {e}")
            return False
            
        if "Interface Contracts" not in content:
            self.log_warning(f"RFC{serial}.md should include 'Interface Contracts' section")
            return False
            
        # Check for code blocks (basic check for verbatim interfaces)
        if "```" not in content:
            self.log_warning(f"RFC{serial}.md should include code blocks with verbatim interfaces")
            
        return True

    def validate_todo_phase0(self, serial: str) -> bool:
        """Validate that TODO includes Phase 0 context harvest."""
        todo_file = self.initiatives_dir / f"TODO{serial}.md"
        
        if not todo_file.exists():
            return True  # TODO validation is only relevant if file exists
            
        try:
            with open(todo_file) as f:
                content = f.read()
        except Exception as e:
            self.log_error(f"Cannot read TODO{serial}.md: {e}")
            return False
            
        if "Phase 0" not in content or "Context Harvest" not in content:
            self.log_error(f"TODO{serial}.md must include 'Phase 0 — Context Harvest'")
            return False
            
        return True

    def validate_initiative(self, serial: str, adjacency_data: Dict) -> bool:
        """Validate a complete initiative."""
        self.log_info(f"Validating initiative {serial}")
        
        # Check all required files exist
        if not self.validate_initiative_files(serial):
            return False
            
        # Validate CONTEXT file and get adjacent components
        context_ok, adjacent_components = self.validate_context_file(serial, adjacency_data)
        if not context_ok:
            return False
            
        # Skip further adjacency checks if isolated
        if not adjacent_components:  # Empty list indicates isolation
            return True
            
        # Validate adjacent components are in index
        index_ok = self.validate_adjacent_index(adjacent_components)
        
        # Validate RFC has interface contracts
        rfc_ok = self.validate_rfc_interfaces(serial)
        
        # Validate TODO has Phase 0
        todo_ok = self.validate_todo_phase0(serial)
        
        return all([context_ok, index_ok, rfc_ok, todo_ok])

    def find_initiatives(self) -> List[str]:
        """Find all initiative serials in the initiatives directory."""
        if not self.initiatives_dir.exists():
            return []
            
        serials = set()
        for file_path in self.initiatives_dir.glob("*.md"):
            filename = file_path.name
            # Extract serial from files like CONTEXT001.md, PRD042.md, etc.
            import re
            match = re.match(r'(CONTEXT|PRD|RFC|TODO)(\d{3})\.md', filename)
            if match:
                serials.add(match.group(2))
                
        return sorted(list(serials))

    def validate_all(self, specific_serial: Optional[str] = None) -> bool:
        """Run complete validation."""
        print("🔍 Documentation Contract Validation")
        print("=" * 50)
        
        # Validate basic structure
        if not self.validate_structure():
            self.print_results()
            return False
            
        # Load adjacency data
        adjacency_data = self.load_adjacency_json()
        if not adjacency_data:
            self.print_results()
            return False
            
        # Find initiatives to validate
        if specific_serial:
            initiatives = [specific_serial] if specific_serial else []
        else:
            initiatives = self.find_initiatives()
            
        if not initiatives:
            self.log_info("No initiatives found to validate")
            self.print_results()
            return True
            
        # Validate each initiative
        all_valid = True
        for serial in initiatives:
            if not self.validate_initiative(serial, adjacency_data):
                all_valid = False
                
        self.print_results()
        return all_valid

    def print_results(self):
        """Print validation results."""
        print()
        
        if self.errors:
            print("🚨 ERRORS:")
            for error in self.errors:
                print(f"   {error}")
            print()
            
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
            
        if self.info:
            print("ℹ️  INFO:")
            for info in self.info:
                print(f"   {info}")
            print()
            
        if not self.errors:
            print("✅ Documentation contract validation PASSED")
        else:
            print("❌ Documentation contract validation FAILED")
            print("\nReview docs/DOCS_READINESS_CHECKLIST.md for requirements.")


def main():
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Parse command line arguments
    specific_serial = None
    if len(sys.argv) > 1:
        specific_serial = sys.argv[1]
        if not specific_serial.isdigit() or len(specific_serial) != 3:
            print("Error: Serial must be a 3-digit number (e.g., 001)")
            sys.exit(1)
    
    validator = DocsValidator(str(repo_root))
    success = validator.validate_all(specific_serial)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()