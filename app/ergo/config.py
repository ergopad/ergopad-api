from types import SimpleNamespace
from base64 import b64encode

class dotdict(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, dotdict(value))
            else:
                self.__setattr__(key, value)

Network = 'testnet'
Config = {
  # 'devnet':
  'testnet': dotdict({
    'node'              : 'http://localhost:9054',
    'explorer'          : 'https://api-testnet.ergoplatform.com/api/v1',
    'apiKey'            : 'goalspentchillyamber',
    'assembler'         : 'http://localhost:8080',
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'nergAmount'        : .1, # default
    'qtyTokens'         : 5, 
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadWallet'     : '3WzKopFYhfRGPaUvC7v49DWgeY1efaCD3YpNQ6FZGr2t5mBhWjmw',
    'testingWallet'     : '3WwjaerfwDqYvFwvPRVJBJx2iUvCjD2jVpsL82Zho1aaV5R95jsG',
    'ergopadTokenId'    : '81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a',
    'b64ergopadTokenId' : b64encode(bytes.fromhex('81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a')).decode(),
    'requestedTokens'   : 4,
    'vestingPeriods'    : 2,
    'wallet'            : 'http://localhost:9053',
    'walletApiKey'      : 'oncejournalstrangeweather',
  }),
  'mainnet': dotdict({
    'node'              : 'http://localhost:9053',
    'explorer'          : 'https://api.ergoplatform.com/api/v1',
    'apiKey'            : 'helloworld',
    'assembler'         : 'http://localhost:8080',
    'minTx'             : 10000000, # required
    'txFee'             : 2000000, # tips welcome
    'nanoergsInErg'     : 1000000000, # 1e9
    'nergAmount'        : .1, # default
    'qtyTokens'         : 5, 
    'tokenPriceNergs'   : 1500000000, # 1.5 ergs
    'ergopadTokenId'    : '81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a',
    'b64ergopadTokenId' : b64encode(bytes.fromhex('81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a')).decode(),
    'requestedTokens'   : 4,
    'vestingPeriods'    : 2,
    'wallet'            : 'http://localhost:9054',
    'walletApiKey'      : 'xyzpdq',
  })
}
