# Security and HIPAA Considerations

This project uses synthetic data only and is not a HIPAA-covered production system. It nonetheless follows the relevant engineering principles: minimum necessary access, no credentials in Git, separate environments, encryption in transit/at rest for deployed services, audit-friendly run metadata, retention policies, and explicit prohibition of PHI in fixtures, logs, notebooks, screenshots, and dashboards.

Repository controls include ignored environment/output paths, private-key detection in pre-commit, scheduled dependency updates, read-only GitHub Actions permissions, bounded exception text, and a release checklist that prohibits secrets and PHI. These controls reduce engineering risk but do not constitute a HIPAA security risk analysis, business associate agreement, access-control program, incident-response program, or compliance certification.
