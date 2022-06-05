import requests

from address import Address
from base64 import b64encode

### LOGGING
import logging 
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=logging.DEBUG)

### INIT 
HOST = 'localhost'
PORT = 8080
ERGONODE_NETWORK  = 'testnet'
ERGO_PLATFORM_URL = { 
    'mainnet': 'https://api.ergoplatform.com/api/v1',
    'testnet': 'https://api-testnet.ergoplatform.com/api/v1'
}

headers       = {'Content-Type': 'application/json'}
assembler_url = f'http://{HOST}:{PORT}'
api_key       = 'goalspentchillyamber'

# node wallet
userWallet  = Address('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw')
# userWallet  = Address('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG')
userTreeHex = userWallet.ergoTree()
userTree    = b64encode(bytes.fromhex(userTreeHex)).decode()

# send tokens to wallet
toWallet  = Address('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw') # ergopad
# toWallet  = Address('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG') # testnet
toTreeHex = toWallet.ergoTree()
toTree    = b64encode(bytes.fromhex(toTreeHex)).decode()

# tx details
minTx         = 10000000 # required
txFee         = 2000000 # tips welcome
nanoergsInErg = 1000000000 # 1e9
ergAmount     = .1 # default
nergAmount    = int(ergAmount * nanoergsInErg)
qtyTokens     = 10000000 # number of tokens to send
decimals      = 0
name          = 'ergopad'
description   = 'ergopad.io'

# ergoscript
scriptAlwaysTrue = "{ 1 == 1 }"
scriptIssueToken = f"""{{
  val outputOk = {{
    val issued = OUTPUTS(0).tokens.getOrElse(0, (INPUTS(0).id, 0L))
    INPUTS(0).id == issued._1 && issued._2 == {qtyTokens}L && 
    OUTPUTS(0).value == {nergAmount + minTx}L && 
    OUTPUTS(0).propositionBytes == fromBase64("{toTree}")
  }}
  val returnFunds = {{
    val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 4000000
    OUTPUTS(0).value >= total && 
    OUTPUTS(0).propositionBytes == fromBase64("{userTree}")
  }}
  sigmaProp(OUTPUTS.size == 2 && (outputOk || returnFunds))
}}"""

# make sure assembler is happy
res = requests.get(f'{assembler_url}/state', headers=headers)
if res.ok:
  functioning = res.json()['functioning']
  if functioning != True:
    logging.error('assembler not ready, quitting.')
    quit()

# get the P2S address (basically a hash of the script??)
p2s = requests.post(f'{assembler_url}/compile', headers=headers, json=scriptIssueToken)
smartContract = p2s.json()['address']
logging.info(f'smart contract: {smartContract}')

outBox = {
    'ergValue': nergAmount + minTx, # OUTPUTS(0).value
    'amount': qtyTokens, # OUTPUTS(0).tokens_2 
    'address': toWallet.address, # OUTPUTS(0).propositionBytes
    'name': name, 
    'description': description,
    'decimals': decimals,
}

request = {
    'address': smartContract,
    'returnTo': userWallet.address,
    'startWhen': {
        'erg': nergAmount + minTx + txFee
    },
    'txSpec': {
        'requests': [outBox],
        'fee': txFee,
        'inputs': ['$userIns'],
        'dataInputs': [],
    },
}

# assembler to watch transaction
res = requests.post(f'{assembler_url}/follow', headers=headers, json=request)
id = res.json()['id']
logging.info(f'id: {id}')

# send payment
sendMe = [{
    'address': smartContract,
    'value': nergAmount + minTx + txFee,
    'assets': [],
}]
pay = requests.post(f'http://localhost:9054/wallet/payment/send', headers=dict(headers, **{'api_key': api_key}), json=sendMe)
pay.json()

# wait 30s and see if it's there, may need to recheck
from time import sleep
sleep(30)
fin = requests.get(f'{assembler_url}/result/{id}')
logging.info(f'result: {fin.json()}')
logging.info('fin...')

# tokenId = '67ba5e86afa43da553c2719870a6ae3d95a99b8fb024aa99edb0ebd57df90c73'
# tkn = requests.get(f'{ERGO_PLATFORM_URL[ERGONODE_NETWORK]}/tokens/{tokenId}'); tkn.json()
