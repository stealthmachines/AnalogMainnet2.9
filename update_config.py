#!/usr/bin/env python3
"""
HDGL Analog Mainnet Configuration Sanitizer

This tool replaces sensitive real values in configuration files with placeholder values
to prepare the repository for safe distribution and deployment.

Usage:
    python update_config.py --sanitize
    python update_config.py --restore --backup-dir ./config_backup
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import shutil
from datetime import datetime

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

class ConfigSanitizer:
    """Handles sanitization of configuration files by replacing sensitive data with placeholders."""

    # Sensitive patterns to replace
    SENSITIVE_PATTERNS = {
        # IP addresses (but not localhost/127.0.0.1)
        r'\b(?!127\.0\.0\.1\b)(?!localhost\b)\d+\.\d+\.\d+\.\d+\b': 'YOUR_IP_ADDRESS',

        # Ethereum private keys (64 hex chars)
        r'\b[a-fA-F0-9]{64}\b': 'YOUR_PRIVATE_KEY',

        # Ethereum addresses (40 hex chars after 0x)
        r'\b0x[a-fA-F0-9]{40}\b': '0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF',

        # Enode URLs
        r'enode://[a-fA-F0-9]+@[^@]+': 'YOUR_ENODE_KEY@YOUR_IP_ADDRESS:YOUR_PORT',

        # Generic secrets and keys
        r'\b[a-fA-F0-9]{32,}\b': 'YOUR_SECRET_KEY',

        # Password patterns
        r'password["\s]*:[\s]*["\'][^"\']+["\']': 'password": "YOUR_PASSWORD"',

        # API keys
        r'api[_-]?key["\s]*:[\s]*["\'][^"\']+["\']': 'api_key": "YOUR_API_KEY"',
    }

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.backup_dir = None

    def create_backup(self, backup_dir: Optional[str] = None) -> Path:
        """Create a backup of all configuration files before modification."""
        if backup_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"config_backup_{timestamp}"

        backup_path = self.workspace_path / backup_dir
        backup_path.mkdir(exist_ok=True)

        # Find and backup config files - exclude backup directories
        config_extensions = ['.json', '.toml', '.yaml', '.yml', '.config', '.conf']

        for root, dirs, files in os.walk(self.workspace_path):
            # Skip backup directories
            dirs[:] = [d for d in dirs if not d.startswith('config_backup')]

            for file in files:
                if any(file.endswith(ext) for ext in config_extensions):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(self.workspace_path)
                    backup_file = backup_path / relative_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, backup_file)

        print(f"Created backup in: {backup_path}")
        self.backup_dir = backup_path
        return backup_path

    def sanitize_configs(self):
        """Replace sensitive data in configuration files with placeholders."""
        print("Starting configuration sanitization...")

        # Find all config files - exclude backup directories
        config_files = []
        config_extensions = ['.json', '.toml', '.yaml', '.yml', '.config', '.conf']

        for root, dirs, files in os.walk(self.workspace_path):
            # Skip backup directories
            dirs[:] = [d for d in dirs if not d.startswith('config_backup')]

            for file in files:
                if any(file.endswith(ext) for ext in config_extensions):
                    config_files.append(Path(root) / file)

        sanitized_count = 0

        for config_file in config_files:
            try:
                content = config_file.read_text()
                original_content = content

                # Apply all sensitive pattern replacements
                for pattern, replacement in self.SENSITIVE_PATTERNS.items():
                    content = re.sub(pattern, replacement, content)

                # Special handling for known sensitive files
                if 'config.toml' in str(config_file):
                    content = self._sanitize_toml_config(content)
                elif 'config.json' in str(config_file):
                    content = self._sanitize_json_config(content)

                # Write back if changed
                if content != original_content:
                    config_file.write_text(content)
                    print(f"Sanitized: {config_file.relative_to(self.workspace_path)}")
                    sanitized_count += 1

            except Exception as e:
                print(f"Error processing {config_file}: {e}")

        print(f"Sanitization complete. Processed {len(config_files)} files, sanitized {sanitized_count} files.")

    def _sanitize_toml_config(self, content: str) -> str:
        """Special handling for TOML configuration files."""
        # Handle BootstrapNodes, StaticNodes, TrustedNodes arrays
        node_patterns = [
            (r'BootstrapNodes\s*=\s*\[([^\]]*)\]', 'BootstrapNodes'),
            (r'StaticNodes\s*=\s*\[([^\]]*)\]', 'StaticNodes'),
            (r'TrustedNodes\s*=\s*\[([^\]]*)\]', 'TrustedNodes')
        ]

        for pattern, node_type in node_patterns:
            def replace_nodes(match):
                nodes_content = match.group(1)
                # Replace enode URLs in the array
                sanitized_nodes = re.sub(
                    r'enode://[a-fA-F0-9]+@[^@]+',
                    'YOUR_ENODE_KEY@YOUR_IP_ADDRESS:YOUR_PORT',
                    nodes_content
                )
                return f'{node_type} = [{sanitized_nodes}]'

            content = re.sub(pattern, replace_nodes, content, flags=re.DOTALL)

        return content

    def _sanitize_json_config(self, content: str) -> str:
        """Special handling for JSON configuration files."""
        try:
            # Try to parse as JSON and sanitize specific fields
            config_data = json.loads(content)

            # Sanitize known sensitive fields
            sensitive_fields = [
                'eth_private_key', 'private_key', 'password', 'secret',
                'api_key', 'jwt_secret', 'database_url', 'connection_string'
            ]

            def sanitize_dict(data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key.lower() in sensitive_fields:
                            if isinstance(value, str) and len(value) > 10:
                                data[key] = f"YOUR_{key.upper()}"
                        else:
                            sanitize_dict(value)
                elif isinstance(data, list):
                    for item in data:
                        sanitize_dict(item)

            sanitize_dict(config_data)
            return json.dumps(config_data, indent=2)

        except json.JSONDecodeError:
            # If not valid JSON, return as-is
            return content

    def restore_backup(self, backup_dir: str):
        """Restore configuration files from backup."""
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            print(f"Backup directory not found: {backup_path}")
            return

        restored_count = 0

        # Restore all files from backup
        for backup_file in backup_path.rglob('*'):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(backup_path)
                target_file = self.workspace_path / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, target_file)
                restored_count += 1

        print(f"Restored {restored_count} files from backup.")

def main():
    parser = argparse.ArgumentParser(description='HDGL Analog Mainnet Configuration Sanitizer')
    parser.add_argument('--sanitize', action='store_true',
                       help='Replace sensitive data with placeholders')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup before sanitization')
    parser.add_argument('--backup-dir', type=str,
                       help='Specify backup directory name')
    parser.add_argument('--restore', type=str,
                       help='Restore from specified backup directory')

    args = parser.parse_args()

    # Get workspace path
    workspace_path = os.getcwd()

    # Initialize sanitizer
    sanitizer = ConfigSanitizer(workspace_path)

    if args.restore:
        sanitizer.restore_backup(args.restore)

    elif args.sanitize:
        if args.backup or args.backup_dir:
            backup_dir = args.backup_dir or "config_backup"
            sanitizer.create_backup(backup_dir)

        sanitizer.sanitize_configs()

    else:
        parser.print_help()

if __name__ == '__main__':
    main()