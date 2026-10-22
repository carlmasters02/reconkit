"""Importing this package registers all bundled modules.
Add a new tool by dropping a <tool>_mod.py here and importing it below."""

# subprocess wrappers (external CLIs)
from . import sherlock_mod      # noqa: F401
from . import holehe_mod        # noqa: F401
from . import subfinder_mod     # noqa: F401
from . import theharvester_mod  # noqa: F401

# native modules (Python libs) — X-osint-style breadth
from . import phone_mod         # noqa: F401
from . import exif_mod          # noqa: F401
from . import dns_mod           # noqa: F401
from . import ip_mod            # noqa: F401
