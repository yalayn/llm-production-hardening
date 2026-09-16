"""The kill switch.

If stopping a misbehaving feature requires shipping a release, it is not a kill
switch. So the variable is read on every call rather than captured at import: a
value read once needs a restart to take effect, and a restart is a deployment
with extra steps.
"""

import os
from typing import Mapping, Optional

ENV_VAR = "LLM_EXTRACTION_ENABLED"

# Explicit, because "false" and "0" are both truthy strings in Python and a
# plain truthiness check would leave the switch permanently on.
OFF_VALUES = frozenset({"0", "false", "no", "off"})


def extraction_enabled(environ: Optional[Mapping[str, str]] = None) -> bool:
    """True unless the variable says otherwise.

    On by default: the switch exists to stop something in an emergency, and
    forgetting to set it must not be what takes the feature down.

    An unrecognised value also leaves it on, deliberately. A typo causing an
    outage is a worse failure than a typo failing to prevent one.
    """
    env = os.environ if environ is None else environ
    raw = env.get(ENV_VAR)
    if raw is None:
        return True
    return raw.strip().lower() not in OFF_VALUES
