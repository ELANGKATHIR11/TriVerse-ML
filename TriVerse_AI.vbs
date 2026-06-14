' TriVerse AI — Silent Launcher (VBScript)
' Launches the app without any CMD/terminal window flash.
' Double-click this file or use the Desktop shortcut.

Dim shell, project_root, bat_path
Set shell = CreateObject("WScript.Shell")

' Resolve the path to the batch file relative to this VBS file
project_root = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
bat_path = project_root & "launch_triverse.bat"

' Run the batch file hidden (0 = invisible window, False = don't wait)
shell.Run "cmd /c """ & bat_path & """", 0, False

Set shell = Nothing
