import os
import subprocess
import sys


# un nodo del arbol sintactico. tipo es NUMERO, IDENTIFICADOR u OPERADOR
class Nodo:
    def __init__(self, nombre, tipo, hijos=None):
        self.nombre = nombre
        self.tipo = tipo
        if hijos is None:
            hijos = []
        self.hijos = hijos


class ErrorSintactico(Exception):
    def __init__(self, mensaje, linea, columna, lexema):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        self.lexema = lexema


# corre analizador.exe (el analizador lexico hecho con flex) y devuelve sus tokens
def obtener_tokens(texto):
    # si la app esta empaquetada con pyinstaller, analizador.exe viene adentro
    # del ejecutable y se descomprime en la carpeta sys._MEIPASS
    if getattr(sys, "frozen", False):
        carpeta = sys._MEIPASS
    else:
        carpeta = os.path.dirname(os.path.abspath(__file__))
    ruta_analizador = os.path.join(carpeta, "analizador.exe")

    # CREATE_NO_WINDOW es para que no se abra una ventana negra de consola
    resultado = subprocess.run(
        [ruta_analizador],
        input=texto.encode("utf-8"),
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    salida = resultado.stdout.decode("utf-8", errors="replace")

    tokens = []
    for linea in salida.splitlines():
        # cada linea viene asi: TOKEN <tab> lexema <tab> linea <tab> columna
        tipo, resto = linea.split("\t", 1)
        lexema, numero_linea, columna = resto.rsplit("\t", 2)
        tokens.append((tipo, lexema, int(numero_linea), int(columna)))
    return tokens


# analizador sintactico descendente recursivo: una funcion por cada regla de la gramatica.
# cada instruccion ocupa una linea
class AnalizadorSintactico:
    def __init__(self, tokens):
        self.tokens = tokens
        self.posicion = 0
        self.linea = 0

    # el token que se esta viendo, pero solo si esta en la linea de la instruccion.
    # si ya se paso a la linea siguiente, la instruccion se termino y devuelve None
    def actual(self):
        if self.posicion < len(self.tokens) and self.tokens[self.posicion][2] == self.linea:
            return self.tokens[self.posicion]
        return None

    def avanzar(self):
        token = self.tokens[self.posicion]
        self.posicion = self.posicion + 1
        return token

    # error cuando la linea se acaba y todavia faltaba algo
    def error_fin_de_linea(self, que_faltaba):
        anterior = self.tokens[self.posicion - 1]
        mensaje = f"Falta {que_faltaba} después de '{anterior[1]}'"
        raise ErrorSintactico(mensaje, anterior[2], anterior[3], anterior[1])

    # revisa que el token actual sea del tipo esperado y lo consume
    def esperar(self, tipo, que_se_espera):
        token = self.actual()
        if token is None:
            self.error_fin_de_linea(que_se_espera)
        if token[0] != tipo:
            mensaje = f"Se esperaba {que_se_espera}, pero llegó '{token[1]}'"
            raise ErrorSintactico(mensaje, token[2], token[3], token[1])
        return self.avanzar()

    # programa -> instruccion*
    def programa(self):
        instrucciones = []
        errores = []
        while self.posicion < len(self.tokens):
            self.linea = self.tokens[self.posicion][2]
            try:
                arbol = self.instruccion()
                instrucciones.append((self.linea, arbol))
            except ErrorSintactico as error:
                errores.append(error)
                self.saltar_linea()
        return instrucciones, errores

    # modo de panico: despues de un error se descartan los tokens que quedan
    # en esa linea y se sigue analizando desde la linea siguiente
    def saltar_linea(self):
        while self.actual() is not None:
            self.avanzar()

    # instruccion -> IDENTIFICADOR = expresion
    def instruccion(self):
        nombre = self.esperar("IDENTIFICADOR", "el nombre de una variable")
        self.esperar("ASIGNACION", "'='")
        valor = self.expresion()

        sobra = self.actual()
        if sobra is not None:
            mensaje = f"Sobra '{sobra[1]}': la instrucción ya estaba completa"
            raise ErrorSintactico(mensaje, sobra[2], sobra[3], sobra[1])

        return Nodo("=", "OPERADOR", [Nodo(nombre[1], "IDENTIFICADOR"), valor])

    # expresion -> termino ( (+ | -) termino )*
    def expresion(self):
        nodo = self.termino()
        while self.actual() is not None and self.actual()[0] in ("SUMA", "RESTA"):
            operador = self.avanzar()
            derecho = self.termino()
            nodo = Nodo(operador[1], "OPERADOR", [nodo, derecho])
        return nodo

    # termino -> factor ( (* | /) factor )*
    def termino(self):
        nodo = self.factor()
        while self.actual() is not None and self.actual()[0] in ("MULT", "DIV"):
            operador = self.avanzar()
            derecho = self.factor()
            nodo = Nodo(operador[1], "OPERADOR", [nodo, derecho])
        return nodo

    # factor -> NUMERO | IDENTIFICADOR | ( expresion ) | - factor
    def factor(self):
        token = self.actual()
        if token is None:
            self.error_fin_de_linea("un número, una variable o '('")

        if token[0] == "NUMERO" or token[0] == "IDENTIFICADOR":
            self.avanzar()
            return Nodo(token[1], token[0])

        if token[0] == "PAR_IZQ":
            self.avanzar()
            nodo = self.expresion()
            self.esperar("PAR_DER", "')'")
            return nodo

        if token[0] == "RESTA":
            self.avanzar()
            return Nodo("-", "OPERADOR", [self.factor()])

        mensaje = f"Se esperaba un número, una variable o '(', pero llegó '{token[1]}'"
        raise ErrorSintactico(mensaje, token[2], token[3], token[1])


# calcula el valor de un arbol de expresion
def evaluar(nodo, variables):
    if nodo.tipo == "NUMERO":
        return float(nodo.nombre)

    if nodo.tipo == "IDENTIFICADOR":
        if nodo.nombre not in variables:
            raise ValueError(f"la variable '{nodo.nombre}' no tiene valor todavía")
        return variables[nodo.nombre]

    # el menos de un numero negativo tiene un solo hijo
    if len(nodo.hijos) == 1:
        return -evaluar(nodo.hijos[0], variables)

    izquierdo = evaluar(nodo.hijos[0], variables)
    derecho = evaluar(nodo.hijos[1], variables)
    if nodo.nombre == "+":
        return izquierdo + derecho
    if nodo.nombre == "-":
        return izquierdo - derecho
    if nodo.nombre == "*":
        return izquierdo * derecho
    if derecho == 0:
        raise ValueError("división entre cero")
    return izquierdo / derecho


# recorre las instrucciones en orden y va guardando el valor de cada variable.
# devuelve una lista de (linea, variable, valor, problema)
def calcular_valores(instrucciones):
    variables = {}
    resultados = []
    for linea, arbol in instrucciones:
        nombre = arbol.hijos[0].nombre
        try:
            valor = evaluar(arbol.hijos[1], variables)
            variables[nombre] = valor
            resultados.append((linea, nombre, valor, ""))
        except ValueError as problema:
            resultados.append((linea, nombre, None, str(problema)))
    return resultados


# muestra 135.0 como 135 y corta los decimales largos
def formatear(valor):
    valor = round(valor, 4)
    if valor == int(valor):
        return str(int(valor))
    return str(valor)
