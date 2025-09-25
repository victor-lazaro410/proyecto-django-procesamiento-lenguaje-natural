
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional, Any

@dataclass
class PToken:
    type: str
    lexeme: str
    line: int
    col: int

@dataclass
class Node:
    name: str
    children: List[Any]

class ParseError(Exception):
    def __init__(self, message: str, line: int, col: int, expected: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.expected = expected or []

class Parser:
    def __init__(self, tokens: List[PToken]):
        norm = []
        for t in tokens:
            ttype = t.type
            if ttype in ("NUMERO","NUMERO_FLOAT","NUMERO_HEX","NUMERO_BIN","NUMERO_OCT"):
                ttype = "NUM"
            elif ttype == "IDENTIFICADOR":
                ttype = "IDENT"
            elif ttype == "PALABRA_RESERVADA":
                ttype = f"KW_{t.lexeme.lower()}"
            elif ttype == "DELIMITADOR" and t.lexeme in ("(",")","[","]","{","}"):
                ttype = t.lexeme
            elif ttype == "OPERADOR":
                ttype = t.lexeme
            norm.append(PToken(ttype, t.lexeme, t.line, t.col))
        self.tokens = norm
        self.i = 0

    def peek(self) -> PToken:
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        if self.tokens:
            last = self.tokens[-1]
            return PToken("EOF","", last.line, last.col)
        return PToken("EOF","",1,1)

    def match(self, *types):
        if self.peek().type in types:
            tok = self.peek()
            self.i += 1
            return tok
        return None

    def expect(self, *types):
        tok = self.peek()
        if tok.type in types:
            self.i += 1
            return tok
        raise ParseError(f"Se esperaba uno de {types} y se encontró '{tok.lexeme}' [{tok.type}]", tok.line, tok.col, list(types))

    def at_end(self) -> bool:
        return self.i >= len(self.tokens)

    def parse(self) -> Node:
        node = self.programa()
        if not self.at_end():
            t = self.peek()
            raise ParseError(f"Entrada no consumida a partir de '{t.lexeme}'", t.line, t.col, ["EOF"])
        return node

    def programa(self) -> Node:
        ss = self.secuencia_sent()
        return Node("programa", [ss])

    def secuencia_sent(self) -> Node:
        children = [ self.sentencia() ]
        while self.match(";"):
            children.append(Node(";", []))
            children.append(self.sentencia())
        return Node("secuencia_sent", children)

    def sentencia(self) -> Node:
        tok = self.peek()
        if tok.type == "KW_if":
            return self.sent_if()
        if tok.type == "KW_repeat":
            return self.sent_repeat()
        if tok.type == "KW_read":
            return self.sent_read()
        if tok.type == "KW_write":
            return self.sent_write()
        if tok.type == "IDENT":
            return self.sent_assign()
        raise ParseError("Sentencia inválida", tok.line, tok.col, ["if","repeat","read","write","identificador"])

    def sent_if(self) -> Node:
        self.expect("KW_if")
        e = self.exp()
        self.expect("KW_then")
        ss_then = self.secuencia_sent()
        if self.match("KW_else"):
            ss_else = self.secuencia_sent()
            self.expect("KW_end")
            return Node("sent_if", [Node("if",[]), e, Node("then",[]), ss_then, Node("else",[]), ss_else, Node("end",[])])
        self.expect("KW_end")
        return Node("sent_if", [Node("if",[]), e, Node("then",[]), ss_then, Node("end",[])])

    def sent_repeat(self) -> Node:
        self.expect("KW_repeat")
        ss = self.secuencia_sent()
        self.expect("KW_until")
        e = self.exp()
        return Node("sent_repeat", [Node("repeat",[]), ss, Node("until",[]), e])

    def sent_assign(self) -> Node:
        idt = self.expect("IDENT")
        self.expect(":=")
        e = self.exp()
        return Node("sent_assign", [Node("identificador", [Node(idt.lexeme, [])]), Node(":=", []), e])

    def sent_read(self) -> Node:
        self.expect("KW_read")
        idt = self.expect("IDENT")
        return Node("sent_read", [Node("read",[]), Node(idt.lexeme,[])])

    def sent_write(self) -> Node:
        self.expect("KW_write")
        e = self.exp()
        return Node("sent_write", [Node("write",[]), e])

    # Expressions with precedence
    def exp(self) -> Node:
        left = self.term_sum()
        if self.match("<"):
            right = self.term_sum()
            return Node("exp_cmp", [left, Node("<",[]), right])
        if self.match("=") or self.match("=="):
            right = self.term_sum()
            return Node("exp_cmp", [left, Node("=",[]), right])
        return left

    def term_sum(self) -> Node:
        node = self.term_mul()
        while True:
            if self.match("+"):
                node = Node("sum", [node, Node("+",[]), self.term_mul()])
            elif self.match("-"):
                node = Node("sum", [node, Node("-",[]), self.term_mul()])
            else:
                break
        return node

    def term_mul(self) -> Node:
        node = self.unary()
        while True:
            if self.match("*"):
                node = Node("mul", [node, Node("*",[]), self.unary()])
            elif self.match("/"):
                node = Node("mul", [node, Node("/",[]), self.unary()])
            else:
                break
        return node

    def unary(self) -> Node:
        return self.primary()

    def primary(self) -> Node:
        if self.match("("):
            e = self.exp()
            self.expect(")")
            return Node("group", [Node("(",[]), e, Node(")",[])])
        tok = self.peek()
        if tok.type == "NUM":
            self.i += 1
            return Node("numero", [Node(tok.lexeme,[])])
        if tok.type == "IDENT":
            self.i += 1
            return Node("identificador", [Node(tok.lexeme,[])])
        raise ParseError("Expresión inválida", tok.line, tok.col, ["(","numero","identificador"])
