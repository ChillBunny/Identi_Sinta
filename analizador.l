%{
/*
   Analizador lexico para una calculadora con variables.
   Lee el texto de la entrada estandar y escribe un token por linea:
   TOKEN <tab> lexema <tab> linea <tab> columna
*/
#include <stdio.h>

int columna = 1;

void mostrar(const char *token);
%}

%option noyywrap nounistd never-interactive yylineno

digito      [0-9]
letra       [a-zA-Z_]

%%

{digito}+("."{digito}+)?        { mostrar("NUMERO"); }
{letra}({letra}|{digito})*      { mostrar("IDENTIFICADOR"); }
"="                             { mostrar("ASIGNACION"); }
"+"                             { mostrar("SUMA"); }
"-"                             { mostrar("RESTA"); }
"*"                             { mostrar("MULT"); }
"/"                             { mostrar("DIV"); }
"("                             { mostrar("PAR_IZQ"); }
")"                             { mostrar("PAR_DER"); }
"#".*                           { mostrar("COMENTARIO"); }
[ \t\r]+                        { columna = columna + yyleng; }
\n                              { columna = 1; }
[\xC0-\xFF][\x80-\xBF]*         { mostrar("ERROR"); }
.                               { mostrar("ERROR"); }

%%

/* cuenta las letras del lexema. una letra con tilde o una ñ ocupa
   dos bytes, pero en pantalla es una sola letra */
int contarLetras(void) {
    int cantidad = 0;
    for (int i = 0; i < yyleng; i++) {
        unsigned char c = yytext[i];
        if (c < 0x80 || c >= 0xC0) {
            cantidad = cantidad + 1;
        }
    }
    return cantidad;
}

/* imprime el token que se acaba de reconocer y avanza la columna */
void mostrar(const char *token) {
    printf("%s\t%s\t%d\t%d\n", token, yytext, yylineno, columna);
    columna = columna + contarLetras();
}

int main(void) {
    yylex();
    return 0;
}
