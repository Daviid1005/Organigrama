# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import psycopg2

app = Flask(__name__)

# Configuración de la conexión a PostgreSQL
DB_CONFIG = {
    "dbname": "organigrama",
    "user": "postgres",
    "password": "root",  
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Crear la tabla organigramas si no existe
    cur.execute('''
        CREATE TABLE IF NOT EXISTS organigramas (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL
        );
    ''')

    # Crear la tabla nodos si no existe
    cur.execute('''
        CREATE TABLE IF NOT EXISTS nodos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            tipo_cargo VARCHAR(50),
            padre_id INTEGER,
            posicion_x INTEGER,
            posicion_y INTEGER
        );
    ''')

    # Verificar si la columna organigrama_id existe en la tabla nodos
    cur.execute('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'nodos' AND column_name = 'organigrama_id';
    ''')
    if not cur.fetchone():
        # Si no existe, agregar la columna organigrama_id
        cur.execute('''
            ALTER TABLE nodos 
            ADD COLUMN organigrama_id INTEGER REFERENCES organigramas(id) ON DELETE CASCADE;
        ''')
        print("Columna organigrama_id agregada a la tabla nodos.")

    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- Rutas para organigramas ---
@app.route('/organigramas', methods=['GET'])
def get_organigramas():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM organigramas")
        organigramas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"id": org[0], "nombre": org[1]} for org in organigramas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/organigramas', methods=['POST'])
def add_organigrama():
    try:
        data = request.json
        nombre = data['nombre']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO organigramas (nombre) VALUES (%s) RETURNING id", (nombre,))
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"id": new_id, "nombre": nombre})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/organigramas/<int:id>', methods=['PUT'])
def update_organigrama(id):
    try:
        data = request.json
        nombre = data['nombre']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE organigramas SET nombre = %s WHERE id = %s", (nombre, id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Organigrama actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/organigramas/<int:id>', methods=['DELETE'])
def delete_organigrama(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM organigramas WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Organigrama eliminado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Rutas para nodos ---
@app.route('/nodos/<int:organigrama_id>', methods=['GET'])
def get_nodos(organigrama_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, tipo_cargo, padre_id, posicion_x, posicion_y FROM nodos WHERE organigrama_id = %s", (organigrama_id,))
        nodos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([{"id": n[0], "nombre": n[1], "tipo_cargo": n[2], "padre_id": n[3], "x": n[4], "y": n[5]} for n in nodos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nodos/<int:organigrama_id>', methods=['POST'])
def add_nodo(organigrama_id):
    try:
        data = request.json
        print(f"Recibiendo datos para crear nodo: {data}")  # Depuración
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO nodos (organigrama_id, nombre, tipo_cargo, padre_id, posicion_x, posicion_y) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (organigrama_id, data['nombre'], data['tipo_cargo'], data.get('padre_id'), data['x'], data['y'])
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        print(f"Nodo creado con ID: {new_id}")  # Depuración
        return jsonify({"id": new_id})
    except Exception as e:
        print(f"Error al crear nodo: {str(e)}")  # Depuración
        return jsonify({"error": str(e)}), 500

@app.route('/nodos/<int:organigrama_id>/<int:id>', methods=['PUT'])
def update_nodo(organigrama_id, id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE nodos SET nombre = %s, tipo_cargo = %s, padre_id = %s, posicion_x = %s, posicion_y = %s WHERE id = %s AND organigrama_id = %s",
            (data['nombre'], data['tipo_cargo'], data.get('padre_id'), data['x'], data['y'], id, organigrama_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Nodo actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nodos/<int:organigrama_id>/<int:id>', methods=['DELETE'])
def delete_nodo(organigrama_id, id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM nodos WHERE id = %s AND organigrama_id = %s", (id, organigrama_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Nodo eliminado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)