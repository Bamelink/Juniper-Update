# Juniper Software Upgrade Automation

A streamlined Ansible + Python solution for safe, automated Juniper device upgrades with comprehensive pre/post-upgrade validation.

## Features

- **Smart Upgrade Path Computation**: Automatically calculates safe upgrade paths following Juniper's recommended strategy
  - Example: `21.3 → 23.4` becomes `[21.4, 22.4, 23.4]`
- **Per-Device Version Detection**: Fetches current version directly from each device
- **Direct FTP Access**: Devices fetch software images directly from FTP server (not via Ansible controller)
- **Virtual Chassis Support**: Handles both standalone devices (EX2300, EX4100, SRX345) and virtual chassis (EX4400, EX4300)
- **Pre/Post Validation**: Captures interface status, LLDP neighbors, and dot1x statistics
- **Color-Coded Results**: Visual status reporting
  - 🟢 **GREEN**: Post-checks match pre-checks exactly
  - 🟡 **YELLOW**: Changes detected but upgrade succeeded
  - 🔴 **RED**: Upgrade failed or validation errors

## Project Structure

```
.
├── lib/
│   ├── upgrade_path.py        # Compute safe upgrade paths
│   └── report_generator.py    # Color-coded comparison reports
├── tests/
│   └── test_upgrade_path.py   # Unit tests
├── ansible/
│   ├── playbook.yml           # Main orchestration playbook
│   ├── inventory_template.ini # Device inventory template
│   ├── group_vars/
│   │   └── all/
│   │       └── vault.yml      # Encrypted FTP credentials (vault)
│   └── roles/
│       ├── juniper_checks/    # Pre/post-check tasks
│       └── juniper_upgrade/   # Upgrade execution tasks
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Vault with FTP Credentials

Create and encrypt the vault file:

```bash
ansible-vault create ansible/group_vars/all/vault.yml
```

Add your FTP credentials:

```yaml
ftp_user: "your_ftp_service_account"
ftp_password: "your_ftp_password"
```

### 3. Create Inventory

Copy and customize the template:

```bash
cp ansible/inventory_template.ini ansible/inventory.ini
```

Edit `ansible/inventory.ini` with your devices. **Important**: Specify the device model so the correct package naming is used:

```ini
[juniper_devices]
ex2300-01 ansible_host=192.168.1.10 target_version=23.4 device_model=ex2300
srx345-01 ansible_host=192.168.1.11 target_version=23.4 device_model=srx345
ex4400-vc-01 ansible_host=192.168.2.10 target_version=23.4 device_model=ex4400

[juniper_devices:vars]
upgrade_timeout_minutes=10
```

### 4. Run Upgrade Playbook

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --ask-vault-pass
```

Or specify a subset of devices:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --ask-vault-pass \
  -l ex2300-01
```

### 5. View Results

After the playbook completes, check the color-coded report in the playbook output. A JSON report is also saved to `/tmp/upgrade_checks_*.json`.

## Testing

Run the upgrade path unit tests:

```bash
pytest -v tests/test_upgrade_path.py
```

Test specific upgrade paths:

```bash
python3 lib/upgrade_path.py --current 21.3 --target 23.4
python3 lib/upgrade_path.py --current 21.3 --target 23.4 --format json
```

## Upgrade Path Logic

The algorithm follows Juniper's recommended strategy:

1. **Move to .4 train**: If on 21.3, upgrade to 21.4 first
2. **Advance majors on .4**: Move through 22.4, then 23.4, etc.
3. **Reach target**: Finally upgrade to exact target minor (if not .4)

Examples:
- `21.3 → 23.4`: `[21.4, 22.4, 23.4]`
- `21.4 → 23.4`: `[22.4, 23.4]`
- `20.1 → 23.2`: `[20.4, 21.4, 22.4, 23.2]`

## Device Type Handling

### Supported Devices

The role automatically detects the device model and uses the correct package naming:

| Device Model | Package Pattern |
|---|---|
| **SRX345** | `junos-srxme-VERSION.tgz` |
| **EX2300** | `junos-arm-VERSION.tgz` |
| **EX4100** | `junos-install-ex-arm-64-VERSION.tgz` |
| **EX4300** | `jinstall-ex-4300-VERSION.tgz` |
| **EX4400** | `junos-install-ex-x86-64-VERSION.tgz` |

### Standalone Devices
- **EX2300, EX4100**: Standard single-member upgrade
- **SRX345**: Standard single-member upgrade

### Virtual Chassis
- **EX4400, EX4300**: The role handles virtual-chassis detection
  - Coordinates upgrades across members (if needed)
  - Verifies chassis consistency post-upgrade

## Pre/Post-Check Details

### Interfaces
Captures `show interfaces terse` output to verify:
- All interfaces remain up
- No unexpected state changes
- Bandwidth/MTU consistency

### LLDP Neighbors
Captures `show lldp neighbors` to verify:
- Neighbor discovery unchanged
- Physical connectivity preserved

### dot1x
Captures `show dot1x statistics` to verify:
- Authentication state unchanged
- No new supplicant failures

## Vault Management

### Encrypt Vault File

```bash
ansible-vault encrypt ansible/group_vars/all/vault.yml
```

### Edit Vault File

```bash
ansible-vault edit ansible/group_vars/all/vault.yml
```

### View Vault File (encrypted)

```bash
ansible-vault view ansible/group_vars/all/vault.yml
```

## Playbook Tags

Run only specific stages:

```bash
# Pre-checks only
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --ask-vault-pass -t precheck

# Upgrade only (skip pre/post checks)
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --ask-vault-pass -t upgrade

# Post-checks and reporting only
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --ask-vault-pass -t postcheck
```

## Interpreting Results

### Green (✓ PASS)
All post-upgrade checks match pre-upgrade snapshots. The upgrade is clean.

### Yellow (⚠ WARN)
Some metrics changed (e.g., neighbor count, interface status), but the upgrade succeeded. Review the differences to ensure they are expected (e.g., interface resets during boot).

### Red (✗ FAIL)
Upgrade failed or validation detected errors. Check device logs and error messages.

## Troubleshooting

### Device Unreachable After Upgrade
- Wait longer for the device to boot (adjust `wait_for_connection` timeout)
- Check network connectivity and device console logs
- Verify FTP image was valid

### Version Not Reached
- Check device system logs for install failures: `show log messages | last 100`
- Verify FTP credentials and server accessibility
- Confirm image file names match expected format

### Connection Issues During Upgrade
- Ensure `ansible_user` has sufficient privileges
- Verify SSH key or password authentication
- Check firewall rules for NETCONF (port 830) access

## Advanced: Custom Device Handling

### Per-Device Timeout Configuration

Override the default 10-minute timeout for specific devices or groups:

In inventory:

```ini
[juniper_devices]
slow-device-01 ansible_host=192.168.1.10 target_version=23.4 device_model=ex2300 upgrade_timeout_minutes=20
normal-device-01 ansible_host=192.168.1.11 target_version=23.4 device_model=ex4100
```

Or via command line:

```bash
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml \
  --ask-vault-pass \
  -e upgrade_timeout_minutes=15
```

### Custom Device-Specific Configuration

For device-specific configuration, create group variables:

```bash
mkdir -p ansible/group_vars/ex2300_devices
```

Create `ansible/group_vars/ex2300_devices/vars.yml`:

```yaml
# Device-specific timeouts, FTP paths, etc.
upgrade_timeout_minutes: 15
ftp_path: "images/junos/ex2300"
```

Then organize inventory:

```ini
[ex2300_devices]
ex2300-01 ansible_host=192.168.1.10 target_version=23.4 device_model=ex2300
ex2300-02 ansible_host=192.168.1.11 target_version=23.4 device_model=ex2300

[juniper_devices:children]
ex2300_devices
```

## License

See LICENSE file.

## Contributing

Submit issues or pull requests to improve the project.

