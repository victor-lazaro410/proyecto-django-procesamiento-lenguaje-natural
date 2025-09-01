from django.http import HttpResponse

def home(request):
    html = """
    <!doctype html>
    <html lang='es'>
      <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>PLN & Autómata - Mitad y Mitad</title>
        <style>
          body { font-family: system-ui, Arial, sans-serif; margin:0; }
          header { padding: 12px 16px; background:#0f172a; color:#fff; }
          .grid { display:grid; grid-template-columns:1fr 1fr; gap:0; height: calc(100vh - 56px); }
          .panel { border:0; height:100%; width:100%; }
          .left { border-right: 2px solid #e5e7eb; }
          .title { font-weight: 600; }
          .links { float:right; font-size:14px; }
          .links a{ color:#93c5fd; margin-left:8px; text-decoration:none; }
          .links a:hover{ text-decoration:underline; }
        </style>
      </head>
      <body>
        <header>
          <span class='title'>Procesamiento de Lenguaje Natural & Patrones Sintácticos</span>
          <span class='links'>
            <a href='/lenguaje/'>Lenguaje Natural</a>
            <a href='/patrones/'>Patrones Sintácticos</a>
            <a href='/admin/'>Admin</a>
          </span>
        </header>
        <div class='grid'>
          <iframe class='panel left' src='/lenguaje/' title='Lenguaje Natural'></iframe>
          <iframe class='panel' src='/patrones/' title='Patrones Sintácticos'></iframe>
        </div>
      </body>
    </html>
    """
    return HttpResponse(html)
