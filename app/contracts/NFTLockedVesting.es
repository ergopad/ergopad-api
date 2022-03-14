{{
    //NFTLockedVesting, Vesting Key Box => NFTLockedVesting, Vesting Key + RedeemableTokens
    val blockTime = CONTEXT.preHeader.timestamp
    val redeemPeriod = SELF.R4[Coll[Long]].get(0)
    val redeemAmount = SELF.R4[Coll[Long]].get(1)
    val vestingStart = SELF.R4[Coll[Long]].get(2)
    val totalVested = SELF.R4[Coll[Long]].get(3)
    val timeVested = blockTime - vestingStart
    val periods = timeVested/redeemPeriod
    val redeemed = totalVested - SELF.tokens(0)._2
    val totalRedeemable = periods * redeemAmount
    val redeemableTokens = if (totalVested - totalRedeemable < redeemAmount) totalVested - redeemed else totalRedeemable - redeemed

    val userOutput = if (SELF.tokens(0)._2 == redeemableTokens) 0 else 1

    val vestingKeyInput = allOf(Coll(
        INPUTS(1).tokens.exists({{(token: (Coll[Byte], Long)) => token._1 == SELF.R5[Coll[Byte]].get}}),
        INPUTS(0).id == SELF.id
    ))

    val redeemedOutput = allOf(Coll(OUTPUTS(userOutput).propositionBytes == INPUTS(1).propositionBytes, 
                                    OUTPUTS(userOutput).tokens.size==2,
                                    OUTPUTS(userOutput).tokens(0)._1 == SELF.R5[Coll[Byte]].get,
                                    OUTPUTS(userOutput).tokens(1)._1 == SELF.tokens(0)._1,
                                    OUTPUTS(userOutput).tokens(1)._2 == redeemableTokens))

    val selfOutput = SELF.tokens(0)._2 == redeemableTokens || //Either all remaining tokens are taken out OR
                        allOf(Coll(OUTPUTS(0).value == SELF.value, //There is an output box with the exact same characteristics as the current box
                                                    OUTPUTS(0).propositionBytes == SELF.propositionBytes,
                                                    OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
                                                    OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2 - redeemableTokens,
                                                    OUTPUTS(0).R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get,
                                                    OUTPUTS(0).R4[Coll[Long]].get == SELF.R4[Coll[Long]].get
                        ))

    // check for proper tokenId?
    sigmaProp(vestingKeyInput && redeemedOutput && selfOutput)
}}