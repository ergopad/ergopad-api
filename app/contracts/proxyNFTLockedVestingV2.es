{
    // proxyNFTLockedVesting, user + (ergusd) -> proxyNFTLockedVesting, NFTLockedVesting, user, seller
    // R4: Coll[Long]
    //   0: redeemPeriod
    //   1: numberOfPeriods
    //   2: vestingStart
    //   3: priceNum
    //   4: priceDenom
    // R5: Coll[Byte]: vestedTokenId
    // R6: Coll[Byte]: Seller address
    // R7: Coll[Byte]: Whitelist tokenid
    // Assets:
    // 0: Unique NFT for this box
    // 1: Tokens to be vested

    val NFTLockedVestingContract    = _NFTLockedVestingContract
    val ErgUSDOracleNFT             = _ErgUSDOracleNFT
    val SigUSDTokenId               = _SigUSDTokenId

    val correctOracle               = CONTEXT.dataInputs(0).tokens(0)._1 == ErgUSDOracleNFT 
    val nergPerUSD                  = CONTEXT.dataInputs(0).R4[Long].get

    val proxyVestingOutputBox       = OUTPUTS(0)
    val vestingOutputBox            = OUTPUTS(1)
    val userOutputBox               = OUTPUTS(2)
    val sellerOutputBox             = OUTPUTS(3)

    val redeemPeriod                = SELF.R4[Coll[Long]].get(0)
    val numberOfPeriods             = SELF.R4[Coll[Long]].get(1)
    val vestingStart                = SELF.R4[Coll[Long]].get(2)
    val priceNum                    = SELF.R4[Coll[Long]].get(3)
    val priceDenom                  = SELF.R4[Coll[Long]].get(4)
    val vestedTokenId               = SELF.R5[Coll[Byte]].get
    val sellerPropositionBytes      = SELF.R6[Coll[Byte]].get
    val whitelistTokenId            = SELF.R7[Coll[Byte]].get

    val vestedTokens                = SELF.tokens(1)._2 - proxyVestingOutputBox.tokens(1)._2
    val sigUSDNeeded                = vestedTokens * priceNum / priceDenom

    // If the amount of vested tokens is low and the price per token is less than 1 sigusd 
    // token it could result in a price of 0 sigusd
    val requiredSigUSD              = if (sigUSDNeeded > 0L) 
                                        sigUSDNeeded 
                                      else 
                                        1L

    // The seller box will always contain whitelist tokens. If the buyer wants to pay with 
    // sigusd they will be put in the second token slot.
    val sellerSigUSD                = if (sellerOutputBox.tokens.size == 2) 
                                        if (sellerOutputBox.tokens(1)._1 == SigUSDTokenId) 
                                            sellerOutputBox.tokens(1)._2 
                                        else 
                                            0L 
                                      else 
                                        0L

    // Using the oracle data we calculate the sigusd value of the erg in the seller box.
    // We work with sigusd tokens so to account for decimals we multiply by 100
    val ergValueInSigUSD            = sellerOutputBox.value * 100 / nergPerUSD 
    val enoughSigUSD                = (sellerSigUSD + ergValueInSigUSD) >= requiredSigUSD

    val selfOutput                  = allOf(Coll(
                                        SELF.id                 == INPUTS(0).id,
                                        SELF.value              == proxyVestingOutputBox.value,
                                        SELF.propositionBytes   == proxyVestingOutputBox.propositionBytes,
                                        SELF.tokens(0)          == proxyVestingOutputBox.tokens(0),
                                        SELF.tokens(1)._1       == proxyVestingOutputBox.tokens(1)._1,
                                        SELF.R4[Coll[Long]].get == proxyVestingOutputBox.R4[Coll[Long]].get,
                                        SELF.R5[Coll[Byte]].get == proxyVestingOutputBox.R5[Coll[Byte]].get,
                                        SELF.R6[Coll[Byte]].get == proxyVestingOutputBox.R6[Coll[Byte]].get,
                                        SELF.R7[Coll[Byte]].get == proxyVestingOutputBox.R7[Coll[Byte]].get
                                    ))

    val vestingOutput               = allOf(Coll(
                                        vestingOutputBox.value                          == 1000000,
                                        blake2b256(vestingOutputBox.propositionBytes)   == NFTLockedVestingContract,
                                        vestingOutputBox.tokens(0)._1                   == vestedTokenId,
                                        vestingOutputBox.tokens(0)._2                   == vestedTokens,
                                        vestingOutputBox.R4[Coll[Long]].get(0)          == redeemPeriod,
                                        vestingOutputBox.R4[Coll[Long]].get(1)          == numberOfPeriods,
                                        //We need to avoid cases where the amount 
                                        //redeemed per period is 0 
                                        vestingOutputBox.R4[Coll[Long]].get(1)          > 0,   
                                        vestingOutputBox.R4[Coll[Long]].get(2)          == vestingStart,
                                        vestingOutputBox.R4[Coll[Long]].get(3)          == vestedTokens,
                                        vestingOutputBox.R5[Coll[Byte]].get             == SELF.id
                                    ))

    // The user will get a vesting key to be able to redeem tokens on demand. This key is minted in this 
    // transaction and will have the same id as the current box.
    val userOutput                  = allOf(Coll(
                                        userOutputBox.propositionBytes  == INPUTS(1).R5[Coll[Byte]].get,
                                        userOutputBox.tokens(0)._1      == SELF.id,
                                        userOutputBox.tokens(0)._2      == 1L
                                    ))

    val sellerOutput                = allOf(Coll(
                                        sellerOutputBox.propositionBytes    == sellerPropositionBytes,
                                        sellerOutputBox.tokens(0)._1        == whitelistTokenId,
                                        sellerOutputBox.tokens(0)._2        == vestedTokens
                                    ))

    sigmaProp(allOf(Coll(
        correctOracle,
        enoughSigUSD,
        selfOutput,
        vestingOutput,
        userOutput,
        sellerOutput
    )))
}