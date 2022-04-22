{
    //Registers:
    //4: Long: nergPerUSD threshold for refund
    //5: Coll[Byte]: user ergotree
    //6: Coll[Byte]: proxy NFT token id

    val ErgUSDOracleNFT     = _ErgUSDOracleNFT

    //Normal case
    if (OUTPUTS.size==6) {
        val proxyRoundBox       = INPUTS(0).tokens(0)._1 == SELF.R6[Coll[Byte]].get
        val botReward           = OUTPUTS(4).value == 10000000 && OUTPUTS(4).tokens.size == 0
        val minerFee            = OUTPUTS(5).value == 10000000 && OUTPUTS(5).tokens.size == 0

        sigmaProp(allOf(Coll(
            proxyRoundBox,
            botReward,
            minerFee
        )))
    } else {

    val botRewardRefund     = OUTPUTS(1).value == 5000000 && OUTPUTS(1).tokens.size == 0
    val minerFeeRefund      = OUTPUTS(2).value == 2000000 && OUTPUTS(2).tokens.size == 0
    val refundBox           = OUTPUTS(0).value == SELF.value - 7000000 && OUTPUTS(0).tokens == SELF.tokens && OUTPUTS(0).propositionBytes == SELF.R5[Coll[Byte]].get

    //Refund due to erg price slipping
    if (CONTEXT.dataInputs(0).tokens(0)._1 == ErgUSDOracleNFT) {
        val aboveThreshold      = CONTEXT.dataInputs(0).R4[Long].get > SELF.R4[Long].get
        
        sigmaProp(allOf(Coll(
            aboveThreshold,
            botRewardRefund,
            minerFeeRefund,
            refundBox
        )))
    } else {

    if (CONTEXT.dataInputs(0).tokens(0)._1 == SELF.R6[Coll[Byte]].get) {
        val proxySoldOut        = CONTEXT.dataInputs(0).tokens(1)._2 < SELF.tokens(0)._2

        sigmaProp(allOf(Coll(
            proxySoldOut,
            botRewardRefund,
            minerFeeRefund,
            refundBox
        )))
    } else {
        sigmaProp(false)
    }}}
}