import json
import logging

from flask import Response, make_response
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from src.api_functions import Api_functions
from src.logging import LogsAdapter
from src.typing import ChecksumAVAXAddress

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

def _wrap_in_ok_result(result: Any) -> Dict[str, Any]:
    return {'result': result, 'message': ''}

def _wrap_in_result(result: Any, message: str) -> Dict[str, Any]:
    return {'result': result, 'message': message}

def wrap_in_fail_result(message: str, status_code: Optional[HTTPStatus] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {'result': None, 'message': message}
    if status_code:
        result['status_code'] = status_code

    return result

def api_response(
        result: Dict[str, Any],
        status_code: HTTPStatus = HTTPStatus.OK,
) -> Response:
    if status_code == HTTPStatus.NO_CONTENT:
        assert not result, "Provided 204 response with non-zero length response"
        data = ""
    else:
        data = json.dumps(result)
        
    return make_response(
        (data, status_code, {"mimetype": "application/json", "Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}),
    )

class RestAPI():
    def __init__(self, api_functions: Api_functions) -> None:
        self.api_functions = api_functions
    
    def getnfts(self, address: ChecksumAVAXAddress, chainID: str) -> Dict[str, Any]:
        return api_response(_wrap_in_ok_result(self.api_functions.get_nfts_user(address, chainID)))