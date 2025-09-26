# Demo 01 - Basic AML scan

This demo runs TXGRAPH against a small, hand-crafted transaction log
(`transactions.csv`) that contains three planted laundering patterns plus
ordinary noise.

## The data

`transactions.csv` columns: `tx_id,src,dst,amount,timestamp,currency`.

Planted patterns:

1. **Structuring (smurfing)** - account `ACCT_SMURF` sends five separate
   sub-$10,000 transfers (each $9,200-$9,800) to different mule accounts
   within a single day, aggregating to well over the $10,000 reporting
   threshold.
2. **Layering** - `ORIG_A` -> `HOP_1` -> `HOP_2` -> `HOP_3` -> `DEST_Z`,
   where ~$48,000 is forwarded across each hop within hours (a fast
   pass-through chain).
3. **Mule fan-in/fan-out** - `MULE_X` receives from four distinct senders
   and forwards ~95% of the collected value onward to `EXIT_OFFSHORE`.

Plus a handful of benign transactions (salary, rent, coffee) as noise.

## Run it

```bash
python -m txgraph scan demos/01-basic/transactions.csv
python -m txgraph scan demos/01-basic/transactions.csv --format json
python -m txgraph scan demos/01-basic/transactions.csv --sar
```

## Expected result

The scan detects **at least three findings** - one each of
`structuring`, `layering`, and `mule`. The process exits with a
**non-zero status** because findings exist (useful as a CI gate). The
benign transactions produce no findings.
