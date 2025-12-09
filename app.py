from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
import os
import random
import string
import json

# --------------------------------------------------------------------
# PROMPT PER LA PREPARAZIONE DELL’INTENZIONE
# --------------------------------------------------------------------
INTENTION_REFINER_SYSTEM_PROMPT = """
Sei il modulo di PREPARAZIONE INTENZIONE del sistema "The Secret of Power".

Il tuo compito è prendere l'INTENZIONE GREZZA dell’utente e restituire
una versione più chiara, leggibile e pulita SENZA modificarne il significato
e SENZA trasformarla in qualcosa che non è.

REGOLE FONDAMENTALI:

1. Mantieni la forma originale dell'utente:
   - Se è una DOMANDA, rimane una DOMANDA.
   - Se è un’AFFERMAZIONE, rimane un’AFFERMAZIONE.
   - Se è un dubbio, rimane un dubbio.
   - Non convertire mai una domanda in affermazione o viceversa.

2. Mantieni il contenuto energetico invariato:
   - Non aggiungere desideri, obiettivi o intenzioni nuovi.
   - Non trasformare il senso della frase.
   - Non cambiare il focus (lavoro, emozioni, famiglia, percorso, salute, ecc.).

3. Migliora solo forma e chiarezza:
   - Correggi grammatica e punteggiatura.
   - Rendi la frase più scorrevole e comprensibile.
   - Elimina ripetizioni inutili.
   - Mantieni un linguaggio naturale, umano, non spirituale.
   - Non rendere la frase più “positiva” o “evolutiva” del necessario.

4. Output obbligatorio in JSON con questa struttura:

{
  "refined_intention": "...",
  "explanation": "..."
}

   - "refined_intention" è la frase finale da usare come intenzione.
   - "explanation" spiega brevemente cosa hai corretto sulla forma (max 2 frasi).

Rispondi SEMPRE e solo in italiano e restituisci soltanto il JSON, senza testo aggiuntivo.
"""

# --------------------------------------------------------------------
# FLASK APP E DB
# --------------------------------------------------------------------
app = Flask(__name__)

# Configurazione database per i Codici Lettura
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///sop_codes.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app)

# Segreto per l'admin dei codici
ADMIN_SECRET = os.environ.get("SOP_ADMIN_SECRET", "M3nt3v3loc3!_SOP")

# Client OpenAI: usa la variabile di ambiente OPENAI_API_KEY
client = OpenAI()

SYSTEM_PROMPT = """Sei l'oracolo delle carte "The Secret of Power", un mazzo dedicato alla Legge di Attrazione e alla crescita interiore.
Parli in modo chiaro, responsabile e incoraggiante.
Non fai previsioni fatalistiche, non dai risposte assolute, non sostituisci terapie mediche o psicologiche.
Aiuti la persona a comprendere il messaggio simbolico delle carte, mettendo l'accento su:
- consapevolezza di sé
- responsabilità personale
- possibilità di scelta
- allineamento tra pensieri, emozioni, azioni e intenzione.

Mantieni le risposte focalizzate ed essenziali: in genere non più di 5-8 paragrafi.
Evita ripetizioni inutili e non diluire i concetti: vai al punto.
Se fornisci spunti pratici, limitati a 2-3 azioni concrete, brevi e chiare.
"""

# --------------------------------------------------------------------
# SIGNIFICATI DELLE CARTE (esempio, da completare nel file reale)
# --------------------------------------------------------------------
CARD_MEANINGS = {
    1: """In riferimento alla Legge d'Attrazione, il termine "uomo" si riferisce alla consapevolezza e al potere dell'essere umano di creare la propria realtà attraverso i pensieri, le emozioni e le azioni. ...""",  # UOMO
    2: """Le emozioni svolgono un ruolo cruciale nel processo di manifestazione. ...""",  # EMOZIONE
    3: """Si riferisce alla parte di noi che rappresenta la nostra essenza più autentica, spontanea e pura, spesso associata alle esperienze e alle emozioni vissute durante l'infanzia. ...""",  # BAMBINO INTERIORE
    4: """Si riferisce alla capacità di liberarsi dei sentimenti negativi, come la rabbia, il risentimento o il rancore, verso se stessi o verso gli altri, in modo da ripristinare equilibrio ed armonia interiore. ...""",  # PERDONO
    5: """Si riferisce alla capacità di avere una chiara comprensione di ciò che si desidera realmente. ...""",  # CHIAREZZA INTENTO
    6: """La mente subconscia è una parte della mente che opera al di sotto del livello della consapevolezza cosciente e che immagazzina pensieri, credenze, emozioni e ricordi anche molto profondi. ...""",  # MENTE SUBCONSCIA
    # ... completa fino alla 33 come avevi nel file originale ...
}

# --------------------------------------------------------------------
# Mappa dal nome della carta al suo significato (usa gli ID sopra)
# --------------------------------------------------------------------
CARD_MEANINGS_BY_NAME = {
    "Uomo": CARD_MEANINGS.get(1, ""),
    "Emozione": CARD_MEANINGS.get(2, ""),
    "Bambino Interiore": CARD_MEANINGS.get(3, ""),
    "Perdono": CARD_MEANINGS.get(4, ""),
    "Chiarezza Intento": CARD_MEANINGS.get(5, ""),
    "Mente Subconscia": CARD_MEANINGS.get(6, ""),
    "Fiducia": CARD_MEANINGS.get(7, ""),
    "Credere a ciò che si vuole": CARD_MEANINGS.get(8, ""),
    "Osservatore Massimo": CARD_MEANINGS.get(9, ""),
    "Sensazione": CARD_MEANINGS.get(10, ""),
    "Gratitudine": CARD_MEANINGS.get(11, ""),
    "Parte superiore del Sé": CARD_MEANINGS.get(12, ""),
    "Legge d'Attrazione": CARD_MEANINGS.get(13, ""),
    "Desiderio Chiaro": CARD_MEANINGS.get(14, ""),
    "Messaggero": CARD_MEANINGS.get(15, ""),
    "Meditazione": CARD_MEANINGS.get(16, ""),
    "Abbondanza": CARD_MEANINGS.get(17, ""),
    "Orologio": CARD_MEANINGS.get(18, ""),
    "Quaderni": CARD_MEANINGS.get(19, ""),
    "Non": CARD_MEANINGS.get(20, ""),
    "Nero": CARD_MEANINGS.get(21, ""),
    "Potere Immaginazione Creativa": CARD_MEANINGS.get(22, ""),
    "Legge di Resistenza": CARD_MEANINGS.get(23, ""),
    "Come in Cielo così in Terra": CARD_MEANINGS.get(24, ""),
    "Universo": CARD_MEANINGS.get(25, ""),
    "La Rabbia": CARD_MEANINGS.get(26, ""),
    "Bianco": CARD_MEANINGS.get(27, ""),
    "L'Amore": CARD_MEANINGS.get(28, ""),
    "Agire nonostante la paura": CARD_MEANINGS.get(29, ""),
    "Fossa Leoni": CARD_MEANINGS.get(30, ""),
    "Consapevolezza": CARD_MEANINGS.get(31, ""),
    "Obiettivo": CARD_MEANINGS.get(32, ""),
    "Io Sono": CARD_MEANINGS.get(33, ""),
}

# --------------------------------------------------------------------
# MODELLO DB PER I CODICI LETTURA
# --------------------------------------------------------------------
class ReadingCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    credits_total = db.Column(db.Integer, default=0)
    credits_used = db.Column(db.Integer, default=0)
    disabled = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(255))

    @property
    def credits_left(self):
        return self.credits_total - self.credits_used

    def can_use(self):
        return not self.disabled and self.credits_left > 0

    def use_credit(self):
        if self.can_use():
            self.credits_used += 1
            return True
        return False


# Crea le tabelle se non esistono
with app.app_context():
    db.create_all()

# --------------------------------------------------------------------
# FUNZIONI DI SUPPORTO
# --------------------------------------------------------------------
def build_prompt(spread_type, cards, intention):
    st = (spread_type or "").lower().replace("_", "-")

    if st in ("1-carta", "1 carta", "una-carta"):
        spread_label = "Lettura a 1 carta (messaggio essenziale / focus energetico)"
    elif st in ("3-carte", "3 carte", "tre-carte"):
        spread_label = "Lettura a 3 carte (situazione energetica complessiva)"
    elif st in ("5-carte", "5 carte", "cinque-carte"):
        spread_label = "Lettura a 5 carte (schema avanzato)"
    else:
        spread_label = "Lettura di carte (schema generico)"

    parts = []
    parts.append(f"Tipo di lettura: {spread_label}.")

    if intention:
        parts.append(f"Intenzione dichiarata dall'utente: {intention}")
    else:
        parts.append(
            "L'utente non ha scritto un'intenzione specifica. "
            "Offri un messaggio generale ma sempre pratico e centrato sulla crescita interiore."
        )

    parts.append("\nCarte estratte:")

    for idx, name in enumerate(cards, start=1):
        meaning = CARD_MEANINGS_BY_NAME.get(name, "")
        parts.append(f"\nCarta {idx}: {name}")
        if meaning:
            parts.append(
                "Significato guida (informazione per te, non da copiare integralmente nella risposta):\n"
                f"{meaning}\n"
            )

    # Istruzioni finali generali
    parts.append(
        "\nUsa queste informazioni per restituire UNA SOLA interpretazione integrata, in italiano, "
        "organizzata in brevi paragrafi o punti chiari. "
        "Non fare previsioni fatalistiche, non dare ordini, non ripetere pari pari i testi guida. "
        "Collega il messaggio delle carte all'intenzione dell'utente e proponi spunti concreti di "
        "riflessione o di azione pratica."
    )

    # Se è una lettura a 3 carte, chiediamo una sintesi più profonda
    if st in ("3-carte", "3 carte", "tre-carte"):
        parts.append(
            "\nPer questa lettura a 3 carte, dopo aver accennato al significato di ciascuna carta, "
            "focalizzati con particolare cura sulla COMBINAZIONE delle tre carte tra loro rispetto "
            "all'intenzione dell'utente."
            "\n- Descrivi come le carte si parlano tra loro: quali tensioni, equilibri o passaggi di fase "
            "mettono in luce? Ci sono aspetti che si compensano, si rafforzano o si mettono in contrasto?"
            "\n- Evidenzia almeno 2 o 3 collegamenti concreti tra i simboli delle carte e la situazione "
            "dell'utente, spiegando in che modo, insieme, raccontano una 'storia energetica' unica."
            "\n- Non limitarti a consigliare strumenti generici (come tenere un diario, meditare, ripetere "
            "affermazioni) a meno che non siano legati in modo molto specifico al contenuto di questa "
            "combinazione di carte. Se li citi, spiega perché questa combinazione LI RENDE particolarmente "
            "adatti adesso."
            "\nL'obiettivo è che chi legge senta che il messaggio nasce davvero dall'incastro di queste tre "
            "carte rispetto alla sua intenzione, non da una lista standard di suggerimenti."
        )

    return "\n".join(parts)


def validate_and_consume_code(code_string):
    raw = (code_string or "").upper()
    clean_code = "".join(ch for ch in raw if not ch.isspace())

    if not clean_code:
        return {
            "ok": False,
            "error": "CODICE_MANCANTE",
            "message": "È necessario inserire un Codice Lettura."
        }

    code = ReadingCode.query.filter_by(code=clean_code).first()
    if not code:
        return {
            "ok": False,
            "error": "CODICE_NON_VALIDO",
            "message": "Il Codice Lettura inserito non esiste."
        }

    if code.disabled:
        return {
            "ok": False,
            "error": "CODICE_DISABILITATO",
            "message": "Questo Codice Lettura è stato disabilitato."
        }

    if code.credits_left <= 0:
        return {
            "ok": False,
            "error": "CREDITI_INSUFFICIENTI",
            "message": "Non ci sono più crediti disponibili per questo codice."
        }

    code.use_credit()
    db.session.commit()

    return {
        "ok": True,
        "credits_left": code.credits_left,
        "credits_total": code.credits_total
    }


def generate_random_code(prefix="SOP-", length=10):
    chars = string.ascii_uppercase + string.digits
    while True:
        suffix = "".join(random.choice(chars) for _ in range(length))
        code = prefix + suffix
        if not ReadingCode.query.filter_by(code=code).first():
            return code

# --------------------------------------------------------------------
# ROUTE ADMIN PER GENERARE CODICI
# --------------------------------------------------------------------
@app.route("/admin/genera-codice", methods=["GET", "POST"])
def admin_generate_code():
    secret = request.args.get("secret", "")
    if secret != ADMIN_SECRET:
        return "Accesso non autorizzato.", 403

    if request.method == "GET":
        html_form = """
        <html>
        <head><title>Genera Codice Lettura</title></head>
        <body>
          <h2>Genera Codice Lettura</h2>
          <form method="post">
            <label>Numero crediti:</label><br>
            <input type="number" name="credits" value="3" min="1"><br><br>
            <label>Note (facoltative):</label><br>
            <input type="text" name="note" style="width:300px;"><br><br>
            <button type="submit">Genera Codice</button>
          </form>
        </body>
        </html>
        """
        return render_template_string(html_form)

    credits_str = request.form.get("credits", "1")
    note = request.form.get("note", "").strip()

    try:
        credits = int(credits_str)
    except ValueError:
        credits = 1
    if credits < 1:
        credits = 1

    code_value = generate_random_code()

    new_code = ReadingCode(
        code=code_value,
        credits_total=credits,
        credits_used=0,
        disabled=False,
        note=note
    )
    db.session.add(new_code)
    db.session.commit()

    html_result = f"""
    <html>
    <head><title>Codice generato</title></head>
    <body>
      <h2>Codice generato</h2>
      <p><strong>Codice:</strong> {code_value}</p>
      <p><strong>Crediti totali:</strong> {credits}</p>
      <p><strong>Crediti usati:</strong> 0</p>
      <p><strong>Note:</strong> {note}</p>
      <hr>
      <a href="?secret={secret}">Genera un altro codice</a>
      &nbsp;|&nbsp;
      <a href="/admin/codici?secret={secret}">Vai alla lista codici</a>
    </body>
    </html>
    """
    return render_template_string(html_result)

# --------------------------------------------------------------------
# ENDPOINT ADMIN PER OTTENERE LA LISTA DEI CODICI IN JSON
# --------------------------------------------------------------------
@app.route("/admin/codici-json", methods=["GET"])
def admin_codici_json():
    secret = request.args.get("secret", "")
    if secret != ADMIN_SECRET:
        return jsonify({"ok": False, "error": "UNAUTHORIZED"}), 401

    codes = ReadingCode.query.order_by(ReadingCode.id.desc()).all()

    data = []
    for c in codes:
        data.append({
            "id": c.id,
            "code": c.code,
            "credits_total": c.credits_total,
            "credits_used": c.credits_used,
            "credits_left": c.credits_left,
            "disabled": bool(c.disabled),
            "note": c.note or ""
        })

    return jsonify({"ok": True, "codes": data})
# --------------------------------------------------------------------
# ENDPOINT ADMIN PER ELIMINARE I CODICI ESAURITI (2.1)
# --------------------------------------------------------------------
@app.route("/admin/elimina-codici-esauriti", methods=["POST"])
def elimina_codici_esauriti():
    secret = request.args.get("secret", "")
    if secret != ADMIN_SECRET:
        return jsonify({"ok": False, "error": "UNAUTHORIZED"}), 401

    # Trova tutti i codici con crediti esauriti
    exhausted_codes = ReadingCode.query.filter(
        ReadingCode.credits_total <= ReadingCode.credits_used
    ).all()

    count = len(exhausted_codes)

    # Cancella uno per uno
    for c in exhausted_codes:
        db.session.delete(c)
    db.session.commit()

    return jsonify({
        "ok": True,
        "deleted": count,
        "message": f"Eliminati {count} codici esauriti."
    })
# --------------------------------------------------------------------
# ENDPOINT PER GENERARE CODICI DA WOOCOMMERCE
# --------------------------------------------------------------------
@app.route("/admin/genera-codice-da-woocommerce", methods=["POST"])
def genera_codice_da_woocommerce():
    data = request.get_json(silent=True) or {}

    secret = data.get("secret")
    if secret != ADMIN_SECRET:
        return jsonify({"ok": False, "error": "UNAUTHORIZED"}), 401

    credits_total = data.get("credits_total")
    if not isinstance(credits_total, int) or credits_total <= 0:
        return jsonify({"ok": False, "error": "CREDITS_INVALIDI"}), 400

    order_id = data.get("order_id")
    note = data.get("note") or ""
    if order_id:
        note = f"Generato da WooCommerce ordine #{order_id} - " + note

    code_value = generate_random_code()

    new_code = ReadingCode(
        code=code_value,
        credits_total=credits_total,
        credits_used=0,
        disabled=False,
        note=note
    )
    db.session.add(new_code)
    db.session.commit()

    return jsonify({
        "ok": True,
        "code": code_value,
        "credits_total": new_code.credits_total,
        "credits_used": new_code.credits_used
    })

@app.route("/admin/disabilita-codice", methods=["POST"])
def admin_disabilita_codice():
    data = request.get_json(silent=True) or {}
    secret = data.get("secret")
    if secret != ADMIN_SECRET:
        return jsonify({"ok": False, "error": "UNAUTHORIZED"}), 401

    try:
        code_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "ID_NON_VALIDO"}), 400

    code = ReadingCode.query.get(code_id)
    if not code:
        return jsonify({"ok": False, "error": "CODICE_NON_TROVATO"}), 404

    code.disabled = True
    db.session.commit()

    return jsonify({"ok": True, "id": code.id})

# --------------------------------------------------------------------
# PAGINA ADMIN PER ELENCO CODICI
# --------------------------------------------------------------------
@app.route("/admin/codici")
def lista_codici():
    secret = request.args.get("secret")
    if secret != ADMIN_SECRET:
        return "Non autorizzato", 401

    codes = ReadingCode.query.order_by(ReadingCode.id.desc()).all()

    rows = []
    for c in codes:
        rows.append(f"""
            <tr>
                <td style="white-space:nowrap;">{c.id}</td>
                <td style="white-space:nowrap;">{c.code}</td>
                <td>{c.credits_total}</td>
                <td>{c.credits_used}</td>
                <td>{c.credits_left}</td>
                <td>{"Sì" if c.disabled else "No"}</td>
                <td>{c.note or ""}</td>
            </tr>
        """)

    html = f"""
    <html>
    <head>
        <title>Codici Lettura - The Secret of Power</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; max-width: 1000px; margin: 20px auto; }}
            th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 0.9em; }}
            th {{ background: #f0f0f0; }}
            h1 {{ text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Codici Lettura - The Secret of Power</h1>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Codice</th>
                    <th>Crediti Totali</th>
                    <th>Crediti Usati</th>
                    <th>Crediti Rimasti</th>
                    <th>Disabilitato</th>
                    <th>Note</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# --------------------------------------------------------------------
# ENDPOINT STATUS E INTERPRETAZIONE
# --------------------------------------------------------------------
@app.route("/api/status")
def status():
    return jsonify({"ok": True, "status": "online"})


@app.route("/api/secret-of-power/interpretation", methods=["POST", "OPTIONS"])
def interpretation():
    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json(silent=True) or {}

    spread_type = data.get("spread_type") or data.get("spreadType") or "1_carta"
    cards_raw = data.get("cards", [])
    intention = data.get("intention")
    reading_code = (data.get("code") or "").strip()

    credit_check = validate_and_consume_code(reading_code)
    if not credit_check.get("ok"):
        return jsonify(credit_check), 400

    normalized_cards = []
    for c in cards_raw:
        if isinstance(c, dict):
            nm = c.get("name") or c.get("label") or c.get("title") or ""
            if not nm:
                nm = str(c)
        else:
            nm = str(c)
        normalized_cards.append(nm)

    if not normalized_cards:
        return jsonify(
            {
                "ok": False,
                "interpretation": None,
                "error": "NESSUNA_CARTA",
                "message": "Nessuna carta ricevuta."
            }
        ), 400

    try:
        user_content = build_prompt(spread_type, normalized_cards, intention)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        text = completion.choices[0].message.content.strip()
        return jsonify({
            "ok": True,
            "interpretation": text,
            "message": text,
            "credits_left": credit_check.get("credits_left"),
            "credits_total": credit_check.get("credits_total")
        })

    except Exception as e:
        print("Errore OpenAI:", e)

        fallback = (
            "Le carte sono state estratte, ma al momento non è possibile generare "
            "un messaggio approfondito. Lascia comunque che i loro simboli lavorino dentro di te "
            "e torna più tardi per una nuova lettura."
        )
        return jsonify({
            "ok": False,
            "interpretation": fallback,
            "message": fallback,
            "credits_left": credit_check.get("credits_left"),
            "credits_total": credit_check.get("credits_total"),
            "error": "OPENAI_ERROR"
        }), 200

# --------------------------------------------------------------------
# ENDPOINT RIFORMULAZIONE INTENZIONE (CON OPTIONS)
# --------------------------------------------------------------------
@app.route("/api/secret-of-power/refine-intention", methods=["POST", "OPTIONS"])
def refine_intention():
    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json(silent=True) or {}
    raw_intention = (data.get("raw_intention") or "").strip()

    if not raw_intention:
        return jsonify({
            "status": "error",
            "message": "Per favore descrivi prima la tua intenzione nel riquadro."
        }), 400

    if len(raw_intention) < 20:
        return jsonify({
            "status": "error",
            "message": "Il testo è troppo breve. Prova a descrivere un po’ meglio situazione e desiderio."
        }), 400

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": INTENTION_REFINER_SYSTEM_PROMPT},
                {"role": "user", "content": raw_intention}
            ],
            temperature=0.2,
            max_tokens=300
        )

        content = completion.choices[0].message.content.strip()

        refined = ""
        explanation = ""
        try:
            parsed = json.loads(content)
            refined = (parsed.get("refined_intention") or "").strip()
            explanation = (parsed.get("explanation") or "").strip()
        except Exception:
            refined = content

        if not refined:
            return jsonify({
                "status": "error",
                "message": "Non sono riuscito a riformulare l’intenzione. Riprova con una descrizione più chiara."
            }), 500

        return jsonify({
            "status": "ok",
            "refined_intention": refined,
            "explanation": explanation,
            "warnings": []
        })

    except Exception as e:
        print("Errore refine-intention:", e)
        return jsonify({
            "status": "error",
            "message": "Si è verificato un errore durante la riformulazione dell’intenzione."
        }), 500


@app.route("/")
def index():
    return "API The Secret of Power – online"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
