import logging
import os
import signal

from src.api.server import APIServer, RestAPI
from src.args import app_args
from src.logging import LogsAdapter
from src.api_functions import Api_functions

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

class No_covalent_key(Exception):
    def __str__(self):
        return "No gived covalent key on env/args"

class Server():
    def __init__(self) -> None:
        """Initializes the backend server
        May raise:
        - SystemPermissionError due to the given args containing a datadir
        that does not have the correct permissions
        """
        arg_parser = app_args(
            prog='api-fractional-art',
            description=(
                'Fractional Art api, tracker for nfts ands vaults'
            ),
        )
        self.args = arg_parser.parse_args()
        
        covalent_key = os.environ.get('COVALENT_KEY', "")
        if (self.args.covalent_key != ""):
            os.environ["COVALENT_KEY"] = self.args.covalent_key

        if (covalent_key == "" and self.args.covalent_key == ""):
            raise No_covalent_key()
        
        
        self.api_functions = Api_functions(self.args)
        self.api_server = APIServer(
            rest_api=RestAPI(api_functions=self.api_functions),
        )
        
    def shutdown(self) -> None:
        log.debug('Shutdown initiated')
        self.api_server.stop()
    
    def main(self) -> None:
        self.api_server.start(
            host=self.args.api_host,
            port=self.args.rest_api_port,
        )
        
    def run_local(self) -> None:
        self.api_server.run(
            host=self.args.api_host,
            port=self.args.rest_api_port,
        )    
        
    def run_heroku(self) -> None:
        self.api_server.run_heroku()
