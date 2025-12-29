__version__ = "0.0.1"

# Apply LMS patches on module import
from education_custom.lms_patches import apply_lms_patches
apply_lms_patches()
