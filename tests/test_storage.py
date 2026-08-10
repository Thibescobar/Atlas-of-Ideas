from atlas_of_ideas.models import Workspace
from atlas_of_ideas.storage import WorkspaceStore


def test_workspace_roundtrip(tmp_path):
    store = WorkspaceStore(tmp_path)
    workspace = Workspace(id="demo", name="Demo")
    store.create_workspace(workspace)
    loaded = store.load_workspace("demo")
    assert loaded is not None
    assert loaded.name == "Demo"
