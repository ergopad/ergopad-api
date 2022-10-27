---
name: Bootstrap IDO
about: Steps to bootstrap an IDO
title: BOOTSTRAP
labels: documentation
assignees: ''

---

# [Auction House Token](https://www.ergopad.io/projects/auctionhouse#roadmap)
AHT used as an example for template
```
project wallet: _________ (is this ergopad-owned?)
seller address: _________ (most likely create this new for the IDO)
token name: _________ (i.e. AHT)
token id: _________ (create this on the node wallet)
```
1. gather address/token_id
2. fill out template json for rounds
2.1 create token on node; can send remaining after smart contracts created (if any)
2.2 may work well to have new wallet as sellerAddress controlled by ergopad
2.3 tgeTime_ms and roundEnd_ms should be IDO time (unix timestamp in ms)
3. [bootstrap staking rounds](http://delta:2718/api/docs#/vesting/vesting_bootstrapRound_api_vesting_bootstrapRound_post)
4. put /api/vesting/activeRounds into cms

### Notes
- when minting, token name typically abbv+UPPER: AHT
- unlock node wallet when calling bootstrap endpoint
- for amounts -like roundAllocation- do not include the additional decimals (i.e. 12 tokens with 2 decimals would only be 12 and not 1200)
- consider making the whitelist multiplier at least 1.1 (or 2 if can't do float) to have tokens to test with
- roundName as [token name] [round] Round: EPOS Staker Round
- tgeTime is when vesting starts
- roundEnds is when possible to remove unsold tokens
- common timeframes 1d=86400000ms, 1mo=2628000000 | periods: 1m=30, 6m=182, 9m=274, 10m=304 .. *30.44
- once complete, test airdrop and make sure bots are processing

# !! EXAMPLE
```json
{
    "roundName": "Auction House Seed Round",
    "tokenId": "18c938e1924fc3eadc266e75ec02d81fe73b56e4e9f4e268dffffcb30387c42d",
    "roundAllocation": 90000000, 
    "vestingPeriods": 152,
    "vestingPeriodDuration_ms": 86400000,
    "cliff_ms": 2628000000,
    "tokenSigUSDPrice": 0.003,
    "whitelistTokenMultiplier": 2,
    "sellerAddress": "9gDxvcBkUKcu5cxKmKmhAFMBdrX5qjFz1YScoeuHrgRGu1v5jPu",
    "tgeTime_ms": 1666728000000,
    "tgePct": 0,
    "roundEnd_ms": 1666728000000
}
{
    "Whitelist token id": "33b5e5ad9c6452ecaa8f433075cb7dce217cfc7a8a496da02a072d437fc06539",
    "Proxy NFT": "b21d38f671759704fe9a4983cd316d3d05e74eea24cb97ccf48fde704e1f9d49",
    "NFT mint transaction": "2f18a31186ff3bf438ba9ae8ef8f27086dc9c15558451a00bc9b57074b3d746b",
    "Whitelist token mint and token lock transaction": "788daaed88bcf30c548f4ef4b799d4431c1b93d714f78e2f29623735ee89cef4",
    "Proxy address": "4qyzRyJzKPEYP9XSTWsXH6hzhMCH1rMx5JvcYpVwWpD79bLDex79Bj6hbLR1NnVVYFFLCGCTSGQDQTkh5dm5d2BQY5bQRpf1AycoDjAEZyQwxiLRpbwB8Kiqyi7mUvb5UcJRdtUQ6sqcDZpgyf3hBUCCy2vg8e8P3wSopzkensJ4SoG86upev1TXacBRqsm54dshaMdToMAyFBLD2DMsZPP89gEZF4UAuLbRxZDiK871fT1NVCwa7pWK29ySAipERxWwno112zQoF5a9htj37VavXkYTzcZQ24iVjrkrfxU12huR9ZPkvLHkrdu8y8WgFdFr5oKFMsm2teFCrXMx8n9MUEEymFSWhMXBvg5UAkKW5ido9Zo2BYWDj81ew5fUoWhdJGGCu33SegnLzbNiB6VaRNusiZSPwLBA2NZ5yF5UJrUnMZAqPqWZb7zZ2zL2cBwSrFJ7kxSrQeaJ1RNGcQiDyXmzDE9vpyWTbG9W1mW5KzzMD4B9FZoUcRYbmFdp31H5Ho27rTNfx64tr7Crgjm7WfWVp8zPXjxfjW6su6u2GK6cx3feavARGNjyKKrYW3H8yPFi1Y9ruwmNwTyW96Z42FE1D28VuD5C2SJYmegbg9nPKc3ByUbS5CHJQQ4DLX9DdgZvbtq44VsiR2VmbpZNrjMwEHybRcoiDeLNhoPqxinXNvFNjg9gSca1C47EiYy4S94eFqbY1rrcF84siSEUq31e9A6snNTcDEiQ3efCcEyCb1JgA5iLDU7kqoi6xxCt7TKVfA96EKSczjaqBk5jvrmAhZrDpwrKm1sSf8py21tUgbdyDoJccUdRniahbibSRc5PVpukkkKtAUXEDG91qNbbuh47QA2NjSMiqNQjYGNJTaiBBDsGbxXjwgFkJA45E9FaFzvMvGuJyKJY9Yx9e6KBoSq1ktY38WHkFe7PBLwyZxUowb4fmgexLKiUWfLNzoZhHYu8DuAkgRtVoPRQxZYrqdgkg4PwAF6AE7XHVJEUr6iQHwTWVkp9LajbPXKtFQmVpnFNowcVVrVSabX5aqAmEu1PKVKJjvLwumUwoyRi6NwMqudVKAEqP3vdtmqr1KWzs9mNqgAybP8qaUM9pif9CxTGUKPR5FEsgnJv3WwvdJwbYv2J"
}
```
