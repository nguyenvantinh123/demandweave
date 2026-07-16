from abc import ABC,abstractmethod
class Connector(ABC):
    name:str;version:str="1.0"
    @abstractmethod
    async def healthcheck(self)->bool:...
    @abstractmethod
    async def fetch_signals(self)->list[dict]:...
    async def push_result(self,result:dict)->None:return None
class AIAdapter(ABC):
    name:str
    @abstractmethod
    async def extract_signal(self,text:str)->dict:...
    @abstractmethod
    async def explain_opportunity(self,data:dict)->str:...
class MockAIAdapter(AIAdapter):
    name="mock"
    async def extract_signal(self,text:str)->dict:return {"title":text,"confidence":.5}
    async def explain_opportunity(self,data:dict)->str:return f"Opportunity compiled from {len(data.get('evidence',[]))} evidence signals."
