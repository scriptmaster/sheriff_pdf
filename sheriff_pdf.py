import os
import zlib # this is allowed

# const
DECODER='latin_1'

def decoder(byte):
  return byte.decode(DECODER)

def isalnum_(byte): # the libless pattern does not allow you to import from libcurses/other import isalnum_
  return byte == 95 or (byte >= 48 and byte <= 57) or (byte >= 65 and byte <= 90) or (byte >= 97 and byte <= 122)

def isalnum(byte): # the libless pattern does not allow you to import from libcurses/other import isalnum
  return (byte >= 48 and byte <= 57) or (byte >= 65 and byte <= 90) or (byte >= 97 and byte <= 122)

def isnum(byte): # the libless pattern does not allow you to import from libcurses/other import isnum
  return byte >= 48 and byte <= 57

def isalpha(byte): # the libless pattern does not allow you to import from libcurses/other import isalpha
  return (byte >= 65 and byte <= 90) or (byte >= 97 and byte <= 122)

def byte2int(byte):
  return int.from_bytes(byte, 'big')

def str2int(s):
  return int.from_bytes(bytes(s, DECODER), 'big')

def filter_deflate(b):
  return zlib.decompress(b)

def decode_obj_hash(raw_hash):
  hash = {}
  raw_len = len(raw_hash)

  double_angle_enclosed = raw_hash[0] + raw_hash[1] + raw_hash[-2] + raw_hash[-1]
  # print(f'double_angle_enclosed [{raw_len}]:',double_angle_enclosed, raw_hash[2:-2])

  if not double_angle_enclosed == '<<>>':
    print('Given obj is not enclosed within << and >>')
    return hash

  n = 2

  in_symbol = False
  symbol = ''
  symbols = []

  in_delim = True
  delim = ''
  delims = []

  key_order = []
  key = ''
  value = ''

  in_array = 0 # to inc multiple nested arrays and dec them as they are being paired
  in_hash = 0 # to inc multiple nested hashes and dec them as they are being paired
  aval = []

  n = 2
  while n < raw_len:
    s = raw_hash[n]
    n += 1
    if s == '/':
      if in_delim:
        in_delim = False
        delim = delim.strip()
        if delim:
          delims.append(delim)
          if key:
            hash[key] = delim
            key_order.append(key)
            key = ''
        delim = ''
      in_symbol = True
      if symbol:
        symbols.append(symbol)
        if key:
            hash[key] = symbol
            key_order.append(key)
            key = ''
        else:
          key = symbol
      symbol = s
    elif isalnum_(str2int(s)): # includes _
      if in_symbol:
        symbol += s
      elif in_delim:
        delim += s
    elif n == raw_len:
      # print('reached eoh', s, n, raw_len, delim)
      if in_delim:
        delim = delim.strip()
        if delim:
          if delim[-1]+s == '>>':
            delim = delim[:-1]
          delims.append(delim)
          if key:
            hash[key] = delim
            key_order.append(key)
            key = ''
      # elif in_symbol: # this prolly not occur
      #   symbols.append(symbol)
      #   if key:
      #     hash[key] = symbol
      #     key_order.append(key)
      #     key = ''
    else:
      # ie. if.special chars
      if in_symbol:
        in_symbol = False
        if symbol:
          symbols.append(symbol)
          if key:
            hash[key] = symbol
            key_order.append(key)
            key = ''
          else:
            key = symbol
          symbol = ''
        in_delim = True
        if delim:
          delims.append(delim)
        delim = ''
      # else:
      #   pass
      delim += s
      if delim[-2:] == '<<': # ? if delim.strip() == '<<': # ?
        in_hash += 1
        h = n + 1
        hh = raw_hash[n:h]
        while in_hash > 0 and h < raw_len:
          h += 1
          hh = raw_hash[n:h]
          if hh[-2:] == '<<':
            in_hash += 1
            h += 1
          elif hh[-2:] == '>>':
            in_hash -= 1
            h += 1
        hh = raw_hash[n:h-1]
        hh = '<<'+hh
        # print('hh:', hh)
        # print('key:', key)
        if key:
          hash[key] = decode_obj_hash(hh)
          key_order.append(key)
          key = ''
        # print(f'n: {n} h: {h}')
        n = h - 1 # woahh!
        # print('n:',n,'h:',h, hh, key)

  # hash['keys'] = key_order
  # hash['symbols'] = symbols
  # hash['delims'] = delims
  # print('hash:', hash)
  return hash

def decode_stream(stream, obj):
  st = {}
  h = obj['hash']
  if not '/Filter' in h or not h['/Filter'] == '/FlateDecode':
    print('obj stream is not a FlateDecode filter')
    return st
  if '/DecodeParms' in h and '/Predictor' in h['/DecodeParms'] and h['/DecodeParms']['/Predictor'] != '1':
    print('obj stream /Predictor on FlateDecode filter is not 1: ', h['/DecodeParms']['/Predictor'])
    return st
  print(f'decode_stream: {len(stream)} {obj["hash"]}')
  for i in range(min(len(stream), 10)):
    print(f'{i}: {stream[i]}')
  print(f'decode_stream[2]:', filter_deflate(stream[2:]))
  return st

## start fn to read, convert and draw
def parse_pdf(pdffilepath):
  n = 0

  lines = []
  line = ''

  tokens = []
  token = ''

  words = []
  word = ''

  specials = []
  special = ''

  s = ''
  prev = ''
  prev2 = ''

  is_obj = False
  objs = []
  obj = {}
  # obj = {'typ': 'root', 'num': 0, 'v': 0, 'name': 'root', 'has': []}
  # objs.append(obj)
  sobj = ''

  is_stream = False
  bstream = []
  stream = ''

  # ideally everything should be a pointer... but... save it for regional programming languages or the drag and droppers
  with open(pdffilepath, "rb") as f:
    while (byte := f.read(1)):
      if byte == b'\r' or byte == b'\n':
        n += 1
        if line != '':
          lines.append(line)
          if line == 'endstream':
            is_stream = False
            print('endstream')
            st = stream[:-10]
            while st and (st[-1:] == '\r' or st[-1:] == '\n'):
              st = st[:-1]
            if 'stream' in obj:
                lst = len(st)
                minlen = min(4,lst)
                obj['stream']['len'] = lst
                obj['stream']['preview'] = st[:minlen] + '...' + st[-minlen:]
                obj['stream']['raw'] = st.encode()
            # if 'streams' in obj and len(obj['streams']) > 0:
            #   lst = len(st)
            #   minlen = min(4,lst)
            #   obj['streams'][-1]['len'] = lst
            #   obj['streams'][-1]['preview'] = st[:minlen] + '...' + st[-minlen:]
            #   obj['streams'][-1]['raw'] = st.encode()
            #   print('stream-data:', obj['streams'][-1]['raw'])
            stream = ''
          elif line == 'endobj':
            is_obj = False
            print('endobj')
            ob = sobj[:-6]
            while ob and (ob[-1:] == '\r' or ob[-1:] == '\n'):
              ob = ob[:-1]
            while ob and ob[-2:] != '>>':
              ob = ob[:-1]
            # obj['raw_hash'] = ob
            if ob:
              print('ob: decode obj hash: ', ob)
              obj['hash'] = decode_obj_hash(ob)
              if 'stream' in obj and 'raw' in obj['stream']:
                obj['stream']['decompressed'] = decode_stream(obj['stream']['raw'], obj)
            # if obj['stream']:
            objs.append(obj)
            obj = {}
            # print('obj-data:', ob)
            sobj = ''

        if word != '':
          words.append(word)
          if word == 'stream' and specials[-1][-2:] == '>>':
            is_stream = True
            bstream = []
            stream = ''
            print('stream start', specials[-1][-2:])
            if not 'stream' in obj:
                obj['stream'] = {}
            # if not 'streams' in obj:
            #   obj['streams'] = []
            # obj['streams'].append({
            #     'from': obj
            # })
        if special != '':
          specials.append(special)
        word = ''
        special = ''
        line = ''

        if token != '%' and token != '':
          tokens.append(token)
        token = ''
        prev2 = ''
        prev = ''
        s = ''
      elif is_stream:
        bstream.append(byte)
        s = decoder(byte)
        stream += s
        line += s
      else:
        try:
          prev2 = prev
          prev = s
          s = decoder(byte)
          i = byte2int(byte)
          # print('i:', i, 's:', s)
          if token != '%':
            if prev != '' and not isalnum_(str2int(prev)):
              tokens.append(prev)
              token = ''
            if isalnum_(i):
              token += s
            else:
              if token > '':
                tokens.append(token)
              token = s

            if isalnum_(byte2int(byte)):
              word += s
              if special != '':
                specials.append(special)
              special = ''
            else:
              if word != '':
                words.append(word)
              word = ''
              special += s

            if token == 'obj':
              is_obj = True
              nobj = {'R': words[-2:]}
              if obj:
                print('prev obj:', obj)
                objs.append(obj)
                nobj['prev'] = obj
              obj = nobj
              sobj = ''
            elif is_obj:
              sobj += s
            # pass
          line += s
        except Exception as e:
          # exc_type, exc_obj, exc_tb = sys.exc_info()
          # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
          # print(e, exc_type, fname, exc_tb.tb_lineno, byte, 'token:', token, 'line:', line)
          print(e)
          break
      # if n > 20:
      #   break

    # print(lines)
    # print(words)
    # print(specials)
    # print(tokens)

    # n = 1
    # for o in objs:
    #   print(f'#{n} o: {o}')
    #   n += 1

# parse_pdf('Income - ATS - SGP.pdf')
