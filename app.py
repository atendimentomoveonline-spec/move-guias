import os, io, re, zipfile, urllib.request, json, traceback
from flask import Flask, request, jsonify, render_template, send_file, abort

app = Flask(__name__)

GOOGLE_API_KEY  = os.environ.get("GOOGLE_API_KEY", "")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
DRIVE_API = "https://www.googleapis.com/drive/v3"

MESES = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

def limpar_cnpj(v): return re.sub(r"\D", "", v)
def formatar_cnpj(v):
    v = limpar_cnpj(v)
    return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}" if len(v)==14 else v

def label_competencia(nome):
    m = re.search(r'[_\-](\d{2})(\d{4})[_\-]', nome)
    if m:
        mes, ano = int(m.group(1)), m.group(2)
        if 1 <= mes <= 12:
            return f"{MESES[mes]}/{ano}"
    return nome

def drive_listar(folder_id):
    url = (f"{DRIVE_API}/files?q=%27{folder_id}%27+in+parents+and+trashed%3Dfalse"
           f"&fields=files(id,name,mimeType,size)&key={GOOGLE_API_KEY}&pageSize=200")
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())["files"]

def drive_baixar(file_id):
    url = f"{DRIVE_API}/files/{file_id}?alt=media&key={GOOGLE_API_KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()

def extrair_pdf_do_zip(dados):
    with zipfile.ZipFile(io.BytesIO(dados)) as zf:
        pdfs = [n for n in zf.namelist() if n.lower().endswith(".pdf")]
        if not pdfs: return None
        nome = os.path.basename(pdfs[0])
        return nome, zf.read(pdfs[0])

_cache: dict = {}

@app.route("/minhas-guias")
def index(): return render_template("index.html")

@app.route("/api/guias", methods=["POST"])
def api_guias():
    data = request.get_json(force=True)
    cnpj = limpar_cnpj(data.get("cnpj", ""))
    if len(cnpj) != 14:
        return jsonify({"erro": "CNPJ inválido."}), 400
    if not GOOGLE_API_KEY or not DRIVE_FOLDER_ID:
        return jsonify({"erro": f"Config ausente. KEY={bool(GOOGLE_API_KEY)} FOLDER={bool(DRIVE_FOLDER_ID)}"}), 500
    try:
        arquivos = drive_listar(DRIVE_FOLDER_ID)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"erro": f"Erro Drive: {e}"}), 500
    encontrados = [f for f in arquivos if cnpj in re.sub(r"\D","",f["name"])]
    if not encontrados:
        return jsonify({"erro": "Nenhuma guia encontrada para este CNPJ."}), 404
    guias = []
    for arq in sorted(encontrados, key=lambda x: x["name"], reverse=True):
        ext = os.path.splitext(arq["name"])[1].lower()
        if ext == ".pdf":
            guias.append({"label": label_competencia(arq["name"]),
                          "url": f"/download/{cnpj}/{arq['id']}/{arq['name']}"})
        elif ext == ".zip":
            try:
                dados = drive_baixar(arq["id"])
                resultado = extrair_pdf_do_zip(dados)
                if resultado:
                    pdf_nome, pdf_bytes = resultado
                    cache_key = f"{cnpj}_{arq['id']}"
                    _cache[cache_key] = pdf_bytes
                    guias.append({"label": label_competencia(pdf_nome),
                                  "url": f"/download/{cnpj}/zip/{arq['id']}/{pdf_nome}"})
            except Exception as e:
                traceback.print_exc()
    return jsonify({"cnpj": formatar_cnpj(cnpj), "guias": guias})

@app.route("/download/<cnpj>/<file_id>/<nome>")
def download_pdf_direto(cnpj, file_id, nome):
    if not nome.lower().endswith(".pdf"): abort(403)
    dados = drive_baixar(file_id)
    return send_file(io.BytesIO(dados), mimetype="application/pdf",
                     as_attachment=True, download_name=nome)

@app.route("/download/<cnpj>/zip/<file_id>/<nome>")
def download_pdf_zip(cnpj, file_id, nome):
    if not nome.lower().endswith(".pdf"): abort(403)
    cache_key = f"{cnpj}_{file_id}"
    dados = _cache.get(cache_key)
    if not dados:
        try:
            zip_dados = drive_baixar(file_id)
            resultado = extrair_pdf_do_zip(zip_dados)
            if resultado: _, dados = resultado; _cache[cache_key] = dados
        except Exception: abort(404)
    if not dados: abort(404)
    return send_file(io.BytesIO(dados), mimetype="application/pdf",
                     as_attachment=True, download_name=nome)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
