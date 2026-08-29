# DA-001 — Emergency Department Utilization

## Business question

How many completed emergency encounters occur each month, how many unique patients use the ED, and how concentrated is repeat ED use among those patients?

## Definition

- Emergency encounter: a FHIR `Encounter` whose normalized `class.code` is `EMER`.
- Completion rule: `Encounter.status` is `finished` or `completed`.
- Reporting period: calendar month of `Encounter.period.start` in UTC.
- Patient count: distinct referenced patients with at least one qualifying ED encounter in the month.
- Intensity: qualifying ED encounters divided by patients with a qualifying ED encounter.

This is an encounter-intensity metric, not a population utilization rate. A true rate requires an independently modeled eligible/enrolled member-month denominator. Facility and demographic segmentation also remain out of scope until encounter-location and reporting-dimension mappings are present.

## Acceptance criteria

- [x] Implement one-row-per-month SQL mart.
- [x] Apply documented encounter-class and status mappings.
- [x] Independently reconcile mart encounter and patient counts to `core.encounter`.
- [x] Verify qualifying encounters have a reporting timestamp.
- [x] Expose the mart through a reproducible dashboard export.
- [x] Document limitations and synthetic-data findings.

## Evidence

- Mart: `sql/marts/030_ed_utilization.sql`
- Independent checks: `validation.sql`
- Implementation and findings: `solution.md`
- Consumer-ready interpretation: `stakeholder_summary.md`

Status: complete for the synthetic Phase 1 scope.
