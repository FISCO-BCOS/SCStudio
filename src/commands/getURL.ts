import * as vscode from 'vscode';
export async function getURL(
    defaultVal : string
) : Promise<string> {
    let inputOptions : vscode.InputBoxOptions =
	{
		prompt       : "Please input the url of to deploy the web service.",
		placeHolder  : "Input a url (Default value is " + defaultVal.toString() +" )"
    };

    let val : any;
    await vscode.window.showInputBox(inputOptions).then(value =>{
		if (!value)
            val = defaultVal;
		else
            val = value;
    });
    return val;
}