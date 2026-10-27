# Metadata Contract Versioning Policy

**Current Version:** `1.0.0`  
**Subsystem:** `dera.metadata.contracts`  

---

## 1. Versioning Principles

DERA canonical metadata models follow Semantic Versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR:** Breaking schema alterations (removal or renaming of canonical model fields, changes in stable ObjectId hash algorithms).
- **MINOR:** Backward-compatible additions (new metadata fields with default values, additional `CanonicalTypeCategory` entries).
- **PATCH:** Bug fixes in normalization adapters that preserve existing output shapes.

---

## 2. Deprecation & Migration Policy

Any planned schema migration or breaking change requires:
1. Deprecation notice documented in release notes across two minor versions.
2. Formal acceptance audit before incrementing the MAJOR contract version.
