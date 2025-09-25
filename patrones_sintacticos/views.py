
import re, io
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from .models import DocumentoPatrones
from .lexer import scan
from .parser import Parser, ParseError

def index(request):
    return render(request, "patrones_sintacticos/index.html")

@csrf_protect
def upload(request):
    if request.method != "POST" or "file" not in request.FILES:
        return render(request, "patrones_sintacticos/index.html", {"error": "Sube un archivo .txt con código para analizar."}, status=400)
    f = request.FILES["file"]
    raw = f.read()
    try:
        content = raw.decode("utf-8")
    except Exception:
        content = raw.decode("latin-1", errors="ignore")

    tokens = scan(content)
    counts = {}
    for t in tokens:
        counts[t.type] = counts.get(t.type, 0) + 1

    parse_tree = None
    parse_error = None
    try:
        p = Parser(tokens)
        parse_tree = p.parse()
    except ParseError as e:
        parse_error = {"message": e.message, "line": e.line, "col": e.col, "expected": e.expected}

    doc = DocumentoPatrones(nombre_original=f.name, reservadas=counts.get("PALABRA_RESERVADA",0), variables=counts.get("IDENTIFICADOR",0))
    doc.save()
    doc.archivo.save(f.name, ContentFile(raw), save=False)

    lines = ["tipo\tlexema\tlinea\tcolumna"]
    for t in tokens:
        safe_lex = t.lexeme.replace("\t", "\\t").replace("\n", "\\n")
        lines.append(f"{t.type}\t{safe_lex}\t{t.line}\t{t.col}")
    tsv = "\n".join(lines).encode("utf-8")
    out_name = f.name.rsplit('.',1)[0] + "_tokens.tsv"
    doc.archivo_transformado.save(out_name, ContentFile(tsv), save=False)
    doc.save()

    def pp(node, depth=0, out=None):
        out = out or []
        if node is None:
            return out
        if hasattr(node, "name"):
            out.append("  " * depth + node.name)
            for ch in getattr(node, "children", []):
                pp(ch, depth+1, out)
        else:
            out.append("  " * depth + str(node))
        return out

    parse_tree_lines = pp(parse_tree) if parse_tree else None

    ctx = {
        "counts": counts,
        "tokens": tokens,
        "download_url": doc.archivo_transformado.url if hasattr(doc.archivo_transformado, "url") else None,
        "parse_tree": parse_tree_lines,
        "parse_error": parse_error,
        "grammar": [
            "programa → secuencia-sent",
            "secuencia-sent → secuencia-sent ; sentencia | sentencia",
            "sentencia → sent-if | sent-repeat | sent-assign | sent-read | sent-write",
            "sent-if → if exp then secuencia-sent end | if exp then secuencia-sent else secuencia-sent end",
            "sent-repeat → repeat secuencia-sent until exp",
            "sent-assign → identificador := exp",
            "sent-read → read identificador",
            "sent-write → write exp",
            "exp → exp-simple op-comparación exp-simple | exp-simple",
            "op-comparación → < | =",
            "exp-simple → exp-simple opsuma term | term",
            "opsuma → + | -",
            "term → term opmult factor | factor",
            "opmult → * | /",
            "factor → ( exp ) | número | identificador",
        ]
    }
    return render(request, "patrones_sintacticos/index.html", ctx)
