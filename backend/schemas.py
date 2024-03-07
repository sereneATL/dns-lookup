from typing import List
from pydantic import BaseModel, HttpUrl, ValidationError, validator


class AppDetails(BaseModel):
    version: str
    date: int
    kubernetes: bool

class HealthCheck(BaseModel):
    status: str = "OK"

class ValidateIPRequest(BaseModel):
    ip: str

class ValidateIPResponse(BaseModel):
    status: bool

class Address(BaseModel):
    ip: str

class Query(BaseModel):
    addresses: List[Address]
    client_ip: str
    created_at: int
    domain: str

class HTTPError(BaseModel):
    message: str
