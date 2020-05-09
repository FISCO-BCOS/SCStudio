import * as vscode from 'vscode';
export class ItemProvider implements vscode.CompletionItemProvider{
	public codeComs : string[];
	public Items : vscode.CompletionItem[];
	constructor(codeComs : string[],Items : vscode.CompletionItem[]){
		this.codeComs = codeComs;
		this.Items = Items;
	};
    public provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.CompletionItem[]{
		if((this.Items).length == 0){
			var codeItems : vscode.CompletionItem[];
			codeItems = [];
			for(var i in this.codeComs){
				var simpleCode = new vscode.CompletionItem(this.codeComs[i]);
				simpleCode.kind = vscode.CompletionItemKind.Function;
				// simpleCode.sortText = i;
				codeItems = codeItems.concat(simpleCode);
			}
			return codeItems;
		}
		else{
			console.log(this.Items)
			return this.Items;
		}
    }
    public resolveCompletionItem(item: vscode.CompletionItem, token: vscode.CancellationToken): any{
        return null;
    }
    dispose(){

    }
}