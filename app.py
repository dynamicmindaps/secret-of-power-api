from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)

# Configurazione database per i Codici Lettura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sop_codes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CORS(app)

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
"""


CARD_MEANINGS = {
    1: """In riferimento alla Legge d'Attrazione, il termine "uomo" si riferisce alla consapevolezza e al potere dell'essere umano di creare la propria realtà attraverso i pensieri, le emozioni e le azioni. L'uomo è considerato un co-creatore della propria esperienza di vita grazie alla capacità di scegliere consapevolmente cosa pensare e cosa focalizzare. In questo contesto, l'uomo è visto come un essere dotato di libero arbitrio e responsabilità nel dirigere la propria attenzione verso ciò che desidera attrarre, poiché ciò che pensa e sente emette vibrazioni che, secondo la Legge d'Attrazione, richiamano esperienze simili. Pertanto, l'uomo è al centro del processo di manifestazione, poiché attraverso le sue convinzioni, emozioni e atteggiamenti attrae situazioni, persone e opportunità che rispecchiano il suo stato interiore. La consapevolezza di questo potere permette agli individui di orientare intenzionalmente il proprio pensiero verso ciò che desiderano, invece di concentrarsi su ciò che temono o non vogliono. In sintesi, l'uomo nella Legge d'Attrazione rappresenta il soggetto che, attraverso la sua mente e il suo cuore, contribuisce attivamente a creare la propria realtà, scegliendo consapevolmente quali pensieri nutrire e quali emozioni coltivare per attrarre nella propria vita le circostanze e le opportunità che desidera. È il fulcro del processo di manifestazione, poiché è attraverso di lui che la Legge d'Attrazione si attiva e si manifesta nella realtà concreta. Per questo motivo, l'uomo è responsabile del proprio benessere e dei risultati che ottiene nella vita, in quanto essi riflettono il suo stato interiore e il modo in cui utilizza la Legge d'Attrazione per manifestare i suoi desideri.""",  # UOMO
    2: """Le emozioni svolgono un ruolo cruciale nel processo di manifestazione. Essendo strettamente legate ai pensieri, le emozioni fungono da motore energetico che amplifica e trasmette le vibrazioni generate dai pensieri verso l'universo. Secondo la Legge d'Attrazione, le emozioni positive, come la gioia, la gratitudine, l'amore e la speranza, emettono una frequenza vibratoria elevata, che attrae esperienze simili nella realtà della persona. Al contrario, emozioni negative, come la paura, la rabbia, la tristezza o il risentimento, emettono vibrazioni più basse che possono attrarre esperienze negative. Imparare a gestire e a scegliere consapevolmente le proprie emozioni permette di allinearsi più facilmente con ciò che si desidera, invece di rimanere bloccati in stati emotivi che attirano circostanze indesiderate. Per esempio, se una persona desidera abbondanza ma si sente costantemente preoccupata o insicura riguardo al denaro, le emozioni di paura e mancanza possono intralciare la manifestazione del benessere economico. Coltivare emozioni positive, attraverso pratiche come la gratitudine, la meditazione, l'immaginazione creativa e l'affermazione, aiuta a mantenere uno stato vibratorio in sintonia con ciò che si vuole attrarre nella propria vita. Le emozioni, quindi, non sono un semplice effetto dei pensieri, ma un elemento fondamentale nel processo di attrazione: esse indicano il grado di allineamento tra ciò che si desidera e ciò che si sta realmente vibrando. Prestare attenzione alle proprie emozioni e imparare a orientarle in modo consapevole è una componente essenziale per utilizzare efficacemente la Legge di Attrazione.""",  # EMOZIONE
    3: """Si riferisce alla parte di noi che rappresenta la nostra essenza più autentica, spontanea e pura, spesso associata alle esperienze e alle emozioni vissute durante l'infanzia. È quella parte emotiva e sensibile che conserva, oltre ai ricordi, anche le sensazioni legate alle esperienze passate, sia positive che negative. Il bambino interiore è il custode di molte delle nostre convinzioni profonde, specialmente quelle sviluppate nei primi anni di vita, quando siamo particolarmente influenzabili dall'ambiente familiare e sociale. Queste convinzioni, spesso inconsce, possono influenzare il modo in cui vediamo noi stessi e il mondo, e quindi anche le nostre capacità di attrarre ciò che desideriamo. Nella Legge d'Attrazione, il bambino interiore è importante perché rappresenta il livello emotivo e subconscio da cui provengono molte delle vibrazioni che emettiamo, in base a quanto ci sentiamo meritevoli, amati, sicuri o al contrario inadeguati, non amabili o insicuri. Se il bambino interiore porta ferite, traumi o credenze limitanti, queste possono sabotare i tentativi consci di manifestare una realtà positiva, perché a livello profondo ci si sente magari non degni di ricevere amore, successo o abbondanza. Prendersi cura del proprio bambino interiore attraverso pratiche di guarigione, accoglienza e riconoscimento permette di sciogliere tali blocchi emotivi, sostituendo vecchie credenze con nuove convinzioni più armoniose e favorevoli. Questo processo favorisce un maggiore allineamento tra ciò che si desidera a livello conscio e ciò che si sente di meritare a livello subconscio. In questo modo, l'energia emotiva che emettiamo diventa più coerente con i nostri desideri, facilitando la manifestazione di esperienze più positive. Il bambino interiore, quindi, non è solo un simbolo psicologico, ma una chiave energetica importante nel lavoro di trasformazione interiore necessario per utilizzare efficacemente la Legge d'Attrazione. Riconoscere, ascoltare e guarire il bambino interiore permette di liberare tanta energia bloccata e di aprirsi a una vita più piena, creativa e allineata ai propri desideri più autentici. Quando il bambino interiore si sente accolto, amato e al sicuro, diventa più facile credere di meritare il meglio e manifestare i nostri desideri con maggiore facilità e autenticità.""",  # BAMBINO INTERIORE
    4: """Si riferisce alla capacità di liberarsi dei sentimenti negativi, come la rabbia, il risentimento o il rancore, verso se stessi o verso gli altri, in modo da ripristinare equilibrio ed armonia interiore. Il perdono non significa giustificare o minimizzare il comportamento altrui, ma piuttosto scegliere consapevolmente di non rimanere intrappolati in emozioni che avvelenano la propria vita e il proprio campo energetico. Nel contesto della Legge d'Attrazione, il perdono è fondamentale perché trattenere emozioni negative mantiene attiva una vibrazione bassa che può attirare esperienze simili nella realtà quotidiana. Quando si prova costantemente rancore o si rimane legati a vecchi dolori, si continua a rivivere interiormente quelle situazioni, anche se esternamente sembrano far parte del passato. Questo stato emotivo, prolungato nel tempo, può ostacolare la manifestazione di desideri positivi, poiché l'energia è occupata nel mantenere in vita pensieri ed emozioni che non sono in armonia con ciò che si vuole attrarre. Perdonare, invece, permette di sciogliere i legami energetici con esperienze e persone che ci hanno ferito, liberando spazio interiore per emozioni più elevate, come la pace, la gratitudine e l'amore. Questo cambiamento di frequenza interiore facilita l'allineamento con nuove esperienze più positive, poiché l'energia della persona non è più concentrata nel rivivere il passato, ma è disponibile per creare nuove possibilità nel presente. Il perdono è, quindi, un atto di amore verso se stessi, perché consente di liberarsi da pesi emotivi che impediscono di vivere pienamente e di utilizzare in modo efficace la Legge d'Attrazione. Non è un processo immediato, ma un percorso di consapevolezza e di scelta, in cui si decide, passo dopo passo, di non lasciare che il dolore passato determini la qualità della propria vita presente e futura. Riconoscere il valore del perdono e praticarlo consapevolmente permette di creare uno spazio per la positività e il benessere.""",  # PERDONO
    5: """Si riferisce alla capacità di avere una chiara comprensione di ciò che si desidera realmente. Nel contesto della Legge d'Attrazione, la chiarezza dell'intento è essenziale, poiché ciò che si emette in termini di pensieri, emozioni e credenze determina ciò che si attrae nella propria vita. Se l'intento è confuso o contraddittorio, anche i risultati che si ottengono possono essere altrettanto confusi o incoerenti. Avere chiarezza d'intento significa definire con precisione ciò che si vuole sperimentare, evitando espressioni generiche o ambigue, e comprendendo anche il perché profondo del proprio desiderio. La Legge d'Attrazione risponde alle vibrazioni emesse, non solo alle parole, quindi è importante che l'intento sia allineato sia a livello mentale che emotivo. Quando una persona è incerta sui propri desideri o nutre dubbi interni, invia segnali misti all'universo, oscillando tra ciò che vuole e ciò che teme. Questo crea una vibrazione instabile che può attirare situazioni in contrasto tra loro. Al contrario, quando l'intento è lucido, coerente e sostenuto da una forte convinzione, la vibrazione emessa è più potente e focalizzata. La chiarezza d'intento richiede anche di essere onesti con se stessi, riconoscendo le motivazioni profonde che stanno dietro ai propri desideri. È importante chiedersi se ciò che si vuole è davvero in armonia con i propri valori, con il proprio benessere e con il bene che si desidera anche per gli altri. Quando l'intento è puro e allineato alla propria verità interiore, la Legge d'Attrazione può agire con maggiore precisione, aprendo la strada a sincronicità, opportunità e incontri significativi. Prendersi il tempo per definire con cura ciò che si desidera, magari scrivendo, visualizzando o meditandoci sopra, aiuta a consolidare la chiarezza d'intento. Questo non solo facilita il processo di manifestazione, ma rafforza anche la fiducia in se stessi e nella vita, poiché si percepisce di avere una direzione chiara verso cui orientare i propri passi e le proprie energie. In sintesi, la chiarezza d'intento è una componente fondamentale per utilizzare consapevolmente la Legge d'Attrazione e dirigere in modo armonico le proprie energie verso un obiettivo ben definito.""",  # CHIAREZZA INTENTO
    6: """La mente subconscia è una parte della mente che opera al di sotto del livello della consapevolezza cosciente e che immagazzina pensieri, credenze, emozioni e ricordi anche molto profondi. Nel contesto della Legge d'Attrazione, la mente subconscia svolge un ruolo fondamentale, poiché molte delle vibrazioni che emettiamo derivano proprio da ciò che è radicato in essa, spesso al di là di ciò che percepiamo consapevolmente. Anche se una persona afferma di desiderare qualcosa a livello cosciente, se nel subconscio sono presenti convinzioni contrarie (ad esempio sentirsi indegni, incapaci o sfortunati), queste convinzioni possono sabotare il processo di manifestazione. La mente subconscia, infatti, tende a riprodurre nella realtà esterna le immagini e le credenze che ospita, indipendentemente da ciò che si dice o si pensa superficialmente. È come un potente motore che dirige la nostra vita in base a programmi interiori spesso installati nell'infanzia o attraverso esperienze emotive intense. Per utilizzare in modo efficace la Legge d'Attrazione, è quindi importante lavorare proprio a livello subconscio, al fine di identificare e trasformare quelle credenze limitanti che non sono in sintonia con ciò che si desidera manifestare. Tecniche come la visualizzazione creativa, le affermazioni ripetute con emozione, la meditazione, l'ipnosi o altre pratiche di introspezione possono essere utili per riprogrammare il subconscio con nuove credenze più favorevoli. Quando la mente subconscia è allineata ai desideri coscienti, il flusso di energia diretta verso la manifestazione diventa molto più armonico e potente. I pensieri smettono di essere in conflitto tra loro e l'energia non viene dispersa in dubbi o autosabotaggi inconsci. Di conseguenza, la persona può sperimentare con maggiore facilità situazioni ed esperienze che riflettono il nuovo schema interiore. La mente subconscia, dunque, è come un terreno fertile: se vi si seminano credenze di paura, scarsità o indegnità, cresceranno situazioni che riflettono tali semi. Se invece vi si piantano semi di fiducia, abbondanza e amore per sé, la realtà esterna tenderà gradualmente a rispecchiare queste nuove convinzioni. Prendersi cura della propria mente subconscia è quindi un passo essenziale per lavorare consapevolmente con la Legge d'Attrazione.""",  # MENTE SUBCONSCIA
    7: """... (omesso qui per brevità nel messaggio – nel tuo file completo ci saranno tutte le carte fino alla 33, come da guida) ...""",  # FIDUCIA
    # NEL TUO file app.py COMPLETO QUI CI SARANNO TUTTE LE VOCI FINO ALLA 33
}

# --------------------------------------------------------------------
# Mappa dal nome della carta al suo significato
# (si appoggia agli ID definiti in CARD_MEANINGS)
# --------------------------------------------------------------------
CARD_MEANINGS_BY_NAME = {
    "Uomo": CARD_MEANINGS.get(1, ""),
    "Emozione": CARD_MEANINGS.get(2, ""),
    "Bambino Interiore": CARD_MEANINGS.get(3, ""),
    "Perdono": CARD_MEANINGS.get(4, ""),
    "Chiarezza Intento": CARD_MEANINGS.get(5, ""),
    "Mente Subconscia": CARD_MEANINGS.get(6, ""),
    "Fiducia": CARD_MEANINGS.get(7, ""),
    "Credere a cio' che si vuole": CARD_MEANINGS.get(8, ""),
    "Osservatore Massimo": CARD_MEANINGS.get(9, ""),
    "Sensazione": CARD_MEANINGS.get(10, ""),
    "Gratitudine": CARD_MEANINGS.get(11, ""),
    "Parte superiore del se'": CARD_MEANINGS.get(12, ""),
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
    "Come in cielo cosi' in terra": CARD_MEANINGS.get(24, ""),
    "Universo": CARD_MEANINGS.get(25, ""),
    "La Rabbia": CARD_MEANINGS.get(26, ""),
    "Bianco": CARD_MEANINGS.get(27, ""),
    "l'Amore": CARD_MEANINGS.get(28, ""),
    "Agire nonostante la paura": CARD_MEANINGS.get(29, ""),
    "Fossa Leoni": CARD_MEANINGS.get(30, ""),
    "Consapevolezza": CARD_MEANINGS.get(31, ""),
    "Obiettivo": CARD_MEANINGS.get(32, ""),
    "Io Sono": CARD_MEANINGS.get(33, ""),
}


def build_prompt(spread_type, cards, intention):
    """
    Crea il testo che viene mandato al modello, usando:
    - tipo di lettura (1 o 3 carte)
    - carte estratte (nomi)
    - intenzione dell'utente (se presente)
    - significati guida dalla tua mappa
    """

    spread_label = (
        "Lettura a 1 carta (messaggio essenziale)"
        if spread_type == "1-carta"
        else "Lettura a 3 carte (passato – presente – potenziale)"
    )

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

    parts.append(
        "\nUsa queste informazioni per restituire UNA SOLA interpretazione integrata, in italiano, "
        "organizzata in brevi paragrafi o punti chiari. "
        "Non fare previsioni fatalistiche, non dare ordini, non ripetere pari pari i testi guida. "
        "Collega il messaggio delle carte all'intenzione dell'utente e proponi spunti concreti di "
        "riflessione o di azione pratica."
    )

    return "\n".join(parts)


# --------------------------------------------------------------------
# Modello per Codici Lettura
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


def validate_and_consume_code(code_string):
    """
    Controlla che il Codice Lettura esista, sia attivo e con crediti disponibili.
    Se ok, scala 1 credito e restituisce credits_left.
    """
    clean_code = (code_string or "").strip().upper()
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
            "error": "CODICE_NON_VALIDO",
            "message": "Il Codice Lettura inserito non è più valido."
        }

    if code.credits_left <= 0:
        return {
            "ok": False,
            "error": "CREDITI_INSUFFICIENTI",
            "message": "Hai esaurito i crediti associati a questo Codice Lettura."
        }

    code.use_credit()
    db.session.commit()

    return {
        "ok": True,
        "credits_left": code.credits_left
    }


def generate_code(credits=3, note=None):
    """
    Utility per generare nuovi Codici Lettura dal backend.
    Esempio d'uso (in una shell o route admin):
        print(generate_code(credits=3, note="Regalo con mazzo carte"))
    """
    raw = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    code_string = "SOP-" + raw

    new_code = ReadingCode(
        code=code_string,
        credits_total=credits,
        credits_used=0,
        disabled=False,
        note=note
    )
    db.session.add(new_code)
    db.session.commit()

    return code_string


# --------------------------------------------------------------------
# Endpoint principale usato dal sito:
#   POST /api/secret-of-power/interpretation
# --------------------------------------------------------------------
@app.route("/api/secret-of-power/interpretation", methods=["POST", "OPTIONS"])
def interpretation():
    # Risposta immediata al preflight CORS (OPTIONS)
    if request.method == "OPTIONS":
        return ("", 200)

    data = request.get_json(silent=True) or {}

    # 1. Controllo Codice Lettura
        # 1. Controllo Codice Lettura
    reading_code = (data.get("code") or "").strip().upper()
    if not reading_code:
        return jsonify({
            "ok": False,
            "error": "CODICE_MANCANTE",
            "message": "È necessario inserire un Codice Lettura."
        }), 400


    credit_check = validate_and_consume_code(reading_code)
    if not credit_check["ok"]:
        # Es. CODICE_NON_VALIDO o CREDITI_INSUFFICIENTI
        return jsonify(credit_check), 400

    # 2. Parametri della lettura
    # accettiamo sia "spread_type" (snake) che "spreadType" (camel)
    spread_type_raw = data.get("spread_type") or data.get("spreadType") or "1-carta"
    # normalizziamo a "1-carta" / "3-carte"
    if str(spread_type_raw) in ("1-carta", "1_carta", "1 carta", "1"):
        spread_type = "1-carta"
    else:
        spread_type = "3-carte"

    cards_raw = data.get("cards", [])      # può essere lista di stringhe O di dict
    intention = data.get("intention")      # stringa o None

    # Normalizziamo le carte in una lista di NOMI (stringhe)
    normalized_cards = []
    for c in cards_raw:
        if isinstance(c, dict):
            # prova a prendere il nome da varie chiavi possibili
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
                "error": "Nessuna carta ricevuta."
            }
        ), 400

    try:
        user_content = build_prompt(spread_type, normalized_cards, intention)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=700,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",  "content": user_content},
            ],
        )

        text = completion.choices[0].message.content.strip()
        return jsonify({
            "ok": True,
            "interpretation": text,
            "message": text,
            "credits_left": credit_check["credits_left"]
        })

    except Exception as e:
        # Log di servizio (lo vedi nei log di Render)
        print("Errore OpenAI:", e)

        fallback = (
            "Le carte sono state estratte, ma al momento non è possibile generare "
            "un messaggio approfondito. Lascia comunque che i loro simboli lavorino dentro di te "
            "e torna più tardi per una nuova lettura."
        )
        return jsonify({
            "ok": False,
            "interpretation": fallback
        }), 200

# ===============================================================
# ADMIN: GENERATORE DI CODICI LETTURA (Semplice, con "password" URL)
# ===============================================================

@app.route("/admin/genera-codice", methods=["GET", "POST"])
def admin_generate_code():
    # Semplice protezione tramite password nell’URL
    secret = request.args.get("secret")
    if secret != "DINAMIC123":  # <-- Cambia questa password!
        return "Accesso negato", 403

    if request.method == "POST":
        try:
            credits = int(request.form.get("credits", 1))
            note = request.form.get("note", "")
            code = generate_code(credits=credits, note=note)

            return f"""
            <h2>Codice generato:</h2>
            <div style='font-size:22px;font-weight:bold;'>{code}</div>
            <p>Crediti: {credits}</p>
            <p>Note: {note}</p>
            <br><br>
            <a href='/admin/genera-codice?secret=DINAMIC123'>Genera un altro codice</a>
            """
        except Exception as e:
            return f"Errore: {e}"

    # FORM HTML
    return """
    <h2>Generatore Codici Lettura</h2>
    <form method='POST'>
        <label>Numero crediti:</label><br>
        <input name='credits' type='number' value='3' /><br><br>

        <label>Note (facoltativo):</label><br>
        <input name='note' type='text' /><br><br>

        <button type='submit'>Genera Codice</button>
    </form>
    """

# Creazione delle tabelle (se non esistono) all'avvio dell'app
with app.app_context():
    db.create_all()

