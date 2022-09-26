from .web3 import get_receipt_from_txhash, create_contract
import web3.exceptions
from .instance_collect import fetch_order
from web3.constants import ADDRESS_ZERO
from eth_abi import encode_abi

settlement = create_contract('0x9008D19f58AAbD9eD0D60971565AA8510560ab41',
                             [
                                 {
                                     "anonymous": False,
                                     "inputs": [
                                         {
                                             "indexed": True,
                                             "internalType": "address",
                                             "name": "owner",
                                             "type": "address"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "contract IERC20",
                                             "name": "sellToken",
                                             "type": "address"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "contract IERC20",
                                             "name": "buyToken",
                                             "type": "address"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "uint256",
                                             "name": "sellAmount",
                                             "type": "uint256"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "uint256",
                                             "name": "buyAmount",
                                             "type": "uint256"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "uint256",
                                             "name": "feeAmount",
                                             "type": "uint256"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "bytes",
                                             "name": "orderUid",
                                             "type": "bytes"
                                         }
                                     ],
                                     "name": "Trade",
                                     "type": "event"
                                 },
                                 {
                                     "anonymous": False,
                                     "inputs": [
                                         {
                                             "indexed": True,
                                             "internalType": "address",
                                             "name": "target",
                                             "type": "address"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "uint256",
                                             "name": "value",
                                             "type": "uint256"
                                         },
                                         {
                                             "indexed": False,
                                             "internalType": "bytes4",
                                             "name": "selector",
                                             "type": "bytes4"
                                         }
                                     ],
                                     "name": "Interaction",
                                     "type": "event"
                                 }
                             ])

erc20 = create_contract(None, [{
    "anonymous": False,
    "inputs": [
        {
            "indexed": True,
            "internalType": "address",
            "name": "from",
            "type": "address"
        },
        {
            "indexed": True,
            "internalType": "address",
            "name": "to",
            "type": "address"
        },
        {
            "indexed": False,
            "internalType": "uint256",
            "name": "value",
            "type": "uint256"
        }
    ],
    "name": "Transfer",
    "type": "event"
}])


def process_log(log):
    try:
        return settlement.events.Trade().processLog(log)
    except web3.exceptions.MismatchedABI:
        pass
    try:
        return settlement.events.Interaction().processLog(log)
    except web3.exceptions.MismatchedABI:
        pass
    try:
        return erc20.events.Transfer().processLog(log)
    except web3.exceptions.MismatchedABI:
        return None
    assert False


def normalize_receiver(receiver, owner):
    return receiver if receiver != ADDRESS_ZERO else owner


def is_eth(token):
    return token.lower() == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"


def normalize_token(token):
    return "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" if is_eth(token) else token


def transferUid(address, from_, to, value):
    return encode_abi(
        ["address", "address", "address", "uint256"],
        [address, from_, to, value],
    )


def collapse_interaction_transfers(accumulator, target, value, selector):
    tokens = {}

    for token_amount in accumulator['ins']:
        token = token_amount['token']
        amount = token_amount['amount']
        if token not in tokens.keys():
            tokens[token] = 0
        tokens[token] += amount
    for token_amount in accumulator['outs']:
        token = token_amount['token']
        amount = token_amount['amount']
        if token not in tokens.keys():
            tokens[token] = 0
        tokens[token] -= amount

    id = f'{target} @{selector}'
    entries = tokens.items()
    if len(entries) == 0:
        return []
    elif len(entries) != 2:
        raise RuntimeError(f"can't collapse interaction {id} transfers into a swap")
    elif value != 0:
        raise RuntimeError(f"can't collapse interaction {id} with Ether value")

    tx0 = {'token': list(entries)[0][0], 'amount': list(entries)[0][1]}
    tx1 = {'token': list(entries)[1][0], 'amount': list(entries)[1][1]}

    if tx0['amount'] > 0:
        swap = {
            'sell_token': tx0['token'],
            'sell_amount': tx0['amount'],
            'buy_token': tx1['token'],
            'buy_amount': -tx1['amount']
        }
    else:
        swap = {
            'sell_token': tx1['token'],
            'sell_amount': tx1['amount'],
            'buy_token': tx0['token'],
            'buy_amount': -tx0['amount'] 
        }

    return [{
      'kind': "interaction",
      'target': target,
      'selector': hex(int.from_bytes(selector, byteorder='big', signed=False)),
      **swap,
    }]


def get_swaps(tx_hash):
    receipt = get_receipt_from_txhash(tx_hash)

    logs = receipt['logs']
    processed_logs = []
    for log in logs:
        address = log['address']
        processed_log = process_log(log)
        if processed_log is not None:
            processed_logs.append({'address': address, **processed_log})

    swaps = []
    accumulator = {
        'ins': [],
        'outs': []
    }
    expected_transfers = set()

    for log in processed_logs:
        args = log['args']
        address = log['address']
        if log['event'] == 'Trade':
            oid = str(
                hex(int.from_bytes(args['orderUid'], byteorder='big', signed=False)))
            order = fetch_order(oid)
            swaps.append({
                'kind': "trade",
                'id': oid,
                'sell_token': args['sellToken'],
                'sell_amount': args['sellAmount'],
                'buy_token': normalize_token(args['buyToken']),
                'buy_amount': args['buyAmount'],
                'fee': args['feeAmount'],
                'is_liquidity_order': order['isLiquidityOrder']
            })
            expected_transfers.add(
                transferUid(args['sellToken'], args['owner'],
                            settlement.address, args['sellAmount'])
            )
            if not is_eth(args.buyToken):
                expected_transfers.add(
                    transferUid(
                        args['buyToken'],
                        settlement.address,
                        normalize_receiver(order['receiver'], args['owner']),
                        args['buyAmount']
                    )
                )

        elif log['event'] == 'Transfer':
            t = transferUid(address, args['from'], args['to'], args['value'])
            if t in expected_transfers:
                expected_transfers.remove(t)
            else:
                if args['to'] == settlement.address:
                    accumulator['ins'].append(
                        {'token': address, 'amount': args['value']})
                if args['from'] == settlement.address:
                    accumulator['outs'].append(
                        {'token': address, 'amount': args['value']})

        elif log['event'] == 'Interaction':
            swaps += collapse_interaction_transfers(
                accumulator, args['target'], args['value'], args['selector'])
            accumulator['ins'] = []
            accumulator['outs'] = []

    return swaps


