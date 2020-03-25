import * as vscode from 'vscode';
export class ItemProvider implements vscode.CompletionItemProvider{
    public provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.CompletionItem[]{

        var completionItems = [];
        var completionItem = new vscode.CompletionItem("ab");
        completionItem.kind = vscode.CompletionItemKind.Snippet;
        completionItem.detail = "aaaefgdfa";
        completionItem.filterText = String.fromCharCode(13)+"bgmhhh";
        completionItem.insertText = new vscode.SnippetString("dddd");

        var completionItem1 = new vscode.CompletionItem("ab");
        completionItem1.kind = vscode.CompletionItemKind.Snippet;
        completionItem1.detail = "aaaefg";
        completionItem1.filterText = "\nbgm";
        completionItem1.insertText = new vscode.SnippetString("pppp");
        completionItems.push(completionItem1);
        completionItems.push(completionItem);
        return completionItems;
    }
    public resolveCompletionItem(item: vscode.CompletionItem, token: vscode.CancellationToken): any{
        return item;
    }
    dispose(){

    }
}