# NaS Core Data Governance

## Purpose

This policy governs data proposed for use in NaS Core. It protects research
participants, honors source terms, preserves scientific provenance, and ensures
that language-model use never bypasses data restrictions.

This document establishes an engineering control baseline. It is not a
substitute for legal, privacy, security, institutional, or scientific review.

## Scope

The policy applies to data registration, acquisition, storage, access,
analysis, retrieval, embedding, model processing, model training, export,
publication, retention, suspension, and deletion.

It covers source data and all derived data. A derivative inherits the most
restrictive classification of its inputs unless a documented and authorized
determination explicitly changes it.

## Cortex v0 rule

NaS Core denies data use by default.

- Public/open data may be used after registration and activation.
- Licensed data may be used only when the governing agreement is documented,
  the proposed use is permitted, and a responsible approver activates it.
- Controlled data is prohibited in Cortex v0.
- PHI is prohibited in Cortex v0.

The prohibition applies at ingestion, storage, analysis, AI transmission,
embedding, training, export, and publication—not only at upload.

## Governance lifecycle

Sources progress through the following recorded states:

`proposed -> under_review -> approved -> active`

An active source may become `suspended`, `expired`, `archived`, or `deleted`.
Suspended sources may return to review. No source outside `active` may be used by
an operational workflow.

## Required registration fields

Each source record must include:

- a stable source identifier, name, owner, and authoritative URL;
- classification and source version;
- intended and prohibited uses;
- license, terms, or data-use agreement references;
- publication, attribution, AI-processing, embedding, and training permissions;
- authorized roles;
- access method and storage restrictions;
- retention and review dates;
- approval decisions and rationale; and
- notes needed to correctly interpret the registration.

Dataset snapshots later add the exact query, manifest, release, download time,
file identifiers, sizes, and cryptographic checksums.

## Roles

- **Data owner:** has authority over the source or receives authority by agreement.
- **Data steward:** maintains classifications, registrations, and lifecycle state.
- **Principal investigator:** owns the scientific purpose and protocol.
- **Privacy/security reviewer:** assesses privacy, contractual, and technical risk.
- **Researcher:** uses data only within an approved purpose.
- **Scientific reviewer:** reviews methods, evidence, limitations, and claims.
- **Publication approver:** approves external release.

One person may perform multiple roles during the earliest company stage, but
the system still records the role under which each decision was made. Higher
risk data will require separation between requester and approver.

## Enforcement

The policy engine evaluates source status, review date, classification,
machine-readable research purpose, actor role, action, and the source-specific
permission flags. It rejects unknown sources, non-active or overdue sources,
unapproved purposes, unauthorized roles, restricted actions, controlled data,
and PHI.

All consequential decisions will become audit events when persistence is added.
No manual application path may silently bypass the policy engine.

## Exceptions

Cortex v0 has no exception path for controlled data or PHI. Supporting either
classification requires a new architecture decision, governance review,
security controls, contracts and authorizations, and explicit implementation.
