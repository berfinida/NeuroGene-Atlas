# Security Policy

This local research application is not hardened for public clinical deployment. Bind services to localhost; never add patient-identifiable data or secrets to Git.

Supported security-fix line: 0.5.x. Pin dependencies, run npm audit and a Python vulnerability scan, and record provenance for upgrades.

Do not disclose credentials or exploit details in public issues. GitHub private vulnerability reporting is enabled: [report a vulnerability privately](https://github.com/berfinida/NeuroGene-Atlas/security/advisories/new). No monitored email address is claimed here.

If credentials were committed, revoke/rotate them first. Deleting a file is insufficient. Review reachable and unreachable Git objects; the bundled heuristic scanner is not comprehensive certification.
