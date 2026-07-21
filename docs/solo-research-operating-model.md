# Founder-Led Research Operating Model

Last reviewed: 2026-07-20

NaS Research is currently a one-person research organization led by Dalron J.
Robertson. This is an operating fact, not a temporary team roster to obscure in
publication language. Until additional people formally join a project, Dalron
serves as founder, study lead, analyst, author, internal scientific reviewer,
and publisher.

Codex and other AI systems may assist with research operations, code, evidence
organization, adversarial review, and drafting. They are not independent human
reviewers, cannot authorize a scientific gate, and are not evidence sources.

## Review provenance

Every review record declares one of four types:

| Review type | Meaning | Can authorize an internal gate? | Can be called peer review? |
| --- | --- | --- | --- |
| `internal_self_review` | The study lead performs a documented review pass | Yes | No |
| `ai_assisted_internal_review` | AI identifies issues or checks consistency | No | No |
| `independent_human_review` | A qualified person outside the study authorship performs review | Only when designated | No, unless part of a journal's formal process |
| `journal_peer_review` | Review administered by a scientific journal | Only for the journal decision | Yes, after the journal confirms it |

AI-assisted review is always advisory. It cannot be marked `approved` or
required as the authority for question selection, preregistration, release, or
publication.

## Founder-led gate procedure

The founder may authorize an internal research gate when all of the following
are true:

1. the relevant plan was written before the gated result or outcome was examined;
2. separate scientific, biological/clinical, statistical, governance, and claim
   checks are completed as applicable;
3. an AI-assisted adversarial pass is resolved or its unresolved findings are
   documented as limitations;
4. the founder records a decision, timestamp, rationale, conflicts, and version;
5. the repository validates and tests pass;
6. the approved commit is tagged where the lifecycle requires a frozen record;
7. public outputs disclose that review was internal and founder-led.

Self-review is not represented as independence. A timestamped protocol, immutable
inputs, clean reruns, independent datasets, and transparent negative results are
used to reduce bias; none of them is described as human peer review.

## Compensating scientific controls

Founder-led studies require stronger procedural evidence:

- decision-led questions and prespecified success criteria;
- versioned literature and analysis protocols;
- outcome-blind protocol locks;
- immutable source snapshots and checksums;
- deterministic code and synthetic tests;
- complete exclusion, missingness, warning, and deviation records;
- prespecified multiplicity and sensitivity analyses;
- preservation of null and contradictory findings;
- independent dataset validation before an external-validation claim;
- clean-environment reruns and numerical-fidelity checks;
- sentence-level claim-to-evidence traceability; and
- explicit abstention when data or diagnostics are inadequate.

An independent validation dataset is independent evidence, not independent
human review. These claims remain distinct.

## External experts near publication

NaS may invite qualified people from Dalron's professional network to review a
near-final release or manuscript. Their names, qualifications, affiliations,
conflicts, reviewed version, comments, and resolutions are recorded when they
agree to be identified.

External expert feedback strengthens a manuscript but is not called journal peer
review unless it occurs through a journal's formal editorial process. A project
does not invent or imply external review when none occurred.

## Publication states

| State | Public wording |
| --- | --- |
| Internal draft | Not public; founder-led work in progress |
| NaS research report | Public, founder-led, internally reviewed, not peer reviewed |
| Preprint | Public preprint; not peer reviewed unless the platform explicitly says otherwise |
| Submitted manuscript | Submitted to a named journal; editorial decision pending |
| Under peer review | Use only after the journal confirms external review is underway |
| Peer-reviewed publication | Use only after formal journal acceptance/publication |
| Corrected or retracted | Preserve prior version and visible correction/retraction record |

The default website disclosure before journal review is:

> This founder-led NaS research report underwent documented internal
> reproducibility, evidence, and claim review. It has not yet undergone formal
> independent journal peer review.

Any external expert feedback is disclosed separately. A preprint or website
publication does not become peer reviewed merely because it is public.

## Authorship and AI disclosure

Human authorship reflects accountable human work. AI assistance is disclosed in
the methods, acknowledgements, or dedicated AI-use statement as appropriate.
Model output is verified against executed artifacts or sources and is never
cited as scientific evidence.

## When the model changes

If a collaborator, employee, contractor, or advisor formally joins a study, the
study records their role, responsibilities, conflicts, and approval authority.
Governance changes prospectively; prior founder-led records are not rewritten to
imply that a team existed earlier.
