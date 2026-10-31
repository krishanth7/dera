# Rule Coverage Specification

## Overview

Rule coverage measures the completeness of static analysis inspection executed across the registered diagnostic rule catalog.

## Mathematical Formulation

$$\text{Coverage Percentage} = \min\left(100, \max\left(0, \frac{\text{Evaluated Rules}}{\text{Total Applicable Rules}} \times 100\right)\right)$$

### Zero Denominator Safety

When no rules are applicable (e.g., an empty schema), the formula explicitly returns $0\%$ rather than raising division by zero or producing `NaN`/`Infinity`.

## Coverage Categories

- **Registered Rules**: Total rules registered in the DERA rule catalog.
- **Evaluated Rules**: Rules that completed inspection and produced findings or clean passes.
- **Skipped Rules**: Rules explicitly disabled via diagnostic configuration.
- **Unsupported Rules**: Rules requiring connector capabilities not provided by the target engine.
- **Partial Metadata**: Rules where limited engine reflection prevented definitive conclusions.

## Operational Boundaries

Rule coverage measures inspection scope, not database health or absence of runtime defects. An empty database evaluated by all rules will report 100% rule coverage despite having no schema workload.
