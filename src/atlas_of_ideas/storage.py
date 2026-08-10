import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .models import CandidateRelation, Concept, Passage, Relation, SourceDocument, Workspace

T = TypeVar("T", bound=BaseModel)


class WorkspaceStore:
    def __init__(self, root: str | Path = "data/workspaces"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def workspace_dir(self, workspace_id: str) -> Path:
        path = self.root / workspace_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_workspaces(self) -> list[Workspace]:
        result: list[Workspace] = []
        for path in sorted(self.root.glob("*/workspace.json")):
            try:
                result.append(Workspace.model_validate_json(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return result

    def create_workspace(self, workspace: Workspace) -> None:
        self._save_model(workspace.id, "workspace.json", workspace)

    def load_workspace(self, workspace_id: str) -> Workspace | None:
        path = self.workspace_dir(workspace_id) / "workspace.json"
        if not path.exists():
            return None
        return Workspace.model_validate_json(path.read_text(encoding="utf-8"))

    def save_documents(self, workspace_id: str, items: list[SourceDocument]) -> None:
        self._save_list(workspace_id, "documents.json", items)

    def load_documents(self, workspace_id: str) -> list[SourceDocument]:
        return self._load_list(workspace_id, "documents.json", SourceDocument)

    def save_passages(self, workspace_id: str, items: list[Passage]) -> None:
        self._save_list(workspace_id, "passages.json", items)

    def load_passages(self, workspace_id: str) -> list[Passage]:
        return self._load_list(workspace_id, "passages.json", Passage)

    def save_concepts(self, workspace_id: str, items: list[Concept]) -> None:
        self._save_list(workspace_id, "concepts.json", items)

    def load_concepts(self, workspace_id: str) -> list[Concept]:
        return self._load_list(workspace_id, "concepts.json", Concept)

    def save_candidates(self, workspace_id: str, items: list[CandidateRelation]) -> None:
        self._save_list(workspace_id, "candidates.json", items)

    def load_candidates(self, workspace_id: str) -> list[CandidateRelation]:
        return self._load_list(workspace_id, "candidates.json", CandidateRelation)

    def save_relations(self, workspace_id: str, items: list[Relation]) -> None:
        self._save_list(workspace_id, "relations.json", items)

    def load_relations(self, workspace_id: str) -> list[Relation]:
        return self._load_list(workspace_id, "relations.json", Relation)

    def _save_model(self, workspace_id: str, filename: str, item: BaseModel) -> None:
        path = self.workspace_dir(workspace_id) / filename
        path.write_text(item.model_dump_json(indent=2), encoding="utf-8")

    def _save_list(self, workspace_id: str, filename: str, items: list[BaseModel]) -> None:
        path = self.workspace_dir(workspace_id) / filename
        payload = [item.model_dump(mode="json") for item in items]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_list(self, workspace_id: str, filename: str, cls: type[T]) -> list[T]:
        path = self.workspace_dir(workspace_id) / filename
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [cls.model_validate(item) for item in raw]
