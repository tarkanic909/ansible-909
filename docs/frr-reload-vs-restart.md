# FRR: `reload` vs `restart`

This document explains when to use `reload` and when to use `restart` with FRR.

## Short rule

- For routine changes to `frr.conf`, prefer `reload`.
- Use `restart` only when you need to fully stop and start FRR processes.

In this Ansible role, the preferred approach is:

- validate the new `frr.conf` before deploying
- run `reload` after a configuration change
- avoid using `restart` as a default response to every change

## What `reload` does

`reload` applies the diff between the configuration on disk and the currently running FRR configuration. It is a less disruptive operation than `restart`.

Typical characteristics:

- lower risk of a brief routing outage
- suitable for routine BGP configuration changes
- suitable after modifying `/etc/frr/frr.conf`
- suitable after enabling a new daemon in `/etc/frr/daemons`, if the FRR init script supports it

In practice, `reload` is the safe default when FRR is already running and you want to apply a new configuration.

## What `restart` does

`restart` stops the running FRR daemons and starts them again.

Typical consequences:

- BGP sessions may be interrupted
- a brief routing outage may occur
- unsaved runtime configuration is lost

`restart` makes sense mainly in these situations:

- initial service bootstrap when FRR is not yet running
- broken or inconsistent process state
- a change that `reload` cannot apply correctly
- diagnostics when you need a clean daemon start

## Why `restart` alone is not enough

If a playbook runs `restart` after every change, even a small mistake in the configuration or template can bring down the service at the worst possible moment.

The problematic sequence looks like this:

1. playbook overwrites the live `frr.conf`
2. handler runs `restart`
3. FRR fails to start or starts only partially
4. routing is down

This is why it is better to validate the configuration first, then run `reload`.

## Recommended flow in Ansible

Recommended sequence for this role:

1. install `frr` and `frr-pythontools` packages
2. enable the required daemons in `/etc/frr/daemons`
3. start and enable `frr`
4. render `frr.conf` via `template` with `validate`
5. notify the handler with `state: reloaded` on change

Validation example:

```yaml
validate: /usr/lib/frr/frr-reload.py --test --stdout %s
```

This checks the new configuration against a temporary file before overwriting `/etc/frr/frr.conf`.

## Project recommendations

For `ansible-909`:

- change to `roles/router/templates/frr.conf.j2`: `reload`
- change to `/etc/frr/daemons`: usually `reload`
- first service start: `state: started`
- recovering from a broken state: `restart`

Practical summary:

- `reload` is the safe default for configuration changes
- `restart` is a service intervention, not a routine deploy mechanism

## References

- FRR Basic Setup: <https://docs.frrouting.org/en/frr-8.2.2/setup.html>
- FRR Reload workflow: <https://docs.frrouting.org/en/latest/frr-reload.html>
- Ansible `template.validate`: <https://docs.ansible.com/projects/ansible/2.5-archive/modules/template_module.html>
