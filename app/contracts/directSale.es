{{
    val buyerPK             = PK("{buyerWallet}")
    val sellerPK            = PK("{nodeWallet}")
    val saleTokenId         = fromBase64("{saleTokenId}")
    val purchaseTokenId     = fromBase64("{purchaseTokenId}")
    val saleTokenAmount     = {saleTokenAmount}L
    val purchaseTokenAmount = {purchaseTokenAmount}L
    val timestamp           = {timestamp}
    val totalErg            = INPUTS.fold(0L, {{(x: Long, b: Box) => x + b.value}})
    val totalTokens         = INPUTS.fold(0L, {{(x: Long, b: Box) => x + b.tokens(0)._2}})

    val sellerOutput = OUTPUTS(0).propositionBytes == sellerPK.propBytes &&
        ((purchaseTokenId.size == 0 && OUTPUTS(0).value == purchaseTokenAmount) ||
        (OUTPUTS(0).tokens(0)._2 == purchaseTokenAmount && OUTPUTS(0).tokens(0)._1 == purchaseTokenId))

    val buyerOutput = OUTPUTS(1).propositionBytes == buyerPK.propBytes && 
        OUTPUTS(1).tokens(0)._2 == saleTokenAmount && 
        OUTPUTS(1).tokens(0)._1 == saleTokenId

    val returnFunds = OUTPUTS(0).value >= totalErg - 2000000 && 
        OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
        OUTPUTS.size == 2

    sigmaProp((returnFunds || (buyerOutput && sellerOutput)) && HEIGHT < timestamp)
}}