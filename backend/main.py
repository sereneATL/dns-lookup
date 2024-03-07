import ast
import logging
import random
import string
import time

from fastapi.exceptions import RequestValidationError
import models
import schemas
import dns.resolver
import dns.ipv4
import dns.exception
from config import settings
from database import get_db, Base, engine
from fastapi import Depends, FastAPI, Query, Request, status, params
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import HttpUrl, ValidationError
from sqlalchemy.orm import Session
from typing import List

# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/{settings.API_V1_STR}/openapi.json",
)

# setup prometheus
Instrumentator().instrument(app).expose(app)

# override default validation error body
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    data = ast.literal_eval(exc_str)[0]
    return JSONResponse(status_code=422, content={"message": f"{data['msg']} - {data['loc']}"})

# create middleware to log all requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    
    return response

@app.get(
    "/",
    summary="Get application details",
    description="Provide current date (UNIX epoch), version and indicates if application is running under Kubernetes",
    status_code=status.HTTP_200_OK,
    response_model=schemas.AppDetails,
)
async def root():
    version = settings.VERSION
    date = int(time.time())
    kubernetes = settings.KUBERNETES
    return schemas.AppDetails(
        version=version,
        date=date,
        kubernetes=kubernetes
    )

@app.get(
    "/health",
    summary="Perform a Health Check",
    response_description="Return application's health - HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=schemas.HealthCheck,
)
def get_health():
    return schemas.HealthCheck(status="OK")

@app.get(
    "/%s/tools/lookup" % (settings.API_V1_STR),
    tags=["tools"],
    description="Lookup domain and return all IPv4 addresses",
    summary="Lookup domain",
    status_code=status.HTTP_200_OK,
    response_description="OK",
    response_model=schemas.Query,
    responses={404: {"model": schemas.HTTPError}, 400: {"model": schemas.HTTPError}, 422: {"model": schemas.HTTPError}}
)
def lookup(request: Request, db: Session = Depends(get_db), domain: str = Query(..., description="Domain name")):
    # If no provided domain, return 400 bad request
    if not domain:
        return JSONResponse(status_code=400, content={"message": "Domain must be provided"})
    
    try:
        # Attempt to parse the domain as an HTTP URL
        HttpUrl('http://' + domain)
    except ValidationError:
        # Return 400 bad request if domain is not a valid domain name
        return JSONResponse(status_code=400, content={"message": "Domain must be a valid domain name"})

    # Perform DNS lookup
    try:
        # Perform DNS resolution for A records (IPv4 addresses) for the given domain
        answers = dns.resolver.resolve(domain, 'A')
        ipv4_addresses = [str(answer) for answer in answers]
    except dns.resolver.NXDOMAIN:
        return JSONResponse(status_code=404, content={"message": "Domain not found"})
    except dns.resolver.Timeout:
        return JSONResponse(status_code=400, content={"message": "DNS lookup timed out"})
    except dns.resolver.NoAnswer:
        return JSONResponse(status_code=400, content={"message": "No answer from DNS server"})
    except dns.resolver.NoNameservers:
        return JSONResponse(status_code=400, content={"message": "No name servers are available"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})

    if len(ipv4_addresses) == 0:
        return JSONResponse(status_code=404, content={"message": "Domain not found"})
        
    # Log successful query and results in the database
    query_log = models.QueryLog(
        domain=domain,
        addresses=ipv4_addresses,
        client_ip=request.client.host,
    )

    db.add(query_log)
    db.commit()
    db.refresh(query_log)

    # Return the result
    return schemas.Query(
        addresses=[schemas.Address(ip=ip) for ip in ipv4_addresses],         
        client_ip=request.client.host, 
        created_at=query_log.created_at, 
        domain=domain
    )

@app.post(
    "/%s/tools/validate" % (settings.API_V1_STR),
    tags=["tools"],
    description="Simple IP validation",
    summary="Simple IP validation",
    status_code=status.HTTP_200_OK,
    response_description="OK",
    response_model=schemas.ValidateIPResponse,
    responses={400: {"model": schemas.HTTPError}, 422: {"model": schemas.HTTPError}})
async def validate(request: schemas.ValidateIPRequest = params.Body(..., description="IP to validate")):
    try:
        # attempt to validate if ip is ipv4
        dns.ipv4.canonicalize(request.ip)
    except dns.exception.SyntaxError:
        # return false if provided IP is not ipv4
        return schemas.ValidateIPResponse(status=False)
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
    return schemas.ValidateIPResponse(status=True)

@app.get(
    "/%s/history" % (settings.API_V1_STR),
    tags=["history"],
    description="List queries",
    summary="List queries",
    status_code=status.HTTP_200_OK,
    response_description="OK",
    response_model=List[schemas.Query],
    responses={400: {"model": schemas.HTTPError}}
)
async def history(db: Session = Depends(get_db)):
    try: 
        queries: List[models.QueryLog] = db.query(models.QueryLog).order_by(models.QueryLog.created_at.desc()).limit(20)
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": str(e)})
    
    return [schemas.Query(
        addresses=[schemas.Address(ip=ip) for ip in query.addresses],         
        client_ip=query.client_ip, 
        created_at=query.created_at, 
        domain=query.domain
    ) for query in queries]

