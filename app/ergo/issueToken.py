import requests, json

from address import Address
from time import sleep
from base64 import b64encode

### LOGGING
import logging
level = logging.DEBUG # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=level)

### INIT 
headers = {'Content-Type': 'application/json'}
assembler_url = 'http://localhost:8080'
api_key = 'oncejournalstrangeweather'

# wallet to send tokens to
userWallet = Address('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG')
userTreeHex = userWallet.ergoTree()
userTree = b64encode(userTreeHex).decode('utf-8')

toWallet = Address('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG')
toTreeHex = toWallet.ergoTree()
toTree = b64encode(userTreeHex).decode('utf-8')

minTx = 10000000
txFee = 2000000
nanoergsInErg = 1000000000
ergAmount = .1
nergAmount = int(ergAmount * nanoergsInErg)
qtyTokens = 10000 # number of tokens
decimals = 0
name = 'ASDFToken123'
description = 'ASDFToken'

# /script/addressToBytes/<address> -- doesn't seem to help
# userTree = toTree = '0e240008cd02946f31c13a75cb07571a63e860fa79ebd866278651cb1268d0c70c8c9beaaf4e'

scriptAlwaysTrue = "{ 1 == 1 }"
scriptIssueToken = f"""{{
  val outputOk = {{
    val issued = OUTPUTS(0).tokens.getOrElse(0, (INPUTS(0).id, 0L))
    INPUTS(0).id == issued._1 && issued._2 == {qtyTokens}L && 
    OUTPUTS(0).value == {nergAmount+minTx}L && 
    OUTPUTS(0).propositionBytes == fromBase64("{toTree}")
  }}
  val returnFunds = {{
    val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 4000000
    OUTPUTS(0).value >= total && 
    OUTPUTS(0).propositionBytes == fromBase64("{userTree}")
  }}
  sigmaProp(OUTPUTS.size == 2 && (outputOk || returnFunds))
}}"""

# get the P2S address (basically a hash of the script??)
p2s = requests.post(f'{assembler_url}/compile', headers=headers, json=scriptIssueToken)
p2s_address = p2s.json()['address']

outBox = {
    'ergValue': nergAmount + minTx,
    'amount': qtyTokens,
    'address': toWallet.address,
    'name': name,
    'description': description,
    'decimals': decimals,
}

request = {
    'address': p2s_address,
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

sendMe = [{
    'address': p2s_address,
    'value': nergAmount + minTx + txFee,
    'assets': [],
}]

res = requests.post(f'{assembler_url}/follow', headers=headers, json=request); id = res.json()['id']; id

sendMe = [{
    'address': p2s_address,
    'value': 2000000,
    'assets': [],
}]

pay = requests.post(f'http://localhost:9053/wallet/payment/send', headers=dict(headers, **{'api_key': api_key}), json=sendMe); pay.json()
fin = requests.get(f'{assembler_url}/result/{id}'); fin.json()
