from flask import Flask, render_template, request, jsonify
from src.generator import (
    generate_microlearning_path,
    valuta_risposta,
    genera_spiegazione_alternativa,
    genera_saluto_finale,
    genera_riepilogo_finale,
    genera_hint,
)
from src.database import (
    init_db,
    save_session,
    save_attempt,
    update_module_state,
    save_riepilogo,
    find_similar_modules,
    get_all_sessions,
    get_session_modules,
    get_module_attempts,
)
from src.config import RAG_TOP_K

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
        context = find_similar_modules(topic, top_k=RAG_TOP_K) or None
        tutor_response = generate_microlearning_path(topic, level, context_modules=context)
        modules_data = [m.model_dump() for m in tutor_response.percorso_studio.moduli]
        sid = save_session(topic, level, modules_data)
        db_modules = get_session_modules(sid)
        module_id_map = {str(dbm["module_index"] + 1): dbm["id"] for dbm in db_modules}
        return jsonify({
            'success': True,
            'session_id': sid,
            'module_db_ids': module_id_map,
            'data': tutor_response.model_dump(),
        }), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    data = request.json or {}
    esercizio = data.get('esercizio', '').strip()
    soluzione = data.get('soluzione', '').strip()
    module_db_id = data.get('module_db_id')

    if not esercizio or not soluzione:
        return jsonify({'success': False, 'error': 'Esercizio e soluzione sono obbligatori.'}), 400

    try:
        feedback = valuta_risposta(esercizio, soluzione)
        esito = feedback.esito or "sbagliata"

        if module_db_id:
            save_attempt(module_db_id, soluzione, esito, feedback.model_dump_json())

        return jsonify({
            'success': True,
            'esito': esito,
            'commento_costruttivo': feedback.commento_costruttivo,
            'suggerimento_miglioramento': feedback.suggerimento_miglioramento,
        }), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/hint', methods=['POST'])
def api_hint():
    data = request.json or {}
    esercizio = data.get('esercizio', '').strip()
    soluzione = data.get('soluzione', '').strip()
    livello = data.get('livello', '').strip().lower()
    tentativo = data.get('tentativo', 1)

    if not esercizio or not soluzione or not livello:
        return jsonify({'success': False, 'error': 'Esercizio, soluzione e livello sono obbligatori.'}), 400

    try:
        hint = genera_hint(esercizio, soluzione, livello, int(tentativo))
        return jsonify({'success': True, 'hint': hint}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/archive-module', methods=['POST'])
def api_archive_module():
    data = request.json or {}
    module_db_id = data.get('module_db_id')
    if not module_db_id:
        return jsonify({'success': False, 'error': 'module_db_id obbligatorio.'}), 400
    try:
        update_module_state(module_db_id, archived=True)
        return jsonify({'success': True}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/complete-module', methods=['POST'])
def api_complete_module():
    data = request.json or {}
    module_db_id = data.get('module_db_id')
    if not module_db_id:
        return jsonify({'success': False, 'error': 'module_db_id obbligatorio.'}), 400
    try:
        update_module_state(module_db_id, completed=True)
        return jsonify({'success': True}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/history', methods=['GET'])
def api_history():
    try:
        sessions = get_all_sessions()
        return jsonify({'success': True, 'data': sessions}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/session-detail', methods=['POST'])
def api_session_detail():
    data = request.json or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id obbligatorio.'}), 400
    try:
        modules = get_session_modules(int(session_id))
        result = []
        for m in modules:
            attempts = get_module_attempts(m["id"])
            result.append({**m, "attempts": attempts})
        return jsonify({'success': True, 'data': result}), 200
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
    session_id = data.get('session_id')

    if not isinstance(solutions, list) or not livello:
        return jsonify({'success': False, 'error': 'Soluzioni e livello sono obbligatori.'}), 400

    try:
        riepilogo = genera_riepilogo_finale(solutions, diary, livello)
        if session_id:
            save_riepilogo(int(session_id), riepilogo.model_dump_json())
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
    init_db()
    app.run(debug=True)
