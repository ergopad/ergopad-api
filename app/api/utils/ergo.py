from base64 import b64encode

def zigzag(i: int):
  return (i >> 63) ^ (i << 1)

def vlq(i: int):
  ret = []
  while i != 0 or len(ret)==0:
    b = i & 0x7F
    i >>= 7
    if i > 0:
      b |= 0x80
    ret.append(b)
  return ret

def encodeLong(n: int):
  z = zigzag(n)
  v = vlq(z)
  r = '05' + ''.join(['{0:02x}'.format(i) for i in v])
  return r

def encodeLongArray(la):
  r = '11'+hex(len(la))[2:].rjust(2,'0')
  for l in la:
    r += encodeLong(l)[2:]
  return r

def encodeString(n: str):
  return '0e'+hex(len(bytes.fromhex(n)))[2:].rjust(2,'0')+n

def hexstringToB64(string: str):
  return b64encode(bytes.fromhex(string)).decode('utf-8')