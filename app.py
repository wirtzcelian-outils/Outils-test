from flask import Flask, jsonify, request
import sqlite3
from contextlib import closing

# créer l'appli avec Flask
app = Flask(__name__)

#Notre base de donnée :
DB_PATH = "etudiants.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn, conn:
        conn.execute(
        """
            CREATE TABLE IF NOT EXISTS etudiants
            (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                nom  TEXT NOT NULL,
                age  INTEGER NOT NULL
            )
        """)

def row_to_dict(row):
    return {"id": row["id"], "nom": row["nom"], "age": row["age"]}

def load_all():
    with closing(get_conn()) as conn:
        cur = conn.execute("SELECT id, nom, age FROM etudiants ORDER BY id")
        return [row_to_dict(r) for r in cur.fetchall()]

#On initialise la base et on charge la liste en mémoire
init_db()
etudiants = load_all()

#La racine de l'Api qui nous permet de tester le serveur
#http://127.0.0.1:5000/
@app.route('/')
def home():
    return "Bienvenue dans l'app"

#petite methode qui liste les étudiants
#http://127.0.0.1:5000/etudiants
@app.route('/etudiants', methods=['GET'])
def get_etudiants():
    return jsonify(etudiants)

#Ajouter un étudiant
@app.route('/ajouter', methods=['POST'])
def add_etudiants():
    data = request.get_json()

    #On vérifie que les étudiants rajoutés sont correctement formés.
    if not data or 'nom' not in data or 'age' not in data:
        return jsonify({"message": "Données invalides. Il faut un nom et un âge."}), 400

    try:
        nom = str(data['nom']).strip()
        age = int(data['age'])

        with closing(get_conn()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO etudiants (nom, age) VALUES (?, ?)",
                (nom, age)
            )
            new_id = cur.lastrowid

        nouveau = {"id": new_id, "nom": nom, "age": age}
        etudiants.append(nouveau)  #On actualise en même temps

        #201 = Ressource créée avec succès
        return jsonify(etudiants), 201

    except Exception as e:
        return jsonify({"message": "Erreur serveur lors de l'ajout.", "detail": str(e)}), 500

#Invoke-RestMethod -Uri http://127.0.0.1:5000/ajouter -Method POST -Body '{"nom":"added","age":82}' -ContentType "application/json"


#Pour récupérer un étudiant par son id
#http://127.0.0.1:5000/etudiants/1
@app.route('/etudiants/<int:etudiant_id>', methods=['GET'])
def get_etudiant(etudiant_id):
    etudiant = next((e for e in etudiants if e['id'] == etudiant_id), None)

    if etudiant:
        return jsonify(etudiant)
    return jsonify({"message": "Étudiant non trouvé"}), 404



#Modifier un étudiant par son id
@app.route('/etudiants/modifier/<int:etudiant_id>', methods=['PUT'])
def update_etudiant(etudiant_id):
    data = request.get_json()

    # On vérifie que les données sont correctes
    if not data or ('nom' not in data and 'age' not in data):
        return jsonify({"message": "Données invalides. Il faut au moins un nom ou un âge à modifier."}), 400

    etudiant = next((e for e in etudiants if e['id'] == etudiant_id), None)
    if not etudiant:
        return jsonify({"message": "Étudiant non trouvé"}), 404

    try:
        new_nom = data.get('nom', etudiant['nom'])
        new_age = int(data.get('age', etudiant['age']))

        with closing(get_conn()) as conn, conn:
            conn.execute(
                "UPDATE etudiants SET nom = ?, age = ? WHERE id = ?",
                (new_nom, new_age, etudiant_id)
            )

        #On met à jour l'objet en mémoire
        etudiant['nom'] = new_nom
        etudiant['age'] = new_age

        return jsonify(etudiant)

    except Exception as e:
        return jsonify({"message": "Erreur serveur lors de la mise à jour.", "detail": str(e)}), 500

#Invoke-RestMethod -Uri http://127.0.0.1:5000/etudiants/modifier/2 -Method PUT -Body '{"nom":"new","age":23}' -ContentType "application/json"
#Pour utiliser en powershell


# Supprimer un étudiant par son id
@app.route('/etudiants/supprimer/<int:et_id>', methods=['DELETE'])
def delete_etudiant(et_id):
    global etudiants #Pour modifier la liste globale

    et = next((e for e in etudiants if e['id'] == et_id), None)
    if not et:
        return jsonify({"message": "Étudiant non trouvé"}), 404

    try:
        with closing(get_conn()) as conn, conn:
            conn.execute("DELETE FROM etudiants WHERE id = ?", (et_id,))

        #Pas oublier de mettre à jour la liste
        etudiants = [e for e in etudiants if e['id'] != et_id]
        return jsonify({"message": f"Étudiant avec id={et_id} supprimé"}), 200

    except Exception as e:
        return jsonify({"message": "Erreur serveur lors de la suppression.", "detail": str(e)}), 500
#Invoke-RestMethod -Uri http://127.0.0.1:5000/etudiants/supprimer/2 -Method DELETE


#pour tester (ne pas faire en production)
if __name__ == '__main__':
    app.run(debug=True)