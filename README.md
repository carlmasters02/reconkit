# reconkit

A unified OSINT orchestrator CLI. One command runs the right best-in-class recon
tools for a given target type (username, email, domain, …) and merges their
output into one JSON or Markdown report.

reconkit does **not** copy or fork those tools. It wraps each one behind a small
plugin and calls it as a subprocess — so the project stays MIT, upstreams keep
their licenses and credit, and adding a tool is ~20 lines.

> ⚠️ **Authorized use only.** Run reconkit against targets you own or have
> written permission to test (CTFs, bug-bounty scope, your own accounts/domains).
> OSINT on people without consent may be illegal in your jurisdiction.

## Install

```bash
git clone https://github.com/carl-masters/reconkit && cd reconkit
pipx install .          # or: pip install -e .
```

Then install the underlying tools you want (reconkit tells you which are missing):

```bash
pipx install sherlock-project holehe theHarvester
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
reconkit doctor         # ✅/❌ per tool
```

## Use

Interactive menu (X-osint style) — just run it with no args:

```bash
reconkit                 # banner + numbered menu: username/email/domain/ip/phone/image
```

Or scripted, one command per target:

```bash
reconkit list                                   # modules + target types
reconkit run johndoe       --type username
reconkit run a@b.com       --type email
reconkit run "+14155552671" --type phone
reconkit run 8.8.8.8       --type ip
reconkit run ./photo.jpg   --type image         # EXIF + GPS
reconkit run example.com   --type domain --md report.md --json report.json
reconkit run example.com   --type domain --only subfinder,theharvester
```

## Modules

| module | kind | target | needs |
|---|---|---|---|
| sherlock | subprocess | username | `sherlock` CLI |
| holehe | subprocess | email | `holehe` CLI |
| subfinder | subprocess | domain | `subfinder` CLI |
| theharvester | subprocess | domain | `theHarvester` CLI |
| dns | native | domain | stdlib |
| phone | native | phone | `phonenumbers` |
| exif | native | image | `Pillow` |
| ipinfo / revdns | native | ip | stdlib + ip-api.com |

`native` modules work out of the box after `pip install .`; `subprocess` modules
need their CLI installed (reconkit reports which via `doctor`).

## Architecture

```
reconkit/
  cli.py              Typer CLI: doctor | list | run
  core/
    schema.py         ReconResult / Finding — the unified output shape
    registry.py       @register plugin registry; shutil.which() install checks
    runner.py         subprocess helper (list args, never shell=True)
  modules/
    sherlock_mod.py   one file per tool — parse its output → Findings
    holehe_mod.py
    subfinder_mod.py
    theharvester_mod.py
```

### Add a tool in 3 steps

1. Create `reconkit/modules/<tool>_mod.py`.
2. Decorate a `run(target)` function with `@register(name, binary, target_types, install_hint)`.
3. Parse the tool's stdout/JSON into `Finding` objects and import it in `modules/__init__.py`.

That's it — `doctor`, `list`, and `run` pick it up automatically.

## Roadmap ideas
- `maigret`, `phoneinfoga`, `amass` modules
- async/parallel module execution
- de-duplication across modules (same email found by two tools → one finding)
- an MCP-server front end so AI agents can call reconkit as a tool
