from flask import Blueprint, Request, Response, request as flask_request
from flask_restful import Resource
from marshmallow import Schema
from marshmallow.utils import missing
from typing import Any, Dict, List, Optional, Union
from webargs.flaskparser import parser, use_kwargs
from webargs.multidictproxy import MultiDictProxy

from src.typing import ChecksumAVAXAddress
from src.api.app import cache
from src.api.rest import RestAPI
from src.api.v1.encoding import (
    NFTsUserSchema,
    PostVaultSchema,
    GetVaultsSchema,
)

def _combine_parser_data(
        data_1: MultiDictProxy,
        data_2: MultiDictProxy,
        schema: Schema,
) -> MultiDictProxy:
    if data_2 is not missing:
        if data_1 == {}:
            data_1 = MultiDictProxy(data_2, schema)
        else:
            all_data = data_1.to_dict() if isinstance(data_1, MultiDictProxy) else data_1
            for key, value in data_2.items():
                all_data[key] = value
            data_1 = MultiDictProxy(all_data, schema)
    return data_1

@parser.location_loader('json_and_view_args')  # type: ignore
def load_json_viewargs_data(request: Request, schema: Schema) -> Dict[str, Any]:
    """Load data from a request accepting either json or view_args encoded data"""
    view_args = parser.load_view_args(request, schema)  # type: ignore
    data = parser.load_json(request, schema)
    if data is missing:
        return data

    data = _combine_parser_data(data, view_args, schema)
    return data

@parser.location_loader('json_and_query')  # type: ignore
def load_json_query_data(request: Request, schema: Schema) -> Dict[str, Any]:
    """Load data from a request accepting either json or query encoded data"""
    data = parser.load_json(request, schema)
    if data is not missing:
        return data
    return parser.load_querystring(request, schema)  # type: ignore

@parser.location_loader('json_and_query_and_view_args')  # type: ignore
def load_json_query_viewargs_data(request: Request, schema: Schema) -> Dict[str, Any]:
    """Load data from a request accepting either json or querystring or view_args encoded data"""
    view_args = parser.load_view_args(request, schema)  # type: ignore
    # Get data either from json or from querystring
    data = parser.load_json(request, schema)
    if data is missing:
        data = parser.load_querystring(request, schema)  # type: ignore

    if data is missing:
        return data

    data = _combine_parser_data(data, view_args, schema)
    return data

def create_blueprint() -> Blueprint:
    # Take a look at this SO question on hints how to organize versioned
    # API with flask:
    # http://stackoverflow.com/questions/28795561/support-multiple-api-versions-in-flask#28797512
    return Blueprint('v1_resources', __name__)

def cache_key():
    url_args = flask_request.args
    args = "?"
    args += '&'.join(
        f"{item[0]}={item[1]}" for item in url_args.items()
    )
    if args != "?":
        return flask_request.base_url+args
    return flask_request.base_url

class BaseResource(Resource):
    def __init__(self, rest_api_object: RestAPI, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.rest_api = rest_api_object

class NFTsUserResource(BaseResource):
    get_schema = NFTsUserSchema()

    @cache.cached(timeout=60, key_prefix=cache_key)
    @use_kwargs(get_schema, location='json_and_query_and_view_args')
    def get(self, chainID: str, address: str) -> Response:
        return self.rest_api.getnfts(address, chainID)

class VaultResource(BaseResource):
    get_schema = NFTsUserSchema()

    @cache.cached(timeout=60, key_prefix=cache_key)
    @use_kwargs(get_schema, location='json_and_query_and_view_args')
    def get(self, chainID: str, address: str) -> Response:
        return self.rest_api.getVault(address=address, chainID=chainID)
    
    post_schema = PostVaultSchema()
    @use_kwargs(post_schema, location='json')
    def post(self,
            chainID: str,
            name: str,
            symbol: str,
            supply: str,
            price: int,
            fee: int,
            contract_address: str,
            curator_address: str,
            nfts: List[Dict[str, Any]],
    ) -> Response:
        vault = {
            "name": name,
            "symbol": symbol,
            "supply": supply,
            "price": price,
            "fee": fee,
            "contract_address": contract_address,
            "curator_address": curator_address,
            "nfts": nfts,
        }
        return self.rest_api.insert_vault(chainID=chainID, vault=vault)        

class VaultsResource(BaseResource):
    get_schema = GetVaultsSchema()
    
    @cache.cached(timeout=60, key_prefix=cache_key)
    @use_kwargs(get_schema, location='json_and_query_and_view_args')
    def get(self, chainID: str, page: int, perpage: int) -> Response:
        return self.rest_api.getVaults(chainID=chainID, page=page, perpage=perpage)