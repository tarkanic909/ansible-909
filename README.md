# Ansible Lab

Ansible configuration management for the lab-909 infrastructure.

## Requirements

- Python 3
- Terraform state from `../terraform-909` (must be applied first)

## Setup

Sets up a Python venv and installs Ansible via pip:

```bash
./setup.sh
source .venv/bin/activate
```

## Inventory

Dynamic inventory reads node information directly from Terraform output:

```bash
ansible-inventory --list
ansible-inventory --graph
```

The inventory script (`inventory/inventory.py`) runs `terraform output -json node_info`
from `../terraform-909` and groups hosts by role and autonomous system:

| Group | Members |
|-------|---------|
| `routers` | `lab-router1`, `lab-router2` |
| `k3s` | all K3s nodes |
| `k3s_single` | single-node K3s |
| `k3s_cluster` | master + workers |
| `k3s_master` | master node only |
| `k3s_workers` | worker nodes only |
| `as65001` | nodes in AS 65001 |
| `as65002` | nodes in AS 65002 |

## Usage

Run the full site playbook:

```bash
ansible-playbook site.yml
```

Run against a specific group:

```bash
ansible-playbook site.yml --limit routers
ansible-playbook site.yml --limit k3s
```

Test connectivity:

```bash
ansible all -m ping
```

## Configuration

`ansible.cfg` defaults:

- Remote user: `ansible` (created by cloud-init)
- Privilege escalation: `sudo` (passwordless)
- Python interpreter: `/usr/bin/python3`
- Inventory: `inventory/inventory` (dynamic script)

## Roles

| Role | Description |
|------|-------------|
| `router` | FRR installation, BGP configuration, reload handler |
| `k3s_install` | Downloads and installs K3s binary (shared by master/worker) |
| `k3s_master` | K3s server setup; set `k3s_expose_token: true` when workers will join |
| `k3s_worker` | K3s agent setup, joins master via LAN IP |
