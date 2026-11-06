"""Runtime paths and source/output boundary checks."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRODUCTION=ROOT
def project_path(path):
 path=Path(path).expanduser().resolve()
 if path==ROOT or path.is_relative_to(ROOT):raise ValueError('Project output must be outside the application folder')
 return path
