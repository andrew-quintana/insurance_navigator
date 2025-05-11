import os
import re
import json
import argparse
from pathlib import Path

# Define security patterns
patterns = {
    'api_key': r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)',
    'password': r'(?i)(password|passwd|pwd)',
    'hardcoded_credentials': r'(?i)(username|user[_-]?id|email)[\s]*=[\s]*[\'"][^\'"]+[\'"]',
    'unsafe_eval': r'eval\s*\(',
    'unsafe_exec': r'exec\s*\(',
    'weak_encryption': r'(?i)(\bmd5\b|\bsha1\b|\bdes\b|\brc4\b)\s*\(',
}

# Function to scan a file for security issues
def scan_file(file_path):
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                issues.append({
                    'file': str(file_path),
                    'line': content[:match.start()].count('\n') + 1,
                    'pattern': pattern_name,
                    'match': match.group(),
                })
    except Exception as e:
        issues.append({'file': str(file_path), 'error': str(e)})
    return issues

# Function to scan a directory for security issues
def scan_directory(path):
    all_issues = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                issues = scan_file(file_path)
                all_issues.extend(issues)
    return all_issues

# Main function to parse arguments and run the scan
def main():
    parser = argparse.ArgumentParser(description='Security Scan Tool')
    parser.add_argument('--path', type=str, default='.', help='Path to scan')
    parser.add_argument('--output', type=str, help='Output file for JSON report')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    args = parser.parse_args()

    issues = scan_directory(args.path)

    if args.verbose:
        for issue in issues:
            print(f"File: {issue['file']}, Line: {issue.get('line', 'N/A')}, Pattern: {issue['pattern']}, Match: {issue['match']}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(issues, f, indent=4)

    print(f"Scan completed. {len(issues)} issues found.")

if __name__ == '__main__':
    main() 