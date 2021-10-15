import json
import logging
import os
import requests

from datauri import DataURI
from ethlite.Contracts import Contract
from json.decoder import JSONDecodeError
from html.parser import HTMLParser
from queue import Queue
from threading import Thread
from typing import Any, Dict, List, Optional

from src.api.app import db
from src.constants.constants import NETWORK_RPC, VAULT_FACTORY_ADDRESS
from src.database.Model import db_insert, db_query_filter, db_query_filter_pag, Vault
from src.externalApis.covalent import Covalent
from src.logging import configure_logging, LogsAdapter
from src.typing import ChecksumAVAXAddress

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

class Api_functions():
    def __init__(self, args):
        self.args = args
        configure_logging(args)

    def get_nfts_user(self, address: ChecksumAVAXAddress, chainID: str = "43114") -> Dict[str, Any]:
        result = None
        covalent = Covalent(chainID)
        result = covalent.get_nft_balances_address(address)

        if (result is None or len(result) == 0):
            return {"address": address, "chainID": chainID, "items": []}

        items = []
        for nft in result:
            if (int(nft["balance"]) > 0 and ("nft_data" in nft)):
                for nftdata in nft["nft_data"]:
                    image = ""
                    if ("token_url" in nftdata) and nftdata["token_url"].startswith("data:"):
                        try:
                            uri = DataURI(nftdata["token_url"])
                            if (uri.mimetype.startswith("image")):
                                image = uri.data
                            elif (uri.mimetype.startswith("application/json")):
                                json_dict = json.loads(uri.data)
                                if ("image" in json_dict):
                                    image = json_dict["image"]
                        except:
                            image = ""
                    elif ("external_data" in nftdata) and ("image" in nftdata["external_data"]):
                        image = nftdata["external_data"]["image"]
                    try:
                        items.append({
                            "address": nft["contract_address"],
                            "name": nft["contract_name"],
                            "symbol": nft["contract_ticker_symbol"],
                            "tokenId": nftdata["token_id"],
                            "ImageURL": image,
                            "URI": nftdata["token_url"],
                        })
                    except:
                        continue
        return {"address": address, "chainID": int(chainID), "items": items}

    def getVaults(self, chainID: str = "43114", page: int = 1, perpage: int = 15):
        vaults = db_query_filter_pag(Vault, Vault.chainId==chainID, page, perpage)
        list_vaults = list(map(lambda item: item.deserialize(), vaults.items))
        return {
            "chainId": int(chainID),
            "vaults": list_vaults,
            "pagination": {
                "has_next": vaults.has_next,
                "has_prev": vaults.has_prev,
                "page": vaults.page,
                "per_page": vaults.per_page,
                "total": vaults.total
            }
        }

    def query_vault(self, address: ChecksumAVAXAddress, chainID: str = "43114") -> Optional[Vault]:
        """Get Vault in db by address

        Args:
            address (ChecksumAVAXAddress): eth address (0x56A....)
            chainID (str, optional): eth chain id (main net: 43114 and test net: 43113). Defaults to "43114".

        Returns:
            Optional[Vault]: return Vault if exist else return None
        """
        vault = db_query_filter(Vault, Vault.contract_address==address and Vault.chainId==chainID)
        if len(vault) != 1:
            return None
        return vault[0]

    def getVault(self, address: ChecksumAVAXAddress, chainID: str = "43114"):
        vault = self.query_vault(address, chainID)
        if vault:
            return {
                "chainId": int(chainID),
                "vault": vault.deserialize(),
            }
        return {
            "chainId": int(chainID),
            "vault": {},
        } 

    def insertVault(self, vault: Dict[str, Any], chainID: str = "43114") -> bool:
        covalent = Covalent(chainID)

        # Check if exist this vault in db
        result = self.query_vault(vault["contract_address"], chainID)
        if (result):
            return False, "Vault already exist in the db!"
    
        # Check if not exist this vault in contract by logs events in transactions
        result = covalent.get_transaction_by_vault_address(
            address = VAULT_FACTORY_ADDRESS[chainID], 
            vault = vault["contract_address"],
        )
        if (len(result) != 1):
            return False, "Vault not exist!"
        
        log.debug("Insert new vault: "+str(vault))
        try:
            vault_object = Vault(
                name = vault["name"], 
                symbol = vault["symbol"],
                supply = vault["supply"],
                price = vault["price"],
                fee = vault["fee"],
                contract_address = vault["contract_address"],
                curator_address = vault["curator_address"],
                description = "",
                verified = 0,
                nfts = json.dumps(vault["nfts"]),
                chainId = int(chainID),
            )
            db_insert(vault_object)
        except Exception as e:
            log.warning(f"Error in insert vault: {e}")
            return False, "Error"
        return True, "Created"
