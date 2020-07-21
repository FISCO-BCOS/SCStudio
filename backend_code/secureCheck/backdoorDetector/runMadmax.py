import os, shutil, re
import csv
import subprocess
import functools

rootPath = '/home/renardbebe/Desktop/SmartIDE/SCCC/backdoorDetect/'

contractPath = rootPath + 'test2/'
tmpPath = rootPath + 'tmp/'
outputPath = rootPath + 'output/'


def dl_clean() :
    os.chdir(rootPath)
    subprocess.call("rm -rf " + tmpPath + "/*", shell=True)


def dl_init() :
    # tmp path
    if os.path.exists(tmpPath) :
        pass
    else :
        os.mkdir(tmpPath)
    # output path
    if os.path.exists(outputPath) :
        pass
    else :
        os.mkdir(outputPath)


def dl_load_data() :
    ret = []
    # for each contract bytecode in contractPath/
    AllFile = os.listdir(contractPath)
    # AllFile.sort(key=lambda x:int(x[:-4], 16))
    for file in AllFile:
        fileName = ''
        file_path = os.path.join(contractPath, file) 
        if os.path.splitext(file_path)[1] == '.sol':
            fileName = os.path.splitext(file_path)[0].split('/')[-1]
            ret.append(fileName)
        else :
            pass
    return ret


def cmp(x, y) :
    if int(x, 16) < int(y, 16):
        return -1
    if x == y:
        return 0
    else:
        return 1


def isLegal(ch) :
    if ch >= '0' and ch <= '9' : return True
    elif ch >= 'a' and ch <= 'z' : return True
    elif ch >= 'A' and ch <= 'Z' : return True
    elif ch == '[' or ch == ']' or ch == '.' : return True
    else : return False


def dl_modify(fileName, funcName, bugType) :
    pos_s = pos_e = -1

    with open(outputPath + fileName + '.sol', 'r') as readFile :
        lines = readFile.readlines()
        # search target funtion
        for i, line in enumerate(lines) :
            if line.find(funcName) != -1 :
                pos_s = i+1
                for j in range(pos_s, len(lines)) :
                    if lines[j].find('function') != -1 :
                        pos_e = j - 1
                        break
                    if j == len(lines) - 1 :
                        pos_e = j
                        break
                break
        print(pos_s, pos_e, bugType)
        readFile.close()

    with open(outputPath + fileName + '.sol', 'w') as outFile :
        # modify target function
        for idx, line in enumerate(lines) :
            if (idx >= pos_s) and (idx <= pos_e) :
                mLine = line
                if bugType == 0 :    # UnboundedMassOp
                    posLoop = line.find('for')
                    if posLoop != -1 :
                        addstr = ' && msg.gas > 100000'
                        posInsert = line.rfind(';')
                        mLine = line[:posInsert] + addstr + line[posInsert:]
                
                elif bugType == 1 :  # WalletGriefing
                    posSend = line.find('send')
                    if posSend != -1 :
                        pos0 = pos1 = pos2 = 0
                        pos3 = line.find(';')

                        for i in range(posSend, 0, -1) :
                            if i == 0 or line[i] == ' ' or line[i] == '\t' : 
                                pos0 = i + 1
                                break
                        for i in range(posSend, 0, -1) :
                            if isLegal(line[i]) :
                                continue
                            else :
                                pos1 = i + 1
                                break
                        cnt = 0
                        for i in range(posSend+4, len(line)) :
                            if line[i] == '(' :
                                cnt += 1
                            elif line[i] == ')' :
                                cnt -= 1
                            if cnt == 0 :
                                pos2 = i + 1
                                break

                        subline = line[pos1:pos2]
                        subline = subline.replace("send", "transfer")
                        # print("*", subline)
                        mLine = line.replace(line[pos0:pos3], subline)
                
                else :               # OverflowLoopIterator
                    posLoop = line.find('for')
                    if posLoop != -1 :
                        mLine = line.replace("var", "uint")
                outFile.write(mLine)
            else :
                outFile.write(line)
        outFile.close()


def dl_run() :
    fileList = dl_load_data()

    for fileName in fileList :
        os.chdir(tmpPath)

        if not os.path.exists(tmpPath + fileName) :
            os.system("mkdir " + fileName)
        curPath = tmpPath + fileName + '/'
        os.chdir(curPath)  # current path is './tmp/filename/

        # get function signature
        cmd_sig = rootPath + 'lib/solc4.26 --hashes ' + contractPath + fileName + \
                '.sol > ' + fileName + '.sig'
        subprocess.call(cmd_sig, shell=True)

        cmd_bin = rootPath + 'lib/solc4.26 --bin-runtime ' + contractPath + fileName + \
                '.sol | tail -n 1 > ' + fileName + '.hex'
        subprocess.call(cmd_bin, shell=True)

        mapList = {}
        with open(fileName + '.sig', 'r') as f1 :
            lines = f1.readlines()
            for line in lines :
                pos1 = line.find(':')
                if pos1 == 8 :
                    pos2 = line.find('(')
                    f_sig = line[0:pos1]
                    f_name = line[pos1+2:pos2]
                    mapList[f_sig] = f_name
                else :
                    pass
            f1.close()
        sigList = list(mapList.keys())
        sigList = sorted(sigList, key=functools.cmp_to_key(cmp))
        # print(sigList)

        # run datalog
        cmd_dl = rootPath + 'MadMax/bin/analyze.sh ' + fileName + '.hex ' + \
                rootPath + 'MadMax/tools/bulk_analyser/mySpec.dl'
        subprocess.call(cmd_dl, shell=True)

        # get suspect function name
        csvList = ['Vulnerability_UnboundedMassOp.csv', 
                'Vulnerability_WalletGriefing.csv', 
                'Vulnerability_OverflowLoopIterator.csv']

        # copy target contract to output/
        # shutil.copy(contractPath + fileName + '.sol', outputPath + fileName + '.sol')
        for i in range(len(csvList)) :
            if os.path.getsize(csvList[i]) == 0 :
                continue
            with open(csvList[i], 'r') as f :
                lines = f.readlines()
                for line in lines :
                    idx = int(line)
                    sig = sigList[idx]
                    funcName = mapList[sig]
                    print(funcName, csvList[i])

                    # dl_modify(fileName, funcName, i)

                f.close()


if __name__ == "__main__":
    dl_init()
    # dl_clean()

    dl_run()
    # shutil.rmtree(tmpPath)
