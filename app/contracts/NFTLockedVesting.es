{
    //NFTLockedVesting, Vesting Key Box => NFTLockedVesting, Vesting Key + RedeemableTokens

    val blockTime           = CONTEXT.preHeader.timestamp

    val redeemPeriod        = SELF.R4[Coll[Long]].get(0)
    val redeemAmount        = SELF.R4[Coll[Long]].get(1)
    val vestingStart        = SELF.R4[Coll[Long]].get(2)
    val totalVested         = SELF.R4[Coll[Long]].get(3)
    val vestingKeyId        = SELF.R5[Coll[Byte]].get

    val timeVested          = blockTime - vestingStart
    val periods             = timeVested/redeemPeriod
    val redeemed            = totalVested - SELF.tokens(0)._2
    val totalRedeemable     = periods * redeemAmount

    /*This is a test to find out whether we have arrived at the final redeeming period, which might 
      have extra tokens due to rounding after dividing by amount of periods.*/
    val redeemableTokens    = if (totalVested - totalRedeemable < redeemAmount) 
                                totalVested - redeemed 
                              else 
                                totalRedeemable - redeemed

    /*If we are in the final redeeming period there will not be a vesting box in the output and the 
      user box will be the first output*/
    val userOutputBox       = if (SELF.tokens(0)._2 == redeemableTokens) 
                                OUTPUTS(0) 
                              else 
                                OUTPUTS(1)

    val vestingOutputBox    = OUTPUTS(0)

    val vestingKeyInput     = allOf(Coll(
                                INPUTS(1).tokens.exists({{(token: (Coll[Byte], Long)) => token._1 == vestingKeyId}}),
                                INPUTS(0).id == SELF.id
                            ))

    val redeemedOutput      = allOf(Coll(
                                userOutputBox.propositionBytes == INPUTS(1).propositionBytes, 
                                userOutputBox.tokens.size==2,
                                userOutputBox.tokens(0)._1 == vestingKeyId,
                                userOutputBox.tokens(1)._1 == SELF.tokens(0)._1,
                                userOutputBox.tokens(1)._2 == redeemableTokens
                            ))

    /*We need to make sure that we are in the final period or that we have a vesting box in the output 
      that is the same as the current vesting box minus the tokens that are redeemed*/
    val selfOutput          = SELF.tokens(0)._2 == redeemableTokens || 
                                allOf(Coll(
                                    vestingOutputBox.value == SELF.value, 
                                    vestingOutputBox.propositionBytes == SELF.propositionBytes,
                                    vestingOutputBox.tokens(0)._1 == SELF.tokens(0)._1,
                                    vestingOutputBox.tokens(0)._2 == SELF.tokens(0)._2 - redeemableTokens,
                                    vestingOutputBox.R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get,
                                    vestingOutputBox.R4[Coll[Long]].get == SELF.R4[Coll[Long]].get
                                ))

    sigmaProp(vestingKeyInput && redeemedOutput && selfOutput)
}