import org.ergoplatform.compiler.ErgoScalaCompiler._
import org.ergoplatform.playgroundenv.utils.ErgoScriptCompiler
import org.ergoplatform.playground._
import org.ergoplatform.{ErgoAddress, ErgoBox, ErgoBoxCandidate}
import org.ergoplatform.settings.ErgoAlgos
import scorex.crypto.hash.Blake2b256

import java.util.Base64
import java.nio.charset.StandardCharsets
import sigmastate.Values.{BigIntConstant, ByteArrayConstant, GroupElementConstant, LongArrayConstant, LongConstant}
import org.ergoplatform.appkit.{ErgoContract, ErgoType, ErgoValue, JavaHelpers}
import org.ergoplatform.playgroundenv.models.TokenInfo
import scorex.crypto.hash.Digest32
import scorex.util.ModifierId
import sigmastate.serialization.ErgoTreeSerializer
import special.collection.Coll

import scala.collection.mutable

object Main extends App {

  ///////////////////////////////////////////////////////////////////////////////////
  // Prepare A Test Scenario //
  ///////////////////////////////////////////////////////////////////////////////////
  // Create a simulated blockchain (aka "Mockchain")
  val blockchainSim = newBlockChainSimulationScenario("ErgoPad Staking Scenario")
  // Defining the amount of nanoergs in an erg, making working with amounts easier
  val nanoergsInErg = 1000000000L
  val minErg = 100000L
  // Create a new token called ERDoge
  val stakedTokenId = blockchainSim.newToken("ErgoPad")
  val stakeStateNFT = blockchainSim.newToken("ErgoPad Stake State")
  val stakePoolNFT = blockchainSim.newToken("ErgoPad Stake Pool")
  val emissionNFT = blockchainSim.newToken("ErgoPad Emission")
  val stakeTokenId = blockchainSim.newToken("ErgoPad Stake Token")

  val stakeKeys: mutable.Map[Coll[Byte], TokenInfo] = mutable.Map()

  // Define the ergopadio wallet
  val ergopadio = blockchainSim.newParty("Ergopad.io")

  // Define the erdoge buyers
  val stakerA = blockchainSim.newParty("Alice")
  val stakerB = blockchainSim.newParty("Bob")

  val emissionScript = """
  {
      // Emission
      // Registers:
      // 4:0 Long: Total amount staked
      // 4:1 Long: Checkpoint
      // 4:2 Long: Stakers
      // 4:3 Long: Emission amount
      // Assets:
      // 0: Emission NFT: Identifier for emit box
      // 1: Staked Tokens (ErgoPad): Tokens to be distributed

      val stakeStateNFT = _stakeStateNFT
      val stakeTokenID = _stakeTokenID
      val stakedTokenID = _stakedTokenID
      val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT

      if (stakeStateInput && INPUTS(2).id == SELF.id) { // Emit transaction
          val remainingAndDust = INPUTS(1).tokens(1)._2 + (if (SELF.tokens.size >= 2) SELF.tokens(1)._2 else 0L)
          sigmaProp(allOf(Coll(
              //Stake State, Stake Pool, Emission (self) => Stake State, Stake Pool, Emission
              OUTPUTS(2).propositionBytes == SELF.propositionBytes,
              OUTPUTS(2).R4[Coll[Long]].get(0) == INPUTS(0).R4[Coll[Long]].get(0),
              OUTPUTS(2).R4[Coll[Long]].get(1) == INPUTS(0).R4[Coll[Long]].get(1),
              OUTPUTS(2).R4[Coll[Long]].get(2) == INPUTS(0).R4[Coll[Long]].get(2),
              OUTPUTS(2).R4[Coll[Long]].get(3) == (if (INPUTS(1).R4[Coll[Long]].get(0) < remainingAndDust) INPUTS(1).R4[Coll[Long]].get(0) else remainingAndDust),
              OUTPUTS(2).tokens(0)._1 == SELF.tokens(0)._1,
              OUTPUTS(2).tokens(1)._1 == stakedTokenID,
              OUTPUTS(2).tokens(1)._2 == OUTPUTS(2).R4[Coll[Long]].get(3)
          )))
      } else {
      if (stakeStateInput && INPUTS(1).id == SELF.id) { // Compound transaction
          // Stake State, Emission (SELF), Stake*N => Stake State, Emission, Stake*N
          val stakeBoxes = INPUTS.filter({(box: Box) => if (box.tokens.size > 0) box.tokens(0)._1 == stakeTokenID && box.R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(1) else false})
          val rewardsSum = stakeBoxes.fold(0L, {(z: Long, box: Box) => z+(box.tokens(1)._2*SELF.R4[Coll[Long]].get(3)/SELF.R4[Coll[Long]].get(0))})
          val remainingTokens = if (SELF.tokens(1)._2 <= rewardsSum) OUTPUTS(1).tokens.size == 1 else (OUTPUTS(1).tokens(1)._1 == stakedTokenID && OUTPUTS(1).tokens(1)._2 >= (SELF.tokens(1)._2 - rewardsSum))
          sigmaProp(allOf(Coll(
               OUTPUTS(1).propositionBytes == SELF.propositionBytes,
               OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
               remainingTokens,
               OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
               OUTPUTS(1).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
               OUTPUTS(1).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2) - stakeBoxes.size,
               OUTPUTS(1).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3)
           )))
      } else {
          sigmaProp(false)
      }
      }
  }
  """.stripMargin

  val emissionContract = ErgoScriptCompiler.compile(
    Map(
      "_stakedTokenID" -> stakedTokenId.tokenId,
      "_stakeStateNFT" -> stakeStateNFT.tokenId,
      "_stakeTokenID" -> stakeTokenId.tokenId
    ),
    emissionScript
  )

  val stakePoolScript = """
  {
      // Stake Pool
      // Registers:
      // 4:0 Long: Emission amount per cycle
      // Assets:
      // 0: Stake Pool NFT
      // 1: Remaining Staked Tokens for future distribution (ErgoPad)

      val stakeStateNFT = _stakeStateNFT
      val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT
      if (stakeStateInput && INPUTS(1).id == SELF.id) { // Emit transaction
          val remainingAndDust = SELF.tokens(1)._2 + (if (INPUTS(2).tokens.size >= 2) INPUTS(2).tokens(1)._2 else 0L)
          val tokensRemaining = if (remainingAndDust > SELF.R4[Coll[Long]].get(0))
                                  OUTPUTS(1).tokens(1)._1 == SELF.tokens(1)._1 &&
                                  OUTPUTS(1).tokens(1)._2 == remainingAndDust - SELF.R4[Coll[Long]].get(0)
                                else
                                  OUTPUTS(1).tokens.size == 1
          sigmaProp(allOf(Coll(
              //Stake State, Stake Pool (self), Emission => Stake State, Stake Pool, Emission
              OUTPUTS(1).propositionBytes == SELF.propositionBytes,
              OUTPUTS(1).tokens(0)._1 == SELF.tokens(0)._1,
              tokensRemaining,
              OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0)
          )))
      } else {
          sigmaProp(false)
      }
  }
  """.stripMargin

  val stakePoolContract = ErgoScriptCompiler.compile(
    Map(
      "_stakeStateNFT" -> stakeStateNFT.tokenId
    ),
    stakePoolScript
  )

  val stakeScript = """
  {
      // Stake
      // Registers:
      // 4:0 Long: Checkpoint
      // 4:1 Long: Stake time
      // 5: Coll[Byte]: Stake Key ID to be used for unstaking
      // Assets:
      // 0: Stake Token: 1 token to prove this is a legit stake box
      // 1: Staked Token (ErgoPad): The tokens staked by the user

      val stakeStateNFT = _stakeStateNFT
      val emissionNFT = _emissionNFT
      val stakeStateInput = INPUTS(0).tokens(0)._1 == stakeStateNFT

      if (INPUTS(1).tokens(0)._1 == emissionNFT) { // Compound transaction
          // Stake State, Emission, Stake*N (SELF) => Stake State, Emission, Stake * N
          val boxIndex = INPUTS.indexOf(SELF,0)
          val selfReplication = OUTPUTS(boxIndex)
           sigmaProp(allOf(Coll(
               stakeStateInput,
               selfReplication.value == SELF.value,
               selfReplication.propositionBytes == SELF.propositionBytes,
               selfReplication.R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + 1,
               selfReplication.R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get,
               selfReplication.R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
               selfReplication.tokens(0)._1 == SELF.tokens(0)._1,
               selfReplication.tokens(0)._2 == SELF.tokens(0)._2,
               selfReplication.tokens(1)._1 == SELF.tokens(1)._1,
               selfReplication.tokens(1)._2 == SELF.tokens(1)._2 + (INPUTS(1).R4[Coll[Long]].get(3) * SELF.tokens(1)._2 / INPUTS(1).R4[Coll[Long]].get(0))
           )))
      } else {
      if (INPUTS(1).id == SELF.id) { // Unstake
          val selfReplication = if (OUTPUTS(2).propositionBytes == SELF.propositionBytes)
                                  if (OUTPUTS(2).R5[Coll[Byte]].isDefined)
                                    OUTPUTS(2).R5[Coll[Byte]].get == SELF.R5[Coll[Byte]].get &&
                                    OUTPUTS(1).tokens(1)._1 == INPUTS(1).R5[Coll[Byte]].get
                                  else
                                    false
                                else true
          sigmaProp(stakeStateInput && selfReplication) //Stake state handles logic here to minimize stake box size
      } else {
          sigmaProp(false)
      }
      }
  }
  """.stripMargin

  val stakeContract = ErgoScriptCompiler.compile(
    Map(
      "_stakeStateNFT" -> stakeStateNFT.tokenId,
      "_emissionNFT" -> emissionNFT.tokenId
    ),
    stakeScript
  )

  val stakeStateScript = s"""
    {
      // Stake State
      // Registers:
      // 4:0 Long: Total amount Staked
      // 4:1 Long: Checkpoint
      // 4:2 Long: Stakers
      // 4:3 Long: Last checkpoint timestamp
      // 4:4 Long: Cycle duration
      // Assets:
      // 0: Stake State NFT: 1
      // 1: Stake Token: Stake token to be handed to Stake Boxes

      val blockTime = 99999999999999L//CONTEXT.preHeader.timestamp
      val stakedTokenID = _stakedTokenID
      val stakePoolNFT = _stakePoolNFT
      val emissionNFT = _emissionNFT
      val cycleDuration = SELF.R4[Coll[Long]].get(4)
      val stakeContract = fromBase64(_stakeContract)
      val minimumStake = 1000L

      def isStakeBox(box: Box) = if (box.tokens.size >= 1) box.tokens(0)._1 == SELF.tokens(1)._1 else false
      def isCompoundBox(box: Box) = if (box.tokens.size >= 1) isStakeBox(box) || box.tokens(0)._1 == emissionNFT || box.tokens(0)._1 == SELF.tokens(0)._1 else false

      val selfReplication = allOf(Coll(
          OUTPUTS(0).propositionBytes == SELF.propositionBytes,
          OUTPUTS(0).value == SELF.value,
          OUTPUTS(0).tokens(0)._1 == SELF.tokens(0)._1,
          OUTPUTS(0).tokens(0)._2 == SELF.tokens(0)._2,
          OUTPUTS(0).tokens(1)._1 == SELF.tokens(1)._1,
          OUTPUTS(0).R4[Coll[Long]].get(4) == cycleDuration,
          OUTPUTS(0).tokens.size == 2
      ))
      if (OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1) { // Stake transaction
          // Stake State (SELF), User wallet => Stake State, Stake, Stake Key (User)
          sigmaProp(allOf(Coll(
              selfReplication,
              // Stake State
              OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + OUTPUTS(1).tokens(1)._2,
              OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
              OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2)+1,
              OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
              OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2-1,
              // Stake
              blake2b256(OUTPUTS(1).propositionBytes) == stakeContract,
              OUTPUTS(1).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(1),
              //Disabled in playground OUTPUTS(1).R4[Coll[Long]].get(1) >= blockTime - 1800000L, //Give half an hour leeway for staking start
              //Disabled in playground OUTPUTS(1).R5[Coll[Byte]].get == SELF.id,
              OUTPUTS(1).tokens(0)._1 == SELF.tokens(1)._1,
              OUTPUTS(1).tokens(0)._2 == 1L,
              OUTPUTS(1).tokens(1)._1 == stakedTokenID,
              OUTPUTS(1).tokens(1)._2 >= minimumStake,
              //Stake key
              OUTPUTS(2).propositionBytes == INPUTS(1).propositionBytes,
              OUTPUTS(2).tokens(0)._1 == OUTPUTS(1).R5[Coll[Byte]].get,
              OUTPUTS(2).tokens(0)._2 == 1L
          )))
      } else {
      if (INPUTS(1).tokens(0)._1 == stakePoolNFT && INPUTS.size >= 3) { // Emit transaction
           // Stake State (SELF), Stake Pool, Emission => Stake State, Stake Pool, Emission
           sigmaProp(allOf(Coll(
               selfReplication,
               //Emission INPUT
               INPUTS(2).tokens(0)._1 == emissionNFT,
               INPUTS(2).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1) - 1L,
               INPUTS(2).R4[Coll[Long]].get(2) == 0L,
               //Stake State
               OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0),
               OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1) + 1L,
               OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
               OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3) + SELF.R4[Coll[Long]].get(4),
               OUTPUTS(0).R4[Coll[Long]].get(3) < blockTime,
               OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
           )))
      } else {
      if (INPUTS(1).tokens(0)._1 == emissionNFT) { // Compound transaction
            //Stake State (SELF), Emission, Stake*N => Stake State, Emission, Stake*N
            val leftover = if (OUTPUTS(1).tokens.size == 1) 0L else OUTPUTS(1).tokens(1)._2
            sigmaProp(allOf(Coll(
                 selfReplication,
                 //Stake State
                 OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0) + INPUTS(1).tokens(1)._2 - leftover,
                 OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
                 OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2),
                 OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
                 OUTPUTS(0).R4[Coll[Long]].get(4) == SELF.R4[Coll[Long]].get(4),
                 OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2
             )))
       } else {
       if (SELF.R4[Coll[Long]].get(0) > OUTPUTS(0).R4[Coll[Long]].get(0) && INPUTS.size >= 3) { // Unstake
           // Stake State (SELF), Stake, Stake Key Box => Stake State, User Wallet, Stake (optional for partial unstake)
           val unstaked = SELF.R4[Coll[Long]].get(0) - OUTPUTS(0).R4[Coll[Long]].get(0)
           val stakeKey = INPUTS(2).tokens.exists({(token: (Coll[Byte],Long)) => token._1 == INPUTS(1).R5[Coll[Byte]].get})
           val remaining = INPUTS(1).tokens(1)._2 - unstaked
           val timeInWeeks = (blockTime - INPUTS(1).R4[Coll[Long]].get(1))/(1000*3600*24*7)
           val penalty =  if (timeInWeeks >= 8) 0L else
                           if (timeInWeeks >= 6) unstaked*5/100 else
                           if (timeInWeeks >= 4) unstaked*125/1000 else
                           if (timeInWeeks >= 2) unstaked*20/100 else
                           unstaked*25/100
           val penaltyBurned = if (remaining == 0L)
                                OUTPUTS.size <= 4 && OUTPUTS(2).tokens.size==0
                                else
                                OUTPUTS.size <= 5 && OUTPUTS(3).tokens.size==0
           sigmaProp(allOf(Coll(
               selfReplication,
               stakeKey,
               penaltyBurned,
               //Stake State
               OUTPUTS(0).R4[Coll[Long]].get(0) == SELF.R4[Coll[Long]].get(0)-unstaked,
               OUTPUTS(0).R4[Coll[Long]].get(1) == SELF.R4[Coll[Long]].get(1),
               OUTPUTS(0).R4[Coll[Long]].get(2) == SELF.R4[Coll[Long]].get(2) - (if (remaining == 0L) 1L else 0L),
               OUTPUTS(0).R4[Coll[Long]].get(3) == SELF.R4[Coll[Long]].get(3),
               OUTPUTS(0).tokens(1)._2 == SELF.tokens(1)._2 + (if (remaining == 0L) 1L else 0L),
               //User wallet
               OUTPUTS(1).propositionBytes == INPUTS(2).propositionBytes,
               OUTPUTS(1).tokens(0)._1 == INPUTS(1).tokens(1)._1,
               OUTPUTS(1).tokens(0)._2 == unstaked - penalty,
               if (remaining > 0L) allOf(Coll(
                 //Stake output
                 OUTPUTS(2).value == INPUTS(1).value,
                 OUTPUTS(2).tokens(0)._1 == INPUTS(1).tokens(0)._1,
                 OUTPUTS(2).tokens(0)._2 == INPUTS(1).tokens(0)._2,
                 OUTPUTS(2).tokens(1)._1 == INPUTS(1).tokens(1)._1,
                 OUTPUTS(2).tokens(1)._2 == remaining,
                 remaining >= minimumStake,
                 OUTPUTS(2).R4[Coll[Long]].get(0) == INPUTS(1).R4[Coll[Long]].get(0),
                 OUTPUTS(2).R4[Coll[Long]].get(1) == INPUTS(1).R4[Coll[Long]].get(1)
                ))
                else true
           )))
       } else {
           sigmaProp(false)
       }
       }
       }
      }
  }
  """.stripMargin

  // Compile the contract with an included `Map` which specifies what the values of given parameters are going to be hard-coded into the contract
  val stakeStateContract = ErgoScriptCompiler.compile(
    Map(
      "_stakedTokenID" -> stakedTokenId.tokenId,
      "_stakePoolNFT" -> stakePoolNFT.tokenId,
      "_emissionNFT" -> emissionNFT.tokenId,
      "_stakeContract" -> Base64.getEncoder.encodeToString(
        Blake2b256(stakeContract.ergoTree.bytes)
      )
    ),
    stakeStateScript
  )

  ///////////////////////////////////////////////////////////////////////////////////
  // Wallet initializations                                                        //
  ///////////////////////////////////////////////////////////////////////////////////

  ergopadio.generateUnspentBoxes(
    toSpend = 1000 * nanoergsInErg,
    tokensToSpend = List(
      stakedTokenId -> 40000000000L,
      stakeStateNFT -> 1L,
      stakePoolNFT -> 1L,
      emissionNFT -> 1L,
      stakeTokenId -> 1000000000L
    )
  )
  ergopadio.printUnspentAssets()
  println("-----------")
  stakerA.generateUnspentBoxes(
    toSpend = 10 * nanoergsInErg,
    tokensToSpend = List(stakedTokenId -> 10000L))
  stakerB.generateUnspentBoxes(
    toSpend = 10 * nanoergsInErg,
    tokensToSpend = List(stakedTokenId -> 10000L))

  //Bootstrap

  def bootStrap(executor: Party): IndexedSeq[ErgoBox] =
  {
    val initStakeStateBox = Box(
      value = minErg,
      tokens = List(
        stakeStateNFT -> 1L,
        stakeTokenId -> 1000000000L
      ),
      registers = Map(
        R4 -> Array[Long](0L,0L,0L,0L,300000L)
      ),
      script = stakeStateContract
    )

    val initStakePoolBox = Box(
      value = minErg,
      tokens = List(
        stakePoolNFT -> 1L,
        stakedTokenId -> 32100000000L
      ),
      registers = Map(
        R4 -> Array[Long](29300000L)
      ),
      script = stakePoolContract
    )

    val initEmissionBox = Box(
      value = minErg,
      token = emissionNFT -> 1L,
      registers = Map(
        R4 -> Array[Long](0L,-1L,0L,29300000L)
      ),
      script = emissionContract
    )

    val bootstrapTransaction = Transaction(
      inputs = executor.selectUnspentBoxes(
        toSpend = 3 * minErg + MinTxFee,
        tokensToSpend = List(
          stakeStateNFT -> 1L,
          stakeTokenId -> 1000000000L,
          stakePoolNFT -> 1L,
          stakedTokenId -> 32100000000L,
          emissionNFT -> 1L
        )
      ),
      outputs = List(initStakeStateBox, initStakePoolBox, initEmissionBox),
      fee = MinTxFee,
      sendChangeTo = executor.wallet.getAddress
    )

    val bootstrapTransactionSigned = executor.wallet.sign(bootstrapTransaction)

    // Submit the tx to the simulated blockchain
    blockchainSim.send(bootstrapTransactionSigned)
    bootstrapTransactionSigned.outputs
  }

  val bootStrapOutput = bootStrap(ergopadio)
  var stakeState = bootStrapOutput(0)
  var stakePool = bootStrapOutput(1)
  var emission = bootStrapOutput(2)

  def stake(staker: Party, currentStakeState: ErgoBox, stakeAmount: Long): IndexedSeq[ErgoBox] = {
    val newStakeStateBox = Box(
      value = currentStakeState.value,
      tokens = List(
        stakeStateNFT -> 1L,
        stakeTokenId -> (currentStakeState.additionalTokens(1)._2 - 1L)
      ),
      registers = Map(
        R4 -> Array[Long]((LongArrayConstant
          .unapply(currentStakeState.additionalRegisters(R4))
          .get(0) + stakeAmount),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1),
          (LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(2) + 1L),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(3),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(4))
      ),
      script = stakeStateContract
    )

    //Simulate minting new nft
    val stakeKey = blockchainSim.newToken("ErgoPad Stake Key")
    stakeKeys += (stakeKey.tokenId -> stakeKey)
    val stakerBox = Box(
      value = minErg,
      token = stakeKey -> 1L,
      script = contract(staker.wallet.getAddress.pubKey)
    )

    val stakeBox = Box(
      value = minErg,
      tokens = List(
        stakeTokenId -> 1L,
        stakedTokenId -> stakeAmount
      ),
      registers = Map(
        R4 -> Array[Long](LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1),
          99998790400000L),
        R5 -> stakerBox.additionalTokens(0)._1
      ),
      script = stakeContract
    )

    val stakeTransaction = Transaction(
      inputs = List(currentStakeState) ++ staker.selectUnspentBoxes(
        toSpend = minErg + MinTxFee,
        tokensToSpend = List(stakedTokenId -> stakeAmount)
      ),
      outputs = List(newStakeStateBox, stakeBox, stakerBox),
      fee = MinTxFee,
      sendChangeTo = staker.wallet.getAddress
    )

    val stakeTransactionSigned = staker.wallet.sign(stakeTransaction)
    blockchainSim.send(stakeTransactionSigned)

    stakeTransactionSigned.outputs
  }

  var stakeOutput = stake(stakerA,stakeState,100000000L)
  stakeState = stakeOutput(0)
  var stakerABox = stakeOutput(1)

  stakeOutput = stake(stakerB,stakeState,1000L)
  stakeState = stakeOutput(0)
  var stakerBBox = stakeOutput(1)

  def emit(executor: Party, currentStakeState: ErgoBox, currentStakePool: ErgoBox, currentEmission: ErgoBox): IndexedSeq[ErgoBox] = {
    println("Emit")

    val newStakeState = Box(
      value = currentStakeState.value,
      tokens = List(
        stakeStateNFT -> 1L,
        stakeTokenId -> (currentStakeState.additionalTokens(1)._2)
      ),
      registers = Map(
        R4 -> Array[Long](LongArrayConstant
          .unapply(currentStakeState.additionalRegisters(R4))
          .get(0),
          (LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1) + 1L),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(2),
          (LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(3)+LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(4)),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(4))
      ),
      script = stakeStateContract
    )
    val newStakePoolAmount = if (currentEmission.additionalTokens.size > 1)
      (currentStakePool.additionalTokens(1)._2 - LongArrayConstant.unapply(currentStakePool.additionalRegisters(R4)).get(0) + currentEmission.additionalTokens(1)._2).max(0L)
    else
      (currentStakePool.additionalTokens(1)._2 - LongArrayConstant.unapply(currentStakePool.additionalRegisters(R4)).get(0)).max(0L)
    val emissionAmount = if (currentEmission.additionalTokens.size > 1)
      currentStakePool.additionalTokens(1)._2 - newStakePoolAmount + currentEmission.additionalTokens(1)._2
    else
      currentStakePool.additionalTokens(1)._2 - newStakePoolAmount
    val newStakePool = Box(
      value = currentStakePool.value,
      tokens = if (newStakePoolAmount>0L) List(
        stakePoolNFT -> 1L,
        stakedTokenId -> newStakePoolAmount
      ) else List(stakePoolNFT -> 1L),
      registers = Map(
        R4 -> Array[Long](LongArrayConstant.unapply(currentStakePool.additionalRegisters(R4)).get(0))
      ),
      script = stakePoolContract
    )

    val newEmission = Box(
      value = currentEmission.value,
      tokens = List(
        emissionNFT -> 1L,
        stakedTokenId -> emissionAmount
      ),
      registers = Map(
        R4 -> Array[Long](LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(0),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(2),
          emissionAmount)
      ),
      script = emissionContract
    )

    val emitTransaction = Transaction(
      inputs = List(currentStakeState, currentStakePool, currentEmission) ++ executor.selectUnspentBoxes(
        toSpend = MinTxFee
      ),
      outputs = List(newStakeState, newStakePool, newEmission),
      fee = MinTxFee,
      sendChangeTo = executor.wallet.getAddress
    )

    val emitTransactionSigned = executor.wallet.sign(emitTransaction)

    // Submit the tx to the simulated blockchain
    blockchainSim.send(emitTransactionSigned)
    emitTransactionSigned.outputs
  }

  var emitOutput = emit(ergopadio,stakeState,stakePool,emission)
  stakeState = emitOutput(0)
  stakePool = emitOutput(1)
  emission = emitOutput(2)

  def compound(executor: Party, currentStakeState: ErgoBox, currentEmission: ErgoBox, currentStakeBoxes: Array[ErgoBox]): IndexedSeq[ErgoBox] = {
    println("Compound")
    var totalAdded = 0L

    val stakeBoxOutputs = currentStakeBoxes.map((stakeBox: ErgoBox) => {
      val stakerReward = stakeBox.additionalTokens(1)._2 * LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(3) / LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(0)
      totalAdded += stakerReward

      Box(
        value = stakeBox.value,
        tokens = List(
          stakeTokenId -> 1L,
          stakedTokenId -> (stakeBox.additionalTokens(1)._2 + stakerReward)
        ),
        registers = Map(
          R4 -> Array[Long]((LongArrayConstant.unapply(stakeBox.additionalRegisters(R4)).get(0) + 1), LongArrayConstant.unapply(stakeBox.additionalRegisters(R4)).get(1)),
          R5 -> ByteArrayConstant.unapply(stakeBox.additionalRegisters(R5)).get.toArray
        ),
        script = stakeContract
      )
    })

    val newStakeState = Box(
      value = currentStakeState.value,
      tokens = List(
        stakeStateNFT -> 1L,
        stakeTokenId -> currentStakeState.additionalTokens(1)._2
      ),
      registers = Map(
        R4 -> Array[Long]((LongArrayConstant
          .unapply(currentStakeState.additionalRegisters(R4))
          .get(0) + totalAdded),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(2),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(3),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(4))
      ),
      script = stakeStateContract
    )

    val newEmission = Box(
      value = currentEmission.value,
      tokens = if (currentEmission.additionalTokens(1)._2 - totalAdded > 0) List(emissionNFT -> 1L, stakedTokenId -> (currentEmission.additionalTokens(1)._2 - totalAdded))
      else List(emissionNFT -> 1L),
      registers = Map(
        R4 -> Array[Long](LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(0),
          LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(1),
          (LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(2) - currentStakeBoxes.size),
          LongArrayConstant.unapply(currentEmission.additionalRegisters(R4)).get(3))
      ),
      script = emissionContract
    )

    val compoundTransaction = Transaction(
      inputs = List(currentStakeState, currentEmission) ++ currentStakeBoxes ++ executor.selectUnspentBoxes(
        toSpend = 2 * MinTxFee
      ),
      outputs = List(newStakeState, newEmission) ++ stakeBoxOutputs,
      fee = 2 * MinTxFee,
      sendChangeTo = executor.wallet.getAddress
    )

    val compoundTransactionSigned = executor.wallet.sign(compoundTransaction)

    // Submit the tx to the simulated blockchain
    blockchainSim.send(compoundTransactionSigned)
    compoundTransactionSigned.outputs
  }

  var compoundOutput = compound(ergopadio,stakeState,emission,Array[ErgoBox](stakerABox,stakerBBox))
  stakeState = compoundOutput(0)
  emission = compoundOutput(1)
  stakerABox = compoundOutput(2)
  stakerBBox = compoundOutput(3)

  emitOutput = emit(ergopadio,stakeState,stakePool,emission)
  stakeState = emitOutput(0)
  stakePool = emitOutput(1)
  emission = emitOutput(2)

  compoundOutput = compound(ergopadio,stakeState,emission,Array[ErgoBox](stakerBBox))
  stakeState = compoundOutput(0)
  emission = compoundOutput(1)
  stakerBBox = compoundOutput(2)

  compoundOutput = compound(ergopadio,stakeState,emission,Array[ErgoBox](stakerABox))
  stakeState = compoundOutput(0)
  emission = compoundOutput(1)
  stakerABox = compoundOutput(2)

  def unstake(unstaker: Party, _unstakeAmount: Long, currentStakeState: ErgoBox, stakeBox: ErgoBox): IndexedSeq[ErgoBox] = {
    val partialUnstake = (stakeBox.additionalTokens(1)._2 > _unstakeAmount)
    if (partialUnstake) println("Partial unstake") else println("Unstake")
    val unstakeAmount = math.min(_unstakeAmount,stakeBox.additionalTokens(1)._2)
    val outputs = new mutable.ListBuffer[ErgoBoxCandidate]()
    val unstakeKey = stakeKeys(ByteArrayConstant.unapply(stakeBox.additionalRegisters(R5)).get)
    outputs += Box(
      value = currentStakeState.value,
      tokens = List(
        stakeStateNFT -> 1L,
        stakeTokenId -> (currentStakeState.additionalTokens(1)._2 + (if (partialUnstake) 0L else 1L))
      ),
      registers = Map(
        R4 -> Array[Long]((LongArrayConstant
          .unapply(currentStakeState.additionalRegisters(R4))
          .get(0) - unstakeAmount),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(1),
          (LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(2) - (if (partialUnstake) 0L else 1L)),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(3),
          LongArrayConstant.unapply(currentStakeState.additionalRegisters(R4)).get(4))
      ),
      script = stakeStateContract
    )
    val penalty = unstakeAmount*25/100
    outputs += Box(
      value = minErg,
      tokens = if (partialUnstake) List(stakedTokenId -> (unstakeAmount-penalty), unstakeKey -> 1L)
        else List(stakedTokenId -> (unstakeAmount-penalty)),
      script = contract(unstaker.wallet.getAddress.pubKey)
    )
    if (partialUnstake) {
      outputs += Box(
        value = stakeBox.value,
        tokens = List(
          stakeTokenId -> 1L,
          stakedTokenId -> (stakeBox.additionalTokens(1)._2 - unstakeAmount)
        ),
        registers = Map(
          R4 -> Array[Long](LongArrayConstant.unapply(stakeBox.additionalRegisters(R4)).get(0),
            LongArrayConstant.unapply(stakeBox.additionalRegisters(R4)).get(1)),
          R5 -> ByteArrayConstant.unapply(stakeBox.additionalRegisters(R5)).get.toArray
        ),
        script = stakeContract
      )
    }
    //Steal penalty test
    //outputs += Box(
    //  value = minErg,
    //  tokens = List(stakedTokenId -> (unstakeAmount*25/100)),
    //  script = contract(unstaker.wallet.getAddress.pubKey)
    //)
    val unstakeTransaction = Transaction(
      inputs = List(currentStakeState, stakeBox) ++ unstaker.selectUnspentBoxes(
        toSpend = 2 * MinTxFee,
        tokensToSpend = List(unstakeKey -> 1L)
      ),
      outputs = outputs.toList,
      fee = 2 * MinTxFee,
      sendChangeTo = unstaker.wallet.getAddress
    )

    val unstakeTransactionSigned = unstaker.wallet.sign(unstakeTransaction)

    // Submit the tx to the simulated blockchain
    blockchainSim.send(unstakeTransactionSigned)
    unstakeTransactionSigned.outputs
  }

  var unstakeOutputs = unstake(stakerA,10000000000L,stakeState,stakerABox)
  stakeState = unstakeOutputs(0)

  emitOutput = emit(ergopadio,stakeState,stakePool,emission)
  stakeState = emitOutput(0)
  stakePool = emitOutput(1)
  emission = emitOutput(2)

  compoundOutput = compound(ergopadio,stakeState,emission,Array[ErgoBox](stakerBBox))
  stakeState = compoundOutput(0)
  emission = compoundOutput(1)
  stakerBBox = compoundOutput(2)

  unstakeOutputs = unstake(stakerB,100000L,stakeState,stakerBBox)
  stakeState = unstakeOutputs(0)
  stakerBBox = unstakeOutputs(2)

  emitOutput = emit(ergopadio,stakeState,stakePool,emission)
  stakeState = emitOutput(0)
  stakePool = emitOutput(1)
  emission = emitOutput(2)

  compoundOutput = compound(ergopadio,stakeState,emission,Array[ErgoBox](stakerBBox))
  stakeState = compoundOutput(0)
  emission = compoundOutput(1)
  stakerBBox = compoundOutput(2)
}