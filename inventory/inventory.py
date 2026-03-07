#!/usr/bin/env python3
"""
Dynamic Ansible inventory — reads from Terraform output.

Usage:
  ansible -i inventory/inventory.py all -m ping
  ansible-inventory -i inventory/inventory.py --list
"""

import json
import subprocess
import sys
from pathlib import Path

TERRAFORM_DIR = Path(__file__).parent.parent.parent / "terraform"

ANSIBLE_USER = "ansible"


def get_terraform_output() -> dict:
    result = subprocess.run(
        ["terraform", "output", "-json", "node_info"],
        cwd=TERRAFORM_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: terraform output failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def build_inventory(nodes: dict) -> dict:
    inventory = {
        "_meta": {"hostvars": {}},
        "all": {"children": ["ungrouped"]},
    }

    groups = {
        "routers":     [],
        "k3s":         [],
        "k3s_master":  [],
        "k3s_workers": [],
        "as65001":     [],
        "as65002":     [],
    }

    for name, node in nodes.items():
        ip   = node["ip"]
        role = node["role"]
        bgp_as = node["as"]

        # Host vars
        inventory["_meta"]["hostvars"][name] = {
            "ansible_host": ip,
            "ansible_user": ANSIBLE_USER,
            "bgp_as":       bgp_as,
            "role":         role,
        }

        # Functional groups
        if role == "router":
            groups["routers"].append(name)
        elif role == "master":
            groups["k3s"].append(name)
            groups["k3s_master"].append(name)
        elif role == "worker":
            groups["k3s"].append(name)
            groups["k3s_workers"].append(name)

        # AS groups
        if bgp_as == 65001:
            groups["as65001"].append(name)
        elif bgp_as == 65002:
            groups["as65002"].append(name)

    # Write groups into inventory
    for group, hosts in groups.items():
        if hosts:
            inventory[group] = {"hosts": hosts}

    # Register all groups as children of all
    inventory["all"]["children"] = list(groups.keys()) + ["ungrouped"]

    return inventory


if __name__ == "__main__":
    nodes = get_terraform_output()
    inventory = build_inventory(nodes)
    print(json.dumps(inventory, indent=2))
