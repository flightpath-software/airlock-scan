---
id: ADR-0002
title: Reports stay local; nothing leaves the machine except a configured Tier-2 call or explicit export
date: 2026-07-21
decider: sean
status: accepted
considering:
  - write-a-report-file-into-the-scanned-repo
  - send-results-to-a-central-service-by-default
---

airlock runs against repositories the user does not trust, and its output can contain
detected secrets or excerpts of the code under review. That output is written only to
a user-local store (default `~/airlock/`), never into the scanned repo, and the only
bytes that leave the machine are a deliberately-configured Tier-2 cloud call (Tier-1
secrets redacted first, and avoidable entirely with the local backend) or an explicit
export. Writing a report into the scanned tree, or phoning results home by default,
were the alternatives and are rejected: the first leaks findings back into untrusted
code, the second exfiltrates potentially-sensitive results without consent.
