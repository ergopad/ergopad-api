def zigzag(i: int):
  return (i >> 63) ^ (i << 1)

def vlq(i: int):
  ret = []
  while i != 0:
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

def encodeString(n: str):
  return '0e'+hex(len(bytes.fromhex(n)))[2:]+n