"""RQ3.1-local inherited renderer plus contrastive representation projections.

The inherited files were copied from the frozen RQ2.1 renderer before RQ3.1
changes.  See the stage-1 representation report for exact parent/tree hashes.
"""

from .contrast import (  # noqa: F401
    RepresentationCapacityError,
    RepresentationError,
    project_compact_comparative_text,
    project_natural_text,
    render_contrast_dashboard,
    render_standard_dashboard,
    render_text_screenshot,
)
