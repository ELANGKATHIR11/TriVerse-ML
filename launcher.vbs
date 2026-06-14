Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

exePath = currentDir & "\frontend\unified_dashboard\dist-electron\TriVerse ML-win32-x64\TriVerse ML.exe"
frontendDir = currentDir & "\frontend\unified_dashboard"

' 1. Try to start local Ollama if not running
WshShell.Run "cmd /c netstat -ano | findstr :11434 || start /b ollama serve", 0, False

' 2. Launch the native App silently
If fso.FileExists(exePath) Then
    WshShell.Run """" & exePath & """", 0, False
Else
    ' Fallback to dev-mode launcher if compiled app isn't found
    WshShell.Run "cmd /c cd /d """ & frontendDir & """ && npm run electron", 0, False
End If
