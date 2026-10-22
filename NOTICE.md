# Third-party tools

reconkit is an **orchestrator**. It does not contain or redistribute the source
code of the tools below — it invokes them as separate processes at runtime, and
each must be installed independently by the user. This keeps reconkit MIT while
respecting each upstream license.

| Tool | Upstream | License | Invoked as |
|---|---|---|---|
| sherlock | github.com/sherlock-project/sherlock | MIT | subprocess |
| maigret | github.com/soxoj/maigret | MIT | subprocess (planned) |
| holehe | github.com/megadose/holehe | GPL-3.0 | subprocess |
| theHarvester | github.com/laramies/theHarvester | GPL-2.0 | subprocess |
| subfinder | github.com/projectdiscovery/subfinder | MIT | subprocess |

**Why this matters:** GPL's copyleft attaches when you *link or include* GPL
code in your own program. Calling a GPL binary as an independent subprocess is
"mere aggregation" and does not impose GPL on reconkit. If you ever `import` a
GPL tool's Python modules directly instead of shelling out, reconkit would have
to become GPL too — so keep GPL tools behind the subprocess boundary.

## On X-osint (github.com/TermuxHackz/X-osint, GPL-3.0)

reconkit's interactive menu and its native `phone`, `exif`, `dns`, and `ipinfo`
modules were **inspired by** X-osint's feature set and menu-driven UX, but were
written from scratch against public libraries (`phonenumbers`, `Pillow`, Python
stdlib, ip-api.com). No X-osint source code is copied or included, so reconkit
remains MIT. Credit to X-osint by AnonyminHack5 for the original concept. If you
prefer to literally reuse X-osint's code, relicense this whole project GPL-3.0.

