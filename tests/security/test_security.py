import pytest
import os
import json
import re
from typing import List, Dict
import ast
from pathlib import Path

class SecurityTester:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.security_issues = []
        
        # Common security patterns to check
        self.patterns = {
            'api_key': r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)',
            'password': r'(?i)(password|passwd|pwd)',
            'hardcoded_credentials': r'(?i)(username|user[_-]?id|email)[\s]*=[\s]*[\'"][^\'"]+[\'"]',
            'unsafe_eval': r'eval\s*\(',
            'unsafe_exec': r'exec\s*\(',
            'shell_injection': r'(?i)(os\.system|subprocess\.call|subprocess\.Popen)',
            'sql_injection': r'(?i)(SELECT|INSERT|UPDATE|DELETE).*\+.*',
            'xss': r'(?i)(<script|javascript:)',
            'file_path_traversal': r'(?i)(\.\.\/|\.\.\\|~\/)',
        }

    def check_file(self, file_path: Path) -> List[Dict]:
        """Check a single file for security issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip binary files
            if '\0' in content:
                return issues
                
            # Check for security patterns
            for pattern_name, pattern in self.patterns.items():
                matches = re.finditer(pattern, content)
                for match in matches:
                    issues.append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': content[:match.start()].count('\n') + 1,
                        'pattern': pattern_name,
                        'match': match.group(),
                        'context': content[max(0, match.start()-20):min(len(content), match.end()+20)]
                    })
            
            # Check for Python-specific issues
            if file_path.suffix == '.py':
                try:
                    tree = ast.parse(content)
                    issues.extend(self._check_python_ast(tree, file_path))
                except SyntaxError:
                    pass
                    
        except Exception as e:
            issues.append({
                'file': str(file_path.relative_to(self.root_dir)),
                'error': f'Error checking file: {str(e)}'
            })
            
        return issues

    def _check_python_ast(self, tree: ast.AST, file_path: Path) -> List[Dict]:
        """Check Python AST for security issues."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for unsafe imports
            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name in ['pickle', 'marshal']:
                        issues.append({
                            'file': str(file_path.relative_to(self.root_dir)),
                            'line': node.lineno,
                            'pattern': 'unsafe_import',
                            'match': f'import {name.name}',
                            'context': f'Unsafe import: {name.name}'
                        })
            
            # Check for unsafe function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        issues.append({
                            'file': str(file_path.relative_to(self.root_dir)),
                            'line': node.lineno,
                            'pattern': 'unsafe_call',
                            'match': f'{node.func.id}()',
                            'context': f'Unsafe function call: {node.func.id}'
                        })
        
        return issues

    def scan_project(self) -> List[Dict]:
        """Scan the entire project for security issues."""
        all_issues = []
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.md')):
                    file_path = Path(root) / file
                    issues = self.check_file(file_path)
                    all_issues.extend(issues)
        
        return all_issues

def test_security_scan():
    """Run security scan and assert no critical issues found."""
    tester = SecurityTester()
    issues = tester.scan_project()
    
    # Filter out non-critical issues
    critical_issues = [
        issue for issue in issues 
        if issue.get('pattern') in ['api_key', 'password', 'hardcoded_credentials', 'unsafe_eval', 'unsafe_exec']
    ]
    
    if critical_issues:
        print("\nCritical Security Issues Found:")
        for issue in critical_issues:
            print(f"\nFile: {issue['file']}")
            print(f"Line: {issue.get('line', 'N/A')}")
            print(f"Pattern: {issue['pattern']}")
            print(f"Match: {issue['match']}")
            print(f"Context: {issue.get('context', 'N/A')}")
    
    assert not critical_issues, "Critical security issues found in the codebase"

def test_no_hardcoded_credentials():
    """Test that no hardcoded credentials are present."""
    tester = SecurityTester()
    issues = tester.scan_project()
    
    credential_issues = [
        issue for issue in issues 
        if issue.get('pattern') in ['api_key', 'password', 'hardcoded_credentials']
    ]
    
    assert not credential_issues, "Hardcoded credentials found in the codebase"

def test_no_unsafe_eval():
    """Test that no unsafe eval or exec calls are present."""
    tester = SecurityTester()
    issues = tester.scan_project()
    
    unsafe_calls = [
        issue for issue in issues 
        if issue.get('pattern') in ['unsafe_eval', 'unsafe_exec']
    ]
    
    assert not unsafe_calls, "Unsafe eval or exec calls found in the codebase" 