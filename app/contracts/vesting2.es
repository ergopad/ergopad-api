{{
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
    val totalBuyerOutput = OUTPUTS.filter({{(box: Box) => box.propositionBytes == SELF.R4[Coll[Byte]].get && 
                                                        box.R4[Coll[Byte]].get == SELF.R9[Coll[Byte]].get &&
                                                        box.tokens.size==1 &&
                                                        box.tokens(0)._1 == SELF.tokens(0)._1}})
                                    .fold(0L, {{(z: Long,box: Box) => z+box.tokens(0)._2}})

    val tokenZeroSum = totalBuyerOutput == redeemableTokens

    val selfOutput = SELF.tokens(0)._2 == redeemableTokens || //Either all remaining tokens are taken out OR
                        OUTPUTS.exists {{(box: Box) => box.value == SELF.value && //There is an output box with the exact same characteristics as the current box
                                                    box.propositionBytes == SELF.propositionBytes &&
                                                    box.tokens(0)._1 == SELF.tokens(0)._1 &&
                                                    box.tokens(0)._2 == SELF.tokens(0)._2 - redeemableTokens &&
                                                    box.R4[Coll[Byte]].get == SELF.R4[Coll[Byte]].get &&
                                                    box.R5[Long].get == SELF.R5[Long].get &&
                                                    box.R6[Long].get == SELF.R6[Long].get &&
                                                    box.R7[Long].get == SELF.R7[Long].get &&
                                                    box.R8[Long].get == SELF.R8[Long].get &&
                                                    box.R9[Coll[Byte]].get == SELF.R9[Coll[Byte]].get}}

    // check for proper tokenId?
    sigmaProp(tokenZeroSum && selfOutput)
}}