import gevent
import json
import logging
import os
import werkzeug

from http import HTTPStatus
from flask import Flask, Response, request
from flask_restful import Api, Resource, abort
from gevent.pywsgi import WSGIServer
from marshmallow import Schema
from marshmallow.exceptions import ValidationError
from typing import Any, Dict, List, Optional, Tuple, Union
from webargs.flaskparser import parser
from werkzeug.exceptions import NotFound

from src.logging import LogsAdapter
from src.api.app import app
from src.api.rest import RestAPI, api_response, wrap_in_fail_result
from src.api.v1.parser import resource_parser
from src.api.v1.resources import (
    NFTsUserResource,
    VaultResource,
    VaultsResource,
    create_blueprint,
)

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

URLS = [
    ('/getNftsUser', NFTsUserResource),
    (
        '/<string:chainID>/getNftsUser/<string:address>', 
        NFTsUserResource, 
        "named_getNftsUser_resource"
    ),
    ('/vault', VaultResource),
    (
        '/<string:chainID>/vault', 
        VaultResource, 
        "named_vault_resource"
    ),
    ('/vaults', VaultsResource),
    (
        '/<string:chainID>/vaults', 
        VaultsResource, 
        "named_vaults_resource"
    ),
]

def setup_urls(
        flask_api_context: Api,
        rest_api: RestAPI,
        urls,
) -> None:
    for url_tuple in urls:
        if len(url_tuple) == 2:
            route, resource_cls = url_tuple  # type: ignore
            endpoint = resource_cls.__name__.lower()
        elif len(url_tuple) == 3:
            route, resource_cls, endpoint = url_tuple  # type: ignore
        else:
            raise ValueError(f"Invalid URL format: {url_tuple!r}")
        flask_api_context.add_resource(
            resource_cls,
            route,
            resource_class_kwargs={"rest_api_object": rest_api},
            endpoint=endpoint,
        )

def endpoint_not_found(e: 'NotFound') -> Response:
    # The isinstance check is because I am not sure if `e` is always going to
    # be a "NotFound" error here
    msg = e.description if isinstance(e, NotFound) else 'invalid endpoint'
    return api_response(wrap_in_fail_result(msg), HTTPStatus.NOT_FOUND)

@parser.error_handler  # type: ignore
@resource_parser.error_handler
def handle_request_parsing_error(
        err: ValidationError,
        _request: werkzeug.local.LocalProxy,
        _schema: Schema,
        error_status_code: Optional[int],  # pylint: disable=unused-argument
        error_headers: Optional[Dict],  # pylint: disable=unused-argument
) -> None:
    """ This handles request parsing errors generated for example by schema
    field validation failing."""
    msg = str(err)
    if isinstance(err.messages, dict):
        # first key is just the location. Ignore
        key = list(err.messages.keys())[0]
        msg = json.dumps(err.messages[key])
    elif isinstance(err.messages, list):
        msg = ','.join(err.messages)

    abort(HTTPStatus.BAD_REQUEST, result=None, message=msg)


async def start_server(wsgiserver: WSGIServer) -> None:
    wsgiserver.serve_forever()
    
class APIServer():
    
    def __init__(
            self,
            rest_api: RestAPI,
    ) -> None:
        flask_app = app
        blueprint_v1 = create_blueprint()
        flask_api_context = Api(blueprint_v1)
        setup_urls(
            flask_api_context=flask_api_context,
            rest_api=rest_api,
            urls=URLS,
        )
        self.rest_api = rest_api
        self.flask_app = flask_app
        
        self.wsgiserver: Optional[WSGIServer] = None
        
        self.blueprint_v1 = blueprint_v1
        self.flask_app.register_blueprint(self.blueprint_v1, url_prefix='/v1')
        
        self.flask_app.errorhandler(HTTPStatus.NOT_FOUND)(endpoint_not_found)
        self.flask_app.register_error_handler(Exception, self.unhandled_exception)

    @staticmethod
    def unhandled_exception(exception: Exception) -> Response:
        """ Flask.errorhandler when an exception wasn't correctly handled """
        log.critical(
            "Unhandled exception when processing endpoint request",
            exc_info=True,
        )
        return api_response(wrap_in_fail_result(str(exception)), HTTPStatus.INTERNAL_SERVER_ERROR)
    
    def run(self, host: str = '127.0.0.1', port: int = 5042, **kwargs: Any) -> None:
        """This is only used for the data faker and not used in production"""
        msg = f'REST API server is running at: {host}:{port}'
        print(msg)
        log.info(msg)
        log.info('Local run')
        self.flask_app.run(host=host, port=port, debug=True, **kwargs)
        
    def run_heroku(self) -> None:
        """This is only used  to run in heroku"""
        host = '0.0.0.0'
        port = int(os.environ.get('PORT', 5000))
        self.start(host, port)

    def start(
            self,
            host: str = '127.0.0.1',
            port: int = 5042,
    ) -> None:
        wsgi_logger = logging.getLogger(__name__ + '.pywsgi')
        self.wsgiserver = WSGIServer(
            listener=(host, port),
            application=self.flask_app,
            log=wsgi_logger,
            error_log=wsgi_logger,
        )
        msg = f'REST API server is running at: {host}:{port}'
        print(msg)
        log.info(msg)
        #create server 
        self.wsgiserver.serve_forever()

    def stop(self, timeout: int = 5) -> None:
        """Stops the API server. If handlers are running after timeout they are killed"""
        if self.wsgiserver is not None:
            self.wsgiserver.stop(timeout)
            self.wsgiserver = None
