"""
Permissions for the Operations Dashboard endpoints.

Phase 1 reuses the existing OCC service-key scopes (`occ:read` / `occ:write`) so
the same service API keys that call `/api/occ/` can call `/api/ops/`. If the ops
surface ever needs its own scopes, define `HasOpsReadScope` / `HasOpsWriteScope`
here and switch the views over.
"""

from dispatcher.permissions import HasOCCReadScope, HasOCCWriteScope

# Aliases so views read naturally and we can swap implementations later.
HasOpsReadScope = HasOCCReadScope
HasOpsWriteScope = HasOCCWriteScope

__all__ = ["HasOpsReadScope", "HasOpsWriteScope"]
