# Validation coverage

Local Linux/Python 3.12 validation includes core unit/integration cases, real
ecosystem APIs where used, runnable invented example, wheel build and clean
installed console-command checks outside the source tree. The original failure
expectations are preserved while implementation defects are corrected.

## Acceptance checks

- Exact type/name or explicit typed mappings produce deterministic target references.
- Ambiguous names, wrong types and dynamic child IDs stay unresolved and block application.
- Changing an input or tampering with plan operations rejects application.
- Credential payload fields and duplicate node IDs reject.

CI must pass on the intended public default-branch commit before this project is
counted as a verified launch. Public repository existence alone is insufficient.
Remote CI links and commit receipts belong in the portfolio ledger; this text
does not claim an unobserved run passed.

Windows/macOS, production data and live external service operation are untested.
4 MiB JSON, up to2000 nodes and5000 credential metadata records. Literal executeWorkflow workflowId references only; expressions remain unresolved. Does not resolve arbitrary node parameters, URLs, environment variables, custom/community-node references, access rights or encryption. No n8n server execution/import, credential decryption, copying, activation or API calls. Relocated output is always active:false and cannot overwrite an existing file. Exports and reports can contain sensitive names/parameters; keep real files private.

The cloud browser rejects local file URLs, so the generated HTML report was
checked structurally and for escaped output but was not visually inspected in
that browser. Console behavior and installed commands are independently tested.

The initial new-project environment audit flagged its preinstalled pip 25.0.1.
The installer is upgraded to pip 26.2+ before dependency installation and the
full environment audit is rerun. Project runtime dependencies were not the
source of those installer advisories. No advisory is suppressed.
