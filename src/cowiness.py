from .swaps import get_swaps
from networkx import MultiDiGraph, all_simple_edge_paths
import argparse

def compute_vol_fraction_along_path(path, edge_vol_fraction):
    p = 1
    for source, target, id in path:
        p *= edge_vol_fraction[id]
    return p


def path_contains_order(path, swaps, consider_match_with_liquidity_orders):
    for source, target, id in path:
        if swaps[id]['kind'] == 'trade' and (
            consider_match_with_liquidity_orders or
            not swaps[id]['is_liquidity_order']
        ):
            return True
    return False


def compute_cowiness_for_swap(swap_id, swaps, g, consider_match_with_liquidity_orders):
    all_paths = list(all_simple_edge_paths(g, swaps[swap_id]['sell_token'], swaps[swap_id]['buy_token']))
    
    # compute graph considering of just the paths in these edges paths 
    g = MultiDiGraph(set(sum(all_paths, [])))

    edge_vol_fraction = {id: 0 for id in swaps.keys()}

    for n, nbrsdict in g.adjacency():
        # nbrsdict is {node_to: {edge_id:{}} } dict
        total_buy_amount = 0
        for sell_token, edge_ids in nbrsdict.items():
            for edge_id in edge_ids.keys():
                total_buy_amount += swaps[edge_id]['buy_amount']
        for sell_token, edge_ids in nbrsdict.items():
            for edge_id in edge_ids.keys():
                edge_vol_fraction[edge_id] = swaps[edge_id]['buy_amount'] / total_buy_amount

    #print(all_paths)

    cowiness = 0
    for path in all_paths:
        if path_contains_order(path, swaps, consider_match_with_liquidity_orders):
            cowiness += compute_vol_fraction_along_path(path, edge_vol_fraction)

    return cowiness

def compute_cowiness(tx_hash, consider_match_with_liquidity_orders):
    swaps = get_swaps(tx_hash)
    swaps = { id: swap for id, swap in enumerate(swaps)}
    import json
    print(json.dumps(swaps, indent=2))

    edges = [(swap['buy_token'], swap['sell_token'], id) for id, swap in swaps.items()]
    g = MultiDiGraph(edges)

    print("Order  : Cowiness")
    for id, swap in swaps.items():
        if swap['kind'] == 'trade'  and not swap['is_liquidity_order']:
            cowiness = compute_cowiness_for_swap(id, swaps, g, consider_match_with_liquidity_orders)
            print(f"{swap['id'][:6]} : {cowiness*100:.2f} %")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compute cowiness of each order in a settlement."
    )

    parser.add_argument(
        'txhash',
        type=str,
        help="Transaction hash of settlement."
    )

    parser.add_argument(
        '--consider-match-with-liquidity-orders',
        type=bool,
        default=False,
        help="Whether matching with liquidity orders increases cowiness."
    )

    args = parser.parse_args()

    txhash = args.txhash
    consider_match_with_liquidity_orders = args.consider_match_with_liquidity_orders

    compute_cowiness(txhash, consider_match_with_liquidity_orders)

#tx_hash="0xd531066dcf029e67ef9c1431106d7f03cdaf165de748ce121a355dbfadf775c3"   # No cow
#tx_hash = "0xfb9380a01bf8743fb9ea2a4b07dadd52dce701c4055dd1249473ffbd458ef561"  # 100% cow
#tx_hash = "0x6096b3f7d2c1ee87aebefbee0befd3ec5f79f9304c66bb5edf27603146faaccd"  # mixed
#tx_hash = "0x060c32d4ecbbd987d1d3c00761ee8ab7b189f7e3324658b9ab24fc0b6293d441"  # partial & complex
#tx_hash = "0xa797e6ca3952ff7bf4cbd4f465f1e49a2b2c1e8d12d1db3980fa87adbed4ff7c"  # partial
#compute_cowiness(tx_hash)