from hashlib import blake2b
import pytest
from config import Config, Network
from ergo.appkit import ErgoAppKit, ErgoValueT
from sigmastate.lang.exceptions import InterpreterException
from org.ergoplatform.appkit import Address

CFG = Config[Network]
DEBUG = True # CFG.DEBUG

class TestProxyNFTLockedVesting:
    appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)

    sigusd = "81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a"
    ergusdoracle = "011d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
    proxyNFT = "021d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
    vestedTokenId = "031d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
    sellerAddress = Address.create("9h7L7sUHZk43VQC3PHtSp5ujAWcZtYmWATBH746wi75C5XHi68b")
    sellerProp = sellerAddress.getErgoContract().getErgoTree()
    whitelistTokenId = "041d3364de07e5a26f0c4eef0852cddb387039a921b7154ef3cab22c6eda887f"
    nErgPrice = 3.19e-7 #
    vestedTokenPrice = 0.001 #2 decimals

    with open(f'contracts/NFTLockedVesting.es') as f:
        script = f.read()
    nftLockedVestingContractTree = appKit.compileErgoScript(script)

    with open(f'contracts/proxyNFTLockedVesting.es') as f:
        script = f.read()
    proxyNftLockedVestingTree = appKit.compileErgoScript(
        script,
        {
            "_NFTLockedVestingContract": appKit.ergoValue(blake2b(bytes.fromhex(nftLockedVestingContractTree.bytesHex()), digest_size=32).digest(), ErgoValueT.ByteArray).getValue(),
            "_ErgUSDOracleNFT": appKit.ergoValue(ergusdoracle, ErgoValueT.ByteArrayFromHex).getValue(),
            "_SigUSDTokenId": appKit.ergoValue(sigusd, ErgoValueT.ByteArrayFromHex).getValue()     
        }
    )

    proxyVestingBox = appKit.buildInputBox(
        value=int(1e6),
        tokens={proxyNFT: 1, vestedTokenId: 1000000},
        registers = [
            appKit.ergoValue([
                int(1000*60*60*24),     #redeemPeriod
                int(365),               #numberOfPeriods
                int(1648771200000),     #vestingStart
                int(1),                 #priceNum
                int(1000)                 #priceDenom
            ],ErgoValueT.LongArray),
            appKit.ergoValue(vestedTokenId,ErgoValueT.ByteArrayFromHex),    #vestedTokenId
            appKit.ergoValue(sellerProp.bytes(),ErgoValueT.ByteArray),      #Seller address
            appKit.ergoValue(whitelistTokenId, ErgoValueT.ByteArrayFromHex) #Whitelist tokenid
        ],
        contract = appKit.contractFromTree(proxyNftLockedVestingTree))

    oracleBox = appKit.buildInputBox(
        value=int(1e6),
        tokens={ergusdoracle: 1},
        registers = [appKit.ergoValue(313479623,ErgoValueT.Long)],
        contract = Address.create("NTkuk55NdwCXkF1e2nCABxq7bHjtinX3wH13zYPZ6qYT71dCoZBe1gZkh9FAr7GeHo2EpFoibzpNQmoi89atUjKRrhZEYrTapdtXrWU4kq319oY7BEWmtmRU9cMohX69XMuxJjJP5hRM8WQLfFnffbjshhEP3ck9CKVEkFRw1JDYkqVke2JVqoMED5yxLVkScbBUiJJLWq9BSbE1JJmmreNVskmWNxWE6V7ksKPxFMoqh1SVePh3UWAaBgGQRZ7TWf4dTBF5KMVHmRXzmQqEu2Fz2yeSLy23sM3pfqa78VuvoFHnTFXYFFxn3DNttxwq3EU3Zv25SmgrWjLKiZjFcEcqGgH6DJ9FZ1DfucVtTXwyDJutY3ksUBaEStRxoUQyRu4EhDobixL3PUWRcxaRJ8JKA9b64ALErGepRHkAoVmS8DaE6VbroskyMuhkTo7LbrzhTyJbqKurEzoEfhYxus7bMpLTePgKcktgRRyB7MjVxjSpxWzZedvzbjzZaHLZLkWZESk1WtdM25My33wtVLNXiTvficEUbjA23sNd24pv1YQ72nY1aqUHa2").getErgoContract())

    def test_vesting_pure_erg(self):
        userInputBox = self.appKit.buildInputBox(
            value=int(10e9),
            tokens={self.whitelistTokenId: 100000},
            registers=None,
            contract=self.appKit.dummyContract()
        )

        proxyVestingOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.proxyNFT: 1, self.vestedTokenId: 900000},
            registers = [
                self.appKit.ergoValue([
                    int(1000*60*60*24),     #redeemPeriod
                    int(365),               #numberOfPeriods
                    int(1648771200000),     #vestingStart
                    int(1),                 #priceNum
                    int(1000)                 #priceDenom
                ],ErgoValueT.LongArray),
                self.appKit.ergoValue(self.vestedTokenId,ErgoValueT.ByteArrayFromHex),    #vestedTokenId
                self.appKit.ergoValue(self.sellerProp.bytes(),ErgoValueT.ByteArray),              #Seller address
                self.appKit.ergoValue(self.whitelistTokenId, ErgoValueT.ByteArrayFromHex) #Whitelist tokenid
            ],
            contract = self.appKit.contractFromTree(self.proxyNftLockedVestingTree)
        )

        vestingOutput = self.appKit.buildOutBox(
            value=int(1e6), 
            tokens={self.vestedTokenId: 100000}, 
            registers=[       
                self.appKit.ergoValue([
                    int(1000*60*60*24), #Redeem period
                    int(100000/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(100000)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.proxyVestingBox.getId().toString(), ErgoValueT.ByteArrayFromHex)                        
            ], 
            contract=self.appKit.contractFromTree(self.nftLockedVestingContractTree)
        )

        userOutput = self.appKit.mintToken(
            value=int(1e6),
            tokenId=self.proxyVestingBox.getId().toString(),
            tokenName="Vesting Key",
            tokenDesc="Vested",
            mintAmount=1,
            decimals=0,
            contract=self.appKit.dummyContract()
        )

        nergamount = int(100000*self.vestedTokenPrice/self.nErgPrice)
        print(nergamount)

        sellerOutput = self.appKit.buildOutBox(
            value=int(100000*self.vestedTokenPrice/self.nErgPrice+1),
            tokens={self.whitelistTokenId: 100000},
            registers=None,
            contract=self.sellerAddress.getErgoContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.proxyVestingBox, userInputBox],
            dataInputs= [self.oracleBox],
            outputs = [proxyVestingOutput,vestingOutput,userOutput,sellerOutput],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader()
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_vesting_pure_sigusd(self):
        userInputBox = self.appKit.buildInputBox(
            value=int(10e9),
            tokens={self.whitelistTokenId: 100000, self.sigusd: 100},
            registers=None,
            contract=self.appKit.dummyContract()
        )

        proxyVestingOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.proxyNFT: 1, self.vestedTokenId: 900000},
            registers = [
                self.appKit.ergoValue([
                    int(1000*60*60*24),     #redeemPeriod
                    int(365),               #numberOfPeriods
                    int(1648771200000),     #vestingStart
                    int(1),                 #priceNum
                    int(1000)                 #priceDenom
                ],ErgoValueT.LongArray),
                self.appKit.ergoValue(self.vestedTokenId,ErgoValueT.ByteArrayFromHex),    #vestedTokenId
                self.appKit.ergoValue(self.sellerProp.bytes(),ErgoValueT.ByteArray),              #Seller address
                self.appKit.ergoValue(self.whitelistTokenId, ErgoValueT.ByteArrayFromHex) #Whitelist tokenid
            ],
            contract = self.appKit.contractFromTree(self.proxyNftLockedVestingTree)
        )

        vestingOutput = self.appKit.buildOutBox(
            value=int(1e6), 
            tokens={self.vestedTokenId: 100000}, 
            registers=[       
                self.appKit.ergoValue([
                    int(1000*60*60*24), #Redeem period
                    int(100000/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(100000)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.proxyVestingBox.getId().toString(), ErgoValueT.ByteArrayFromHex)                        
            ], 
            contract=self.appKit.contractFromTree(self.nftLockedVestingContractTree)
        )

        userOutput = self.appKit.mintToken(
            value=int(1e6),
            tokenId=self.proxyVestingBox.getId().toString(),
            tokenName="Vesting Key",
            tokenDesc="Vested",
            mintAmount=1,
            decimals=0,
            contract=self.appKit.dummyContract()
        )

        sellerOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.whitelistTokenId: 100000, self.sigusd: 100},
            registers=None,
            contract=self.sellerAddress.getErgoContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.proxyVestingBox, userInputBox],
            dataInputs= [self.oracleBox],
            outputs = [proxyVestingOutput,vestingOutput,userOutput,sellerOutput],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader()
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_vesting_erg_sigusd(self):
        userInputBox = self.appKit.buildInputBox(
            value=int(10e9),
            tokens={self.whitelistTokenId: 100000, self.sigusd: 50},
            registers=None,
            contract=self.appKit.dummyContract()
        )

        proxyVestingOutput = self.appKit.buildOutBox(
            value=int(1e6),
            tokens={self.proxyNFT: 1, self.vestedTokenId: 900000},
            registers = [
                self.appKit.ergoValue([
                    int(1000*60*60*24),     #redeemPeriod
                    int(365),               #numberOfPeriods
                    int(1648771200000),     #vestingStart
                    int(1),                 #priceNum
                    int(1000)                 #priceDenom
                ],ErgoValueT.LongArray),
                self.appKit.ergoValue(self.vestedTokenId,ErgoValueT.ByteArrayFromHex),    #vestedTokenId
                self.appKit.ergoValue(self.sellerProp.bytes(),ErgoValueT.ByteArray),              #Seller address
                self.appKit.ergoValue(self.whitelistTokenId, ErgoValueT.ByteArrayFromHex) #Whitelist tokenid
            ],
            contract = self.appKit.contractFromTree(self.proxyNftLockedVestingTree)
        )

        vestingOutput = self.appKit.buildOutBox(
            value=int(1e6), 
            tokens={self.vestedTokenId: 100000}, 
            registers=[       
                self.appKit.ergoValue([
                    int(1000*60*60*24), #Redeem period
                    int(100000/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(100000)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.proxyVestingBox.getId().toString(), ErgoValueT.ByteArrayFromHex)                        
            ], 
            contract=self.appKit.contractFromTree(self.nftLockedVestingContractTree)
        )

        userOutput = self.appKit.mintToken(
            value=int(1e6),
            tokenId=self.proxyVestingBox.getId().toString(),
            tokenName="Vesting Key",
            tokenDesc="Vested",
            mintAmount=1,
            decimals=0,
            contract=self.appKit.dummyContract()
        )

        sellerOutput = self.appKit.buildOutBox(
            value=int(50000*self.vestedTokenPrice/self.nErgPrice+1),
            tokens={self.whitelistTokenId: 100000, self.sigusd: 50},
            registers=None,
            contract=self.sellerAddress.getErgoContract()
        )

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.proxyVestingBox, userInputBox],
            dataInputs= [self.oracleBox],
            outputs = [proxyVestingOutput,vestingOutput,userOutput,sellerOutput],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = self.appKit.preHeader()
        )

        signed = False

        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

class TestNFTLockedVesting:

    appKit = ErgoAppKit(CFG.node, Network, CFG.explorer)

    with open(f'contracts/NFTLockedVesting.es') as f:
        script = f.read()
    tree = appKit.compileErgoScript(script)
    contract = appKit.contractFromTree(tree)

    vestedTokenId = '81ba2a45d4539045995ad6ceeecf9f14b942f944a1c9771430a89c3f88ee898a'
    vestingKey = 'f9e5ce5aa0d95f5d54a7bc89c46730d9662397067250aa18a0039631c0f5b809'
    fakeVestingKey = 'f9e5ce5aa0d95f5d54a7bc89c46730d9662397067250aa18a0039631c0f5b808'

    duration = int(1000*60*60*24)

    vestingInputBox = appKit.buildInputBox(int(1e6), 
            {
                vestedTokenId: 999999
            }, 
            [       
                appKit.ergoValue([
                    duration,           #Redeem period
                    int(999999/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(999999)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                appKit.ergoValue(vestingKey, ErgoValueT.ByteArrayFromHex)                        
            ], 
            contract)

    def test_normal_redeem(self):          
        userInputBox = self.appKit.buildInputBox(int(2e6), 
            {
                self.vestingKey: 1
            }, 
            registers=None, contract=self.appKit.dummyContract())

        #Set the preheader to 2.5 days after vesting start, so 2*redeem amount should be free to claim
        preHeader = self.appKit.preHeader(timestamp=int(1648771200000+self.duration*2.5))

        newVestingBox = self.appKit.buildOutBox(self.vestingInputBox.getValue(), {
                self.vestedTokenId: int(999999-int(999999/365)*2)
            },
            [
                self.appKit.ergoValue([
                    self.duration,      #Redeem period
                    int(999999/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(999999)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.vestingKey, ErgoValueT.ByteArrayFromHex)                         
            ], self.contract)

        newUserBox = self.appKit.buildOutBox(int(1e6), {
            self.vestingKey: 1,
            self.vestedTokenId: int(999999/365)*2
            }, registers=None, contract=self.appKit.dummyContract())

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.vestingInputBox, userInputBox],
            outputs = [newVestingBox,newUserBox],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = preHeader
        )
        signed = False
        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_final_redeem(self):
        userInputBox = self.appKit.buildInputBox(int(2e6), 
            {
                self.vestingKey: 1
            }, 
            registers=None, contract=self.appKit.dummyContract())

        #Set the preheader to 2.5 days after vesting start, so 2*redeem amount should be free to claim
        preHeader = self.appKit.preHeader(timestamp=int(1648771200000+self.duration*366))

        newUserBox = self.appKit.buildOutBox(int(1e6), {
            self.vestingKey: 1,
            self.vestedTokenId: int(999999)
            }, registers=None, contract=self.appKit.dummyContract())

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.vestingInputBox, userInputBox],
            outputs = [newUserBox],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = preHeader
        )
        signed = False
        try:
            self.appKit.signTransaction(unsignedTx)
            signed = True
        except Exception as e:
            print(f"Error: {e}")
            signed = False
    
        assert signed

    def test_redeem_too_much(self):          
        userInputBox = self.appKit.buildInputBox(int(2e6), 
            {
                self.vestingKey: 1
            }, 
            registers=None, contract=self.appKit.dummyContract())

        #Set the preheader to 2.5 days after vesting start, so 2*redeem amount should be free to claim
        preHeader = self.appKit.preHeader(timestamp=int(1648771200000+self.duration*2.5))

        newVestingBox = self.appKit.buildOutBox(self.vestingInputBox.getValue(), {
                self.vestedTokenId: int(999999-int(999999/365)*3)
            },
            [
                self.appKit.ergoValue([
                    self.duration,      #Redeem period
                    int(999999/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(999999)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.vestingKey, ErgoValueT.ByteArrayFromHex)                         
            ], self.contract)

        newUserBox = self.appKit.buildOutBox(int(1e6), {
            self.vestingKey: 1,
            self.vestedTokenId: int(999999/365)*3
            }, registers=None, contract=self.appKit.dummyContract())

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.vestingInputBox, userInputBox],
            outputs = [newVestingBox,newUserBox],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = preHeader
        )

        with pytest.raises(InterpreterException):
            self.appKit.signTransaction(unsignedTx)

    def test_wrong_key_redeem(self):          
        userInputBox = self.appKit.buildInputBox(int(2e6), 
            {
                self.fakeVestingKey: 1
            }, 
            registers=None, contract=self.appKit.dummyContract())

        #Set the preheader to 2.5 days after vesting start, so 2*redeem amount should be free to claim
        preHeader = self.appKit.preHeader(timestamp=int(1648771200000+self.duration*2.5))

        newVestingBox = self.appKit.buildOutBox(self.vestingInputBox.getValue(), {
                self.vestedTokenId: int(999999-int(999999/365)*2)
            },
            [
                self.appKit.ergoValue([
                    self.duration,      #Redeem period
                    int(999999/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(999999)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.vestingKey, ErgoValueT.ByteArrayFromHex)                         
            ], self.contract)

        newUserBox = self.appKit.buildOutBox(int(1e6), {
            self.fakeVestingKey: 1,
            self.vestedTokenId: int(999999/365)*2
            }, registers=None, contract=self.appKit.dummyContract())

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.vestingInputBox, userInputBox],
            outputs = [newVestingBox,newUserBox],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = preHeader
        )
        with pytest.raises(InterpreterException):
            self.appKit.signTransaction(unsignedTx)

    def test_redeem_not_enough(self):          
        userInputBox = self.appKit.buildInputBox(int(2e6), 
            {
                self.vestingKey: 1
            }, 
            registers=None, contract=self.appKit.dummyContract())

        #Set the preheader to 2.5 days after vesting start, so 2*redeem amount should be free to claim
        preHeader = self.appKit.preHeader(timestamp=int(1648771200000+self.duration*2.5))

        newVestingBox = self.appKit.buildOutBox(self.vestingInputBox.getValue(), {
                self.vestedTokenId: int(999999-int(999999/365)*1)
            },
            [
                self.appKit.ergoValue([
                    self.duration,      #Redeem period
                    int(999999/365),    #Redeem amount per period  
                    int(1648771200000), #Start vesting april 1st
                    int(999999)         #Initial vesting amount
                ], ErgoValueT.LongArray),            
                #Vesting key
                self.appKit.ergoValue(self.vestingKey, ErgoValueT.ByteArrayFromHex)                         
            ], self.contract)

        newUserBox = self.appKit.buildOutBox(int(1e6), {
            self.vestingKey: 1,
            self.vestedTokenId: int(999999/365)*1
            }, registers=None, contract=self.appKit.dummyContract())

        unsignedTx = self.appKit.buildUnsignedTransaction(
            inputs = [self.vestingInputBox, userInputBox],
            outputs = [newVestingBox,newUserBox],
            fee = int(1e6),
            sendChangeTo = self.appKit.dummyContract().getAddress().getErgoAddress(),
            preHeader = preHeader
        )

        with pytest.raises(InterpreterException):
            self.appKit.signTransaction(unsignedTx)

