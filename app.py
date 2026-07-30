import ast
import operator
import os
import sqlite3

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

secret_key = os.getenv("FLASK_SECRET_KEY")
if not secret_key:
    raise RuntimeError("La variable FLASK_SECRET_KEY debe estar configurada")

app.secret_key = secret_key
csrf = CSRFProtect(app)

OPERADORES_PERMITIDOS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def evaluar_nodo(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(
        nodo.value, (int, float)
    ):
        return nodo.value

    if (
        isinstance(nodo, ast.BinOp)
        and type(nodo.op) in OPERADORES_PERMITIDOS
    ):
        izquierda = evaluar_nodo(nodo.left)
        derecha = evaluar_nodo(nodo.right)
        return OPERADORES_PERMITIDOS[type(nodo.op)](
            izquierda,
            derecha,
        )

    if (
        isinstance(nodo, ast.UnaryOp)
        and type(nodo.op) in OPERADORES_PERMITIDOS
    ):
        return OPERADORES_PERMITIDOS[type(nodo.op)](
            evaluar_nodo(nodo.operand)
        )

    raise ValueError("Expresión no permitida")


def evaluar_expresion(expresion):
    if len(expresion) > 100:
        raise ValueError("Expresión demasiado larga")

    arbol = ast.parse(expresion, mode="eval")
    return evaluar_nodo(arbol.body)


@app.get("/buscar")
def buscar():
    termino = request.args.get("q", "").strip()

    with sqlite3.connect("datos.db") as conexion:
        resultados = conexion.execute(
            "SELECT * FROM productos WHERE nombre = ?",
            (termino,),
        ).fetchall()

    return {"resultados": resultados}


@app.get("/calcular")
def calcular():
    expresion = request.args.get("expr", "")

    try:
        resultado = evaluar_expresion(expresion)
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return {"error": "Expresión inválida"}, 400

    return {"resultado": resultado}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
