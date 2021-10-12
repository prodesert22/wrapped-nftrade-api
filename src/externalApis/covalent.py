import logging
import os

from json.decoder import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple

import requests

from src.logging import LogsAdapter
from src.typing import ChecksumAVAXAddress

CONST_RETRY = 0
DATE_FORMAT_COVALENT = '%Y-%m-%dT%H:%M:%SZ'
COVALENT_QUERY_LIMIT = 200
PAGESIZE = 100

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

class Covalent():
    def __init__(
            self,
            chain_id: str,
    ) -> None:
        self.session = requests.session()
        self.session.headers.update({'User-Agent': 'rotkehlchen'})
        self.chain_id = chain_id

    def _query(
            self,
            module: str,
            action: str,
            address: str = None,
            options: Optional[Dict[str, Any]] = None,
            timeout: Optional[Tuple[int, int]] = 20,
    ) -> Optional[Dict[str, Any]]:
        """Queries Covalent
        May raise:
        - RemoteError if there are any problems with reaching Covalent or if
        an unexpected response is returned
        """
        query_str = f'https://api.covalenthq.com/v1/{self.chain_id}/{action}'
        if address:
            query_str += f'/{address}'
        query_str += f'/{module}/'

        # If exists covalent key in env, it will use it
        KEY = os.environ.get('COVALENT_KEY', "")
        query_str += f'?key={KEY}'

        if options:
            for name, value in options.items():
                query_str += f'&{name}={value}'

        retry = 0
        while retry <= CONST_RETRY:
            log.debug(f'Querying covalent: {query_str}')
            try:
                response = self.session.get(
                    query_str, 
                    timeout= timeout,
                )

            except requests.exceptions.RequestException as e:
                # In timeout retry
                if isinstance(e, requests.exceptions.Timeout):
                    if retry == CONST_RETRY:
                        return None
                    retry += 1
                    continue
                log.warn(f'Covalent API request failed due to {e}')
                return None 

            try:
                result = response.json()
            except JSONDecodeError as e:
                log.warn(
                    f'Covalent API request {response.url} returned invalid '
                    f'JSON response: {response.text}'
                )
                return None

            if response.status_code != 200:
                error_message = result['error_message'] if 'error_message' in result else None
                log.warn(
                    f'Covalent API request {response.url} failed '
                    f'with HTTP status code {response.status_code} and '
                    f'Error message: {error_message} and text',
                    f'{response.text}',
                )
                return None

            # success, break out of the loop and return result
            break
        return result

    def get_nft_balances_address(
            self,
            address: ChecksumAVAXAddress,
    ) -> Optional[List[Dict[str, Any]]]:
        options = {'limit': COVALENT_QUERY_LIMIT, "nft": True, "match": '{type:nft}', 'page-size': PAGESIZE}
        result = self._query(
            module='balances_v2',
            address=address,
            action='address',
            options=options,
        )

        if result is None:
            return None

        try:
            return result["data"]["items"]
        except:
            return []

    def get_transaction_by_vault_address(
        self,
        address: ChecksumAVAXAddress,
        vault: str,
    ) -> bool:
        options = {
            'limit': COVALENT_QUERY_LIMIT, 
            "nft": True, 
            "match": '{log_events.2.decoded.params.3.value:'+vault+'}',
            'page-size': PAGESIZE
        }
        result = self._query(
            module='transactions_v2',
            address=address,
            action='address',
            options=options,
            timeout=60
        )
        try:
            return result["data"]["items"]
        except:
            return []
