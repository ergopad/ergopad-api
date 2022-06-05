import requests, json

from address import Address
from time import sleep

### LOGGING
import logging
level = logging.DEBUG # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=level)

### INIT 
assembler_url = 'http://assembler:8080' 
assembler_url = 'http://localhost:8080'
address = '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG'
initial = ''
bidder = '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG'
step = 1000
start = 1636642258
end = 1636642258
description = 'description...'
autoExtend = ''
auctionFee = 100000000 # .1 erg/1e8 stoshis
token = 'helloworld'
headers = {'Content-Type': 'application/json'}

### MAIN
if __name__ == '__main__':
    template = f"""{{
        val userAddress = fromBase64("{address}")
        val bidAmount = 2000000000
        val endTime = {end}
        val bidDelta = 1000000000
        val startAuction = {{
            OUTPUTS(0).tokens.size > 0 && OUTPUTS(0).R4[Coll[Byte]].getOrElse(INPUTS(0).id) == userAddress &&
            OUTPUTS(0).R5[Int].getOrElse(0) == endTime && OUTPUTS(0).R6[Long].getOrElse(0L) == bidDelta &&
            OUTPUTS(0).R8[Coll[Byte]].getOrElse(INPUTS(0).id) == userAddress && OUTPUTS(0).value == bidAmount
        }}
        val returnFunds = {{
            val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 4000000
            OUTPUTS(0).value >= total && OUTPUTS(0).propositionBytes == userAddress
        }}
        sigmaProp(startAuction || returnFunds)
    }}"""

    tree = Address(bidder)
    info = f'${initial},${step},${start}'
    auctionAddress = None
    reqs = [
        {
            "address": auctionAddress,
            "value": initial,
            "assets": [
                {
                    "tokenId": token,
                    "amount": 0
                }
            ],
            "registers": {
                "R4": tree.address,
                "R5": -1,
                "R6": step,
                "R7": description,
                "R8": tree.address,
                "R9": info,
            }
        }
    ]

    request = {
        "address": address,
        "returnTo": bidder,
        "startWhen": {
            "erg": str(int(initial or 0) + int(auctionFee)),
        },
        "txSpec": {
            "requests": json.dumps(reqs),
            "fee": auctionFee,
            "inputs": ['*'],
            "dataInputs": ""
        },
    }

    # handle workflow
    try:
        logging.info('/follow...')
        res = requests.post(f'{assembler_url}/follow', json=request, headers=headers)
        if res.status_code == 200:
            logging.info(f'status ok: {res.status_code}, getting result')
            # logging.info(res.content) # find id
            id = None
            if 'id' in res.json(): 
                id = res.json()['id']

            res = requests.get(f'{assembler_url}/result/{id}')
            detail = res.json()['detail']
            logging.debug(f'detail: {detail}\nresult: {res.content}')
            while detail == 'pending': 
                logging.info(f'sleeping 10s...')
                sleep(10)
                res = requests.get(f'{assembler_url}/result/{id}')
                detail = res.json()['detail']
                logging.debug(f'detail: {detail}\nresult: {res.content}')
            else:
                logging.warning(f'follow returned status: {detail}')

            logging.debug(f'final status: {res.content}') # display result
    
    except Exception as e:
        logging.debug(e)

