# MonkeyBots | Troubleshooting & Diagnostics Guide

---

## 1. Port 8765 Conflict ("Address already in use")

### Symptom:
`uvicorn.error: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8765): only one usage of each socket address`

### Solution:
A previous backend instance may still be holding the port. In PowerShell:
```powershell
# Identify process using port 8765
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# Terminate orphaned process
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8765).OwningProcess -Force
```

---

## 2. Simulation Divergence ("Simulation status: DIVERGED")

### Symptom:
The status indicator displays a red `DIVERGED` badge, and simulation stepping stops.

### Cause:
Extreme commanded torques, unstable PID gains ($K_p$ or $K_d$ set excessively high), or integration timesteps $\Delta t > 0.005\text{ s}$ under stiff contact conditions.

### Resolution:
1. Click **Reset (Key `R`)** on the timeline toolbar to restore generalized coordinates to initial conditions.
2. In **Motion and Control**, lower proportional gain $K_p$ and increase damping $K_d$.
3. In **Simulation**, set integrator to `RK4` or decrease timestep to $0.001\text{ s}$ ($1\text{ ms}$).

---

## 3. Corrupted Project Recovery

### Symptom:
A power loss or crash interrupted a project save.

### Automatic Recovery:
MonkeyBots automatically recovers corrupted manifests:
1. It first inspects `project.json.bak` and restores it if valid.
2. If `.bak` is unreadable, it scans `.snapshots/` and restores the most recent clean state.
3. If all backups are compromised, run:
   ```powershell
   python -c "from core.monkeybots.projects import ProjectManager; pm = ProjectManager(); pm.validate_project('<project_id>')"
   ```
