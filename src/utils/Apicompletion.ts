import {CompletionItem, CompletionItemKind} from 'vscode'

export function GetContextualAutoCompleteByGlobalVariable(lineText: string, wordEndPosition: number): CompletionItem[] {
    if (isAutocompleteTrigeredByVariableName('block', lineText, wordEndPosition)) {
        return getBlockCompletionItems();
    }
    if (isAutocompleteTrigeredByVariableName('msg', lineText, wordEndPosition)) {
        return getMsgCompletionItems();
    }
    if (isAutocompleteTrigeredByVariableName('tx', lineText, wordEndPosition)) {
        return getTxCompletionItems();
    }
    if (isAutocompleteTrigeredByVariableName('abi', lineText, wordEndPosition)) {
        return getAbiCompletionItems();
    }
    return [];
}


function getBlockCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(address): Current block miner’s address',
            kind: CompletionItemKind.Property,
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
            kind: CompletionItemKind.Property,
            label: 'difficulty',
        },
        {
            detail: '(uint): current block gaslimit',
            kind: CompletionItemKind.Property,
            label: 'gaslimit',
        },
        {
            detail: '(uint): current block number',
            kind: CompletionItemKind.Property,
            label: 'number',
        },
        {
            detail: '(uint): current block timestamp as seconds since unix epoch',
            kind: CompletionItemKind.Property,
            label: 'timestamp',
        },
    ];
}

function getMsgCompletionItems(): CompletionItem[] {
    return [
        {
            detail: '(bytes): complete calldata',
            kind: CompletionItemKind.Property,
            label: 'data',
        },
        {
            detail: '(uint): remaining gas DEPRICATED in 0.4.21 use gasleft()',
            kind: CompletionItemKind.Property,
            label: 'gas',
        },
        {
            detail: '(address): sender of the message (current call)',
            kind: CompletionItemKind.Property,
            label: 'sender',
        },
        {
            detail: '(bytes4): first four bytes of the calldata (i.e. function identifier)',
            kind: CompletionItemKind.Property,
            label: 'sig',
        },
        {
            detail: '(uint): number of wei sent with the message',
            kind: CompletionItemKind.Property,
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
            kind: CompletionItemKind.Property,
            label: 'gas',
        },
        {
            detail: '(address): sender of the transaction (full call chain)',
            kind: CompletionItemKind.Property,
            label: 'origin',
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
