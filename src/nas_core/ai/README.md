# AI gateway

Model providers will be hidden behind a NaS-owned interface. Providers receive
only the minimum retrieved evidence and compact derived results required for a
task, with structured outputs, citations, uncertainty, and abstention.

The first implementation is a title/abstract advisory screener. It uses the
OpenAI Responses API through a replaceable gateway, requires typed structured
outputs, sentence-level evidence references, explicit confidence, and human
review for every recommendation. Requests, responses, and manifests remain in
external object storage. API keys, abstracts, and model output never enter Git.

AI recommendations cannot populate the human decision ledger. Calibration and
locked routing rules are required before recommendations may prioritize founder
review. Autonomous exclusions are prohibited for NAS-BRCA-002.
