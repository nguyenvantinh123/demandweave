import httpx
class DemandWeaveClient:
    def __init__(self,base_url:str,token:str=""):
        self.base_url=base_url.rstrip('/');self.token=token
    def _headers(self):return {"Authorization":f"Bearer {self.token}"} if self.token else {}
    def login(self,email:str,password:str):
        data=httpx.post(f"{self.base_url}/api/v1/auth/login",json={"email":email,"password":password}).raise_for_status().json();self.token=data["access_token"];return data
    def create_signal(self,participant_id:int,text:str,visibility_scope:str="aggregated"):
        return httpx.post(f"{self.base_url}/api/v1/signals/natural",headers=self._headers(),json={"participant_id":participant_id,"text":text,"visibility_scope":visibility_scope}).raise_for_status().json()
    def compile(self):return httpx.post(f"{self.base_url}/api/v1/opportunities/compile",headers=self._headers()).raise_for_status().json()
    def opportunities(self):return httpx.get(f"{self.base_url}/api/v1/opportunities",headers=self._headers()).raise_for_status().json()
