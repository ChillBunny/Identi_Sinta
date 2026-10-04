# Analizador sintáctico

Analizador sintáctico descendente recursivo para una calculadora con variables, hecho en
Python con una ventana en Tkinter. Los tokens los entrega el analizador léxico hecho con FLEX
(`analizador.l`), y el sintáctico revisa que estén en un orden válido según la gramática.

Para usarlo basta con abrir `AnalizadorSintactico.exe`, escribir el código y presionar
**Analizar** (o F5). La ventana muestra el resultado de cada instrucción, el árbol
sintáctico, el valor de las variables, los tokens y la gramática.

## El lenguaje

Una calculadora con variables. Cada instrucción es una asignación y ocupa una línea.

```
# precio con descuento
precio = 150.50
descuento = 0.15
total = precio - (precio * descuento)
mitad = total / 2
```

Los tokens son los del analizador léxico: NUMERO, IDENTIFICADOR, ASIGNACION (`=`), SUMA,
RESTA, MULT, DIV, PAR_IZQ, PAR_DER y COMENTARIO (`#` hasta el final de la línea). Los
comentarios no entran al análisis sintáctico.

## La gramática

```
programa     →  instruccion*
instruccion  →  IDENTIFICADOR  =  expresion
expresion    →  termino  ( ( + | - )  termino )*
termino      →  factor  ( ( * | / )  factor )*
factor       →  NUMERO
             |  IDENTIFICADOR
             |  ( expresion )
             |  -  factor
```

- Las sumas y restas están en `expresion` y las multiplicaciones y divisiones en `termino`.
  Por eso `2 + 3 * 4` da 14: se multiplica primero.
- Las operaciones del mismo nivel se agrupan por la izquierda: `10 - 4 - 3` da 3.
- La gramática no tiene recursividad por la izquierda. En lugar de
  `expresion → expresion + termino` se usa la repetición `( ... )*`, para que el analizador
  descendente recursivo no entre en un ciclo infinito.

Cada regla es una función en `sintactico.py`: `programa`, `instruccion`, `expresion`,
`termino` y `factor`.

## Errores

Cuando una instrucción tiene un error de sintaxis, se reporta y el análisis sigue en la línea
siguiente (modo de pánico). Ejemplos:

| Instrucción | Error |
|---|---|
| `a = 5 +` | Falta un número, una variable o '(' después de '+' |
| `b = (3 + 4` | Falta ')' después de '4' |
| `d = 3 4` | Sobra '4': la instrucción ya estaba completa |
| `c 5` | Se esperaba '=', pero llegó '5' |
| `e = * 2` | Se esperaba un número, una variable o '(', pero llegó '*' |

Si hay errores léxicos, como un `@`, se muestran primero y no se hace el análisis sintáctico.

Usar una variable que no tiene valor o dividir entre cero no es un error de sintaxis: la
instrucción es correcta, y el problema se muestra en la pestaña de valores.
