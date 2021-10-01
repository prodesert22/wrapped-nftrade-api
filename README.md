# Api Fractional Nft
API for tracking NFTs, vaults both information about them and vaults created 

## Install and Run

### Install
1 - install python

2- `pip install -r requirements.tx`

### Run
Production/local    
`python localrun.py <args>`

Normal run  
`python . <args>`

## Supported Chains 

| Name     | ChainID |
|----------|----------|
| Fuji test net   | 43113    |
| Avalanche main Net | 43114    |

## Endpoints
### getNftsUser
`/v1/<chainID>/getNftsUser/<address>`

This endpoint returns a list of nfts of an address entered in a given chain

### Example
`/v1/43113/getNftsUser/0xA8B37246513a9EFF184ab3A936FFB1900334d5f0`
