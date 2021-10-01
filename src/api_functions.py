import json
import logging
import os
import requests

from ethlite.Contracts import Contract
from json.decoder import JSONDecodeError
from html.parser import HTMLParser
from queue import Queue
from threading import Thread
from typing import Any, Dict, List, Optional

from src.constants.constants import NETWORK_RPC, NFTINDEX_ADDRESS
from src.externalApis.covalent import Covalent
from src.logging import configure_logging, LogsAdapter
from src.typing import ChecksumAVAXAddress

logger = logging.getLogger(__name__)
log = LogsAdapter(logger)

PATH_ABS = os.path.abspath(".")
PATH_SRC = os.path.join(PATH_ABS, 'src')
PATH_CONST = os.path.join(PATH_SRC, 'constants')
PATH_ABI = os.path.join(PATH_CONST, 'ABI')
PATH_NFTINDEX_ABI = os.path.join(PATH_ABI, 'NFTIndex_ABI.json')

def format_to_dict(value, image, contracts):
    # Get name symbol and address for nft by address in result request in covalent
    contract_nft = list(filter(lambda x: x["contract_address"] == value[0], contracts))
    return {
        "address": value[0],
        "name": contract_nft[0]["contract_name"],
        "symbol": contract_nft[0]["contract_ticker_symbol"],
        "tokenId": value[1],
        "ImageURL": image,
        "URI": value[2],
    }

class Api_functions():
    def __init__(self, args):
        self.args = args
        configure_logging(args)
        with open(PATH_NFTINDEX_ABI) as file:
            self.nftindex_abi = json.load(file)
    
    def _patch(self, address: ChecksumAVAXAddress, chainID: str) -> List[Optional[Dict[str, Any]]]:
        #This function extract tokens of address via avalanche explorer instead of using covalent because it's slow
        class MyHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs= True
                self.texts = []

            def handle_data(self, data):
                self.texts.append(data.replace("\n",""))
                
            def get_data(self):
                return self.texts
            
        if(chainID == "43113"):
            url = f"https://cchain.explorer.avax-test.network/address/{address}/tokens?type=JSON"
        else:
            url = f"https://cchain.explorer.avax.network/address/{address}/tokens?type=JSON"
            
        response = requests.get(url)
        if (response.status_code != 200):
            return []
        try: 
            data = response.json()
            if (len(data["items"]) == 0):
                return []
            items = []
            for item in data["items"]:
                parser = MyHTMLParser()
                parser.feed(item)
                data_items = parser.get_data()
                if (data_items[5].startswith("ERC-721")):
                    index_0x = data_items[5].find("0x")
                    address = data_items[5][index_0x:]
                    name = data_items[3].replace(" ","")
                    index_space = data_items[9].find(" ")
                    symbol = data_items[9][index_space:].replace(" ","")
                    items.append({
                        "contract_address": address,
                        "contract_name": name,
                        "contract_ticker_symbol": symbol,
                    })
            return items
        except:
            return []
    
    def _parallel_requests(self, nfts_user: Any, contracts: Any, no_workers: int) -> List[str]:
        """ This fuction get image from token uri
            Base code 
            https://towardsdatascience.com/parallel-web-requests-in-python-4d30cc7b8989
        """
        class Worker(Thread):
            def __init__(self, request_queue: Queue):
                Thread.__init__(self)
                self.queue = request_queue
                self.results = []

            def run(self):
                while True:
                    content = self.queue.get()
                    if content == "":
                        break
                    
                    uri = content[2]
                    image = None
                    try:
                        r = requests.head(uri)
                    except:
                        image = ""
                    
                    if (image is None):
                        if (r.headers["content-type"].startswith("image")):
                            image = uri
                        else:
                            try:
                                response = requests.get(uri)
                                data = response.json()
                                image = data["image"]
                            except:
                                image = ""
                    
                    self.results.append(format_to_dict(content, image, contracts))
                    self.queue.task_done()
        
         # Create queue and add urls         
        q = Queue()
        for nft_user in nfts_user:
            q.put(nft_user)
            
        # Create workers and add tot the queue
        workers = []
        for _ in range(no_workers):
            worker = Worker(q)
            worker.start()
            workers.append(worker)
        # Workers keep working till they receive an empty string
        for _ in workers:
            q.put("")
        # Join workers to wait till they finished
        for worker in workers:
            worker.join()

        # Combine results from all workers
        r = []
        for worker in workers:
            r.extend(worker.results)
        return r
    
    def get_nfts_user(self, address: ChecksumAVAXAddress, chainID: str = "43114") -> Dict[str, Any]:
        # Covalent is disabled as it goes through instabilities
        # covalent = Covalent(chainID)
        # result = covalent.get_nft_balances_address(address)
        
        # Temporary function to replace the covalent
        result = self._patch(address, chainID)
        
        if len(result) == 0:
            return {"address": address, "chainID": chainID, "items": []}
        
        nftindex_contract = Contract(
            self.nftindex_abi, 
            address=NFTINDEX_ADDRESS[chainID],
            jsonrpc_provider=NETWORK_RPC[chainID],
        )
        # List of addresses of nft contracts  
        nfts_contracts_address = list(map(lambda x: x["contract_address"], result))
        # Get nfts uris by NFT INDEX contract
        nfts_user = nftindex_contract.functions.getNFTsIndexAndUrl(nfts_contracts_address, address)
        
        items = self._parallel_requests(nfts_user, result, 16)
        
        return {"address": address, "chainID": chainID, "items": items}
