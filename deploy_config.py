#!/usr/bin/env python3
"""
HDGL Analog Mainnet Deployment Configuration Tool

This tool allows users to populate configuration placeholders during deployment.
It supports multiple configuration formats (JSON, TOML) and provides interactive
prompts for sensitive values like IP addresses, private keys, and contract addresses.

Usage:
    python deploy_config.py --interactive
    python deploy_config.py --template deployment-config.template.json
    python deploy_config.py --restore-placeholders
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
import shutil

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

class DeploymentConfig:
    """Handles deployment configuration with placeholder population."""

    # Placeholder patterns to look for
    PLACEHOLDER_PATTERNS = [
        r'YOUR_[A-Z_]+',           # YOUR_IP_ADDRESS, YOUR_PRIVATE_KEY, etc.
        r'0x[A-F0-9]{8,}',         # Ethereum addresses (but only if they match known patterns)
        r'\d+\.\d+\.\d+\.\d+',     # IP addresses
        r'enode://[a-f0-9]+@',     # enode keys
    ]

    # Known dummy/placeholder values
    DUMMY_VALUES = {
        'ip_address': 'YOUR_IP_ADDRESS',
        'private_key': 'YOUR_PRIVATE_KEY',
        'contract_address': '0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF',
        'enode_key': 'YOUR_ENODE_KEY',
        'port': 'YOUR_PORT',
        'rpc_url': 'YOUR_RPC_URL',
        'endpoint': 'YOUR_ENDPOINT'
    }

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.config_files = self._find_config_files()
        self.placeholders_found = {}

    def _find_config_files(self) -> List[Path]:
        """Find all configuration files that might contain placeholders."""
        config_files = []

        # Common config file patterns
        patterns = [
            '**/*.json',
            '**/*.toml',
            '**/*.yaml',
            '**/*.yml',
            '**/*.config',
            '**/*.conf'
        ]

        for pattern in patterns:
            config_files.extend(self.workspace_path.glob(pattern))

        return config_files

    def scan_for_placeholders(self) -> Dict[str, List[str]]:
        """Scan all config files for placeholder patterns."""
        placeholders = {}

        for config_file in self.config_files:
            try:
                content = config_file.read_text()
                file_placeholders = []

                # Look for our known dummy values first
                for dummy_value in self.DUMMY_VALUES.values():
                    if dummy_value in content:
                        if dummy_value not in file_placeholders:
                            file_placeholders.append(dummy_value)

                # Then look for pattern matches
                for pattern in self.PLACEHOLDER_PATTERNS:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match not in file_placeholders:
                            file_placeholders.append(match)

                if file_placeholders:
                    placeholders[str(config_file.relative_to(self.workspace_path))] = file_placeholders

            except Exception as e:
                print(f"Warning: Could not read {config_file}: {e}")

        self.placeholders_found = placeholders
        return placeholders

    def interactive_config(self):
        """Run interactive configuration setup."""
        print("HDGL Analog Mainnet Deployment Configuration")
        print("=" * 50)

        # Scan for placeholders first
        placeholders = self.scan_for_placeholders()

        if not placeholders:
            print("No placeholders found in configuration files.")
            return

        print(f"Found placeholders in {len(placeholders)} files:")
        for file_path, file_placeholders in placeholders.items():
            print(f"\n{file_path}:")
            for placeholder in file_placeholders:
                print(f"  - {placeholder}")

        # Collect user inputs
        user_config = {}

        print("\n" + "=" * 50)
        print("Please provide the following configuration values:")
        print("(Press Enter to keep current values or use defaults)")
        print("=" * 50)

        # Common configuration prompts
        prompts = {
            'YOUR_IP_ADDRESS': {
                'prompt': 'Enter your server IP address',
                'default': '127.0.0.1',
                'description': 'IP address where the services will be accessible'
            },
            'YOUR_PRIVATE_KEY': {
                'prompt': 'Enter your Ethereum private key (without 0x prefix)',
                'default': '',
                'description': 'Private key for Ethereum transactions (keep secure!)'
            },
            '0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF': {
                'prompt': 'Enter your HDGL contract address',
                'default': '0x0000000000000000000000000000000000000000',
                'description': 'Deployed HDGL contract address on Ethereum'
            },
            'YOUR_RPC_URL': {
                'prompt': 'Enter your Ethereum RPC URL',
                'default': 'http://localhost:8545',
                'description': 'Ethereum node RPC endpoint'
            },
            'YOUR_ENDPOINT': {
                'prompt': 'Enter your IPFS endpoint',
                'default': 'http://localhost:5001',
                'description': 'IPFS node API endpoint'
            }
        }

        for placeholder_key, config in prompts.items():
            if any(placeholder_key in ph_list for ph_list in placeholders.values()):
                print(f"\n{config['description']}:")
                value = input(f"{config['prompt']} [{config['default']}]: ").strip()
                if not value:
                    value = config['default']
                user_config[placeholder_key] = value

        # Handle enode keys if found
        enode_placeholders = []
        for file_placeholders in placeholders.values():
            enode_placeholders.extend([p for p in file_placeholders if p.startswith('enode://')])

        if enode_placeholders:
            print("\nFound enode keys that need to be configured:")
            for enode in set(enode_placeholders):
                print(f"  - {enode}")
            print("\nNote: Enode keys are typically auto-generated by Geth nodes.")
            print("You can leave these as-is if you're setting up a new network.")

        # Apply configuration
        self.apply_configuration(user_config)

        print("\nConfiguration completed!")
        print("You can now run your deployment with the populated values.")

    def apply_configuration(self, user_config: Dict[str, str]):
        """Apply user configuration to all config files."""
        for config_file in self.config_files:
            try:
                content = config_file.read_text()

                # Apply each configuration replacement
                for placeholder, value in user_config.items():
                    if placeholder in content:
                        content = content.replace(placeholder, value)

                # Write back the modified content
                config_file.write_text(content)
                print(f"Updated {config_file.relative_to(self.workspace_path)}")

            except Exception as e:
                print(f"Error updating {config_file}: {e}")

    def create_template(self, template_path: str):
        """Create a deployment configuration template."""
        template = {
            "deployment_config": {
                "description": "HDGL Analog Mainnet Deployment Configuration Template",
                "version": "1.0",
                "placeholders": {
                    "network": {
                        "ip_address": "YOUR_IP_ADDRESS",
                        "rpc_url": "YOUR_RPC_URL",
                        "ipfs_endpoint": "YOUR_ENDPOINT"
                    },
                    "ethereum": {
                        "private_key": "YOUR_PRIVATE_KEY",
                        "contract_address": "0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF"
                    },
                    "security": {
                        "admin_password": "YOUR_ADMIN_PASSWORD",
                        "jwt_secret": "YOUR_JWT_SECRET"
                    }
                }
            }
        }

        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"Created deployment template: {template_path}")

    def restore_placeholders(self):
        """Restore all configuration files to use placeholder values."""
        # This would need a backup of original values or known mappings
        print("Restoring placeholders...")
        print("Note: This feature requires a backup of original values.")
        print("For now, please use the interactive configuration to set new values.")

def main():
    parser = argparse.ArgumentParser(description='HDGL Analog Mainnet Deployment Configuration Tool')
    parser.add_argument('--interactive', action='store_true',
                       help='Run interactive configuration setup')
    parser.add_argument('--template', type=str,
                       help='Create a deployment configuration template')
    parser.add_argument('--restore-placeholders', action='store_true',
                       help='Restore configuration files to use placeholders')
    parser.add_argument('--scan-only', action='store_true',
                       help='Only scan for placeholders without modifying files')

    args = parser.parse_args()

    # Get workspace path
    workspace_path = os.getcwd()

    # Initialize deployment config
    deploy_config = DeploymentConfig(workspace_path)

    if args.scan_only:
        placeholders = deploy_config.scan_for_placeholders()
        if placeholders:
            print("Found placeholders:")
            for file_path, file_placeholders in placeholders.items():
                print(f"\n{file_path}:")
                for placeholder in file_placeholders:
                    print(f"  - {placeholder}")
        else:
            print("No placeholders found.")

    elif args.template:
        deploy_config.create_template(args.template)

    elif args.restore_placeholders:
        deploy_config.restore_placeholders()

    elif args.interactive:
        deploy_config.interactive_config()

    else:
        parser.print_help()

if __name__ == '__main__':
    main()