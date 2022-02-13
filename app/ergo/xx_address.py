from base58 import b58encode, b58decode #, XRP_ALPHABET
# from base58 import b58encode_check, b58decode_check
from pyblake2 import blake2b
from ecdsa import SECP256k1
from types import SimpleNamespace

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

Network = dotdict({
  'Mainnet': 0 << 4,
  'Testnet': 1 << 4,
})

AddressKind = dotdict({
  'P2PK': 1,
  'P2SH': 2,
  'P2S': 3,
})

class Address:
  def __init__(self, address):
    self.address = address
    self.addrBytes = b58decode(self.address)

  def publicKey(self):
    return self.addrBytes[1:34]

  def ergoTree(self):
    if self.getType() == AddressKind.P2PK:
      return (b'\x00\x08\xcd' + self.publicKey()).hex()
    else:
      return self.addrBytes[:self.addrBytes.length - 4].hex()

  def fromErgoTree(self, ergoTree, network):
    if ergoTree[:6] == '0008cd':
      prefixByte = chr(network + AddressKind.P2PK).encode("utf-8")
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
    prefixByte = chr(network + AddressKind.P2PK).encode("utf-8")
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
      logging.error(f'Invalid Ergo address ${address}')
    return addr

  def fromBytes(self, bytes):
    address = b58encode(bytes)
    return Address.fromBase58(address)

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
  network = Network.Mainnet  
  address = Address('9iD7JfYYemJgVz7nTGg9gaHuWg7hBbHo2kxrrJawyz4BD1r9fLS')
  tree = address.ergoTree()
  fromTree = address.fromErgoTree(tree, network).publicKey()
  pk = tree[6:72]
  fromPk = address.fromPk(pk, network).publicKey()
  isValid = address.isValid()
  logging.info(f"""Validation:
    address: {address.address}
    tree: {tree}
    fromTree: {fromTree}
    fromPk: {fromPk}
    isValid: {isValid}
  """)
