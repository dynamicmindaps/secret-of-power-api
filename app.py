from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
# Consenti richieste solo dal tuo dominio
CORS(app, resources={r"/api/*": {"origins": "https://www.dynamicmind.info"}})

# Client OpenAI: usa la variabile d'ambiente OPENAI_API_KEY
client = OpenAI()

SYSTEM_PROMPT = """
Sei l'oracolo delle carte "The Secret of Power", un mazzo basato sulla Legge di Attrazione.
Rispondi in italiano, con uno stile chiaro, caldo e centrato sulla consapevolezza.
Non essere fatalista né deterministico: le carte mostrano possibilità, non destini fissi.

Linee guida:
- Collega i nomi delle carte al tema dell'intenzione della persona.
- Metti in luce le risorse interiori, non i problemi.
- Dai sempre almeno un piccolo spunto pratico concreto (un gesto, una riflessione, un esercizio).
- Mantieni una lunghezza di 2–4 paragrafi.
"""

def build_user_prompt(spread_type, cards):
    """
    spread_type: '1-carta' oppure '3-carte'
    cards: lista di nomi delle carte
    """
    if spread_type == "1-carta":
        intro = "Lettura a 1 carta (messaggio essenziale)."
    else:
        intro = "Lettura a 3 carte (passato – presente – potenziale)."

    cards_list = ", ".join(cards)
    user_prompt = (
        f"{intro}\n"
        f"Le carte estratte sono: {cards_list}.\n\n"
        "Fornisci un'interpretazione che aiuti la persona a comprendere il messaggio delle carte, "
        "mettendo l'accento su come può usare questa consapevolezza nella vita quotidiana. "
        "Non dare previsioni assolute, ma suggerimenti di crescita."
    )
    return user_prompt

@app.route("/api/secret-of-power/interpretation", methods=["POST"])
def interpretation():
    data = request.get_json() or {}
    spread_type = data.get("spreadType", "1-carta")
    cards = data.get("cards", [])

    if not cards:
        return jsonify({"error": "Nessuna carta fornita"}), 400

    user_prompt = build_user_prompt(spread_type, cards)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
        )

        text = response.choices[0].message.content.strip()
        return jsonify({"interpretation": text})

    except Exception as e:
        # Log su console per debug
        print("Errore OpenAI:", e)
        return jsonify({
            "interpretation": (
                "Le carte sono state estratte, ma al momento non è possibile generare "
                "un messaggio approfondito. Lascia comunque che i loro simboli lavorino dentro di te."
            )
        }), 200

# Punto di ingresso per gunicorn (app:app)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
