import os
import time

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class Stopwatch(object):
    def __init__(self):
        self.start_time = None
        self.stop_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.stop_time = time.time()

    @property
    def time_elapsed(self):
        return time.time() - self.start_time

    @property
    def total_run_time(self):
        return self.stop_time - self.start_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self):
        self.stop()

POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')

Network = os.getenv('ERGONODE_NETWORK', default='mainnet')
Config = {
  # 'devnet':
  'testnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : os.getenv('EXPLORER_API'), # 'http://api.ergoplatform.com/api/v1',
    'ergoWatch'         : os.getenv('ERGOWATCH_API'), # 'https://ergo.watch/api/sigmausd/state',
    'coinGecko'         : os.getenv('COINGECKO_API'), # 'https://api.coingecko.com/api/v3',
    'oraclePool'        : os.getenv('ORACLE_API'), # 'https://erg-oracle-ergusd.spirepools.com/frontendData',
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'nodeWallet'        : os.getenv('ERGOPAD_WALLET'),
    'ergopadToken'      : os.getenv('ERGOPAD_TOKEN'),
    'buyerApiKey'       : os.getenv('BUYER_APIKEY'),
    'validateMe'        : os.getenv('VALIDATE_ME'),
    'validEmailApply'   : {os.getenv('PAGE_APPLY'): True},
    'minTx'             : 1e7, # required
    'txFee'             : 1e6, # tips welcome
    'nanoergsInErg'     : 1e9, # 1e9
    'tokenPriceNergs'   : 1.5e9, # 1.5 ergs
    'vestingPeriods_1'  : 9,
    'vestingDuration_1' : 30, # days
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
    'csExplorer'        : f"postgresql://{os.getenv('EXPLORER_USER')}:{os.getenv('EXPLORER_PASSWORD')}@{os.getenv('EXPLORER_HOST')}:{os.getenv('EXPLORER_PORT')}/{os.getenv('EXPLORER_DBNM')}",
    'csDanaides'        : f"postgresql://{os.getenv('DANAIDES_USER')}:{os.getenv('DANAIDES_PASSWORD')}@{os.getenv('DANAIDES_HOST')}:{os.getenv('DANAIDES_PORT')}/{os.getenv('DANAIDES_DBNM')}",
    'redisHost'         : os.getenv('REDIS_HOST'),
    'redisPort'         : os.getenv('REDIS_PORT'),
    'jwtSecret'         : os.getenv('JWT_SECRET_KEY'),
    'debug'             : True,
    'vestingContract'   : 'Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp',
    'validCurrencies'   : {
      'seedsale'        : '129804369cc01c02f9046b8f0e37f8fc924e71b64652a0a331e6cd3c16c1f028',
      'strategic_sale'  : 'e403836f51838b949c05cd4ab221ba3e004bddc9b5af4025c39031bb8853dc43',
      'sigusd'          : '931aadfacfdde2849a7353472910b2e5e56f5b6f8f2be92859a7ff61d0bf9948',
      'ergopad'         : '129804369cc01c02f9046b8f0e37f8fc924e71b64652a0a331e6cd3c16c1f028', # 
    }
  }),
  'mainnet': dotdict({
    'node'              : os.getenv('ERGONODE_HOST'),
    'explorer'          : os.getenv('EXPLORER_API'), # 'http://api.ergoplatform.com/api/v1',
    'ergoWatch'         : os.getenv('ERGOWATCH_API'), # 'https://ergo.watch/api/sigmausd/state',
    'coinGecko'         : os.getenv('COINGECKO_API'), # 'https://api.coingecko.com/api/v3',
    'oraclePool'        : os.getenv('ORACLE_API'), # 'https://erg-oracle-ergusd.spirepools.com/frontendData',
    'ergopadApiKey'     : os.getenv('ERGOPAD_APIKEY'),
    'bogusApiKey'       : os.getenv('BOGUS_APIKEY'),
    'nodeWallet'        : os.getenv('ERGOPAD_WALLET'),
    'ergopadTokenId'    : os.getenv('ERGOPAD_TOKENID'),
    'ergopadWallet'     : os.getenv('ERGOPAD_WALLET'),
    'validateMe'        : os.getenv('VALIDATE_ME'),
    'validEmailApply'   : {os.getenv('PAGE_APPLY'): True},
    'emailUsername'     : os.getenv('EMAIL_ERGOPAD_USERNAME'),
    'emailPassword'     : os.getenv('EMAIL_ERGOPAD_PASSWORD'),
    'emailSMTP'         : os.getenv('EMAIL_ERGOPAD_SMTP'),
    'emailFrom'         : os.getenv('EMAIL_ERGOPAD_FROM'),
    'minTx'             : 1e7, # required
    'txFee'             : 1e6, # tips welcome
    'nanoergsInErg'     : 1e9, # 1e9
    'tokenPriceNergs'   : 1.5e9, # 1.5 ergs
    'vestingPeriods_1'  : 9,
    'vestingDuration_1' : 30, # days
    'connectionString'  : f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
    'csExplorer'        : f"postgresql://{os.getenv('EXPLORER_USER')}:{os.getenv('EXPLORER_PASSWORD')}@{os.getenv('EXPLORER_HOST')}:{os.getenv('EXPLORER_PORT')}/{os.getenv('EXPLORER_DBNM')}",
    'csDanaides'        : f"postgresql://{os.getenv('DANAIDES_USER')}:{os.getenv('DANAIDES_PASSWORD')}@{os.getenv('DANAIDES_HOST')}:{os.getenv('DANAIDES_PORT')}/{os.getenv('DANAIDES_DBNM')}",
    'redisHost'         : os.getenv('REDIS_HOST'),
    'redisPort'         : os.getenv('REDIS_PORT'),
    'jwtSecret'         : os.getenv('JWT_SECRET_KEY'),
    'debug'             : True,
    'vestingContract'   : 'Y2JDKcXN5zrz3NxpJqhGcJzgPRqQcmMhLqsX3TkkqMxQKK86Sh3hAZUuUweRZ97SLuCYLiB2duoEpYY2Zim3j5aJrDQcsvwyLG2ixLLzgMaWfBhTqxSbv1VgQQkVMKrA4Cx6AiyWJdeXSJA6UMmkGcxNCANbCw7dmrDS6KbnraTAJh6Qj6s9r56pWMeTXKWFxDQSnmB4oZ1o1y6eqyPgamRsoNuEjFBJtkTWKqYoF8FsvquvbzssZMpF6FhA1fkiH3n8oKpxARWRLjx2QwsL6W5hyydZ8VFK3SqYswFvRnCme5Ywi4GvhHeeukW4w1mhVx6sbAaJihWLHvsybRXLWToUXcqXfqYAGyVRJzD1rCeNa8kUb7KHRbzgynHCZR68Khi3G7urSunB9RPTp1EduL264YV5pmRLtoNnH9mf2hAkkmqwydi9LoULxrwsRvp',
    'validCurrencies'   : {
      'seedsale'        : '02203763da5f27c01ba479c910e479c4f479e5803c48b2bf4fd4952efa5c62d9', # mainnet seed
      'strategic_sale'  : '60def1ed45ffc6493c8c6a576c7a23818b6b2dfc4ff4967e9867e3795886c437', # mainnet strategic token
      'ergopad'         : 'd71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413', # official
      'sigusd'          : '03faf2cb329f2e90d6d23b58d91bbb6c046aa143261cc21f52fbe2824bfcbf04', # official SigUSD (SigmaUSD - V2)
    }
  })
}
