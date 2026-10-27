# DERA API Versioning & Compatibility Policy

This document defines DERA's API versioning lifecycle, compatibility guarantees, deprecation protocols, and breaking-change policies.

---

## 1. Versioning Architecture

DERA utilizes URI-based path versioning for major API lifecycles:

```http
/api/v1/...
```

The active production API version is **`v1`**. New major versions (`/api/v2`) are introduced only when backward-incompatible structural changes are strictly required and cannot be accommodated via additive modifications.

---

## 2. Compatibility Classifications

### Additive (Backward-Compatible) Changes

The following changes are considered non-breaking and may be introduced in minor or patch platform releases:

1. **New Endpoints**: Adding a new resource path or HTTP method.
2. **New Optional Fields**: Adding optional properties to request models with safe defaults.
3. **New Response Fields**: Adding new properties to response JSON schemas (clients MUST ignore unknown fields).
4. **New Query Parameters**: Adding optional filter, sort, or pagination query options.
5. **Broadened Enums**: Adding new enum choices to query parameters or request inputs.

### Breaking (Backward-Incompatible) Changes

The following changes are strictly breaking and will be rejected by DERA's automated CI breaking-change detector:

1. **Removed Routes**: Deleting an existing endpoint path.
2. **Removed Methods**: Removing support for an existing HTTP verb on a path.
3. **New Required Parameters**: Introducing a required path, header, query, or body parameter to an existing endpoint.
4. **Removed Response Properties**: Deleting properties from existing response schemas.
5. **Changed Property Types**: Altering the primitive or object type of an existing field.
6. **Narrowed Enum Values**: Removing supported choices from an enum parameter.
7. **Removed Success Codes**: Removing an existing 2xx success status code.

---

## 3. Deprecation Protocol

When a field or endpoint is marked for retirement:

1. **OpenAPI `deprecated: true`**: The OpenAPI specification is updated to flag the element as deprecated.
2. **HTTP Headers**: Deprecated responses include standard RFC 8594 headers:
   * `Deprecation: @<timestamp>`
   * `Sunset: <date>` (minimum 6 months from initial deprecation notice)
   * `Link: <canonical_new_url>; rel="successor-version"`
3. **Documentation**: Clear migration paths and timelines are published in release notes.
