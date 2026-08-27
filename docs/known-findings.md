# Known findings

There are currently no HIGH or CRITICAL findings in either Python image. This
is dated scan evidence, not a promise that the images stay empty.

Nothing is suppressed. Trivy prints every HIGH and CRITICAL finding before the
risk gate decides whether publication can continue. A future finding needs an
entry here before the gate can pass, even when it is below the blocking
thresholds.

Each entry records the last evidence review and the first date a fix became
available, or `none` when no fix exists:

```text
gate: cve=CVE-YYYY-NNNNN reviewed=YYYY-MM-DD fix-available=none
```

The gate blocks CISA KEV findings, EPSS above 0.1, fixes available for at least
30 days, and entries not reviewed for 90 days. Missing evidence fails closed.
VEX may only state a fact true of the image itself. Application-specific
reachability does not belong in a shared runtime image.
