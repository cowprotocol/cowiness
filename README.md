# What

This repo contains code to compute, for every order in a settlement, the percent of volume that is matched against another order, a.k.a cowiness.

# How does it work

Take this example:

![image](https://user-images.githubusercontent.com/624308/192263717-646562a0-3d0a-43ce-9b19-7ad5d9461443.png)

1. Select a user order (0xceda), and compute all paths from its sell token (USDC) to its buy token (WETH). The union of the edges in these paths is the order's residual graph. 
2. For every node in the residual graph, compute the percent of volume going out of its outgoing edges (in red):

![image](https://user-images.githubusercontent.com/624308/192264653-a22832c2-1113-4933-af12-bdb6342c20ff.png)

3. For every path from its sell token (USDC) to its buy token (WETH) (there is just one in this example), compute the total fraction of volume flowing  on this path, which can be obtained by multiplying the percent of volume attached to every crossed outgoing edge. In this example is 100%.

4. If that path crosses another user order, then accumulate that value. Return the sum of these values for all paths.

For the second order, 0x2041, the residual graph is

![image](https://user-images.githubusercontent.com/624308/192265346-ebda3253-6254-4d9c-b6a6-fd1f1faf6fa1.png)

and the total fraction of volume that crosses another user order is 31%.

# Install

```bash
pip -m venv venv
venv/bin/activate
pip install -r requirements.txt
```

# Run

Set the following env vars (e.g. a src/.env file works too):

```
ORDERBOOK_URL=https://api.cow.fi/mainnet
WEB3_URL=https://mainnet.infura.io/v3/...
```

Activate virtualenv

```bash
venv/bin/activate
```

Run:

```bash
python -m src.cowiness 0xa797e6ca3952ff7bf4cbd4f465f1e49a2b2c1e8d12d1db3980fa87adbed4ff7c
```

# Examples

```bash
python -m src.cowiness 0xd531066dcf029e67ef9c1431106d7f03cdaf165de748ce121a355dbfadf775c3   # No cow
python -m src.cowiness 0xfb9380a01bf8743fb9ea2a4b07dadd52dce701c4055dd1249473ffbd458ef561   # 100% cow
python -m src.cowiness 0x6096b3f7d2c1ee87aebefbee0befd3ec5f79f9304c66bb5edf27603146faaccd  --consider-match-with-liquidity-orders 1 # mixed
python -m src.cowiness 0xa797e6ca3952ff7bf4cbd4f465f1e49a2b2c1e8d12d1db3980fa87adbed4ff7c   # partial
python -m src.cowiness 0x060c32d4ecbbd987d1d3c00761ee8ab7b189f7e3324658b9ab24fc0b6293d441   # partial & complex
```
