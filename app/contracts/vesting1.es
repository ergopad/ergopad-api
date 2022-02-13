{{
    val buyerPK = PK("{buyerWallet}")
    val sellerPK = PK("{nodeWallet}")
    val vestingErgoTree = fromBase64("{vestingErgoTree}")
    val purchaseTokenId = fromBase64("{purchaseToken}")
    val purchaseTokenAmount = {purchaseTokenAmount}L
    val saleTokenId = fromBase64("{saleToken}")
    val saleTokenAmount = {saleTokenAmount}L
    val redeemPeriod = {redeemPeriod}L
    val redeemAmount = {redeemAmount}L
    val vestingStart = {vestingStart}L
    val timestamp = {timestamp}
    val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 2000000

    val sellerOutput = OUTPUTS(0).propositionBytes == sellerPK.propBytes &&
        ((purchaseTokenId.size == 0 && OUTPUTS(0).value == purchaseTokenAmount) ||
            (OUTPUTS(0).tokens(0)._2 == purchaseTokenAmount && OUTPUTS(0).tokens(0)._1 == purchaseTokenId))

    val vestingOutput = OUTPUTS(1).propositionBytes == vestingErgoTree &&
                        OUTPUTS(1).tokens(0)._1 == saleTokenId &&
                        OUTPUTS(1).tokens(0)._2 == saleTokenAmount &&
                        OUTPUTS(1).R4[Coll[Byte]].get == buyerPK.propBytes &&
                        OUTPUTS(1).R5[Long].get == redeemPeriod &&
                        OUTPUTS(1).R6[Long].get == redeemAmount &&
                        OUTPUTS(1).R7[Long].get == vestingStart &&
                        OUTPUTS(1).R8[Long].get == saleTokenAmount

    val returnFunds = OUTPUTS(0).value >= total && 
        OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
        OUTPUTS.size == 2

    sigmaProp((returnFunds || (sellerOutput && vestingOutput)) && HEIGHT < timestamp)
}}