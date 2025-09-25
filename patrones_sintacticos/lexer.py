
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Tuple, Iterable, Dict, Optional
import keyword

PY_KW = set(keyword.kwlist)
C_KW = {
    "auto","break","case","char","const","continue","default","do","double","else","enum","extern","float","for","goto",
    "if","int","long","register","return","short","signed","sizeof","static","struct","switch","typedef","union","unsigned",
    "void","volatile","while","class","public","private","protected","virtual","template","typename","namespace","using",
    "new","delete","include","define","bool","true","false","try","catch","throw","this","operator","friend","inline"
}
JAVA_KW = {
    "abstract","assert","boolean","break","byte","case","catch","char","class","const","continue","default","do","double",
    "else","enum","extends","final","finally","float","for","goto","if","implements","import","instanceof","int","interface",
    "long","native","new","package","private","protected","public","return","short","static","strictfp","super","switch","synchronized",
    "this","throw","throws","transient","try","void","volatile","while","true","false","null"
}
KW = {k.lower() for k in (PY_KW | C_KW | JAVA_KW)}

OPERATORS = [
    ">>>=","<<=",">>=","==","!=",">=","<=","&&","||","++","--","->","::","+=","-=","*=","/=","%=","&=","|=","^=","<<",">>",
    "+","-","*","/","%","=","<",">","!","~","&","|","^","?",":",".",",",";"
]
DELIMS = ["(",")","[","]","{","}"]

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int

def is_space(ch: str) -> bool:
    return ch in " \t\r"

def is_newline(ch: str) -> bool:
    return ch == "\n"

def is_letter(ch: str) -> bool:
    return ch.isalpha() or ch == "_"

def is_digit(ch: str) -> bool:
    return ch.isdigit()

def scan(code: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(code)
    line = 1
    col = 1

    def emit(ttype: str, lex: str, l: int, c: int):
        tokens.append(Token(ttype, lex, l, c))

    # Pre-sort operators for greedy match (longest first)
    OPS = sorted(OPERATORS, key=len, reverse=True)
    while i < n:
        ch = code[i]

        # Newline
        if is_newline(ch):
            i += 1
            line += 1
            col = 1
            continue

        # Whitespace
        if is_space(ch):
            i += 1
            col += 1
            continue

        # Comments
        if ch == "/":
            if i+1 < n and code[i+1] == "/":
                # line comment
                start_col = col
                j = i+2
                while j < n and not is_newline(code[j]):
                    j += 1
                emit("COMENTARIO", code[i:j], line, start_col)
                col += (j - i)
                i = j
                continue
            if i+1 < n and code[i+1] == "*":
                # block comment
                start_line, start_col = line, col
                j = i+2
                while j < n-1 and not (code[j] == "*" and code[j+1] == "/"):
                    if code[j] == "\n":
                        line += 1
                        col = 1
                    else:
                        col += 1
                    j += 1
                j_end = min(j+2, n)
                emit("COMENTARIO", code[i:j_end], start_line, start_col)
                col += (j_end - i)
                i = j_end
                continue

        # String literal (double quotes)
        if ch == '"':
            start_line, start_col = line, col
            j = i + 1
            while j < n:
                if code[j] == "\\" and j+1 < n:
                    j += 2
                    continue
                if code[j] == '"':
                    j += 1
                    break
                if code[j] == "\n":
                    line += 1
                    col = 1
                j += 1
            emit("CADENA", code[i:j], start_line, start_col)
            col += (j - i)
            i = j
            continue

        # Char literal (single quotes)
        if ch == "'":
            start_line, start_col = line, col
            j = i + 1
            while j < n:
                if code[j] == "\\" and j+1 < n:
                    j += 2
                    continue
                if code[j] == "'":
                    j += 1
                    break
                if code[j] == "\n":
                    line += 1
                    col = 1
                j += 1
            emit("CARACTER", code[i:j], start_line, start_col)
            col += (j - i)
            i = j
            continue

        # Number: int, float, hex, bin, oct, exponentials
        if is_digit(ch) or (ch == "." and i+1 < n and is_digit(code[i+1])):
            start_line, start_col = line, col
            j = i
            # Hex, bin, oct prefixes: 0x, 0b, 0o
            if code[j] == "0" and j+1 < n and code[j+1] in "xX":
                j += 2
                while j < n and (code[j].isdigit() or code[j].lower() in "abcdef"):
                    j += 1
                emit("NUMERO_HEX", code[i:j], start_line, start_col)
                col += (j - i)
                i = j
                continue
            if code[j] == "0" and j+1 < n and code[j+1] in "bBoO":
                base = code[j+1].lower()
                j += 2
                valid = "01" if base == "b" else "01234567"
                while j < n and code[j] in valid:
                    j += 1
                emit("NUMERO_BIN" if base=="b" else "NUMERO_OCT", code[i:j], start_line, start_col)
                col += (j - i)
                i = j
                continue
            # Decimal / float / exponent
            has_dot = False
            has_exp = False
            while j < n and (code[j].isdigit() or code[j] == "." or (code[j] in "eE" and j+1 < n and (code[j+1].isdigit() or code[j+1] in "+-"))):
                if code[j] == ".":
                    if has_dot: break
                    has_dot = True
                elif code[j] in "eE":
                    if has_exp: break
                    has_exp = True
                    j += 1
                    if j < n and code[j] in "+-":
                        j += 1
                    while j < n and code[j].isdigit():
                        j += 1
                    break
                j += 1
            lex = code[i:j]
            emit("NUMERO" if not has_dot and not has_exp else "NUMERO_FLOAT", lex, start_line, start_col)
            col += (j - i)
            i = j
            continue

        # Identifier / keyword
        if is_letter(ch):
            start_line, start_col = line, col
            j = i + 1
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            lex = code[i:j]
            ttype = "PALABRA_RESERVADA" if lex.lower() in KW else "IDENTIFICADOR"
            emit(ttype, lex, start_line, start_col)
            col += (j - i)
            i = j
            continue

        # Delimiters
        if ch in "".join(DELIMS):
            emit("DELIMITADOR", ch, line, col)
            i += 1
            col += 1
            continue

        # Operators (greedy)
        matched = False
        for op in OPS:
            if code.startswith(op, i):
                emit("OPERADOR", op, line, col)
                i += len(op)
                col += len(op)
                matched = True
                break
        if matched:
            continue

        # Unknown / single char fallback
        emit("DESCONOCIDO", ch, line, col)
        i += 1
        col += 1

    return tokens
