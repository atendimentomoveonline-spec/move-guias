import os
import io
import re
import zipfile
import urllib.request
import json
from flask import Flask, request, jsonify, render_template, send_file, abort

app = Flask(__name__)

# ── Configuração (variáveis no Railway) ───────────────────────────────────────
GOOGLE_API_KEY  = os.environ.get("GOOGLE_API_KEY", "")   # Chave API do Google
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")  # ID da pasta no Drive

DRIVE_API = "https://www.googleapis.com/drive/v3"

MESES = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
         "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def limpar_cnpj(v: str) -> str:
    return re.sub(r"\D", "", v)

def formatar_cnpj(v: str) -> str:
    v = limpar_cnpj(v)
    return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}" if len(v) == 14 else v

def label_competencia(nome: str) -> str:
    """Ex: GuiaPagamento_53578465000190_042026_... → Abril/2026"""
    m = re.search(r'[_\-](\d{2})(\d{4})[_\-]', nome)
    if m:
        mes, ano = int(m.group(1)), m.group(2)
        if 1 <= mes <= 12:
            return f"{MESES[mes]}/{ano}"
    return nome

def drive_listar(folder_id: str) -> list:
    """Lista arquivos na pasta do Drive (pasta deve ser pública)."""
    url = (
        f"{DRIVE_API}/files"
        f"?q=%27{folder_id}%27+in+parents+and+trashed%3Dfalse"
        f"&fields=files(id,name,mimeType,size)"
        f"&key={GOOGLE_API_KEY}"
        f"&pageSize=200"
    )
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())["files"]

def drive_baixar(file_id: str) -> bytes:
    """Baixa arquivo do Drive em memória."""
    url = f"{DRIVE_API}/files/{file_id}?alt=media&key={GOOGLE_API_KEY}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()

def extrair_pdf_do_zip(dados: bytes) -> tuple[str, bytes] | None:
    """Extrai o primeiro PDF de um ZIP. Retorna (nome, bytes) ou None."""
    with zipfile.ZipFile(io.BytesIO(dados)) as zf:
        pdfs = [n for n in zf.namelist() if n.lower().endswith(".pdf")]
        if not pdfs:
            return None
        nome = os.path.basename(pdfs[0])
        return nome, zf.read(pdfs[0])

# Cache em memória: {cnpj_arquivo: bytes}
_cache: dict[str, bytes] = {}

# ── Rotas ─────────────────────────────────────────────────────────────────────
@app.route("/minhas-guias")
def index():
    return render_template("index.html")

@app.route("/api/guias", methods=["POST"])
def api_guias():
    data = request.get_json(force=True)
    cnpj = limpar_cnpj(data.get("cnpj", ""))

    if len(cnpj) != 14:
        return jsonify({"erro": "CNPJ inválido. Digite os 14 dígitos."}), 400

    if not GOOGLE_API_KEY or not DRIVE_FOLDER_ID:
        return jsonify({"erro": "Sistema em configuração. Contate a Move Online."}), 500

    try:
        arquivos = drive_listar(DRIVE_FOLDER_ID)
    except Exception:
        return jsonify({"erro": "Não foi possível acessar os arquivos. Tente novamente."}), 500

    # Filtrar arquivos que contém o CNPJ no nome
    encontrados = [f for f in arquivos if cnpj in re.sub(r"\D", "", f["name"])]

    if not encontrados:
        return jsonify({"erro": "Nenhuma guia encontrada para este CNPJ.\nEm caso de dúvida, entre em contato com a Move Online."}), 404

    guias = []
    for arq in sorted(encontrados, key=lambda x: x["name"], reverse=True):
        nome = arq["name"]
        ext  = os.path.splitext(nome)[1].lower()
        fid  = arq["id"]

        if ext == ".pdf":
            guias.append({
                "label": label_competencia(nome),
                "url":   f"/download/{cnpj}/{fid}/{nome}",
            })

        elif ext == ".zip":
            # Baixa e extrai PDF em memória
            try:
                dados = drive_baixar(fid)
                resultado = extrair_pdf_do_zip(dados)
                if resultado:
                    pdf_nome, pdf_bytes = resultado
                    cache_key = f"{cnpj}_{fid}"
                    _cache[cache_key] = pdf_bytes
                    guias.append({
                        "label": label_competencia(pdf_nome) or label_competencia(nome),
                        "url":   f"/download/{cnpj}/zip/{fid}/{pdf_nome}",
                    })
            except Exception:
                continue

    if not guias:
        return jsonify({"erro": "Arquivos encontrados mas sem PDF válido. Contate a Move Online."}), 404

    return jsonify({
        "cnpj":    formatar_cnpj(cnpj),
        "guias":   guias,
    })

@app.route("/download/<cnpj>/<file_id>/<nome>")
def download_pdf_direto(cnpj, file_id, nome):
    """PDF direto do Drive."""
    if not nome.lower().endswith(".pdf"):
        abort(403)
    try:
        dados = drive_baixar(file_id)
        return send_file(io.BytesIO(dados), mimetype="application/pdf",
                         as_attachment=True, download_name=nome)
    except Exception:
        abort(404)

@app.route("/download/<cnpj>/zip/<file_id>/<nome>")
def download_pdf_zip(cnpj, file_id, nome):
    """PDF extraído de ZIP (servido do cache)."""
    if not nome.lower().endswith(".pdf"):
        abort(403)
    cache_key = f"{cnpj}_{file_id}"
    dados = _cache.get(cache_key)
    if not dados:
        # Tenta baixar novamente se cache expirou
        try:
            zip_dados = drive_baixar(file_id)
            resultado = extrair_pdf_do_zip(zip_dados)
            if resultado:
                _, dados = resultado
                _cache[cache_key] = dados
        except Exception:
            abort(404)
    if not dados:
        abort(404)
    return send_file(io.BytesIO(dados), mimetype="application/pdf",
                     as_attachment=True, download_name=nome)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Acesse: http://localhost:{port}/minhas-guias\n")
    app.run(host="0.0.0.0", port=port, debug=False)
