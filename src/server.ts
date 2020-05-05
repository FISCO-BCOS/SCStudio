import {
    createConnection,
    TextDocuments,
    TextDocument,
    Diagnostic,
    DiagnosticSeverity,
    ProposedFeatures,
    InitializeParams,
    DidChangeConfigurationNotification,
    CompletionItem,
    CompletionItemKind,
    TextDocumentPositionParams,
    SymbolInformation,
    WorkspaceSymbolParams,
    WorkspaceEdit,
    WorkspaceFolder
} from 'vscode-languageserver';
// import Uri from 'vscode-uri';
import { HandlerResult } from 'vscode-jsonrpc';
import { configure, getLogger } from "log4js";
configure({
    appenders: {
        lsp_demo: {
            type: "dateFile",
            filename: "D:/Desktop/log",
            pattern: "yyyy-MM-dd-hh.log",
            alwaysIncludePattern: true,
        },
    },
    categories: { default: { appenders: ["lsp_demo"], level: "debug" } }
});
const logger = getLogger("lsp_demo");

let connection = createConnection(ProposedFeatures.all);

connection.onInitialize((params: InitializeParams) => {
    let capabilities = params.capabilities;
    return {
        capabilities: {
            completionProvider: {
                resolveProvider: false
            }
        }
    };
});

connection.onInitialized(() => {
    connection.window.showInformationMessage('Hello World! form server side');
});


connection.onCompletion(
    (_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
        let completionItems: any[] = [];
        const simpleCompletion2 = CompletionItem.create('code1');
        simpleCompletion2.detail = 'uint x = accounts[i].balance;';
        simpleCompletion2.kind = CompletionItemKind.Snippet;
        console.log(simpleCompletion2)
        completionItems = completionItems.concat(simpleCompletion2);
        connection.window.showInformationMessage('Completion *************')
        return completionItems;
    }
);

// connection.onCompletionResolve(
//     (item: CompletionItem): CompletionItem => {
//     }
// );