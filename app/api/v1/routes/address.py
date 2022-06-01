from base58 import b58encode, b58decode #, XRP_ALPHABET
# from base58 import b58encode_check, b58decode_check
from base64 import b64encode, b64decode
from pyblake2 import blake2b
from ecdsa import SECP256k1
from types import SimpleNamespace
from api.utils.logger import logger, myself, LEIF

class dotdict(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, dotdict(value))
            else:
                self.__setattr__(key, value)

### INIT
curve = SECP256k1

Network = {
  'Mainnet': 0 << 4,
  'Testnet': 1 << 4,
}

AddressKind = {
  'P2PK': 1,
  'P2SH': 2,
  'P2S': 3,
}

class Address:
  def __init__(self, address):
    self.address = address
    self.addrBytes = b58decode(address)

  def publicKey(self):
    return self.addrBytes[1:34]

  def ergoTree(self):
    if self.getType() == AddressKind['P2PK']:
      # return (b'\x00\x08\xcd' + self.publicKey()).hex()
      return (self.publicKey()).hex()
    else:
      return (self.addrBytes[:len(self.addrBytes) - 4]).hex()

  def bs64(self):
    return b64encode(self.ergoTree().encode('utf-8')).decode('utf-8')

  def vlq(self):
    vlq = lambda x: int("".join(bin(a|128)[3:] for a in x), 2)
    return vlq([int(x) for x in str(int(self.ergoTree(), 16))])

  def hex2vlq(self, hexString):
    vlq = lambda x: int("".join(bin(a|128)[3:] for a in x), 2)
    return vlq([int(x) for x in str(int(hexString, 16))])

  def int2vlq(self, intString):
    # hexString2intArray = [int(x) for x in str(int(e, 16))]
    vlq = lambda x: int("".join(bin(a|128)[3:] for a in x), 2)
    return vlq([int(x) for x in intString])

  def fromErgoTree(self, ergoTree, network):
    if ergoTree[:6] == '0008cd':
      prefixByte = chr(network + AddressKind['P2PK']).encode("utf-8")
      pk = ergoTree[6:72]
      contentBytes = str.encode(pk)
      checksum =  blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest().encode("utf-8")
      address = (prefixByte + contentBytes + checksum)[:38]
    else:
      prefixByte = chr(network + AddressKind.P2S).encode("utf-8")
      contentBytes = ergoTree.hex()
      hash = blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest()
      checksum = str.encode(hash[:4])
      address = prefixByte + contentBytes + checksum
    return Address(b58encode(address))

  def fromPk(self, pk, network):
    prefixByte = chr(network + AddressKind['P2PK']).encode("utf-8")
    contentBytes = str.encode(pk)
    checksum = blake2b((prefixByte + contentBytes), key=b'', digest_size=32).hexdigest().encode("utf-8")
    address = (prefixByte + contentBytes + checksum)[:38]
    return Address(b58encode(address))

  def fromSk(self, sk, network):
    pk = curve.g.mul(sk).encodeCompressed()
    return self.fromPk(pk, network)

  def fromBase58(self, address):
    addr = Address(address)
    if (not addr.isValid()):
      logger.error(f'Invalid Ergo address ${address}')
    return addr

  def fromBytes(self, bytes):    
    return self.fromBase58(b58encode(bytes))

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

if __name__ == '__main__':
  network = Network['Mainnet']
  address = Address('3WvsT2Gm4EpsM9Pg18PdY6XyhNNMqXDsvJTbbf6ihLvAmSb7u5RN')
  # address = Address('9fRAWhdxEsTcdb8PhGNrZfwqa65zfkuYHAMmkQLcic1gdLSV5vA')
  
  Krowten = dict([(v, k) for k, v in Network.items()])
  Dnik = dict([(v, k) for k, v in AddressKind.items()])
  tree = address.ergoTree()
  
  # fromBytes: {address.fromBytes(address.addrBytes)}
  logger.info(f"""Validation:
    address: {address.address}
    addressBytes: {address.addrBytes}
    ergoTree: {address.ergoTree()}
    b64_ergoTree: {address.bs64()}
    fromTree: {address.fromErgoTree(tree, network).publicKey()}
    fromPk: {address.fromPk(tree[6:72], network).publicKey()}
    fromBase58: {address.fromBase58(address.address).address}
    fromBytes: {address.fromBytes(address.addrBytes).address.decode('utf-8')}
    isValid: {address.isValid()}
    getNetwork: {address.getNetwork()} ({Krowten[address.getNetwork()]})
    getType: {address.getType()} ({Dnik[address.getType()]})
    headByte: {address.headByte()}
  """)
