from flask import Flask, render_template,session,json
import model as md
import ssl

app = Flask(__name__)


@app.route('/map')
def index():
  return render_template('index.html')

@app.route('/home')
def home():
  return render_template('home.html')

@app.route('/questionnaire')
def questionnaire():
  return render_template('questionnaire.html')


@app.route('/')
def data_point():
  return render_template('data_points.html')

@app.route("/map/<division>/<etablissement>")
def get_geodata (division,etablissement,methods=['GET', 'POST']):
    print(division)
    map_value = dict(commune="ADM2_PCODE",departement="ADM1_PCODE")
    data_json,map_data,total= md.filter_and_build_dataset(division=division,revenu=['NA'])
    r = json.dumps(dict(data= data_json,color_map=map_data,total= str(total)))
    loaded_r = json.loads(r)
    return r

@app.route("/map1/<division>/<revenu>/<site_internet>/<subvension>/<discipline>/<log_transform>/<normalize>")
def get_geodata2 (division,revenu,site_internet,subvension,discipline,log_transform,normalize,methods=['GET', 'POST']):
    revenu = revenu.split(",")
    discipline =  discipline.split(",")
    print(revenu)
    print(discipline)
   
    data_json,map_data,total= md.filter_and_build_dataset(division=division,log_transform=bool(int(log_transform)),normalize=bool(int(normalize)),revenu=revenu,discipline=discipline,site_internet=site_internet,subvension=subvension)
    r = json.dumps(dict(data= data_json,color_map=map_data,total= str(total)))
   
    return r

@app.route("/map2/<group_age>/<sexe>/<discipline>/<firstname>/<lastname>/<search_artiste>")
def get_geodata3 (group_age,sexe,discipline,firstname,lastname,search_artiste,methods=['GET', 'POST']):
    group_age = group_age.split(",")
    discipline =  discipline.split(",")
    data_json= md.filter_data_point(group_age=group_age,sexe=sexe,discipline=discipline,firstname=firstname,lastname=lastname,nom_artiste=search_artiste)
    return data_json

if __name__ == "__main__": 
  app.run(debug=True, host='127.0.0.1', port=5000)
