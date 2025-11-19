# HDGL Analog Mainnet Deployment Tools

This repository now includes deployment tools that allow users to populate configuration placeholders during deployment, ensuring sensitive data is not committed to version control.

## Quick Start

1. **Sanitize the repository** (replace real values with placeholders):
   ```bash
   python update_config.py --sanitize --backup
   ```

2. **Configure for deployment** (interactive setup):
   ```bash
   python deploy_config.py --interactive
   ```

3. **Deploy your services**:
   ```bash
   ./start.ps1 -mode all -build
   ```

## Available Tools

### deploy_config.py - Deployment Configuration Tool

**Interactive Configuration:**
```bash
python deploy_config.py --interactive
```
- Scans all configuration files for placeholders
- Prompts user for actual values
- Updates all config files automatically

**Scan Only Mode:**
```bash
python deploy_config.py --scan-only
```
- Shows all placeholders found without modifying files

**Create Template:**
```bash
python deploy_config.py --template my-deployment-config.json
```
- Creates a configuration template file

### update_config.py - Configuration Sanitizer

**Sanitize Repository:**
```bash
python update_config.py --sanitize --backup
```
- Replaces sensitive data (IP addresses, private keys, etc.) with placeholders
- Creates automatic backup before changes

**Restore from Backup:**
```bash
python update_config.py --restore config_backup_20241201_120000
```
- Restores configuration files from a backup directory

## Placeholder Patterns

The tools recognize these placeholder patterns:

- `YOUR_IP_ADDRESS` - Server IP addresses
- `YOUR_PRIVATE_KEY` - Ethereum private keys
- `0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF` - Ethereum contract addresses
- `YOUR_RPC_URL` - Ethereum RPC endpoints
- `YOUR_ENDPOINT` - IPFS API endpoints
- `YOUR_ENODE_KEY@YOUR_IP_ADDRESS:YOUR_PORT` - Ethereum node enodes

## Configuration Files

The tools automatically scan and update these file types:
- `*.json` - JSON configuration files
- `*.toml` - TOML configuration files
- `*.yaml` / `*.yml` - YAML configuration files
- `*.config` / `*.conf` - Generic config files

## Security Best Practices

1. **Always backup before sanitizing:**
   ```bash
   python update_config.py --sanitize --backup
   ```

2. **Never commit real sensitive data** to version control

3. **Use environment variables** for runtime secrets when possible

4. **Test configuration** after population:
   ```bash
   python deploy_config.py --scan-only
   ```

## Deployment Workflow

### For New Deployments:

1. Clone the repository
2. Sanitize if needed: `python update_config.py --sanitize --backup`
3. Configure interactively: `python deploy_config.py --interactive`
4. Build and deploy: `./start.ps1 -mode all -build`

### For Existing Deployments:

1. Pull latest changes
2. Check for new placeholders: `python deploy_config.py --scan-only`
3. Update configuration: `python deploy_config.py --interactive`
4. Redeploy services

## Troubleshooting

**Tool not found error:**
- Ensure Python 3.6+ is installed
- Install dependencies: `pip install -r requirements.txt`

**Permission denied:**
- Run with appropriate permissions or use `sudo` if needed

**No placeholders found:**
- Check that configuration files exist and contain placeholder patterns
- Use `--scan-only` to see what was detected

**Backup not created:**
- Ensure write permissions in the workspace directory
- Check available disk space

## Advanced Usage

### Custom Placeholder Patterns

Edit the `PLACEHOLDER_PATTERNS` in `deploy_config.py` to add custom patterns:

```python
CUSTOM_PATTERNS = [
    r'MY_CUSTOM_[A-Z_]+',  # MY_CUSTOM_VALUE
    r'PLACEHOLDER_[A-Z_]+', # PLACEHOLDER_VALUE
]
```

### Environment Variable Integration

The tools can be extended to read from environment variables:

```bash
export HDGL_IP_ADDRESS="192.168.1.100"
export HDGL_PRIVATE_KEY="your_private_key_here"
python deploy_config.py --interactive
```

## Support

For issues with deployment tools:
1. Check the troubleshooting section above
2. Run with verbose output if available
3. Check the backup directory for original files
4. Review the generated logs for error details