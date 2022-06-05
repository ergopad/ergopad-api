import requests

from base58 import b58encode, b58decode #, XRP_ALPHABET, b58encode_check, b58decode_check
from base64 import b64encode
from pyblake2 import blake2b
from ecdsa import SECP256k1
from config import dotdict, Network, Config

### LOGGING
import logging
level = logging.DEBUG # TODO: set from .env
logging.basicConfig(format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s", datefmt='%m-%d %H:%M', level=level)

### INIT
curve = SECP256k1
CFG = Config[Network]

NetworkEnvironment = {
  'Mainnet': 0 << 4,
  'Testnet': 1 << 4,
}

WalletKind = dotdict({
  'P2PK': 1,
  'P2SH': 2,
  'P2S': 3,
})

### CLASSES
class Wallet:
  def __init__(self, address):
    self.address = address
    self.addrBytes = b58decode(self.address)

  def publicKey(self):
    return self.addrBytes[1:34]

  def ergoTree(self):
    if self.getType() == WalletKind.P2PK:
      return (b'\x00\x08\xcd' + self.publicKey()).hex()
    else:
      return self.addrBytes[:self.addrBytes.length - 4].hex()

  def b64(self):
      b64encode(bytes.fromhex(self.ergoTree())).decode()

  def fromErgoTree(self, ergoTree, network):
    if ergoTree[:6] == '0008cd':
      prefixByte = chr(network + WalletKind.P2PK).encode("utf-8")
      pk = ergoTree[6:72]
      contentBytes = str.encode(pk)
      checksum =  blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest().encode("utf-8")
      address = (prefixByte + contentBytes + checksum)[:38]
    else:
      prefixByte = chr(network + WalletKind.P2S).encode("utf-8")
      contentBytes = ergoTree.hex()
      hash = blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest()
      checksum = str.encode(hash[:4])
      address = prefixByte + contentBytes + checksum
    return Wallet(b58encode(address))

  def fromPk(self, pk, network):
    prefixByte = chr(network + WalletKind.P2PK).encode("utf-8")
    contentBytes = str.encode(pk)
    checksum = blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest().encode("utf-8")
    address = (prefixByte + contentBytes + checksum)[:38]
    return Wallet(b58encode(address))

  def fromSk(self, sk, network):
    pk = curve.g.mul(sk).encodeCompressed()
    return self.fromPk(pk, network)

  def fromBase58(self, address):
    addr = Wallet(address)
    if (not addr.isValid()):
      logging.error(f'Invalid Ergo address ${address}')
    return addr

  def fromBytes(self, bytes):
    address = b58encode(bytes)
    return Wallet.fromBase58(address)

  def isValid(self):
    size = len(self.addrBytes)
    script = self.addrBytes[:size - 4]
    checksum = self.addrBytes[size - 4: size]
    calculatedChecksum = blake2b(script, key=b'', digest_size=32)
    return calculatedChecksum.hexdigest()[:8] == checksum.hex()

  def getNetwork(self):
    return self.headByte() & 0xF0

  def getType(self): 
    return self.headByte() & 0xF

  def headByte(self):
    return self.addrBytes[0]

  # send payment if defined in config; this may be inalid in production
  def sendPayment(self, address, value, assets):
    sendMe = [{
      'address': address,
      'value': value,
      'assets': assets,
    }]
    try:
      pay = requests.post(f'{CFG.wallet}/payment/send', headers={'Content-Type': 'application/json', 'api_key': CFG.walletApiKey}, json=sendMe)        
      if pay.ok:
        return pay.json() # dict
      else: 
        return {
          'status': pay.status_code, 
          'message': pay.content
        }
    except:
      return {
        'status': 'wallet error', 
        'message': 'wallet config does not exist or invalid.'
      }

### MAIN
if __name__ == '__main__':
  network = NetworkEnvironment[Network]
  Wallet = Wallet('9iD7JfYYemJgVz7nTGg9gaHuWg7hBbHo2kxrrJawyz4BD1r9fLS')
  tree = Wallet.ergoTree()
  fromTree = Wallet.fromErgoTree(tree, network).publicKey()
  pk = tree[6:72]
  fromPk = Wallet.fromPk(pk, network).publicKey()
  isValid = Wallet.isValid()
  logging.info(f"""Validation:
    Wallet: {Wallet.Wallet}
    tree: {tree}
    fromTree: {fromTree}
    fromPk: {fromPk}
    isValid: {isValid}
  """)
