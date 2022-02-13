import requests

from wallet import Wallet
from config import Config, Network

### LOGGING
import logging
level = logging.DEBUG # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=level)

### INIT 
try:
  CFG = Config[Network]
  isSimulation = True
  headers = {'Content-Type': 'application/json'}
  tkn = requests.get(f'{CFG.explorer}/tokens/{CFG.ergopadTokenId}')
  nodeWallet  = Wallet('3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw') # contains tokens
  buyerWallet  = Wallet('3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG') # simulate buyer

except Exception as e:
  logging.error(f'Init {e}')

### CLASSES/FUNCTIONS
# find current height
def getNodeInfo():
  try:
    nodeInfo = {}
    
    res = requests.get(f'{CFG.node}/info', headers=dict(headers, **{'api_key': CFG.apiKey}))
    if res.ok:
      info = res.json()
      if 'parameters' in info:
        if 'height' in info['parameters']:
          nodeInfo['currentHeight'] = info['parameters']['height']
      if 'currentTime' in info:
        nodeInfo['currentTime'] = info['currentTime']
    
    return nodeInfo

  except Exception as e:
    logging.error(f'getNodeInfo {e}')
    return None

# find unspent boxes with tokens
def getBoxesWithUnspentTokens(allowMempool=False):
  try:
    tot = 0
    ergopadTokenBoxes = {}

    res = requests.get(f'{CFG.node}/wallet/boxes/unspent?minConfirmations=0&minInclusionHeight={(0, -1)[allowMempool]}', headers=dict(headers, **{'api_key': CFG.apiKey}))
    if res.ok:
      assets = res.json()
      for ast in assets:
        if 'box' in ast:
          if ast['box']['assets'] != []:
            for tkn in ast['box']['assets']:
              if 'tokenId' in tkn and 'amount' in tkn:
                if tkn['tokenId'] == CFG.ergopadTokenId:
                  tot += tkn['amount']
                  if ast['box']['boxId'] in ergopadTokenBoxes:
                    ergopadTokenBoxes[ast['box']['boxId']].append(tkn)
                  else:
                    ergopadTokenBoxes[ast['box']['boxId']] = [tkn]
                  logging.debug(tkn)

      logging.info(f'found {tot} ergopad tokens in wallet')

    # invalid wallet, no unspent boxes, etc..
    else:
      logging.error('unable to find expeted unspent boxes')

    return ergopadTokenBoxes

  except Exception as e:
    logging.error(f'getBoxesWithUnspentTokens {e}')
    return None

# ergoscript
def getErgoscript(name, params={}):
  try:
    script = ''
    if name == 'alwaysTrue':
      script = "{ 1 == 1 }"

    if name == 'ergopad':
      return f"""
        {{
          val isAvailable = {{
            val tokens = OUTPUTS(0).tokens.getOrElse(0, (INPUTS(0).id, 0L))
            
            // evaluate
            tokens._1 == INPUTS(0).id &&                                   // tokenId requested is available
            tokens._1 == fromBase64("{CFG.b64ergopadTokenId}") &&              // tokenId requested is specifically this token
            tokens._2 == {CFG.qtyTokens}L &&                                   // token qty requested
            OUTPUTS(0).value == {CFG.nergAmount * CFG.tokenPriceNergs + CFG.minTx}L && // token cost
            OUTPUTS(0).propositionBytes == fromBase64("{CFG.buyerTree}")       // expecting this buyer for this amount
          }}

          val returnFunds = {{
            val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 4000000
            
            // evaluate
            OUTPUTS(0).value >= total && 
            OUTPUTS(0).propositionBytes == fromBase64("{CFG.nodeTree}")
          }}

          // 2 outputs? and either tx matches or funds returned
          sigmaProp(OUTPUTS.size == 2 && (isAvailable || returnFunds))
        }}"""

    if name == 'timeLock':
      script = f"""sigmaProp(OUTPUTS(0).R4[Long].getOrElse(0L) >= {params['timeLock']})"""

    if name == 'heightLock':
      script = f"""sigmaProp(OUTPUTS(0).R4[Long].getOrElse(0L) >= {params['heightLock']})"""

    # get the P2S address (basically a hash of the script??)
    p2s = requests.post(f'{CFG.assembler}/compile', headers=headers, json=script)
    smartContract = p2s.json()['address']
    logging.info(f'smart contract: {smartContract}')

    return smartContract
  
  except Exception as e:
    logging.error(f'getErgoscrip {e}')
    return None

# smartcontract- height lock
def scHeightLock(nodeInfo, smartContract):

  try:
    ergopadTokenBoxes = getBoxesWithUnspentTokens()
    outBox = []
    vestingBeginHeight = nodeInfo['currentHeight']+1 # next height

    # 1 outbox per vesting period to lock spending until vesting complete
    for i in range(CFG.vestingPeriods):
      
      # in event the requested tokens do not divide evenly by vesting period, add remaining to final output
      remainder = 0
      if i == CFG.vestingPeriods-1:
        remainder = CFG.requestedTokens % CFG.requestedTokens
      scVesting = getErgoscript('heightLock', {'heightLock': vestingBeginHeight+i*2}) # unlock every 2

      # create outputs for each vesting period; add remainder to final output, if exists
      outBox.append({
        'address': buyerWallet.address,
        'value': CFG.minTx,
        'script': scVesting,
        'register': {
          'R4': vestingBeginHeight+i*2, # heightlock
        },
        'assets': [{ 
          'tokenId': CFG.ergopadTokenId,
          'amount': int(CFG.requestedTokens/CFG.requestedTokens + remainder)
        }]
      })

    # create transaction with smartcontract, into outbox(es), using tokens from ergopad token box
    request = {
        'address': smartContract,
        'returnTo': buyerWallet.address,
        'startWhen': {
            'erg': CFG.txFee + CFG.minTx*CFG.vestingPeriods, # nergAmount + 2*minTx + txFee
        },
        'txSpec': {
            'requests': outBox,
            'fee': CFG.txFee,          
            'inputs': ['$userIns', ','.join([k for k in ergopadTokenBoxes.keys()])], # 'inputs': ['$userIns', '488a6f4cddb8d4565f5eddf065e943765539b5e861df160ab47e8692637a4a4e'],
            'dataInputs': [],
        },
    }

    # make async request to assembler
    # logging.info(request); exit(); # !! testing
    res = requests.post(f'{CFG.assembler}/follow', headers=headers, json=request)
    id = res.json()['id']
    logging.info(f'id: {id}')

    return id
  
  except Exception as e:
    logging.error(f'scHeightLock: {e}')
    return None

# simulate paynent from buyer; testing
def sendPayment(smartContract):
  try:
    sendMe = [{
        'address': smartContract,
        'value': CFG.txFee + CFG.minTx*CFG.vestingPeriods, # nergAmount + 2*minTx + txFee,
        'assets': [],
    }]
    # logging.info(sendMe)
    pay = requests.post(f'http://localhost:9053/wallet/payment/send', headers=dict(headers, **{'api_key': 'oncejournalstrangeweather'}), json=sendMe)
    logging.info(f'payment: {pay.json()}')

  except Exception as e:
    logging.error(f'sendPayment {e}')
    return None

### MAIN
if __name__ == '__main__':

  logging.info(f'network: {Network}\nnode: {nodeWallet.address}\nbuyer: {buyerWallet.address}')

  try:
    nodeInfo = getNodeInfo()  
    smartContract = getErgoscript('alwaysTrue')
    id = scHeightLock(nodeInfo, smartContract)

    # simulate spending
    if isSimulation:
      logging.info(f'simulate payment to smart contract')
      sendPayment(smartContract) # testWallet.sendPayment(adr, val, [])

    # wait for timeout for various events: timeout, error, ...
    i = 0
    timeout = 180 # seconds
    from time import sleep
    while i < timeout:
      fin = requests.get(f'{CFG.assembler}/result/{id}')
      logging.info(f'result({i}): {fin.json()}')
      i = i + 1
      try:
        if fin.json()['detail'] in ('timeout', 'success'):
          i = timeout
      except:
        pass
      sleep(3)
    sleep(5)
    tkn = requests.get(f'http://localhost:9054/wallet/balances/withUnconfirmed', headers=dict(headers, **{'api_key': 'goalspentchillyamber'})

  except Exception as e:
    logging.error(f'Main {e}')
