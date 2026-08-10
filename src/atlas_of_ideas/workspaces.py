def workspace_selectbox_index(workspace_ids: list[str], requested_id: str | None) -> int:
    """Map a persisted workspace id to the selectbox index (0 is create)."""
    if requested_id in workspace_ids:
        return workspace_ids.index(requested_id) + 1
    return 0
