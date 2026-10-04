@echo off
rem Genera el analizador con flex y lo compila con gcc.
rem Si flex y gcc estan en otra carpeta, cambiar HERRAMIENTAS.

cd /d "%~dp0"
set HERRAMIENTAS=%USERPROFILE%\herramientas-compiladores

"%HERRAMIENTAS%\flex\win_flex.exe" -o lex.yy.c analizador.l
if errorlevel 1 goto error

"%HERRAMIENTAS%\mingw64\bin\gcc.exe" -o analizador.exe lex.yy.c
if errorlevel 1 goto error

echo Listo, se genero analizador.exe
goto fin

:error
echo Hubo un error al compilar.

:fin
