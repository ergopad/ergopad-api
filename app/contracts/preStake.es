{{
    // preStake
    // Registers:
    // 4: Coll[Byte]: Ergotree of user wallet
    // Assets
    // 0: ErgoPad: Amount of ergopad the user wants to stake
    val timestamp = {timestamp}
    val buyerPK = PK("{buyerWallet}")
    val stakedTokenID = fromBase64("{stakedTokenID}")
    val stakeStateNFT = fromBase64("{stakeStateNFT}")
    val stakeStateContract = fromBase64("{stakeStateContractHash}")
    val stakeContract = fromBase64("{stakeContractHash}")
    val outputs1Hash = blake2b256(OUTPUTS(1).propositionBytes)
    val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT && blake2b256(INPUTS(0).propositionBytes) == stakeStateContract
    if (stakeStateInput) {{ // Stake transaction
    //Stake State, preStake (SELF) => Stake State, Stake, User Wallet
        sigmaProp(allOf(Coll(
            // Stake
            outputs1Hash == stakeContract,
            OUTPUTS(1).tokens(0)._1 == INPUTS(0).tokens(1)._1,
            OUTPUTS(1).tokens(0)._2 == 1,
            OUTPUTS(1).tokens(1)._1 == stakedTokenID,
            SELF.tokens(0)._1 == stakedTokenID,
            OUTPUTS(1).tokens(1)._2 == SELF.tokens(0)._2,
            HEIGHT < timestamp
        )))
    }} else {{
        val total = INPUTS.fold(0L, {{(x:Long, b:Box) => x + b.value}}) - 2000000
        sigmaProp(OUTPUTS(0).value >= total && 
        OUTPUTS(0).propositionBytes == buyerPK.propBytes && 
        OUTPUTS.size == 2)
    }}
}}