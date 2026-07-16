import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import time,random
from apps.api.app.services.normalize import parse_natural_signal
for n in (1000,10000,100000):
    t=time.perf_counter()
    for i in range(n):parse_natural_signal(f"Cần mua {random.randint(100,50000)} cốc giấy tại Bắc Ninh")
    elapsed=time.perf_counter()-t
    print({"signals":n,"seconds":round(elapsed,4),"signals_per_second":round(n/elapsed,1)})
