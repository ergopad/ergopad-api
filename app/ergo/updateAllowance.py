import os
import json
import requests
import inspect
import asyncio
import csv
import aiofiles

from aiocsv import AsyncReader
from time import time
from argparse import ArgumentParser
# from config import Config, Network # api specific config
# from wallet import Wallet # ergopad.io library

### LOGGING
import logging
logging.basicConfig(format='{asctime}:{name:>8s}:{levelname:<8s}::{message}', style='{', level=logging.INFO)

### ARGV
# parser = ArgumentParser(description='ergo wallet')
# parser.add_argument('-w', '--wallet', help='mainnet wallet address')
# args = parser.parse_args()

### INIT
# CFG = Config[Network]

assembler = 'http://assembler:8080'
ergonode  = 'http://ergonode:9053'
headers   = {'Content-Type': 'application/json'}
myself    = lambda: inspect.stack()[1][3]

### FUNCTIONS
async def getWhitelist():
    list = {}
    try:
        async with aiofiles.open(f'whitelist.csv', mode='r', encoding="utf-8", newline="") as f:
            async for row in AsyncReader(f):
                list[row[2].rstrip()] = {
                    'sigusd': float(row[0])
                }
        return list

        logging.info(f'number of whitelisted wallets: {len(list.keys())}')

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}

async def getBlacklist():
    list = {}
    try:
        async with aiofiles.open(f'blacklist.tsv', mode='r', encoding="utf-8", newline="") as f:            
            async for row in AsyncReader(f, delimiter='\t'):
                # ignore comments
                if row[0][:1] != '#':

                    # key on wallet
                    if row[0] not in list:
                        list[row[0]] = []
                    
                    # save time, qty and assembler uuid
                    list[row[0]].append({
                        'timeStamp': row[1],
                        'sigusd': row[2],
                        'assemblerId': row[3],
                    })

        return list

        logging.info(f'number of blacklisted wallets: {len(list.keys())}')

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}

def getAssemblerIds(list):
    try:
        ids = {}
        if not os.path.exists('assemblerStatus.tsv'):
            open(f'assemblerStatus.tsv', 'w').close() # touch

        with open(f'assemblerStatus.tsv') as f:
            for row in f.readlines():
                try:
                    r = row.rstrip().split('\t')
                    ids[r[0]] = r[1]
                except:
                    pass

        for wallet in list:
            for l in list[wallet]:
                res = requests.get(f'{assembler}/result/{l["assemblerId"]}')
                # if res.ok: # cannot use this since Invoker.first returns json as status_code 400
                try:
                    detail = res.json()['detail']                    
                    logging.debug(f'assmid::{l["assemblerId"]}')
                    logging.debug(f'detail::{detail}')
                    
                    # ignore any other or missing status
                    if detail == 'success' or detail == 'pending' or detail == 'timeout' or detail == 'returning':                        
                        ids[l['assemblerId']] = detail                    
                    elif l['assemblerId'] not in ids:
                        if detail == 'Invoker.first':
                            ids[l['assemblerId']] = 'error'
                        else:
                            ids[l['assemblerId']] = 'unknown'

                except:
                    pass
        
        with open(f'assemblerStatus.tsv', 'w') as f:
            for i in ids:
                f.write(f'{i}\t{ids[i]}\n')

        logging.info(f'number of assembler ids: {len(ids.keys())}')
        logging.debug(ids)

        return ids

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}


def getSpentlist(list, statuslist):
    try:
        # logging.debug(list)
        spentlist = {}
        for wallet in list:
            if wallet not in spentlist:
                spentlist[wallet] = 0.0

            # logging.debug(statuslist)
            for l in list[wallet]:
                if spentlist[wallet] >= 0.0:
                    # success, pending, returning, return failed and timeout
                    if l['assemblerId'] in statuslist:
                        detail = statuslist[l['assemblerId']]
                        logging.debug(f"spentlist: {detail}, {l['assemblerId']}")

                        # no longer being tracked
                        if detail == 'Invoker.first':
                            logging.debug('Invoker.first')

                        # success
                        elif detail == 'success':
                            spentlist[wallet] += float(l['sigusd'])

                        # timeout
                        elif detail == 'timeout':                            
                            logging.debug('timeout, no change')
                            spentlist[wallet] += 0 # float(l['sigusd'])

                        # pending, returning, unknown; block further transactions
                        else: 
                            # block purchases from this wallet
                            spentlist[wallet] = -1.0
                    
                    # assemblerId not found; if in blacklist, should have an assembler status
                    else:
                        spentlist[wallet] = -2.0

        logging.info(f'number of spent items: {len(spentlist.keys())}')
        return spentlist

    except Exception as e:
        return {'status': 'error', 'def': myself(), 'message': e}

async def handleAllowance():
    # whitelist = asyncio.run(getWhitelist())
    whitelist = await getWhitelist()
    # blacklist = asyncio.run(getBlacklist())
    blacklist = await getBlacklist()
    statuslist = getAssemblerIds(blacklist)
    spentlist = getSpentlist(blacklist, statuslist)

    # logging.debug(whitelist)
    # logging.debug(spentlist)

    currentlist = {}
    for w in whitelist:
        total = whitelist[w]['sigusd']
        spent = 0
        if w in spentlist: 
            spent = spentlist[w]
        # logging.debug(f'wallet: {w}, total: {total}, reamining: {total-spent}, spent: {spent}')
        if spent < 0:
            currentlist[w] = {
                'remaining': 0,
                'total': total,
                'spent': spent,
                'status': 'not ready',
            }
        else:
            currentlist[w] = {
                'remaining': total-spent,
                'total': total,
                'spent': spent,
                'status': 'success',
            }

    # logging.info(json.dumps(currentlist))
    with open('remaining.tsv', 'w') as f:    
        for w in currentlist:
            f.write(f'{w}\t{currentlist[w]["total"]}\t{currentlist[w]["spent"]}\t{currentlist[w]["remaining"]}\n')

### MAIN
if __name__ == '__main__':
    logging.info('main')
    asyncio.run(handleAllowance())
