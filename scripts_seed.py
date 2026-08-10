import json
from pathlib import Path

from atlas_of_ideas.models import SourceDocument

SEED = [
    SourceDocument(
        id="science-time",
        title="Science note on entropy and time",
        author="Demo corpus",
        domain="science",
        text=(
            "Entropy is often used to characterize irreversible macroscopic change. "
            "Discussions of the arrow of time connect thermodynamics to questions "
            "about why past and future appear physically asymmetric."
        ),
    ),
    SourceDocument(
        id="philosophy-time",
        title="Philosophy note on duration",
        author="Demo corpus",
        domain="philosophy",
        text=(
            "Philosophical accounts of duration ask whether lived time can be reduced "
            "to measured succession, and how memory changes the experience of the present."
        ),
    ),
    SourceDocument(
        id="spirituality-impermanence",
        title="Spirituality note on impermanence",
        author="Demo corpus",
        domain="spirituality",
        text=(
            "Impermanence describes the instability of conditioned phenomena and invites "
            "attention to change as a basic feature of experience."
        ),
    ),
]

out = Path("data/raw/seed.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    json.dumps([item.model_dump() for item in SEED], ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"Wrote {out}")
