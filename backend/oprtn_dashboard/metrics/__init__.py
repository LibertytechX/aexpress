"""
Metrics package — the single source of dashboard math for the ops app.

Planned modules (later phases — see guide §14.5/§14.6/§9.6):
  - order_metrics.py    : status normalization + counts (OrderMetrics).
  - payment_metrics.py  : order amount across ALL payment methods/statuses (§14.5).
  - cod_metrics.py      : COD goods value, COD fee, collection reconciliation (§14.6).

NOTE: cost-side P&L (fuel/maintenance/misc/airtime) is intentionally OUT OF SCOPE
for now; no financial cost module is created.
"""
