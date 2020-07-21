# -*- coding: utf-8 -*-
import os, sys, json
import subprocess
import time
import datetime
import threading
from runbackdoor import *

CONTRACTFOLDER = '/home/ubuntu/smartIDE/webank/'

mythDict, oyneteDict, scDict, securifyDict, bdDict = {}, {}, {}, {}, {}
vulMap = {}

'''
    Mapping Vulnerability to entID
    @Use: Global Dict
'''

def init_mapping() :
    # some keys are not in the dictionary !! check first
    scDict['SOLIDITY_UNUSED_FUNCTION_SHOULD_BE_EXTERNAL'] = scDict['SOLIDITY_VISIBILITY'] = 'ent1'
    mythDict['101'] = oyneteDict['integer_overflow'] = oyneteDict['integer_underflow'] = scDict['SOLIDITY_SAFEMATH'] = 'ent2'
    scDict['SOLIDITY_PRAGMAS_VERSION'] = 'ent3'
    mythDict['104'] = scDict['SOLIDITY_UNCHECKED_CALL'] = 'ent4'
    mythDict['105'] = securifyDict['UnrestrictedEtherFlow'] = 'ent5'
    mythDict['106'] = oyneteDict['parity_multisig_bug_2'] = 'ent6'
    mythDict['107'] = oyneteDict['reentrancy'] = securifyDict['DAO'] = 'ent7'
    mythDict['110'] = oyneteDict['assertion_failure'] = 'ent8'
    mythDict['111'] = 'ent9'
    mythDict['112'] = 'ent10'
    mythDict['113'] = 'ent11'
    oyneteDict['money_concurrency'] = securifyDict['TODReceiver'] = securifyDict['TODTransfer'] = securifyDict['TODAmount'] = 'ent12'
    scDict['SOLIDITY_TX_ORIGIN'] = 'ent13'
    mythDict['116'] = oyneteDict['time_dependency'] = 'ent14'
    mythDict['117'] = 'ent15'
    mythDict['120'] = 'ent16'
    mythDict['124'] = scDict['SOLIDITY_ARRAY_LENGTH_MANIPULATION'] = 'ent17'
    mythDict['127'] = 'ent18'
    oyneteDict['callstack'] = 'ent19'
    scDict['SOLIDITY_ADDRESS_HARDCODED'] = 'ent20'
    scDict['SOLIDITY_BALANCE_EQUALITY'] = 'ent21'
    scDict['SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES'] = 'ent22'
    scDict['SOLIDITY_CALL_WITHOUT_DATA'] = 'ent23'
    scDict['SOLIDITY_CONSTRUCTOR_RETURN'] = 'ent24'
    scDict['SOLIDITY_DELETE_ON_DYNAMIC_ARRAYS'] = 'ent25'
    scDict['SOLIDITY_DEPRECATED_CONSTRUCTIONS'] = 'ent26'
    scDict['SOLIDITY_DIV_MUL'] = 'ent27'
    scDict['SOLIDITY_DO_WHILE_CONTINUE'] = 'ent28'
    scDict['SOLIDITY_ERC20_APPROVE'] = 'ent29'
    scDict['SOLIDITY_ERC20_FUNCTIONS_ALWAYS_RETURN_FALSE'] = 'ent30'
    scDict['SOLIDITY_ERC20_INDEXED'] = 'ent31'
    scDict['SOLIDITY_ERC20_TRANSFER_SHOULD_THROW'] = 'ent32'
    scDict['SOLIDITY_EXTRA_GAS_IN_LOOPS'] = 'ent33'
    scDict['SOLIDITY_INCORRECT_BLOCKHASH'] = 'ent34'
    scDict['SOLIDITY_LOCKED_MONEY'] = scDict['VYPER_LOCKED_MONEY'] = 'ent35'
    scDict['SOLIDITY_OVERPOWERED_ROLE'] = 'ent36'
    scDict['SOLIDITY_PRIVATE_MODIFIER_DOES_NOT_HIDE_DATA'] = 'ent37'
    scDict['SOLIDITY_REDUNDANT_FALLBACK_REJECT'] = 'ent38'
    scDict['SOLIDITY_REWRITE_ON_ASSEMBLY_CALL'] = 'ent39'
    scDict['SOLIDITY_SEND'] = 'ent40'
    scDict['SOLIDITY_SHOULD_NOT_BE_PURE'] = 'ent41'
    scDict['SOLIDITY_SHOULD_NOT_BE_VIEW'] = 'ent42'
    scDict['SOLIDITY_TRANSFER_IN_LOOP'] = 'ent43'
    scDict['SOLIDITY_UINT_CANT_BE_NEGATIVE'] = 'ent44'
    scDict['SOLIDITY_USING_INLINE_ASSEMBLY'] = 'ent45'
    scDict['SOLIDITY_VAR'] = scDict['SOLIDITY_VAR_IN_LOOP_FOR'] =  'ent46'
    scDict['SOLIDITY_WRONG_SIGNATURE'] = 'ent47'
    scDict['VYPER_BALANCE_EQUALITY'] = 'ent48'
    scDict['VYPER_ERC20_APPROVE'] = 'ent49'

    bdDict['ArbitraryTransfer'] = 'ent50'
    bdDict['GenerateToken'] = 'ent51'
    bdDict['DestroyToken'] = 'ent52'
    bdDict['FrozeAccount'] = 'ent53'
    bdDict['DisableTransfer'] = 'ent54'


'''
    Deal With Output File
    @Output: finalReport.json
'''

def deal_with_mythOut(contractName) :
    filepath = CONTRACTFOLDER + contractName + '/'

    if not os.path.exists(filepath + 'mythReport.txt') :
        print('Mythril file not find!')
        return
    if os.path.getsize(filepath + 'mythReport.txt') == 0 :
        print('Mythril file is empty!')
        return

    with open(filepath + 'mythReport.txt') as f :
        lines = f.readlines()
        maxLen = len(lines)
        mythType = ''
        lineNo = -1

        for idx in range(maxLen) :
            if '====' in lines[idx] :
                for l in range(idx+1, maxLen) :
                    if 'swcId:' in lines[l] :
                        # swcId: 111
                        mythType = lines[l][lines[l].find(':')+2:-1]
                    if 'In file:' in lines[l] :
                        # In file: /tmp/tx_origin.sol:20
                        lineNo = int(lines[l][lines[l].rfind(':')+1:-1])
                    if ('====' in lines[l]) or (l == (maxLen - 1)):
                        idx = l - 1
                        break
                if mythType in mythDict :
                    if lineNo not in vulMap[mythDict[mythType]] :
                        vulMap[mythDict[mythType]].append(lineNo)
                # print("*", mythType, lineNo)
        f.close()


def deal_with_oyenteOut(contractName) :
    # extract Oyente file name
    filename = ''
    f_list = os.listdir(CONTRACTFOLDER + contractName)
    for i in f_list :
        if os.path.splitext(i)[1] == '.json' and os.path.splitext(i)[0].find('.sol:') != -1 :
            filename = os.path.splitext(i)[0]
    # print(filename)

    filepath = CONTRACTFOLDER + contractName + '/'
    if not os.path.exists(filepath + filename + '.json') :
        print('Oyente file not find!')
        return
    if os.path.getsize(filepath + filename + '.json') == 0 :
        print('Oyente file is empty!')
        return

    with open(filepath + filename + '.json', 'r') as f:
        data = json.load(f)
        lineNo = -1

        for key, val in enumerate(data['vulnerabilities']) :
            infoList = data['vulnerabilities'][val]
            for idx, info in enumerate(infoList) :
                pos1 = info.find('.sol:') + 5
                pos2 = info[pos1:].find(':')
                lineNo = int(info[pos1:][:pos2])

                if lineNo not in vulMap[oyneteDict[val]] :
                    vulMap[oyneteDict[val]].append(lineNo)
                # print("**", val, lineNo)

        f.close()


def deal_with_smartcheckOut(contractName) :
    filepath = CONTRACTFOLDER + contractName + '/'

    if not os.path.exists(filepath + 'smartcheckReport.txt') :
        print('SmartCheck file not find!')
        return
    if os.path.getsize(filepath + 'smartcheckReport.txt') == 0 :
        print('SmartCheck file is empty!')
        return

    with open(filepath + 'smartcheckReport.txt') as f :
        lines = f.readlines()
        maxLen = len(lines)
        scType = ''
        lineNo = -1

        for idx in range(maxLen) :
            if 'ruleId:' in lines[idx] :
                for l in range(idx, maxLen) :
                    if 'ruleId:' in lines[l] :
                        # ruleId: SOLIDITY_TX_ORIGIN
                        scType = lines[l][lines[l].rfind(':')+2:-1]
                    if 'line:' in lines[l] :
                        # line: 10
                        lineNo = int(lines[l][lines[l].rfind(':')+2:-1])
                    if ('content:' in lines[l]) or (l == (maxLen - 1)):
                        idx = l
                        break
                if scType in scDict :
                    if lineNo not in vulMap[scDict[scType]] :
                        vulMap[scDict[scType]].append(lineNo)
                # print("***", scType, lineNo)
        f.close()


def deal_with_securifyOut(contractName) :
    pass


def deal_with_backdoorOut(lineList, backdoorList) :
    length = len(backdoorList)
    for i in range(length) :
        bdType = backdoorList[i]
        lineNo = lineList[i]
        vulMap[bdDict[bdType]].append(lineNo)


def dealOut_call(i, contractName) :
    if i == 0 :
        deal_with_smartcheckOut(contractName)
    elif i == 1 :
        deal_with_oyenteOut(contractName)
    elif i == 2 :
        deal_with_mythOut(contractName)
    return


def dealOutputs(num, contractName) :
    threads = []
    for i in range(num):
        t = threading.Thread(target=dealOut_call, args=(i, contractName,))
        threads.append(t)

    for thread in threads:
        thread.start()

    # for thread in threads:
        thread.join()

'''
    Execute Smart Contract Check Tool
    @Tool: Mythril \ Oyente \ SmartCheck \ Securify
    @Output: CURPATH/all report files
'''


from signal import signal, SIGPIPE, SIG_DFL
import shutil

signal(SIGPIPE, SIG_DFL)
   
def execute_command(toolName, cmd, timeout):
    devnull = open(os.devnull, 'w')
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=devnull, shell=True) 
    t_beginning = time.time() 
    seconds_passed = 0 
    while True: 
        if p.poll() is not None: 
            break 
        seconds_passed = time.time() - t_beginning 
        # print("*", seconds_passed)
        if timeout and seconds_passed > timeout: 
            p.terminate() 
            print(toolName + " running out time.")
            # raise TimeoutError(cmd, timeout) 
            return 0, seconds_passed
        time.sleep(0.1) 
    return 1, seconds_passed


def runTool_smartcheck(contractName, limitTime) :
    cmd_smartcheck = 'smartcheck -p ' + contractName + '.sol > smartcheckReport.txt'
    ret1, seconds_passed1 = execute_command("SmartCheck", cmd_smartcheck, timeout=limitTime)
    if ret1 :
        print("Run SmartCheck Complete! cost time :", seconds_passed1)

def runTool_oyente(contractName, limitTime) :
    cmd_oyente = 'sudo docker run -v $(pwd):/project qspprotocol/oyente-0.4.25 -s /project/' + contractName + '.sol -j'
    ret2, seconds_passed2 = execute_command("Oyente", cmd_oyente, timeout=limitTime)
    if ret2 :
        print("Run Oyente Complete! cost time :", seconds_passed2)

def runTool_myth(contractName, limitTime) :
    cmd_myth = 'sudo docker run -v $(pwd):/tmp mythril/myth analyze /tmp/' + contractName + '.sol | tee mythReport.txt'
    ret3, seconds_passed3 = execute_command("Mythril", cmd_myth, timeout=limitTime)
    if ret3 :
        print("Run Mythril Complete! cost time :", seconds_passed3)

# def runTool_securify(contractName, limitTime) :
    # cmd_securify = 'docker run -v $(pwd):/project qspprotocol/securify-usolc-0.5.3 -fs /project/'+ contractName + '.sol | tee securifyReport.json'
    # ret4 = subprocess.call(cmd_securify, shell=True)
    # if ret4 :
    #     print("Run Securify Complete!")


def runTools_call(contractName, limitTime, i) :
    if i == 0 :
        runTool_smartcheck(contractName, limitTime)
    elif i == 1 :
        runTool_oyente(contractName, limitTime)
    elif i == 2 :
        runTool_myth(contractName, limitTime)
    return


def runTools(contractName, limitTime, num) :
    threads = []
    for i in range(num):
        t = threading.Thread(target=runTools_call, args=(contractName, limitTime, i,))
        threads.append(t)
    
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


'''
    Get Attributes of Each Vulnerability
    @Attr: Name \ Description \ swcId \ Advice
'''

def getName(entID) :
    if entID == 'ent1' : return 'Function Default Visibility'
    elif entID == 'ent2' : return 'Integer Overflow and Underflow'
    elif entID == 'ent3' : return 'Outdated Compiler Version'
    elif entID == 'ent4' : return 'Unchecked Call Return Value'
    elif entID == 'ent5' : return 'Unprotected Ether Withdrawal'

    elif entID == 'ent6' : return 'Unprotected SELFDESTRUCT Instruction'
    elif entID == 'ent7' : return 'Reentrancy'
    elif entID == 'ent8' : return 'Assert Violation'
    elif entID == 'ent9' : return 'Use of Deprecated Solidity Functions'
    elif entID == 'ent10' : return 'Delegatecall to Untrusted Callee'

    elif entID == 'ent11' : return 'DoS with Failed Call'
    elif entID == 'ent12' : return 'Transaction Order Dependence'
    elif entID == 'ent13' : return 'Authorization through tx.origin'
    elif entID == 'ent14' : return 'Timestamp Dependence'
    elif entID == 'ent15' : return 'Signature Malleability'

    elif entID == 'ent16' : return 'Weak Sources of Randomness from Chain Attributes'
    elif entID == 'ent17' : return 'Write to Arbitrary Storage Location'
    elif entID == 'ent18' : return 'Arbitrary Jump with Function Type Variable'
    elif entID == 'ent19' : return 'Call-stack Depth Limit Exceeding'
    elif entID == 'ent20' : return 'Contract contains unknown address'

    elif entID == 'ent21' : return 'Checking for strict balance equality'
    elif entID == 'ent22' : return 'Use bytes instead of byte[]'
    elif entID == 'ent23' : return 'Use of call function with no data'
    elif entID == 'ent24' : return 'Use of return in constructor'
    elif entID == 'ent25' : return 'Deletion of dynamically-sized storage array'

    elif entID == 'ent26' : return 'Deprecated constructions'
    elif entID == 'ent27' : return 'Multiplication after division'
    elif entID == 'ent28' : return 'Using continue in the do-while loop'
    elif entID == 'ent29' : return 'Using approve function of the ERC-20 token standard'
    elif entID == 'ent30' : return 'Return value is always false'

    elif entID == 'ent31' : return 'Use of unindexed arguments in ERC-20 standard events'
    elif entID == 'ent32' : return 'ERC-20 transfer should throw'
    elif entID == 'ent33' : return 'Extra gas consumption'
    elif entID == 'ent34' : return 'Incorrect blockhash function'
    elif entID == 'ent35' : return 'Locked money'

    elif entID == 'ent36' : return 'Overpowered role'
    elif entID == 'ent37' : return 'Private modifier'
    elif entID == 'ent38' : return 'Redundant fallback function'
    elif entID == 'ent39' : return 'Output overwrites input of assembly CALLs'
    elif entID == 'ent40' : return 'Send instead of transfer'

    elif entID == 'ent41' : return 'Incorrect Pure-functions'
    elif entID == 'ent42' : return 'Incorrect View-functions'
    elif entID == 'ent43' : return 'ETH transfer inside the loop'
    elif entID == 'ent44' : return 'Non-strict comparison with zero'
    elif entID == 'ent45' : return 'Use inline assembly'

    elif entID == 'ent46' : return 'Unsafe type inference'
    elif entID == 'ent47' : return 'Incorrect function signature'
    elif entID == 'ent48' : return 'Checking for strict balance equality'
    elif entID == 'ent49' : return 'ERC-20 approve function'

    elif entID == 'ent50' : return 'ArbitraryTransfer problem'
    elif entID == 'ent51' : return 'GenerateToken problem'
    elif entID == 'ent52' : return 'DestroyToken problem'
    elif entID == 'ent53' : return 'FrozeAccount problem'
    elif entID == 'ent54' : return 'DisableTransfer problem'

def getDescription(entID) :
    if entID == 'ent1' : return 'Functions that do not have a function visibility type specified are public by default. This can lead to a vulnerability if a developer forgot to set the visibility and a malicious user is able to make unauthorized or unintended state changes.'
    elif entID == 'ent2' : return 'An overflow/underflow happens when an arithmetic operation reaches the maximum or minimum size of a type.'
    elif entID == 'ent3' : return 'Using an outdated compiler version can be problematic especially if there are publicly disclosed bugs and issues that affect the current compiler version.'
    elif entID == 'ent4' : return 'The return value of a message call is not checked. Execution will resume even if the called contract throws an exception. If the call fails accidentally or an attacker forces the call to fail, this may cause unexpected behaviour in the subsequent program logic.'
    elif entID == 'ent5' : return 'Due to missing or insufficient access controls, malicious parties can withdraw some or all Ether from the contract account.'

    elif entID == 'ent6' : return 'Due to missing or insufficient access controls, malicious parties can self-destruct the contract.'
    elif entID == 'ent7' : return 'One of the major dangers of calling external contracts is that they can take over the control flow. In the reentrancy attack (a.k.a. recursive call attack), a malicious contract calls back into the calling contract before the first invocation of the function is finished. This may cause the different invocations of the function to interact in undesirable ways.'
    elif entID == 'ent8' : return 'Properly functioning code should never reach a failing assert statement.'
    elif entID == 'ent9' : return 'Several functions and operators in Solidity are deprecated. Using them leads to reduced code quality. With new major versions of the Solidity compiler, deprecated functions and operators may result in side effects and compile errors.'
    elif entID == 'ent10' : return 'Calling into untrusted contracts is very dangerous, as the code at the target address can change any storage values of the caller and has full control over the caller\'s balance.'

    elif entID == 'ent11' : return 'External calls can fail accidentally or deliberately, which can cause a DoS condition in the contract.'
    elif entID == 'ent12' : return 'A race condition vulnerability occurs when code depends on the order of the transactions submitted to it.'
    elif entID == 'ent13' : return 'tx.origin is a global variable in Solidity which returns the address of the account that sent the transaction. Using the variable for authorization could make a contract vulnerable if an authorized account calls into a malicious contract. A call could be made to the vulnerable contract that passes the authorization check since tx.origin returns the original sender of the transaction which in this case is the authorized account.'
    elif entID == 'ent14' : return 'Developers can\'t rely on the preciseness of the provided timestamp.'
    elif entID == 'ent15' : return 'A system that performs signature verification on contract level might be susceptible to attacks if the signature is part of the signed message hash. Valid signatures could be created by a malicious user to replay previously signed messages.'

    elif entID == 'ent16' : return 'Uable to create a strong enough source of randomness.'
    elif entID == 'ent17' : return 'The contract is responsible for ensuring that only authorized user or contract accounts may write to sensitive storage locations. If an attacker is able to write to arbitrary storage locations of a contract, the authorization checks may easily be circumvented. '
    elif entID == 'ent18' : return 'The problem arises when a user has the ability to arbitrarily change the function type variable and thus execute random code instructions. '
    elif entID == 'ent19' : return 'The Ethereum Virtual Machine implementation limits the call-stack\'s depth to 1024 frames. The call-stack\'s depth increases by one if a contract calls another via the send or call instruction. This opens an attack vector to deliberately cause the send instruction to fail.'
    elif entID == 'ent20' : return 'The contract contains an unknown address. This address might be used for some malicious activity.'

    elif entID == 'ent21' : return 'An adversary can forcibly send ether to any address via selfdestruct() or by mining.'
    elif entID == 'ent22' : return 'For lower gas consumption, byte[] is unsafe.'
    elif entID == 'ent23' : return 'Use of low-level call function with no arguments provided.'
    elif entID == 'ent24' : return 'Return statement is used in the contract\'s constructor. With return the process of deployment will differ from the intuitive one. For instance, deployed bytecode may not include functions implemented in the source.'
    elif entID == 'ent25' : return 'Applying delete or .length = 0 to dynamically-sized storage arrays may lead to Out-of-Gas exception.'

    elif entID == 'ent26' : return 'Deprecated constructions: years, sha3, suicide, throw and constant functions.Use keccak256 instead of sha3.'
    elif entID == 'ent27' : return 'Solidity operates only with integers. Thus, if the division is done before the  multiplication, the rounding errors can increase dramatically.'
    elif entID == 'ent28' : return 'Prior to version 0.5.0, Solidity compiler handles continue inside do-while loop incorrectly: it ignores while condition.'
    elif entID == 'ent29' : return 'The approve function of ERC-20 is vulnerable. Using front-running attack one can spend approved tokens before change of allowance value.'
    elif entID == 'ent30' : return 'The transfer, transferFrom or approve functions do not return true for any values of input parameters.'

    elif entID == 'ent31' : return 'Address arguments of Transfer and Approve events of ERC-20 token standard must be indexed.'
    elif entID == 'ent32' : return 'Functions of ERC-20 Token Standard should throw in special cases: a) transfer should throw if the _from account balance does not have enough tokens to spend; b) transferFrom should throw unless the _from account has deliberately authorized the sender of the message via some mechanism.'
    elif entID == 'ent33' : return 'State variable, .balance, or .length of non-memory array is used in the condition of for or while loop. In this case, every iteration of loop consumes extra gas.'
    elif entID == 'ent34' : return 'Blockhash function returns a non-zero value only for 256 last blocks. Besides, it always returns 0 for the current block.'
    elif entID == 'ent35' : return 'Contracts programmed to receive ether should implement a way to withdraw it.'

    elif entID == 'ent36' : return 'This function is callable only from one address. Therefore, the system depends heavily on this address. In this case, there are scenarios that may lead to undesirable consequences for investors, e.g. if the private key of this address becomes compromised.'
    elif entID == 'ent37' : return 'Contrary to a popular misconception, the private modifier does not make a variable invisible. Miners have access to all contracts\' code and data.'
    elif entID == 'ent38' : return 'The payment rejection fallback is redundant.'
    elif entID == 'ent39' : return 'Dangerous use of inline assembly instruction of CALL family, which overwrites the input with the output.'
    elif entID == 'ent40' : return 'The send function is called inside checks instead of using transfer.'

    elif entID == 'ent41' : return 'In Solidity, functions that do not read from the state or modify it can be declared as pure.'
    elif entID == 'ent42' : return 'In Solidity, functions that do not read from the state or modify it can be declared as view.'
    elif entID == 'ent43' : return 'ETH is transferred in a loop. If at least one address cannot receive ETH (e.g. it is a contract with default fallback function), the whole transaction will be reverted.'
    elif entID == 'ent44' : return 'Variables of uint type cannot be negative. Thus, comparing uint variable with zero (greater than or equal) is redundant. Also, it may lead to an underflow issue. Moreover, comparison with zero used in for-loop condition results in an infinite loop.'
    elif entID == 'ent45' : return 'Inline assembly is a way to access the Ethereum Virtual Machine at a low level. This discards several important safety features of Solidity.'

    elif entID == 'ent46' : return 'May cause overflow error.'
    elif entID == 'ent47' : return 'In Solidity, the function signature is defined as the canonical expression of the basic prototype without data location specifier, i.e. the function name with the parenthesised list of parameter types. Parameter types are split by a single comma - no spaces are used. '
    elif entID == 'ent48' : return 'The balance is checked for strict equality.'
    elif entID == 'ent49' : return 'ERC-20 approve function is vulnerable to front-running attack.'

    elif entID == 'ent50' : return 'When a hacker gets access to controlling this function, he can transfer tokens from one account to another one arbitrarily.'
    elif entID == 'ent51' : return 'When a hacker gets access to controlling this function, he can generate any amount of tokens.'
    elif entID == 'ent52' : return 'When a hacker gets access to controlling this function, he can destory any amount of tokens.'
    elif entID == 'ent53' : return 'When a hacker gets access to controlling this function, he can freeze any account.'
    elif entID == 'ent54' : return 'When a hacker gets access to controlling this function, he can disable all the transferations.'

def getSWC(entID) :
    if entID == 'ent1' : return '100'
    elif entID == 'ent2' : return '101'
    elif entID == 'ent3' : return '102'
    elif entID == 'ent4' : return '104'
    elif entID == 'ent5' : return '105'

    elif entID == 'ent6' : return '106'
    elif entID == 'ent7' : return '107'
    elif entID == 'ent8' : return '110'
    elif entID == 'ent9' : return '111'
    elif entID == 'ent10' : return '112'

    elif entID == 'ent11' : return '113'
    elif entID == 'ent12' : return '114'
    elif entID == 'ent13' : return '115'
    elif entID == 'ent14' : return '116'
    elif entID == 'ent15' : return '117'

    elif entID == 'ent16' : return '120'
    elif entID == 'ent17' : return '124'
    elif entID == 'ent18' : return '127'

    else : return ''

def getAdvice(entID) :
    if entID == 'ent1' : return 'Functions can be specified as being external, public, internal or private. It is recommended to make a conscious decision on which visibility type is appropriate for a function. This can dramatically reduce the attack surface of a contract system.'
    elif entID == 'ent2' : return 'It is recommended to use vetted safe math libraries for arithmetic operations consistently throughout the smart contract system.'
    elif entID == 'ent3' : return 'It is recommended to use a recent version of the Solidity compiler.'
    elif entID == 'ent4' : return 'If you choose to use low-level call methods, make sure to handle the possibility that the call will fail by checking the return value.'
    elif entID == 'ent5' : return 'Implement controls so withdrawals can only be triggered by authorized parties or according to the specs of the smart contract system.'

    elif entID == 'ent6' : return 'Consider removing the self-destruct functionality unless it is absolutely required. If there is a valid use-case, it is recommended to implement a multisig scheme so that multiple parties must approve the self-destruct action.'
    elif entID == 'ent7' : return 'Use transfer() instead of contract.call() to transfer Ether to untrusted addresses. And when using low-level calls, make sure all internal state changes are performed before the call is executed.'
    elif entID == 'ent8' : return 'Consider whether the condition checked in the assert() is actually an invariant. If not, replace the assert() statement with a require() statement. If the exception is indeed caused by unexpected behaviour of the code, fix the underlying bug(s) that allow the assertion to be violated.'
    elif entID == 'ent9' : return 'Solidity provides alternatives to the deprecated constructions. Most of them are aliases, thus replacing old constructions will not break current behavior.'
    elif entID == 'ent10' : return 'Use delegatecall with caution and make sure to never call into untrusted contracts. If the target address is derived from user input ensure to check it against a whitelist of trusted contracts.'

    elif entID == 'ent11' : return 'Implement the contract logic to handle failed calls.'
    elif entID == 'ent12' : return 'From the user perspective it is possible to mediate the ERC20 race condition by setting approvals to zero before changing them.'
    elif entID == 'ent13' : return 'tx.origin should not be used for authorization. Use msg.sender instead.'
    elif entID == 'ent14' : return 'Use block number or external source of timestamp via oracles.'
    elif entID == 'ent15' : return 'A signature should never be included into a signed message hash to check if previously messages have been processed by the contract.'

    elif entID == 'ent16' : return 'Using Bitcoin block hashes, as they are more expensive to mine.'
    elif entID == 'ent17' : return 'As a general advice, given that all data structures share the same storage (address) space, one should make sure that writes to one data structure cannot inadvertently overwrite entries of another data structure.'
    elif entID == 'ent18' : return 'The use of assembly should be minimal. A developer should not allow a user to assign arbitrary values to function type variables.'
    elif entID == 'ent19' : return 'Specifically, an attacker can prepare a contract to call itself 1023 times before sending a transaction to KoET to claim the throne from the current king. Thus, the attacker ensures that the call-stack\'s depth of KoET reaches 1024, causing the send instruction in Line 15 to fail. As the result, the current king will not receive any payment.'
    elif entID == 'ent20' : return 'It is required to check the address. Also, it is required to check the code of the called contract for vulnerabilities.'

    elif entID == 'ent21' : return 'Use non-strict inequality.'
    elif entID == 'ent22' : return 'Use bytes instead of byte[].'
    elif entID == 'ent23' : return 'In this case, transfer or send function call is more secure. Another option is to implement the desired functionality in the separate public function of the target contract. Nevertheless, if use of call function is necessary due to the target contract design, gas limit should be added .gas().'
    elif entID == 'ent24' : return 'Do not use return in the contract\'s constructor in order to increase code readability and transparency unless you clearly understand this vulnerability. Generally, it is not safe to use smart contracts that have assembly in the constructor.'
    elif entID == 'ent25' : return 'Restrict adding too many elements into storage array. Otherwise, allow partial deletion of array\'s elements.'

    elif entID == 'ent26' : return 'Use selfdestruct instead of suicide. Use revert() instead of throw. Use view instead of constant for functions. Use days instead of years.'
    elif entID == 'ent27' : return 'Carefully use * after / .'
    elif entID == 'ent28' : return 'Do not use continue instruction in the do-while loop.'
    elif entID == 'ent29' : return 'Only use the approve function of the ERC-20 standard to change allowed amount to 0 or from 0 (wait till transaction is mined and approved).'
    elif entID == 'ent30' : return 'It is required to return true, if the function was successful.'

    elif entID == 'ent31' : return 'Use indexed events\' arguments, as stated in ERC-20 Token Standard.'
    elif entID == 'ent32' : return 'The ERC20 standard recommends throwing exceptions in functions transfer and transferFrom.'
    elif entID == 'ent33' : return 'If state variable, .balance, or .length is used several times, holding its value in a local variable is more gas efficient. If .length of calldata-array is placed into local variable, the optimisation will be less significant.'
    elif entID == 'ent34' : return ''
    elif entID == 'ent35' : return 'Call transfer (recommended), send or call.value at least once.'

    elif entID == 'ent36' : return ''
    elif entID == 'ent37' : return ''
    elif entID == 'ent38' : return 'Delete it.'
    elif entID == 'ent39' : return ''
    elif entID == 'ent40' : return 'The recommended way to perform checked ether payments is addr.transfer(x), which automatically throws an exception if the transfer is unsuccessful.'

    elif entID == 'ent41' : return 'Use other function modifiers instead.'
    elif entID == 'ent42' : return 'Use other function modifiers instead.'
    elif entID == 'ent43' : return ''
    elif entID == 'ent44' : return 'Delete it.'
    elif entID == 'ent45' : return ''

    elif entID == 'ent46' : return 'Use correct integer type instead of var.'
    elif entID == 'ent47' : return 'Use uint256 and int256 instead of uint or int.'
    elif entID == 'ent48' : return 'Avoid checking for strict balance equality: an adversary can forcibly send Ether to any address via selfdestruct() function or by mining. Also, Ether can be sent to the precomputed contract\'s address.'
    elif entID == 'ent49' : return ''

    elif entID == 'ent50' : return ''
    elif entID == 'ent51' : return ''
    elif entID == 'ent52' : return ''
    elif entID == 'ent53' : return ''
    elif entID == 'ent54' : return ''


class Logger(object):
    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w")
 
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
 
    def flush(self):
        pass


def make_folder(contractName) :
    if os.path.exists(CONTRACTFOLDER + contractName) :
        return
    else :
        os.makedirs(CONTRACTFOLDER + contractName)

    if os.path.exists(CONTRACTFOLDER + contractName + '.sol') :
        shutil.move(CONTRACTFOLDER + contractName + '.sol', CONTRACTFOLDER + contractName + '/')


if __name__ == '__main__' :
    # python3 enTool.py filename limitTime
    contractName = sys.argv[1]
    if len(sys.argv) == 3 :
        limitTime = int(sys.argv[2])
    else : 
        limitTime = 60
    print("Time limit :", limitTime)

    make_folder(contractName)

    os.chdir(CONTRACTFOLDER + contractName)
    print(os.getcwd())

    # init
    init_mapping()
    maxIdx = 54
    for i in range(1, maxIdx+1) :
        idx = 'ent' + str(i)
        vulMap[idx] = []

    path = os.path.abspath(os.path.dirname(__file__))
    type = sys.getfilesystemencoding()
    sys.stdout = Logger(CONTRACTFOLDER + contractName + '/enToolLog.txt')

    with open(CONTRACTFOLDER + contractName + '/finalReport.json', 'w') as f:
        # run smart contract check tools
        checkTools = 3
        runTools(contractName, limitTime, checkTools)
        lineList, backdoorList = detect_backdoor(CONTRACTFOLDER, contractName, limitTime)
        print("Running tools done.")

        # deal with output information
        dealOutputs(checkTools, contractName)
        deal_with_backdoorOut(lineList, backdoorList)
        print("Vulnerability Map: ", vulMap)

        outJson = {"contractname": contractName + '.sol', "vulnerabilities": {}}
        for i in range(1, maxIdx+1) :
            entID = 'ent' + str(i)
            if len(vulMap[entID]) != 0 :
                outJson['vulnerabilities'][entID] = {}

                outJson['vulnerabilities'][entID]['name'] = getName(entID)
                outJson['vulnerabilities'][entID]['description'] = getDescription(entID)
                outJson['vulnerabilities'][entID]['swcId'] = getSWC(entID)
                outJson['vulnerabilities'][entID]['lineNo'] = vulMap[entID]
                outJson['vulnerabilities'][entID]['advice'] = getAdvice(entID)
        # print(outJson)

        # save to finalReport.json
        json.dump(outJson, f, indent=1)
        f.close()

    print("Writting to report file done.")

