#!/usr/bin/env python3
"""
Dynamic Ansible inventory — reads from Terraform output.

Usage:
  ansible-inventory --list
  ansible-inventory --graph
  ./inventory/inventory.py --list
  ./inventory/inventory.py --host lab-router1
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

TERRAFORM_DIR = Path(__file__).parent.parent.parent / "terraform-909"

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
        "k3s_single":  [],
        "k3s_cluster": [],
        "k3s_master":  [],
        "k3s_masters": [],
        "k3s_workers": [],
        "as65001":     [],
        "as65002":     [],
    }

    for name, node in nodes.items():
        ip     = node["mgmt_ip"]
        role   = node["role"]
        bgp_as = node["bgp_as"]

        # Host vars
        inventory["_meta"]["hostvars"][name] = {
            "ansible_host":  ip,
            "ansible_user":  ANSIBLE_USER,
            "lan_ip":        node["lan_ip"],
            "lan_cidr":      node["lan_cidr"],
            "lan_network":   node["lan_network"],
            "interlink_ip":  node["interlink_ip"],
            "bgp_as":        bgp_as,
            "bgp_neighbor_ip":        node["bgp_neighbor_ip"],
            "bgp_neighbor_as":        node["bgp_neighbor_as"],
            "role":          role,
        }

        # Functional groups
        if role == "router":
            groups["routers"].append(name)
        elif role == "single":
            groups["k3s"].append(name)
            groups["k3s_single"].append(name)
            groups["k3s_masters"].append(name)
        elif role == "master":
            groups["k3s"].append(name)
            groups["k3s_master"].append(name)
            groups["k3s_masters"].append(name)
            groups["k3s_cluster"].append(name)
        elif role == "worker":
            groups["k3s"].append(name)
            groups["k3s_workers"].append(name)
            groups["k3s_cluster"].append(name)

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--host")
    args = parser.parse_args()

    nodes = get_terraform_output()
    inventory = build_inventory(nodes)

    if args.host:
        print(json.dumps(inventory["_meta"]["hostvars"].get(args.host, {}), indent=2))
    else:
        # --list alebo bez argumentu — vrati cely inventory
        print(json.dumps(inventory, indent=2))
