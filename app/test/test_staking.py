from hashlib import blake2b
import pytest
from config import Config, Network
from ergo_python_appkit.appkit import ErgoAppKit, ErgoValueT
from sigmastate.lang.exceptions import InterpreterException
from org.ergoplatform.appkit import Address
import logging

CFG = Config[Network]
DEBUG = True # CFG.DEBUG

class TestStakingIncentive:
    appKit = ErgoAppKit(CFG.node, Network, CFG.explorer, CFG.ergopadApiKey)

    stakeTokenID =  "1028de73d018f0c9a374b71555c5b8f1390994f2f41633e7b9d68f77735782ee"
    stakeStateNFT = "05cde13424a7972fbcd0b43fccbb5e501b1f75302175178fc86d8f243f3f3125"
    stakePoolNFT = "0d01f2f0b3254b4a1731e1b61ad77641fe54de2bd68d1c6fc1ae4e7e9ddfb212"
    stakedTokenID = "d71693c49a84fbbecd4908c94813b46514b18b67a99952dc1e6e4791556de413"
    emissionNFT = "0549ea3374a36b7a22a803766af732e61798463c3332c5f6d86c8ab9195eed59"
    emissionAddress = "xhRNa2Wo7xXeoEKbLcsW4gV1ggBwrCeXVkkjwMwYk4CVjHo95CLDHmomXirb8SVVtovXNPuqcs6hNMXdPPtT6nigbAqei9djAnpDKsAvhk5M4wwiKPf8d5sZFCMMGtthBzUruKumUW8WTLXtPupD5jBPELekR6yY4zHV4y21xtn7jjeqcb9M39RLRuFWFq2fGWbu5PQhFhUPCB5cbxBKWWxtNv8BQTeYj8bLw5vAH1WmRJ7Ln7SfD9RVePyvKdWGSkTFfVtg8dWuVzEjiXhUHVoeDcdPhGftMxWVPRZKRuMEmYbeaxLyccujuSZPPWSbnA2Uz6EketQgHxfnYhcLNnwNPaMETLKtvwZygfk1PuU9LZPbxNXNFgHuujfXGfQbgNwgd1hcC8utB6uZZRbxXAHmgMaWuoeSsni99idRHQFHTkmTKXx4TAx1kGKft1BjV6vcz1jGBJQyFBbQCTYBNcm9Yq2NbXmk5Vr7gHYbKbig7eMRT4oYxZdb9rwupphRGK4b2tYis9dXMT8m5EfFzxvAY9Thjbg8tZtWX7F5eaNzMKmZACZZqW3U7qS6aF8Jgiu2gdK12QKKBTdBfxaC6hBVtsxtQXYYjKzCmq1JuGP1brycwCfUmTUFkrfNDWBnrrmF2vrzZqL6WtUaSHzXzC4P4h346xnSvrtTTx7JGbrRCxhsaqTgxeCBMXgKgPGud2kNvgyKbjKnPvfhSCYnwhSdZYj8R1rr4TH5XjB3Wv8Z4jQjCkhAFGWJqVASZ3QXrFGFJzQrGLL1XX6cZsAP8cRHxqa7tJfKJzwcub7RjELPa2nnhhz5zj5F9MU1stJY4SBiX3oZJ6HdP9kNFGMR86Q6Z5qyfSRjwDNjVyvkKNoJ6Yk9nm367gznSVWkS9SG3kCUonbLgRt1Moq7o9CN5KrnyRgLrEAQU83SGY7Bc6FcLCZqQn8VqxP4e8R3vhf24nrzXVopydiYai"
    stakeStateAddress = "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"
    stakePoolAddress = "9hXmgvzndtakdSAgJ92fQ8ZjuKirWAw8tyDuyJrXP6sKHVpCz8XbMANK3BVJ1k3WD6ovQKTCasjKL5WMncRB6V9HvmMnJ2WbxYYjtLFS9sifDNXJWugrNEgoVK887bR5oaLZA95yGkMeXVfanxpNDZYaXH9KpHCpC5ohDtaW1PF17b27559toGVCeCUNti7LXyXV8fWS1mVRuz2PhLq5mB7hg2bqn7CZtVM8ntbUJpjkHUc9cP1R8Gvbo1GqcNWgM7gZkr2Dp514BrFz1cXMkv7TYEqH3cdxX9c82hH6fdaf3n6avdtZ5bgqerUZVDDW6ZsqxrqTyTMQUUirRAi3odmMGmuMqDJbU3Z1VnCF9NBow7jrKUDSgckDZakFZNChsr5Kq1kQyNitYJUh9fra1jLHCQ9yekz3te9E"
    stakeAddress = "3eiC8caSy3jiCxCmdsiFNFJ1Ykppmsmff2TEpSsXY1Ha7xbpB923Uv2midKVVkxL3CzGbSS2QURhbHMzP9b9rQUKapP1wpUQYPpH8UebbqVFHJYrSwM3zaNEkBkM9RjjPxHCeHtTnmoun7wzjajrikVFZiWurGTPqNnd1prXnASYh7fd9E2Limc2Zeux4UxjPsLc1i3F9gSjMeSJGZv3SNxrtV14dgPGB9mY1YdziKaaqDVV2Lgq3BJC9eH8a3kqu7kmDygFomy3DiM2hYkippsoAW6bYXL73JMx1tgr462C4d2PE7t83QmNMPzQrD826NZWM2c1kehWB6Y1twd5F9JzEs4Lmd2qJhjQgGg4yyaEG9irTC79pBeGUj98frZv1Aaj6xDmZvM22RtGX5eDBBu2C8GgJw3pUYr3fQuGZj7HKPXFVuk3pSTQRqkWtJvnpc4rfiPYYNpM5wkx6CPenQ39vsdeEi36mDL8Eww6XvyN4cQxzJFcSymATDbQZ1z8yqYSQeeDKF6qCM7ddPr5g5fUzcApepqFrGNg7MqGAs1euvLGHhRk7UoeEpofFfwp3Km5FABdzAsdFR9"

    with open(f'contracts/stakingIncentive.es') as f:
        script = f.read()
        
    stakingIncentiveTree = appKit.compileErgoScript(
        script,
        {
            "_emissionContractHash": ErgoAppKit.ergoValue(blake2b(bytes.fromhex(appKit.contractFromAddress(emissionAddress).getErgoTree().bytesHex()), digest_size=32).digest(), ErgoValueT.ByteArray).getValue(),
            "_stakeStateContractHash": ErgoAppKit.ergoValue(blake2b(bytes.fromhex(appKit.contractFromAddress(stakeStateAddress).getErgoTree().bytesHex()), digest_size=32).digest(), ErgoValueT.ByteArray).getValue(),
            "_stakeTokenID": ErgoAppKit.ergoValue(stakeTokenID, ErgoValueT.ByteArrayFromHex).getValue()     
        }
    )

    print(f'Staking incentive tree: {stakingIncentiveTree.bytesHex()}')

    stakeStateBox = appKit.buildInputBox(
        value=int(1e6),
        tokens={stakeStateNFT: 1, stakeTokenID: 1000000},
        registers = [
            ErgoAppKit.ergoValue([
                int(1000000),     #Total amount Staked
                int(42),               #Checkpoint
                int(4),     #Stakers
                int(1000),                 #Last checkpoint timestamp
                int(1000)                 #Cycle duration
            ],ErgoValueT.LongArray)
        ],
        contract = appKit.contractFromAddress(stakeStateAddress))

    stakePoolBox = appKit.buildInputBox(
        value=int(1e6),
        tokens={stakePoolNFT: 1, stakedTokenID: 1000000000},
        registers = [
            ErgoAppKit.ergoValue([
                int(293000)     #emission per cycle
            ],ErgoValueT.LongArray)
        ],
        contract = appKit.contractFromAddress(stakePoolAddress))

    emissionBox = appKit.buildInputBox(
        value=int(1e6),
        tokens={emissionNFT: 1, stakedTokenID: 1},
        registers = [
            ErgoAppKit.ergoValue([
                int(1000000),     #Total amount Staked
                int(41),               #Checkpoint
                int(0),     #Stakers
                int(293000)                 #emission per cycle
            ],ErgoValueT.LongArray)
        ],
        contract = appKit.contractFromAddress(emissionAddress))

    incentiveBox = appKit.buildInputBox(
        value=int(5e9),
        tokens=None,
        registers=None,
        contract=appKit.contractFromTree(stakingIncentiveTree)
    )

    def test_emit(self):
        stakeStateOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakeStateNFT: 1, self.stakeTokenID: 1000000},
            registers = [
                ErgoAppKit.ergoValue([
                    int(1292999),     #Total amount Staked
                    int(43),               #Checkpoint
                    int(4),     #Stakers
                    int(2000),                 #Last checkpoint timestamp
                    int(1000)                 #Cycle duration
                ],ErgoValueT.LongArray)
            ],
            contract = self.appKit.contractFromAddress(self.stakeStateAddress))

        stakePoolOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakePoolNFT: 1, self.stakedTokenID: 999707001},
            registers = [
                ErgoAppKit.ergoValue([
                    int(293000)     #emission per cycle
                ],ErgoValueT.LongArray)
            ],
            contract = self.appKit.contractFromAddress(self.stakePoolAddress))

        emissionOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.emissionNFT: 1, self.stakedTokenID: 293000},
            registers = [
                ErgoAppKit.ergoValue([
                    int(1000000),     #Total amount Staked
                    int(42),               #Checkpoint
                    int(4),     #Stakers
                    int(293000)                 #emission per cycle
                ],ErgoValueT.LongArray)
            ],
            contract = self.appKit.contractFromAddress(self.emissionAddress))

        incentiveOutput = self.appKit.buildOutBox(
            value=int(5e9)-int(4e6),
            tokens=None,
            registers=None,
            contract=self.appKit.contractFromTree(self.stakingIncentiveTree)
        )

        botOperatorOutput = self.appKit.buildOutBox(
            value=int(3e6),
            tokens=None,
            registers=None,
            contract=self.appKit.dummyContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.stakeStateBox,self.stakePoolBox,self.emissionBox,self.incentiveBox],
            dataInputs= [],
            outputs = [stakeStateOutput,stakePoolOutput,emissionOutput,incentiveOutput,botOperatorOutput],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().toAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader(100000000)
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_compound(self):
        emissionInput = self.appKit.buildInputBox(
            value=int(1e6),
            tokens={self.emissionNFT: 1, self.stakedTokenID: 293000},
            registers = [
                ErgoAppKit.ergoValue([
                    int(1000000),     #Total amount Staked
                    int(42),               #Checkpoint
                    int(4),     #Stakers
                    int(293000)                 #emission per cycle
                ],ErgoValueT.LongArray)
            ],
            contract = self.appKit.contractFromAddress(self.emissionAddress))
        
        emissionOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.emissionNFT: 1},
            registers = [
                ErgoAppKit.ergoValue([
                    int(1000000),     #Total amount Staked
                    int(42),               #Checkpoint
                    int(0),     #Stakers
                    int(293000)                 #emission per cycle
                ],ErgoValueT.LongArray)
            ],
            contract = self.appKit.contractFromAddress(self.emissionAddress))

        stake1Input = self.appKit.buildInputBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 250000},
            registers=[
                ErgoAppKit.ergoValue([int(42),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.emissionNFT, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake1Output = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 323250},
            registers=[
                ErgoAppKit.ergoValue([int(43),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.emissionNFT, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake2Input = self.appKit.buildInputBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 250000},
            registers=[
                ErgoAppKit.ergoValue([int(42),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakedTokenID, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake2Output = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 323250},
            registers=[
                ErgoAppKit.ergoValue([int(43),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakedTokenID, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake3Input = self.appKit.buildInputBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 250000},
            registers=[
                ErgoAppKit.ergoValue([int(42),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakePoolNFT, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake3Output = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 323250},
            registers=[
                ErgoAppKit.ergoValue([int(43),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakePoolNFT, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake4Input = self.appKit.buildInputBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 250000},
            registers=[
                ErgoAppKit.ergoValue([int(42),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakeTokenID, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        stake4Output = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.stakeTokenID: 1, self.stakedTokenID: 323250},
            registers=[
                ErgoAppKit.ergoValue([int(43),int(0)],ErgoValueT.LongArray),
                ErgoAppKit.ergoValue(self.stakeTokenID, ErgoValueT.ByteArrayFromHex)
            ],
            contract=self.appKit.contractFromAddress(self.stakeAddress)
        )
        txValue = int(900000 + 750000 * 4)
        minerFee = int(1000000 + 500000 * 4)
        incentiveOutput = self.appKit.buildOutBox(
            value=int(5e9)-txValue,
            tokens=None,
            registers=None,
            contract=self.appKit.contractFromTree(self.stakingIncentiveTree)
        )

        botOperatorOutput = self.appKit.buildOutBox(
            value=txValue-minerFee,
            tokens=None,
            registers=None,
            contract=self.appKit.dummyContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [emissionInput,stake1Input,stake2Input,stake3Input,stake4Input,self.incentiveBox],
            dataInputs= [],
            outputs = [emissionOutput,stake1Output,stake2Output,stake3Output,stake4Output,incentiveOutput,botOperatorOutput],
            fee = minerFee,
            sendChangeTo = self.appKit.dummyContract().toAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader(100000000)
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_dust_collection(self):
        incentiveInput1 = self.appKit.buildInputBox(
            value=int(3e6),
            tokens=None,
            registers = None,
            contract = self.appKit.contractFromTree(self.stakingIncentiveTree))
        
        incentiveInput2 = self.appKit.buildInputBox(
            value=int(4e6),
            tokens=None,
            registers = None,
            contract = self.appKit.contractFromTree(self.stakingIncentiveTree))

        incentiveInput3 = self.appKit.buildInputBox(
            value=int(5e6),
            tokens=None,
            registers = None,
            contract = self.appKit.contractFromTree(self.stakingIncentiveTree))
        
        reward = int(500000 * 3)

        incentiveOutput = self.appKit.buildOutBox(
            value=int(12e6)-reward-int(1e6),
            tokens=None,
            registers=None,
            contract=self.appKit.contractFromTree(self.stakingIncentiveTree)
        )

        botOperatorOutput = self.appKit.buildOutBox(
            value=reward,
            tokens=None,
            registers=None,
            contract=self.appKit.dummyContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [incentiveInput1,incentiveInput2,incentiveInput3],
            dataInputs= [],
            outputs = [incentiveOutput,botOperatorOutput],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().toAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader(100000000)
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    