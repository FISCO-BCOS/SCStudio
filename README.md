# SCStudio README

SCStudio is a vscode extension for writing solidity contracts in a safe way. 

The current version of SCStudio supports two ways to analyze your smart contracts. If you don't want to upload your contract to any server, we provide a docker image to let you check your code locally. Please first install `docker` for your system, you can follow the instructions [here](https://docs.docker.com/get-docker/). After installing `docker`, you need to pull the image of our contract analyzing tool by :
```
docker pull renardbebe/entools
```

Meanwhile, if you want to use a web service to analyze the contract, you need first use the following command to enable the web service.
```
SCStudio: Enable the web service
```
Then, please set the url of your web service by the following command:
```
SCStudio: Set the url of the web service
```

Enjoy!

## Features

For now, SCStudio provides such features:

**a) Smart contract security check**

SCStudio use an ensemble analysis tool to check whether there is a vulnerability in the current smart contract. At present, SCStudio supports 56 kinds of common vulnerabilities such as 'Reentrancy', 'Overflow', 'TimeStamp Dependency' and 'Contract Backdoors'.

In order to use this function, the developer can use the following command:
```
SCStudio: Analyze Contract
```
For now, the time limit for each contract is set as 60 seconds by default.
You can set the time limit by using the following command:
```
SCStudio: Set Maximum Wait-time for Security Analysis
```
For now, the time limit for each contract is set as 60 seconds.

![Feature_Security_Check](img/secsolidity_analyze.gif)

**b) Next token suggestion**

SCStudio provides a suggestion for the next token. This is useful for a solidity beginner.

In order to use this function, the developer can click 'space' when he has finished typing the current token.


**c) API completion**
SCStudio supports api completion for common structs in solidity language such as `msg` and `block`.

**d) Highlight**
SCStudio implements a highlight feature for solidity language.


## Usage

The current version of SCStudio is still under development. You can only use it by cloning the repository and run the extension in debugging mode. You can use this tool by the followint commands:
```shell
git clone https://github.com/FISCO-BCOS/SCStudio
cd SCStudio
# install dependency-package
npm install
# install dependency-extension
code --install-extension philhindle.errorlens
code --install-extension JuanBlanco.solidity
code --install-extension atishay-jain.all-autocomplete
# launch vscode
code .
```
After opening the repository in VScode, press F5 to debug and open your workspace which contains the solidity files.

**Enjoy!**
