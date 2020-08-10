import {CompletionItem, CompletionItemKind} from 'vscode'

export function GetContextualAutoCompleteByGlobalVariable(lineText: string, wordEndPosition: number): CompletionItem[] {
    if (isAutocompleteTrigeredByVariableName('block', lineText, wordEndPosition)) {
        return getBlockCompletionItems();
    }
    else if (isAutocompleteTrigeredByVariableName('msg', lineText, wordEndPosition)) {
        return getMsgCompletionItems();
    }
    else if (isAutocompleteTrigeredByVariableName('tx', lineText, wordEndPosition)) {
        return getTxCompletionItems();
    }
    else if (isAutocompleteTrigeredByVariableName('abi', lineText, wordEndPosition)) {
        return getAbiCompletionItems();
    }
    else {
        return getSafeMathCompletionItems();
    }
    return [];
}


function getBlockCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(address): Current block miner’s address',
            kind: CompletionItemKind.Field,
            label: 'coinbase',
        },
        {
            detail: '(bytes32): DEPRICATED In 0.4.22 use blockhash(uint) instead. Hash of the given block - only works for 256 most recent blocks excluding current',
            insertText: 'blockhash(${1:blockNumber});',
            kind: CompletionItemKind.Method,
            label: 'blockhash',
        },
        {
            detail: '(uint): current block difficulty',
            kind: CompletionItemKind.Field,
            label: 'difficulty',
        },
        {
            detail: '(uint): current block gaslimit',
            kind: CompletionItemKind.Field,
            label: 'gaslimit',
        },
        {
            detail: '(uint): current block number',
            kind: CompletionItemKind.Field,
            label: 'number',
        },
        {
            detail: '(uint): current block timestamp as seconds since unix epoch',
            kind: CompletionItemKind.Field,
            label: 'timestamp',
        },
    ];
}

function getMsgCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(bytes): complete calldata',
            kind: CompletionItemKind.Field,
            label: 'data',
        },
        {
            detail: '(uint): remaining gas DEPRICATED in 0.4.21 use gasleft()',
            kind: CompletionItemKind.Field,
            label: 'gas',
        },
        {
            detail: '(address): sender of the message (current call)',
            kind: CompletionItemKind.Field,
            label: 'sender',
        },
        {
            detail: '(bytes4): first four bytes of the calldata (i.e. function identifier)',
            kind: CompletionItemKind.Field,
            label: 'sig',
        },
        {
            detail: '(uint): number of wei sent with the message',
            kind: CompletionItemKind.Field,
            label: 'value',
        },
    ];
}

function getAbiCompletionItems(): CompletionItem[] {
    return [
        {
            detail: 'encode(..) returs (bytes): ABI-encodes the given arguments',
            insertText: 'encode(${1:arg});',
            kind: CompletionItemKind.Method,
            label: 'encode',
        },
        {
            detail: 'encodePacked(..) returns (bytes): Performes packed encoding of the given arguments',
            insertText: 'encodePacked(${1:arg});',
            kind: CompletionItemKind.Method,
            label: 'encodePacked',
        },
        {
            detail: 'encodeWithSelector(bytes4,...) returns (bytes): ABI-encodes the given arguments starting from the second and prepends the given four-byte selector',
            insertText: 'encodeWithSelector(${1:bytes4}, ${2:arg});',
            kind: CompletionItemKind.Method,
            label: 'encodeWithSelector',
        },
        {
            detail: 'encodeWithSignature(string,...) returns (bytes): Equivalent to abi.encodeWithSelector(bytes4(keccak256(signature), ...)`',
            insertText: 'encodeWithSignature(${1:signatureString}, ${2:arg});',
            kind: CompletionItemKind.Method,
            label: 'encodeWithSignature',
        },
    ];
}

function getTxCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(uint): gas price of the transaction',
            kind: CompletionItemKind.Field,
            label: 'gas',
        },
        {
            detail: '(address): sender of the transaction (full call chain)',
            kind: CompletionItemKind.Field,
            label: 'origin',
        },
    ];
}

function getSafeMathCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(uint): using SafeMath Library to get sum',
            insertText: 'add();',
            kind: CompletionItemKind.Method,
            label: 'add',
        },
        {
            detail: '(uint): using SafeMath Library to get difference',
            insertText: 'sub();',
            kind: CompletionItemKind.Method,
            label: 'sub',
        },
        {
            detail: '(uint): using SafeMath Library to get product',
            insertText: 'mul();',
            kind: CompletionItemKind.Method,
            label: 'mul',
        },
        {
            detail: '(uint): using SafeMath Library to get quotient',
            insertText: 'div();',
            kind: CompletionItemKind.Method,
            label: 'div',
        },
    ];
}

function isAutocompleteTrigeredByVariableName(variableName: string, lineText: string, wordEndPosition: number): Boolean {
    const nameLength = variableName.length;
    if (wordEndPosition >= nameLength
        // does it equal our name?
        && lineText.substr(wordEndPosition - nameLength, nameLength) === variableName) {
          return true;
        }
    return false;
}
