{{
    //NFTLockedVesting, Vesting Key Box => NFTLockedVesting, Vesting Key + RedeemableTokens
    val blockTime = CONTEXT.preHeader.timestamp
    val redeemPeriod = SELF.R5[Long].get
    val redeemAmount = SELF.R6[Long].get
    val vestingStart = SELF.R7[Long].get
    val totalVested = SELF.R8[Long].get
    val timeVested = blockTime - vestingStart
    val periods = timeVested/redeemPeriod
    val redeemed = totalVested - SELF.tokens(0)._2
    val totalRedeemable = periods * redeemAmount
    val redeemableTokens = if (totalVested - totalRedeemable < redeemAmount) totalVested - redeemed else totalRedeemable - redeemed

    val vestingKeyInput = allOf(Coll(
        INPUTS(1).tokens.exists({{(token: (Coll[Byte], Long)) => token._1 == SELF.R4[Coll[Byte]].get}}),
        INPUTS(0).id == SELF.id
    ))

    val redeemedOutput = allOf(Coll(OUTPUTS(1).propositionBytes == INPUTS(1).propositionBytes, 
                                    OUTPUTS(1).tokens.size==2,
                                    OUTPUTS(1).tokens(0)._1 == SELF.R4[Coll[Byte]].get,
                                    OUTPUTS(1).tokens(1)._1 == SELF.tokens(0)._1,
                                    OUTPUTS(1).tokens(1)._2 == redeemableTokens))

    val selfOutput = SELF.tokens(0)._2 == redeemableTokens || //Either all remaining tokens are taken out OR
                        allOf(Coll(OUTPUTS(0).value == SELF.value, //There is an output box with the exact same characteristics as the current box
                                                    OUTPUTS(0).propositionBytes == SELF.propositionBytes,
                                                    OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
                                                    OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2 - redeemableTokens,
                                                    OUTPUTS(0).R4[Coll[Byte]].get == SELF.R4[Coll[Byte]].get,
                                                    OUTPUTS(0).R5[Long].get == SELF.R5[Long].get,
                                                    OUTPUTS(0).R6[Long].get == SELF.R6[Long].get,
                                                    OUTPUTS(0).R7[Long].get == SELF.R7[Long].get,
                                                    OUTPUTS(0).R8[Long].get == SELF.R8[Long].get
                        ))

    // check for proper tokenId?
    sigmaProp(vestingKeyInput && redeemedOutput && selfOutput)
}}