# DA-002 Stakeholder Summary

The platform now reports synthetic ED use per 1,000 covered member months instead of presenting ED users as if they were the eligible population. The dashboard receives both the member-month denominator and the payer/month utilization rate, and the original ED-user intensity measure remains separately labeled.

The validation load contained 100 active Coverage records and 950 distinct member months. Coverage completeness and overlap controls passed, and independent SQL reproduced the denominator, numerator, and rate from canonical records.

This is a synthetic engineering demonstration, not a production HEDIS measure or a clinical-performance assessment. Same-month eligibility is based on any overlap with the calendar month, partial months are not prorated, and encounters cannot be assigned to one Coverage when a patient has simultaneous payers because the controlled Encounter profile has no Coverage link.
