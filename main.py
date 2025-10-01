from flask import Flask, render_template, request, url_for, redirect, session
# pour les variables d'environnement faire cet import + dans le terminal : pip install python-dotenv
#from dotenv import load_dotenv
import pymongo
#On importe os, pour mettre les mots de passe en sécurité, dans un fichier .env tel que la clé mongo.db ou le cookie de session
import os

# Charger les variables d'environnement depuis le fichier .env
#load_dotenv()

# Pour crypter les mots de passe
import bcrypt

# Pour gérer les ObjectId
from bson.objectid import ObjectId


app = Flask(__name__)

# Connexion a la bdd mongodb
# connexion à la bdd 
mongo = pymongo.MongoClient("mongodb+srv://soizic-b:GR56#pgjt@marketplace.dlpu8gi.mongodb.net/?retryWrites=true&w=majority&appName=marketplace")



# Cookie de session utilisateur
##app.secret_key = os.getenv("COOKIES_KEY")
app.secret_key = os.urandom(24)



# Page Accueil
@app.route('/')
def index():
  db_annonces = mongo.db.activites
  annonces = db_annonces.find({})
  if 'util' in session:
    return render_template('index.html',
                           nom=session['util'],
                           annonces=annonces)
  else:
    return render_template('index.html', annonces=annonces)


# Route pour créer un nouvel utilisateur
@app.route('/register', methods=['POST', 'GET'])
def register():
  # Si on essaye de soumettre un formulaire
  if request.method == 'POST':
    # On verifie qu'un utilisateur du meme nom n'existe pas
    db_utils = mongo.db.utilisateurs
    # Si l'utilisateur existe déja on demande de re-remplir le formulaire
    if (db_utils.find_one({'nom': request.form['utilisateur']})):
      return render_template('register.html',
                             erreur="Le nom d'utilisateur existe deja")
    # Sinon on créé l'utilisateur
    else:
      if (request.form['mot_de_passe'] == request.form['verif_mot_de_passe']):
        # On crypte le mot de passe
        mdp_encrypte = bcrypt.hashpw(
          request.form['mot_de_passe'].encode('utf-8'), bcrypt.gensalt())
        # On ajoute l'utilisateur
        db_utils.insert_one({
          'nom': request.form['utilisateur'],
          'mdp': mdp_encrypte
        })
        # On le connecte
        session['util'] = request.form['utilisateur']
        # On retourne à la page d'accueil
        return redirect(url_for('index'))
      # Sinon on renvoie le template vide et met un message d'erreur
      else:
        return render_template(
          'register.html', erreur="Les mots de passe doivent être identiques")
  else:
    return render_template('register.html')


# Route de connexion (si l'on a dejà créé un compte)
@app.route('/login', methods=['POST', 'GET'])
def login():
  # Si on essaye de se connecter
  if request.method == 'POST':
    db_utils = mongo.db.utilisateurs
    # On appelle la table utilisateurs de la bdd
    util = db_utils.find_one({'nom': request.form['utilisateur']})
    # Si l'utilisateur existe
    if util:
      # on vérifie si le mot de passe est bon
      if bcrypt.checkpw(request.form['mot_de_passe'].encode('utf-8'),
                        util['mdp']):
        session['util'] = request.form['utilisateur']
        return redirect(url_for("index"))
      # Sinon on envoie un message d'erreur du mot de passe incorrect
      else:
        return render_template('login.html',
                               erreur="Le mot de passe est incorrect")
    # Sinon on envoie un message que l'utilisateur n'existe pas
    else:
      return render_template('login.html',
                             erreur="Le nom d'utilisateur n'existe pas")
  else:
    return render_template('login.html')


# Route de déconnexion
@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for("index"))


# Route pour créer une nouvelle annonce
@app.route('/nouvelle_annonce', methods=['POST', 'GET'])
def nouvelle_annonce():
  # Si l'utilisateur n'est pas connecté
  if 'util' not in session:
    return render_template('register.html')
  # Si on essaye d'envoyer le formulaire
  if request.method == 'POST':
    # On appelle la table "annonces" de la bdd
    db_annonces = mongo.db.annonces
    titre = request.form['titre']
    description = request.form['description']
    # Si les champs titre et description sont remplis
    if (titre and description):
      # On insère ces nouvelles données dans la bdd
      db_annonces.insert_one({
        'titre': titre,
        'description': description,
        'auteur': session['util']
      })
      return render_template("nouvelle_annonce.html",
                             erreur="Votre annonce a bien été soumise")
    else:
      return render_template(
        "nouvelle_annonce.html",
        erreur="Veuillez saisir un titre et une description")
  return render_template("nouvelle_annonce.html")


# Route d'une annonce
@app.route("/annonce/<id_annonces>", methods=['POST', 'GET'])
def annonce(id_annonces):
  # Je récupère l'id unique de l'annonce
  db_annonces = mongo.db.annonces
  annonce = db_annonces.find_one({"_id": ObjectId(id_annonces)})
  # Je récupère les commentaires liés à cette annonce
  db_commentaires = mongo.db.commentaires
  commentaires = db_commentaires.find({"id_annonces": id_annonces})
  # si l'utilisateur essaye d'ajouter un commentaire
  # Si on essaye d'envoyer le formulaire
  if request.method == 'POST':
    # Si l'utilisateur n'est pas connecté
    if 'util' not in session:
      return render_template('register.html')
    else:
      db_commentaires = mongo.db.commentaires
      description = request.form['description']
      # On ajoute notre commentaire aux commentaires actuels
      db_commentaires.insert_one({
        "id_annonces": id_annonces,
        "auteur": session["util"],
        "description": description
      })
      return render_template("annonce.html",
                             annonce=annonce,
                             commentaires=commentaires)
  return render_template("annonce.html",
                         annonce=annonce,
                         commentaires=commentaires)


#Route pour tester la connexion de la bdd
@app.route('/test')
def test():
  db_test = mongo.db.test
  test = db_test.find({})
  return render_template('test.html', test=test)


app.run(host='0.0.0.0', port=81)
