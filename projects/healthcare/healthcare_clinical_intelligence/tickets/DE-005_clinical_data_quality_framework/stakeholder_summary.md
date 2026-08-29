# Stakeholder Summary — Data-Quality Gate

Every pipeline refresh now produces a durable quality scorecard instead of a transient console report. Critical structural or reconciliation problems stop the workflow. Expected rejected-record activity is visible as a warning and can be made blocking during strict validation or release certification.

The current synthetic snapshot passed seven of eight controls and recorded one quarantine-volume warning. The quarantined records are deliberately malformed test fixtures, not silent data loss. Their payloads and reason codes remain available for investigation.

Threshold changes are operational policy decisions. Before production use, data owners should approve tolerances, escalation routes, response time objectives, and whether specific quarantine reasons may be non-blocking.
