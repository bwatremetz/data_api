# https://itsjoshcampos.codes/fast-api-api-key-authorization#heading-api-key-middleware
# 

from config import Settings, get_settings

from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from fastapi import Security, HTTPException, Depends
from starlette.status import HTTP_403_FORBIDDEN


api_key_header = APIKeyHeader(name="access_token", auto_error=False)
api_key_query = APIKeyQuery(name="access_token", auto_error=False)


# check API_KEY from settings
async def get_api_key(settings: Settings = Depends(get_settings), 
                      api_key_header: str = Security(api_key_header),
                      api_key_query: str = Security(api_key_query)):

    if api_key_query == settings.API_KEY:
        return api_key_query
    elif api_key_header == settings.API_KEY:
        return api_key_header   
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate API KEY"
        )