# Release Checklist

## Code and contracts

- [ ] `make quality` passes lint, formatting, typing, tests, and the coverage floor.
- [ ] `make integration` passes against a disposable PostgreSQL database.
- [ ] The second migration reports `already_current`.
- [ ] FHIR, claims, and HL7 reruns load zero duplicate raw records.
- [ ] The dashboard contract validates and contains all expected datasets.
- [ ] Documentation and `CHANGELOG.md` describe the change.

## Data and operations

- [ ] All fixtures and generated outputs are demonstrably synthetic.
- [ ] No secrets, `.env`, outputs, logs, PHI, or temporary databases are committed.
- [ ] The latest gate contains zero `fail` or `error` results.
- [ ] Any warnings are documented and expected.
- [ ] Operations report shows zero running, stale, missing-completion, and count-mismatch signals after completion.
- [ ] Performance report shows zero missing indexes and slow smoke queries.

## Delivery

- [ ] The GitHub Actions workflow passes from the monorepo root.
- [ ] The reviewed commit is pushed to `main` or the intended release branch.
- [ ] External-interface, vocabulary, dashboard-design, or clinical-governance dependencies are explicitly deferred rather than silently assumed.
