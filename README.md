# What

This repo contains code to compute, for every order in a settlement, the percent of volume that is matched against another order, a.k.a cowiness.

# How does it work

Take this example:


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