import requests
import pandas as pd
import numpy as np
import json
import geopandas as gpd
import os
import folium
from dotenv import load_dotenv
import json
from bokeh.palettes import d3,brewer
from sklearn import preprocessing

# load the token
load_dotenv()
token = os.getenv('token')
url = os.getenv('url')


# create function dataframe from api dataset
def get_data_frame_from_api(token,url):
    # build the header api
    headers = {'Authorization': token}
    # get request from the kobotoolbox api
    response  = requests.get(url,headers=headers)
    # convert binary content to string
    content =response.content.decode()
    # convert string to json objects
    content = json.loads(str(content))
    # create the FOKAL dataframe
    df =pd.DataFrame(content[1:])
    # rebuild the column names
    columns = [col.split("/")[-1] for col in df.columns]
    # renames the column names
    df.columns = columns
    # save the dataset to csv file
   # df.to_csv('datasets/fokal_dataset.csv')
    return df

#df_master= get_data_frame_from_api(token,url)


def  get_latitude(x):
    long_ = None
    x =str(x)
    if len(x.split(' ')) >2:
        long_ =x.split(' ')[0]
        
    return long_

def  get_longitude(x):
    lat_ = None
    x =str(x)
    if len(x.split(' ')) >2:
        lat_ =x.split(' ')[1]
    return lat_

def age_group(x):
    x = float(x) if x else 0
    #  18-24 ans			25-35 ans		36-50 ans		50-70 ans		 + de 70 ans
    group = None
    if x>=18 and x<26:
        group="18-25 ans"
    elif x>=26 and x<36:
        group="26-35 ans"
    elif x>=36 and x<50:
        group="36-50 ans"
    elif x>=50 and x<70:
        group="50-70 ans"
    elif x>=70:
        group="+ de 70 ans"
    else:
        group="inconnu"
    
    return group



def replace_all_values(df):
    df_choices = pd.read_excel('datasets/data_dict.xlsx',sheet_name='choices')
    df_survey = pd.read_excel('datasets/data_dict.xlsx',sheet_name='survey')
    map_dict = dict()
    for index,value in zip(df_choices['name'],df_choices['label::French (fr)']):
        if  'ht' not in index:
            map_dict[index] = value
    df.replace(map_dict,inplace=True)
    return df,map_dict



def filter_and_build_dataset(division="commune",revenu=['revenu_tranche1','revenu_tranche2','revenu_tranche4','revenu_tranche5','revenu_tranche6','nan'],site_internet="",subvension="",discipline=['NA'],log_transform=False,normalize=False):
    boundary_id = dict(departement="ADM1_PCODE",commune = "ADM2_PCODE")
    boundary_name =dict(departement="ADM1_FR",commune = "ADM2_FR")
    boundary_url = dict(departement='datasets/boundaries/hti_admbnda_adm1_cnigs_20181129.shp',commune="datasets/boundaries/hti_admbnda_adm2_cnigs_20181129.shp")
   
    boundary_data = None
    boundary_data = gpd.read_file(boundary_url[division])
    boundary_data['long'] = boundary_data.geometry.centroid.x
    boundary_data['lat'] = boundary_data.geometry.centroid.y
    col =[boundary_name[division],boundary_id[division],'geometry','long','lat']
    boundary_data.set_geometry('geometry')
    boundary_data = boundary_data[col]
     
    dataset = pd.read_csv('datasets/fokal_dataset1.csv')
    dataset = get_data_frame_from_api(token,url)
    #dataset = dataset.drop_duplicates(subset=['nom','prenom','age','sexe','email'])
    selected_features = [division,'sexe','prenom','nom','age','email','site_internet','dis_artis_princ','whatsapp','id_whatsapp','adresse_site_internet','subventions','nationalite','email','id_facebook','id_instagram','cause_defendue','aut_act_artis','artist_gps','revenu_temps_normal']
    dataset = dataset[selected_features]
    #dataset=dataset[~(dataset.sexe.isna() | dataset.nom.isna() | dataset.prenom.isna())]
   
    if revenu[-1] != 'NA':
        dataset = dataset[dataset.revenu_temps_normal.isin(revenu)]
       
    if site_internet =='oui':
        dataset = dataset[dataset.site_internet ==site_internet ]
       
    if subvension  =='oui':
        dataset = dataset[dataset.subventions ==subvension ]
      
    if discipline[-1] != 'NA':
        dataset = dataset[dataset.dis_artis_princ.isin(discipline) ]
       

    dataset.rename(columns=boundary_id,inplace=True)
    dataset[boundary_id[division]]= dataset[boundary_id[division]].str.upper()
    
    dataset=dataset.groupby(by=boundary_id[division]).size().reset_index().rename(columns={0:'count'})
    dataset['value'] =  dataset['count']
    total =  dataset['count'].sum()
    if normalize:
        values =np.round(preprocessing.normalize(dataset[['count']])*100,0)
        dataset['count'] = values
    if log_transform:
        dataset['count']= np.round(np.log(dataset['count']),2)
    
       
    
    
    dataset =pd.merge(boundary_data,dataset,how='left')
    dataset.fillna(0,inplace=True)
    

        
    map_color,dataset =df_map_color(dataset,'count',division=division)    
    dataset = dataset.to_json()
    #map_color = map_color.to_json()
    map_color = dict(color=list(map_color['color']),values=list(map_color['count']))
   
    return dataset,map_color,total


def filter_data_point(group_age=['NA'],sexe='NA',subvension='',discipline=['NA'],firstname="",lastname="",nom_artiste=""):
    boundary_id = dict(departement="ADM1_PCODE",commune = "ADM2_PCODE")
    boundary_name =dict(departement="ADM1_FR",commune = "ADM2_FR")
    boundary_url = dict(departement='datasets/boundaries/hti_admbnda_adm1_cnigs_20181129.shp',commune="datasets/boundaries/hti_admbnda_adm2_cnigs_20181129.shp")
    division = 'commune'
    boundary_data = None
    boundary_data = gpd.read_file(boundary_url[division])
    boundary_data.set_geometry('geometry')
    boundary_data['x'] = boundary_data.geometry.centroid.x
    boundary_data['y'] = boundary_data.geometry.centroid.y
    col =[boundary_name[division],boundary_id[division],'x','y']
    boundary_data = boundary_data[col]
     
    #dataset = pd.read_csv('datasets/fokal_dataset1.csv')
    dataset = get_data_frame_from_api(token,url)
    #dataset = dataset.drop_duplicates(subset=['nom','prenom','age','sexe','email'])
    selected_features = [division,'sexe','prenom','nom_artiste','nom','age','email','site_internet','dis_artis_princ','whatsapp','id_whatsapp','adresse_site_internet','subventions','nationalite','id_facebook','id_instagram','cause_defendue','aut_act_artis','artist_gps','revenu_temps_normal','_geolocation']
    dataset = dataset[selected_features]
    #dataset=dataset[~(dataset.sexe.isna() | dataset.nom.isna() | dataset.prenom.isna())]
    dataset['nom']=dataset['nom'].astype('str')
    dataset['prenom']=dataset['prenom'].astype('str')
    dataset['sexe']=dataset['sexe'].astype('str')
    dataset['nom_artiste']=dataset['nom_artiste'].astype('str')
    dataset['id_facebook']=dataset['id_facebook'].astype('str')
    dataset['id_instagram']=dataset['id_instagram'].astype('str')
    dataset['id_instagram'] = dataset['id_instagram'].fillna('N/A')
    dataset['id_facebook'] = dataset['id_facebook'].fillna('N/A')
   
    

      
    dataset.loc[(dataset.prenom == 'Evenie Rose Thafaina') &(dataset.nom == 'Saint Louis')	,'nom_artiste'] = 'Tafa Mi-Soleil'
    dataset.loc[(dataset.prenom == 'Roosevelt') &(dataset.nom == 'Saillant'),'nom_artiste'] = 'BIC'
    dataset.loc[(dataset.prenom == 'Richard') &(dataset.nom == 'Morse'),'nom_artiste'] = 'RAM'
    
    dataset['nom_f'] = dataset['nom'].str.lower() 
    dataset['prenom_f'] = dataset['prenom'].str.lower() 
    dataset['age_group'] = dataset.age.apply(age_group)
    dataset['sexe_f'] =  dataset['sexe'].str.lower()
    dataset['nom_artiste_f'] =  dataset['nom_artiste'].str.lower()
    
	


    
      
    if group_age[-1] != 'NA':
        dataset = dataset[dataset.age_group.isin(group_age)]
      
    if sexe !='NA':
        dataset = dataset[dataset.sexe_f ==sexe.lower() ]
              
    if discipline[-1] != 'NA':
        dataset = dataset[dataset.dis_artis_princ.isin(discipline) ]
    if firstname !='NA':
        dataset = dataset[dataset.nom_f.str.contains(firstname.lower()) ]
    if lastname !='NA':
        dataset = dataset[dataset.prenom_f.str.contains(lastname.lower()) ]
    if nom_artiste !='NA':
        dataset = dataset[dataset.nom_artiste_f.str.contains(nom_artiste.lower()) ]
  

    dataset.rename(columns=boundary_id,inplace=True)
    dataset[boundary_id[division]].fillna('ht0111',inplace=True) 
    dataset[boundary_id[division]]= dataset[boundary_id[division]].str.upper()
           
    
    
    dataset =pd.merge(boundary_data,dataset,how='inner')
    dataset.fillna(0,inplace=True)
    
    dataset['long'] =  dataset.artist_gps.apply(get_longitude)
    dataset['lat'] = dataset.artist_gps.apply(get_latitude)
    dataset['lat'] = dataset['lat'].astype('float')
    dataset['long'] = dataset['long'].astype('float')
    
    dataset['dist'] = np.nan
    dataset['long']=dataset['long'].mask(pd.isnull, dataset['x'])
    dataset['lat']=dataset['lat'].mask(pd.isnull, dataset['y'])
    for index in dataset.index:
        d1= np.array((dataset.at[index,'long'],dataset.at[index,'lat']))
        d2 = np.array((dataset.at[index,'x'],dataset.at[index,'y']))
        dataset.at[index,'dist'] = np.linalg.norm(d1 - d2) 
    
    
    
    dataset.sort_values(by='dist',ascending=0,inplace=True)
    dataset=dataset[dataset.dist <=4]
   

    return dataset.to_json(orient='records')

def df_map_color(data,column,palette = 'RdYlBu',range = 10,division="departement"):
    if division == 'departement':
    # creates a color palette
        palette = brewer['RdYlBu'][range]
        # reverses the color palette
        palette =palette[::-1]
        # add the color column to dataframe
        data['color'] = pd.qcut(data[column],q=range,labels=list(palette),duplicates='drop')
        #data['color'] =  data[column].apply(define_color)
        # computes the palette legend
        color_map = data[data.color.notna()].groupby(['color'])[column].min().to_frame().reset_index() 
        # removes non display colunms
        color_map = color_map[color_map[column].notna()]
    
        return color_map,data
    else:
        range =20
       
        palette = brewer['RdYlBu'][10]
        # reverses the color palette
        palette =palette[::-1]
        # add the color column to dataframe
        val =data.groupby(pd.qcut(data[column], q=[0,.75,0.775,0.8,0.825,0.850,0.875,0.9,0.925,0.950,0.975,1],labels=False,duplicates="drop"))[column].sum()
        val = sorted(val)
       
        data['color'] = pd.cut(data[column],bins=[0,1,2,3,5,11.0, 12.0, 13.0, 15.0,41.0, 261.0],labels=palette[0:10])
        data.loc[data[column] ==0,'color'] ="#a50026"
        print( data.loc[data[column] ==0,'color'])
        #val = sorted(data['bin'])
        #val= list(set(val))
        #print(val)
        #data['color'] =  data['bin'].apply(lambda x: palette[x])
        #print(data['count'].describe())
        #data['color'] =  data[column].apply(define_color)
        # computes the palette legend
       
        color_map = data[data.color.notna()].groupby(['color'])[column].min().to_frame().reset_index() 
        # removes non display colunms
        color_map = color_map[color_map[column].notna()]
        #print(set(data['bin']))
        return color_map,data


   







