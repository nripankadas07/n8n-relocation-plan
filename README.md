# n8n Relocation Plan

Credential IDs and called-workflow IDs are environment-specific. Bulk replacement can bind a node to an ambiguous or incompatible target.

Create a typed reference-mapping plan, report ambiguous/dynamic references and apply a reviewed plan only when both the workflow and catalog still match.

## Try the example

Python 3.11+ on Linux. No account or remote service is needed.

```sh
git clone https://github.com/nripankadas07/n8n-relocation-plan.git
cd n8n-relocation-plan
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade "pip>=26.2" "setuptools>=84.1"
python -m pip install .
n8n-relocation-plan example.json --html report.html
```

The invented example maps one typed credential reference and one literal child-workflow ID. Applying the exact reviewed plan writes a new inactive workflow export and leaves other node parameters/connections intact.

The JSON goes to stdout; open `report.html` in a browser for searchable evidence
tables. The bundled [HTML report](demo.html) and [expected JSON](example-output.json)
come from [example.json](example.json), which uses invented data.

Exit 0 means a completed report without the tool's documented review findings;
exit 1 means findings require review; exit 2 means invalid input or an operational
error, with stderr and no partial JSON report. Some bundled examples intentionally
exit 1 to demonstrate a failure diagnosis. Do not discard those findings.


Create a reviewable plan, then apply that exact plan with the same input:

```sh
n8n-relocation-plan example.json --output reviewed-plan.json
n8n-relocation-plan example.json --apply-plan reviewed-plan.json --output relocated.json
```

Both output paths must be new files. Review the plan and keep exports private.
The resulting export is inactive. This command does not import or activate it.

## Input and supported behavior

Input is one object with `workflow` (one n8n export) and `catalog`. Catalog credentials contain only id/name/type metadata; workflows maps source IDs to target IDs. Optional explicit_credentials keys have TYPE:SOURCE_ID form. Export credential references support assigned string id/name only. Null IDs and AI Gateway managed slots reject.

## Limits and compatibility

4 MiB JSON, up to2000 nodes and5000 credential metadata records. Literal executeWorkflow workflowId references only; expressions remain unresolved. Does not resolve arbitrary node parameters, URLs, environment variables, custom/community-node references, access rights or encryption. No n8n server execution/import, credential decryption, copying, activation or API calls. Relocated output is always active:false and cannot overwrite an existing file. Exports and reports can contain sensitive names/parameters; keep real files private.

Export metadata shape reviewed at n8n commit 9a489b65ed539a042e819012558cfc6985aab78d, interfaces.ts blob e31059c38296d46c7d0361378d61a0dc99644d5f; current release observed n8n@2.44.6. File-format tests only; live server imports are untested.

No runtime dependencies. Recheck export shape and newly managed credential slots against pinned upstream types before broadening support. n8n is fair-code/Sustainable Use licensed with enterprise exclusions, not a permissively licensed dependency. No n8n source, branding or code is bundled; the original interoperable tool is MIT.

## Verify

```sh
python -m unittest -v
python -m compileall -q .
python -m pip wheel --no-deps -w dist .
python -m venv /tmp/n8n-relocation-plan-check
/tmp/n8n-relocation-plan-check/bin/python -m pip install dist/*.whl
/tmp/n8n-relocation-plan-check/bin/python verify_installed.py
```

The installed check executes the real console command from a temporary working
directory and checks malformed-input exit behavior. CI repeats tests and clean
installation on Python 3.11/3.13, then runs a vulnerability audit. See
[validation coverage](VALIDATION.md) for tested behavior and remaining limits.

## Why this project

Existing generic JSON diff tools and agent-sbom do not perform typed n8n reference relocation with stale-plan rejection. This is one complete file-transformation workflow, not a general migration platform.

n8n supplies export/import; n8n Backup Manager backs up/restores instances and snapshots; n8n-porter migrates resources with server configuration and credential payloads. This tool requires neither server/API access nor credential data and binds a reviewable plan to the exact input documents. No claim that the other tools lack all equivalent safeguards.

[Research and alternatives](RESEARCH.md) records dated sources, stars, licenses,
maintenance observations and demand limits. No adoption or performance advantage
is claimed. Original code and invented fixtures, developed with AI assistance.
No affiliation with or endorsement by the upstream project is implied.

[License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Brief](BRIEF.json)
