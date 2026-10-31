# Finding Confidence Terminology Specification

## Overview

DERA prohibits fabricating statistical or probabilistic "confidence percentages" (such as "92.4% confidence") for static analysis findings. Instead, Phase 8.5 standardizes discrete, explainable categorical confidence terms based on verified schema metadata and workload availability.

## Categorical Confidence Levels

| Confidence Level | Definition | Prerequisites |
| :--- | :--- | :--- |
| `VERIFIED` | Full structural evidence exists in the schema snapshot to confirm the finding without assumption. | All referenced objects exist, constraints/indexes are fully reflected, and no metadata limitations apply. |
| `CONDITIONAL` | The finding is structurally valid, but practical remediation depends on workload query patterns or runtime factors. | Example: A missing foreign key index is conditionally needed depending on whether JOIN/DELETE operations frequently query the child table. |
| `INCOMPLETE` | Insufficient metadata exists in the snapshot to reach a definitive conclusion. | Example: Foreign keys in an engine that does not report catalog constraints, or restricted permissions. |
| `UNSUPPORTED` | The target database connector or engine version does not support the introspection required for this rule. | Engine feature limitation recorded in `DatabaseEngineCapabilities`. |

## Safety Directives

1. Findings with `INCOMPLETE` or `UNSUPPORTED` confidence must never be presented as confirmed defects.
2. Reports must highlight conditional assumptions clearly in the finding's engineering recommendation.
