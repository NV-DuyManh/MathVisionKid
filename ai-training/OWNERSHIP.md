# Ownership Boundary

This directory (`ai-training/`) is primarily owned by the AI/ML team member.

Main application developers and Antigravity should not rewrite model-training experiments or annotation data without coordination.

Allowed integration work later:
- reading model manifests
- adapting FastAPI inference loader
- validating exported model compatibility
- updating integration documentation

Do not automatically modify training experiments during unrelated backend/frontend phases.
