@echo off
setlocal

set RS=C:\Program Files\Epic Games\RealityScan_2.1\RealityScan.exe
set IMAGES=C:\temp\input
set OUTPUT=C:\temp\output
set PROJECT=%OUTPUT%\test.rsproj
set MODEL=%OUTPUT%\model.obj

if not exist "%OUTPUT%" mkdir "%OUTPUT%"

echo Starting RealityScan pipeline...
echo Images: %IMAGES%
echo Output: %OUTPUT%

"%RS%" ^
-newScene ^
-addFolder "%IMAGES%" ^
-align ^
-selectMaximalComponent ^
-setReconstructionRegionAuto ^
-calculateNormalModel ^
-calculateTexture ^
-save "%PROJECT%" ^
-exportSelectedModel "%MODEL%" ^
-quit

echo.
echo Done.
echo Project: %PROJECT%
echo Model: %MODEL%