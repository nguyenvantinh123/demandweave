from apps.api.app.plugins import Connector
class MockERPConnector(Connector):
    name="mock-erp";version="1.0"
    async def healthcheck(self):return True
    async def fetch_signals(self):return [{"signal_type":"production_capacity","normalized_category":"paper_cups","quantity":100000,"unit":"cup","confidence":.9,"source":"mock-erp"}]
