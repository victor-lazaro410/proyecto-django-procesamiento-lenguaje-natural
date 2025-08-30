import re
STOPWORDS_ES = {
    "a","acá","ahi","ahí","al","algo","algún","alguna","algunas","alguno","algunos","allá","alli","allí","ambos","ante",
    "antes","aquel","aquella","aquellas","aquello","aquellos","aqui","aquí","arriba","así","aun","aunque","bajo","bastante",
    "bien","cabe","cada","casi","cierta","ciertas","cierto","ciertos","como","cómo","con","conmigo","conseguimos","conseguir",
    "consigo","consigue","consiguen","consigues","contigo","contra","cual","cuales","cualquier","cualquiera","cualquieras",
    "cuan","cuando","cuándo","cuanta","cuánta","cuantas","cuántas","cuanto","cuánto","cuantos","cuántos","de","dejar","del",
    "demás","demasiada","demasiadas","demasiado","demasiados","dentro","desde","donde","dónde","dos","el","él","ella","ellas",
    "ello","ellos","empleais","emplean","emplear","empleas","empleo","en","encima","entonces","entre","era","erais","eramos",
    "eran","eras","eres","es","esa","esas","ese","eso","esos","esta","estaba","estabais","estaban","estabas","estad","estada",
    "estadas","estado","estados","estais","estamos","estan","están","estar","estara","estará","estarán","estarás","estare",
    "estaré","estareis","estareis","estaremos","estaria","estaría","estariais","estaríais","estariamos","estaríamos","estarían",
    "estarías","estas","estás","este","esto","estos","estoy","fin","fue","fueron","fui","fuimos","gueno","ha","hace","haceis",
    "hacemos","hacen","hacer","haces","hacia","hago","hasta","incluso","intenta","intentais","intentamos","intentan","intentar",
    "intentas","intento","ir","jamás","junto","juntos","la","lado","las","le","les","largo","lo","los","mas","más","me","menos",
    "mi","mía","mias","mio","mío","mios","mis","mismo","mucha","muchas","muchisima","muchísimas","muchísimo","muchisimos",
    "muchísimos","mucho","muchos","muy","nada","nadie","ni","ningun","ninguna","ningunas","ninguno","ningunos","no","nos",
    "nosotras","nosotros","nuestra","nuestras","nuestro","nuestros","nunca","os","otra","otras","otro","otros","para","parecer",
    "pero","poca","pocas","poco","pocos","podeis","podemos","poder","podria","podría","podriais","podríais","podriamos",
    "podríamos","podrian","podrían","podrias","podrías","por","porque","primero","puede","pueden","puedo","pues","que","qué",
    "querer","quien","quién","quienes","quienesquiera","quienquiera","quizas","quizás","sabe","sabeis","sabemos","saben",
    "saber","sabes","se","segun","según","ser","si","sí","siempre","siendo","sin","sino","so","sobre","sois","solamente",
    "solo","sólo","somos","soy","su","sus","suya","suyas","suyo","suyos","tal","tales","tambien","también","tampoco","tan",
    "tanta","tantas","tanto","tantos","te","teneis","tenemos","tener","tengo","ti","tiempo","tiene","tienen","toda","todas",
    "todavia","todavía","todo","todos","trabaja","trabajais","trabajamos","trabajan","trabajar","trabajas","trabajo","tras",
    "tú","tu","tus","tuya","tuyas","tuyo","tuyos","ultimo","último","un","una","unas","uno","unos","usa","usais","usamos",
    "usan","usar","usas","uso","usted","ustedes","va","vais","valor","vamos","van","varias","varios","vaya","verdad","verdadera",
    "vosotras","vosotros","voy","vuestra","vuestras","vuestro","vuestros","y","ya","yo"
}
NON_WORD_RE = re.compile(r"[^\wáéíóúñÁÉÍÓÚÑ\s]", flags=re.UNICODE)
def clean_and_tokenize(text: str):
    if not isinstance(text, str):
        text = str(text or "")
    text = text.lower()
    text = NON_WORD_RE.sub(" ", text)
    tokens = re.findall(r"[\wáéíóúñÁÉÍÓÚÑ]+", text, flags=re.UNICODE)
    return [t for t in tokens if t not in STOPWORDS_ES and len(t) > 2]
