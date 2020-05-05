import * as vscode from 'vscode';
export class ItemProvider implements vscode.CompletionItemProvider{
	public codeComs : string[];
	constructor(codeComs : string[]){
		this.codeComs = codeComs;
		console.log(this.codeComs);
	};
    public provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.CompletionItem[]{
			var codeItems : vscode.CompletionItem[];
			codeItems = [];
			for(var i in this.codeComs){
				var simpleCode = new vscode.CompletionItem(this.codeComs[i]);
				codeItems = codeItems.concat(simpleCode);
			}
			return codeItems;
    }
    public resolveCompletionItem(item: vscode.CompletionItem, token: vscode.CancellationToken): any{
        return item;
    }
    dispose(){

    }
}