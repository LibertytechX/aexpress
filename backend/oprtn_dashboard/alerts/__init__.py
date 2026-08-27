"""
Alerts package — alert rules and the generation engine.

Planned modules (later phases — see guide §14.7/§14.8):
  - rules.py   : one evaluator per alert type (BIKE_AFTER_HOURS, INCOMPLETE_ORDER, ...).
  - engine.py  : run_all_rules() — dedupe + upsert + auto-resolve.
"""
