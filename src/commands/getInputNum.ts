import * as vscode from 'vscode';

export async function getInputNum(
    defaultVal : number
) : Promise<number> {
    let inputOptions : vscode.InputBoxOptions =
	{
		prompt       : "Please input the maximum time for analysis.",
		placeHolder  : "Input an integer (Default value is " + defaultVal.toString() +" seconds)"
    };

    let val : any;
    await vscode.window.showInputBox(inputOptions).then(value =>{
		if (!value)
            val = defaultVal;
		else
            val = Number(value);
    });
    return val;
}