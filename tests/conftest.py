import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
os.environ["DATABASE_URL"]="sqlite:///./test_demandweave.db"
os.environ["JWT_SECRET"]="test-secret-abcdefghijklmnopqrstuvwxyz"
os.environ["MANDATE_SECRET"]="test-mandate-abcdefghijklmnopqrstuvwxyz"
