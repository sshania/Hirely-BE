from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware

# Logging Middleware
async def log_requests(request: Request, call_next):
    print(f"Request URL: {request.url}")
    response = await call_next(request)
    print(f"Response Status Code: {response.status_code}")
    return response
