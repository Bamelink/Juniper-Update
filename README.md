# Juniper Software Upgrade Automation

This repository contains an **Ansible + Python** framework for automating Juniper SRX/EX firmware updates. It supports:

- Device groups by **location** (router + switches).  
- Update groups such as `testing`, `staging`, `production` that aggregate locations.  
- Firmware pulled from a custom FTP repo.  
- Pre‑ and post‑upgrade checks (interfaces, ISIS, LLDP).  
- Results rendered as Markdown for easy viewing directly in VS Code.

## Getting Started

1. **Install prerequisites**
   ```powershell
   python -m pip install ansible junos-eznc
   ansible-galaxy collection install juniper.device
   ```

2. **Populate inventory**
   Edit `ansible/inventories/hosts.yml` to reflect your routers and switches. Host groups named `locationX` are used to build update groups.

3. **Run an upgrade**
   ```powershell
   cd ansible
   ansible-playbook -i inventories/hosts.yml playbooks/upgrade.yml \
     -e target_group=testing \
     -e target_version=23.2R1 \
     -e repo_base=ftp://myrepo.example.com/junos \
     -e ansible_user=admin \
     -e reboot_timeout=600            # optional override
   ```
   Package names are computed from the device model using the `package_map` variable in the playbook.
   The custom callback plugin (`juniper_report`) will write `ansible-report.md`.

4. **Generate detailed report**
   ```powershell
   python ..\scripts\generate_report.py
   code upgrade-details.md   # open in VS Code
   ```

## Directory Layout

```
ansible/
├── inventories/     # YAML or INI inventories with location/update groups
├── playbooks/        # upgrade.yml and other workflows
├── plugins/callback/ # juniper_report.py to emit Markdown
└── roles/            # place for custom roles if needed

scripts/
└── generate_report.py   # aggregate pre/post logs

logs/                  # created during playbook runs
```

## Pre/Post-Checks
The playbook records the output of common commands to `logs/<host>_pre.json` and `_post.json`.  
You can extend the command list or add additional validation tasks.

> **Tip:** open the generated Markdown files in VS Code for a quick glance at results.

