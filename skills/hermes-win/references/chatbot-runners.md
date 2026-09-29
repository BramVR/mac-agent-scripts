# Chatbot GitHub Actions runners

Use the Windows `hermes-win` VirtualBox host for `BramVR/chatbot` CI. The Mac only sends control commands. Never start a Colima, Docker, or GitHub Actions runner on the Mac for this repository.

## Untrusted PR jobs

- Inspect `Crabbox Template`, its current clean snapshot, host capacity, and occupied NAT ports with `VBoxManage` over `hermes-win` SSH. Do not alter `HA`, `Hermes`, the template, or `Crabbox Trusted`.
- Create a task-named **linked clone** from the verified template snapshot. Give its inherited SSH NAT forward a free host port, then start this clone headless. Record clone UUID, snapshot UUID, port, and task.
- Verify the clone through SSH as `runner` with strict host-key checking and a task-local known-hosts file. Confirm hostname before registration. Use `crabbox warmup --provider ssh --target linux --static-host hermes-win --static-user runner --static-port <port> --static-work-root /home/runner/crabbox --ttl 2h --idle-timeout 1h`.
- For each queued job, run `crabbox actions register --id <lease-id> --provider ssh --target linux --static-host hermes-win --static-user runner --static-port <port> --static-work-root /home/runner/crabbox --repo BramVR/chatbot --name <unique-task-runner-name> --labels crabbox,untrusted,ephemeral --ephemeral`. Register **one at a time** on this VM. An ephemeral registration handles one job, then unregisters. Inspect `gh run view <run-id> --json jobs` before the next registration.
- After GitHub marks a job complete, wait for that ephemeral `Runner.Listener` and `run.sh` to exit before registering the next runner. Registration restarts the service; starting it during post-job cleanup can cancel an otherwise successful job.
- If a job fails, read its GitHub log, fix the source, rerun review and focused checks, push, and use fresh ephemeral registrations for the new run. Keep the clone until the latest head is green.
- Ubuntu unattended upgrades can take the dpkg lock after VM boot and make Playwright's `--with-deps` step fail. Let the upgrade finish; never kill or bypass it. Rerun the failed job with a fresh ephemeral registration once the lock is free.

## Trusted live proof

The protected `free-tier-smoke` workflow needs `crabbox,trusted,ephemeral` on a **separate** trusted remote VM. Inspect prior proof and current `Crabbox Trusted` state before starting it. Never pass protected secrets to the untrusted PR clone. The main-only workflow must target the exact merged SHA and approved synthetic Worker, with lead capture disabled. Follow the repository deployment and proof docs.

## Cleanup

After all task jobs complete, verify runner registrations and task clone identity. Stop the Crabbox lease, gracefully shut down the task clone, then unregister and delete **only that clone** by its recorded UUID. Leave the template, trusted VM, `HA`, and `Hermes` untouched. Do not stop a VM or process by a name pattern.
