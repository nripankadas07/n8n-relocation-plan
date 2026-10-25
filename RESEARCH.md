# Research and alternatives

Observed on 25 October 2026; repository metadata snapshot at 06:05 UTC, with narrower
comparison searches and README reads later in the same review. Exact receipts
are retained in the portfolio ledger. Searches request GitHub star ordering;
topic/keyword coverage is limited and does not establish a global ranking.

Queries: `topic:workflow-automation stars:>10000 archived:false sort:stars; n8n migration sort:stars; n8n backup sort:stars`.

| Repository | Observed stars | Last push observed UTC | API license classification |
| --- | ---: | --- | --- |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 208516 | 2026-10-24T23:11:27Z | NOASSERTION |
| [aleksnero/n8n-backup-manager](https://github.com/aleksnero/n8n-backup-manager) | 77 | 2026-09-19T09:05:23Z | NOASSERTION |
| [dataprospectors-at/n8n-porter](https://github.com/dataprospectors-at/n8n-porter) | 13 | 2025-04-08T11:52:03Z | MIT |

The highest-star relevant comparable found among these is recorded in the table.
Stars indicate an audience to investigate, not user demand or technical quality.
NOASSERTION/unclassified licenses require separate review before reusing code.
These comparables were read as evidence; no competitor code/prose was reused.

## User and evidence

n8n maintainers moving exported workflows between environments. Credential IDs and called-workflow IDs are environment-specific. Bulk replacement can bind a node to an ambiguous or incompatible target.

- https://docs.n8n.io/build/manage-workflows/export-and-import.md
- https://github.com/n8n-io/n8n/issues/20049
- https://github.com/n8n-io/n8n/blob/9a489b65ed539a042e819012558cfc6985aab78d/packages/workflow/src/interfaces.ts

Issue 20049 records historical credential-import pain and is closed. Existing n8n-porter already supports environment mapping. This tool targets a narrower offline reviewed-plan workflow; demand for it is inferred, not an upstream feature request.

## Workflow comparison

n8n supplies export/import; n8n Backup Manager backs up/restores instances and snapshots; n8n-porter migrates resources with server configuration and credential payloads. This tool requires neither server/API access nor credential data and binds a reviewable plan to the exact input documents. No claim that the other tools lack all equivalent safeguards.

Our first useful result is the bundled install-and-report example. The other
projects have their own setup, examples and support channels; their installation
times were not benchmarked here. No speed, memory, reliability or feature-absence
superiority claim follows from our successful example. Their broader workflows
may be more appropriate for larger or different tasks.

## Scope and portfolio comparison

Existing generic JSON diff tools and agent-sbom do not perform typed n8n reference relocation with stale-plan rejection. This is one complete file-transformation workflow, not a general migration platform.

The five selected projects address separate tasks: join cardinality, fold leakage,
ASGI URL wiring, container startup history and workflow export relocation. They
are not forks or subdivisions of one application. A portfolio-wide inventory of
218 repositories was compared before selection. Reusable packaging/report
boilerplate does not count as the original capability.

No runtime dependencies. Recheck export shape and newly managed credential slots against pinned upstream types before broadening support. n8n is fair-code/Sustainable Use licensed with enterprise exclusions, not a permissively licensed dependency. No n8n source, branding or code is bundled; the original interoperable tool is MIT.

Discovery path: An offline relocation example, ambiguous-name failure case and accurate n8n export/import topics and portfolio index entry.

Candidate rank 5 of 5 reflects practical usefulness, problem evidence,
distinctness, demonstrability and maintenance burden. It is a judgment, not a
measured score or a prediction of attention. Playwright/browser-agent ideas were
set aside because the existing portfolio already has tracing/replay tools.
Generic top-star lists/tutorial collections were not selected as product anchors.
Polars is used for a Polars-native workflow even though pandas has more stars;
scikit-learn fits the selected evaluation task rather than larger general ML repos.
