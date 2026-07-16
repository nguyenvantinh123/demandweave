from datetime import datetime
from pydantic import BaseModel, Field

class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=10)
    tenant_name: str = Field(min_length=2)
class LoginIn(BaseModel): email:str; password:str
class TokenOut(BaseModel): access_token:str; token_type:str="bearer"; tenant_id:int

class ParticipantIn(BaseModel):
    participant_type:str
    display_name:str
    legal_name:str=""
    location:str=""
    latitude:float|None=None
    longitude:float|None=None
    verification_level:str="unverified"
    trust_score:float=Field(default=.5,ge=0,le=1)
    response_score:float=Field(default=.5,ge=0,le=1)
    delivery_score:float=Field(default=.5,ge=0,le=1)
    quality_score:float=Field(default=.5,ge=0,le=1)
    financial_capacity:float=0
    contact:dict=Field(default_factory=dict)
    capabilities:list[str]=Field(default_factory=list)
class ParticipantOut(ParticipantIn):
    id:int
    model_config={"from_attributes":True}

class SignalIn(BaseModel):
    participant_id:int
    signal_type:str
    title:str
    natural_language_input:str=""
    normalized_category:str
    attributes:dict=Field(default_factory=dict)
    quantity:float=0
    unit:str="unit"
    price_min:float=0
    price_max:float=0
    currency:str="VND"
    location:str=""
    confidence:float=Field(default=.7,ge=0,le=1)
    verification_status:str="unverified"
    visibility_scope:str="aggregated"
    source:str="manual"
class NaturalSignalIn(BaseModel): participant_id:int; text:str=Field(min_length=8); visibility_scope:str="aggregated"

class SimulationIn(BaseModel):
    unit_sale_price:float
    unit_variable_cost:float
    fixed_cost:float=0
    conversion_rate:float=Field(default=.6,ge=0,le=1)
    demand_uncertainty:float=Field(default=.2,ge=0,le=1)
    cost_uncertainty:float=Field(default=.1,ge=0,le=1)
    defect_rate:float=Field(default=.02,ge=0,le=.5)
    return_rate:float=Field(default=.01,ge=0,le=.5)
    marketing_cost:float=0
    tax_rate:float=Field(default=0,ge=0,le=1)
    iterations:int=Field(default=3000,ge=200,le=50000)

class ExperimentIn(BaseModel):
    opportunity_id:int
    title:str
    hypothesis:str
    success_metric:str
    failure_metric:str=""
    budget_limit:float=0
    time_limit_days:int=Field(default=14,ge=1,le=365)
    action_plan:list[str]=Field(default_factory=list)
class ExperimentResultIn(BaseModel): observations:list[dict]=Field(default_factory=list); result:dict=Field(default_factory=dict)

class MandateIn(BaseModel):
    opportunity_id:int|None=None
    allowed_actions:list[str]
    forbidden_actions:list[str]=Field(default_factory=list)
    approved_participants:list[int]=Field(default_factory=list)
    budget_limit:float=0
    max_actions:int=Field(default=20,ge=1,le=1000)
    expires_at:datetime
class MandateActionIn(BaseModel): action:str; amount:float=0; participant_id:int|None=None
