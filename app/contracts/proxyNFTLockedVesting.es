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

    val NFTLockedVestingContract = _NFTLockedVestingContract
    val ErgUSDOracleNFT = _ErgUSDOracleNFT
    val SigUSDTokenId = _SigUSDTokenId

    val correctOracle = CONTEXT.dataInputs.size == 0 || CONTEXT.dataInputs(0).tokens(0)._1 == ErgUSDOracleNFT //No datainput or ergusd oracle
    val nergPerUSD = if (CONTEXT.dataInputs.size == 0) 1L else CONTEXT.dataInputs(0).R4[Long].get

    val vestedTokens = SELF.tokens(1)._2 - OUTPUTS(0).tokens(1)._2
    val requiredSigUSD = vestedTokens * SELF.R4[Coll[Long]].get(3) / SELF.R4[Coll[Long]].get(4) + 1
    val sellerSigUSD = if (OUTPUTS(3).tokens.size == 2) if (OUTPUTS(3).tokens(1)._1 == SigUSDTokenId) OUTPUTS(3).tokens(1)._2 else 0L else 0L
    val ergValueInSigUSD = OUTPUTS(3).value * 100 / nergPerUSD
    val enoughSigUSD = (sellerSigUSD + ergValueInSigUSD) >= requiredSigUSD

    val selfOutput = allOf(Coll(
        SELF.id == INPUTS(0).id,
        SELF.value == OUTPUTS(0).value,
        SELF.propositionBytes == OUTPUTS(0).propositionBytes,
        SELF.tokens(0)._1 == OUTPUTS(0).tokens(0)._1,
        SELF.tokens(0)._2 == OUTPUTS(0).tokens(0)._2,
        SELF.tokens(1)._1 == OUTPUTS(0).tokens(1)._1,
        SELF.R4[Coll[Long]].get == OUTPUTS(0).R4[Coll[Long]].get,
        SELF.R5[Coll[Byte]].get == OUTPUTS(0).R5[Coll[Byte]].get,
        SELF.R6[Coll[Byte]].get == OUTPUTS(0).R6[Coll[Byte]].get,
        SELF.R7[Coll[Byte]].get == OUTPUTS(0).R7[Coll[Byte]].get
    ))

    val vestingOutput = allOf(Coll(
        OUTPUTS(1).value == 1000000,
        blake2b256(OUTPUTS(1).propositionBytes) == NFTLockedVestingContract,
        OUTPUTS(1).tokens(0)._1 == SELF.R5[Coll[Byte]].get,
        OUTPUTS(1).tokens(0)._2 == vestedTokens,
        OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
        OUTPUTS(1).R4[Coll[Long]].get(1) == vestedTokens/SELF.R4[Coll[Long]].get(1),
        OUTPUTS(1).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
        OUTPUTS(1).R4[Coll[Long]].get(3) == vestedTokens,
        OUTPUTS(1).R5[Coll[Byte]].get == SELF.id,
    ))

    val userOutput = allOf(Coll(
        OUTPUTS(2).propositionBytes == INPUTS(1).propositionBytes,
        OUTPUTS(2).tokens(0)._1 == SELF.id,
        OUTPUTS(2).tokens(0)._2 == 1L
    ))

    val sellerOutput = allOf(Coll(
        OUTPUTS(3).propositionBytes == SELF.R6[Coll[Byte]].get,
        OUTPUTS(3).tokens(0)._1 == SELF.R7[Coll[Byte]].get,
        OUTPUTS(3).tokens(0)._2 == vestedTokens
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