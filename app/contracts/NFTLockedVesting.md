# NFT Locked Vesting with whitelist token buyin
In this protocol the project that can sell tokens that need to be locked according to a certain vesting schedule and only to individuals holding whitelist tokens (which can be distributed in an airdrop according to a whitelist gathered using standard web2.0 methods).

## proxyNFTLockedVestingV2
This contract locks the tokens that need to be vested after the user has contributed. It ensures the correct user address gains the vesting key (NFT) that allows the user to redeem tokens when available. It also ensures the vesting parameters are correct (start date, period length etc.)

### Registers
- R4: Coll[Long]
  - 0: redeemPeriod
  - 1: numberOfPeriods
  - 2: vestingStart
  - 3: priceNum
  - 4: priceDenom
- R5: Coll[Byte]: vestedTokenId
- R6: Coll[Byte]: Seller address
- R7: Coll[Byte]: Whitelist tokenid

### Assets
0. Proxy NFT
1. Tokens to be vested

### Hardcoded values
- NFTLockedVestingContract: blake2b256 hash of NFTLockedVesting ergotree bytes
- ErgUSDOracleNFT: Token id of ergusd oracle NFT
- SigUSDTokenId: SigUSD token id

### Actions
- [Bootstrap](#action-bootstrap)
- [Vest](#action-vest)

## userProxyNFTLockedVesting
This is a simple proxy contract that the user will send funds to, to allow for a smoother UX during times of utxo contention. Once the user has contributed funds to this contract it will be picked up by off-chain bots to perform the vest transaction.

### Registers
- R4: Long: nergPerUSD threshold for refund
- R5: Coll[Byte]: user ergotree
- R6: Coll[Byte]: proxy NFT token id

### Assets
0. Whitelist tokens
1. (Optional) SigUSD

### Hardcoded values
- ErgUSDOracleNFT: Token id of ergusd oracle NFT

### Actions
- [Contribute](#action-contribute)
- [Vest](#action-vest)
- [Refund - Round sold out](#action-refund---round-sold-out)
- [Refund - Erg price slipped](#action-refund---erg-price-slipped)

## NFTLockedVesting
This is the long term contract the tokens the user received for contributing will be locked in. The tokens will be made available according to the vesting schedule configured in the registers.

### Registers
- R4: Coll[Long]
  - 0: redeemPeriod
  - 1: numberOfPeriods
  - 2: vestingStart
  - 3: totalVested
- R5: Coll[Byte]: vestingKeyId

### Assets
0. The vested tokens

### Actions
- [Vest](#action-vest)
- [Redeem](#action-redeem)

## Action: Bootstrap
This is the transaction where the seller locks the tokens into the proxyNFTLockedVestingV2 contract.

### Inputs
0. Seller box(es) holding the proxy NFT, the tokens to be vested and a minimal amount of erg

### Outputs
0. [proxyNFTLockedVestingV2](#proxynftlockedvestingv2)

## Action: Contribute
The user that owns whitelist tokens locks them along with enough erg or sigusd to allow the off-chain bots to perform the vest transaction.

### Inputs
0. User box(es) holding the whitelist tokens, sigusd and erg

### Outputs
0. [userProxyNFTLockedVesting](#userproxynftlockedvesting)

## Action: Vest
This is the transaction where the users' funds are transferred to the token seller and the tokens are vested in the vesting contract. The transaction mints a vesting key that is send to the user which can be used in redeem transactions. This transaction is normally handled by off-chain bots.

### Data-Inputs
0. ErgUSD oracle

### Inputs
0. [proxyNFTLockedVestingV2](#proxynftlockedvestingv2)
1. [userProxyNFTLockedVesting](#userproxynftlockedvesting)

### Outputs
0. [proxyNFTLockedVestingV2](<## proxyNFTLockedVestingV2>)
1. [NFTLockedVesting](#nftlockedvesting)
2. A box on the users' address holding the minted NFT, vesting key
3. A box holding the funds contributed by the user at the sellers' address
4. A box on the bot operators address holding the reward

## Action: Refund - Round sold out
When a round is sold out and a users funds are still locked in a proxy contract they need to be refunded.

### Data-Inputs
0. [proxyNFTLockedVestingV2](#proxynftlockedvestingv2)

### Inputs
0. [userProxyNFTLockedVesting](#userproxynftlockedvesting)

### Outputs
0. User box with refunded assets
1. A box on the bot operators address holding the reward

## Action: Refund - Erg price slipped
If for some reason the users funds have been waiting in a proxy contract for a long time and the erg price compared to usd has dropped enough for the proxyNFTLockedVestingV2 contract to no longer accept it the funds need to be refunded so the user can try again.

### Data-Inputs
0. ErgUSD oracle

### Inputs
0. [userProxyNFTLockedVesting](#userproxynftlockedvesting)

### Outputs
0. User box with refunded assets
1. A box on the bot operators address holding the reward

## Action: Redeem
This action allows the user holding the vesting key NFT to redeem the tokens that are available.

### Inputs
0. [NFTLockedVesting](#nftlockedvesting)
1. User box holding the vesting key NFT

### Ouputs
0. [NFTLockedVesting](#nftlockedvesting)
1. User box holding the redeemed tokens and vesting key NFT