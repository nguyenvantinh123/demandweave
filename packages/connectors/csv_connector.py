import csv
from pathlib import Path
from apps.api.app.plugins import Connector
class CSVConnector(Connector):
    name="csv";version="1.0"
    def __init__(self,path:str):self.path=Path(path)
    async def healthcheck(self):return self.path.exists()
    async def fetch_signals(self):
        with self.path.open(encoding="utf-8-sig") as f:return list(csv.DictReader(f))
