import re
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from .models import DocumentoPatrones
RESERVED = {
    "auto","break","case","char","const","continue","default","do","double","else","enum","extern","float","for","goto",
    "if","int","long","register","return","short","signed","sizeof","static","struct","switch","typedef","union","unsigned",
    "void","volatile","while","class","public","private","protected","virtual","template","typename","namespace","using",
    "new","delete","include","define","bool","true","false","try","catch","throw"
}
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
def index(request):
    return render(request, "patrones_sintacticos/index.html")
@csrf_protect
def upload_txt(request):
    if request.method != "POST" or "file" not in request.FILES:
        return HttpResponse("Debe enviar un archivo .txt por POST en el campo 'file'.", status=400)
    f = request.FILES["file"]
    name = f.name.lower()
    if not name.endswith(".txt"):
        return HttpResponse("Solo se aceptan .txt", status=400)
    raw = f.read()
    content = raw.decode("utf-8", errors="ignore")
    def repl(m):
        tok = m.group(0)
        return "palabra reservada" if tok.lower() in RESERVED else "variable"
    transformed = IDENTIFIER_RE.sub(repl, content)
    tokens = IDENTIFIER_RE.findall(content)
    reservadas = sum(1 for t in tokens if t.lower() in RESERVED)
    variables = sum(1 for t in tokens if t.lower() not in RESERVED)
    doc = DocumentoPatrones(nombre_original=f.name, reservadas=reservadas, variables=variables); doc.save()
    doc.archivo.save(f.name, ContentFile(raw), save=False)
    out_name = f.name.rsplit('.', 1)[0] + "_transformado.txt"
    doc.archivo_transformado.save(out_name, ContentFile(transformed.encode('utf-8')), save=False)
    doc.save()
    resp = HttpResponse(transformed, content_type="text/plain; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{out_name}"'
    return resp
