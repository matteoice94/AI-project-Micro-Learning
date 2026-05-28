from flask import Flask, render_template, request, jsonify
from src.generator import (
    generate_microlearning_path,
    valuta_risposta,
    genera_spiegazione_alternativa,
    genera_saluto_finale,
    genera_riepilogo_finale,
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json or {}
    topic = data.get('topic', '').strip()
    level = data.get('level', '').strip().lower()
    name = data.get('name', '').strip() or 'Studente'

    if not topic or not level:
        return jsonify({'success': False, 'error': 'Topic e livello sono obbligatori.'}), 400

    try:
        tutor_response = generate_microlearning_path(topic, level)
        return jsonify({'success': True, 'data': tutor_response.model_dump()}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    data = request.json or {}
    esercizio = data.get('esercizio', '').strip()
    soluzione = data.get('soluzione', '').strip()

    if not esercizio or not soluzione:
        return jsonify({'success': False, 'error': 'Esercizio e soluzione sono obbligatori.'}), 400

    try:
        feedback = valuta_risposta(esercizio, soluzione)
        return jsonify({
            'success': True,
            'commento_costruttivo': feedback.commento_costruttivo,
            'suggerimento_miglioramento': feedback.suggerimento_miglioramento,
        }), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/api/clarify', methods=['POST'])
def api_clarify():
    data = request.json or {}
    argomento = data.get('argomento', '').strip()
    spiegazione = data.get('spiegazione', '').strip()
    dubbio = data.get('dubbio', '').strip()
    livello = data.get('livello', '').strip().lower()

    if not argomento or not spiegazione or not dubbio or not livello:
        return jsonify({'success': False, 'error': 'Argomento, spiegazione, dubbio e livello sono obbligatori.'}), 400

    try:
        result = genera_spiegazione_alternativa(argomento, spiegazione, dubbio, livello)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/api/final-summary', methods=['POST'])
def api_final_summary():
    data = request.json or {}
    solutions = data.get('solutions')
    diary = data.get('diary', [])
    livello = data.get('livello', '').strip().lower()

    if not isinstance(solutions, list) or not livello:
        return jsonify({'success': False, 'error': 'Soluzioni e livello sono obbligatori.'}), 400

    try:
        riepilogo = genera_riepilogo_finale(solutions, diary, livello)
        return jsonify({'success': True, 'data': riepilogo.model_dump()}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

@app.route('/api/saluto', methods=['POST'])
def api_saluto():
    data = request.json or {}
    nome = data.get('nome', '').strip() or 'Studente'
    livello = data.get('livello', '').strip().lower()
    interruzione = data.get('interruzione', False)

    if not livello:
        return jsonify({'success': False, 'error': 'Il livello è obbligatorio.'}), 400

    try:
        saluto = genera_saluto_finale(nome, livello, bool(interruzione))
        return jsonify({'success': True, 'saluto': saluto}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

if __name__ == '__main__':
    app.run(debug=True)
