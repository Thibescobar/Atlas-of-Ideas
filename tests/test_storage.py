from atlas_of_ideas.models import Workspace
from atlas_of_ideas.storage import WorkspaceStore
from atlas_of_ideas.workspaces import workspace_selectbox_index


def test_workspace_roundtrip(tmp_path):
    store = WorkspaceStore(tmp_path)
    workspace = Workspace(id="demo", name="Demo")
    store.create_workspace(workspace)
    loaded = store.load_workspace("demo")
    assert loaded is not None
    assert loaded.name == "Demo"


def test_created_workspace_becomes_selectbox_selection(tmp_path):
    store = WorkspaceStore(tmp_path)
    store.create_workspace(Workspace(id="new-workspace", name="New"))
    ids = [workspace.id for workspace in store.list_workspaces()]
    assert workspace_selectbox_index(ids, "new-workspace") == 1
