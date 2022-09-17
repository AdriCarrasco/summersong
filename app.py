import streamlit as st
import json
import pandas as pd
import plotly.express as px
import boto3
from streamlit_elements import elements, mui, html
import yaml
import streamlit_authenticator as stauth
from streamlit_authenticator import Authenticate

aws_access_key_id = st.secrets["aws_key"]
aws_secret_access_key = st.secrets["aws_secret_key"]

st.set_page_config(page_title="SUMMER SONG", 
                   page_icon="https://thechurch.es/wp-content/uploads/2020/06/Summer.jpg",
                   layout = "wide")
def GetJSON(key_ , aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key):
    client = boto3.client('s3',aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    f = client.get_object(Bucket = 'summer-song', Key= key_)
    text = f["Body"].read().decode()
    return json.loads(text)

def PutJSON(key_, data_votes,aws_access_key_id = aws_access_key_id, aws_secret_access_key = aws_secret_access_key):
    client = boto3.client('s3',aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    client.put_object(
                Body=json.dumps(data_votes),
                Bucket='summer-song',
                Key='data_votes.json'
    )

s3_client = boto3.client('s3',aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
response = s3_client.get_object(Bucket='summer-song', Key="config_password.yaml")
try:
    configfile = yaml.safe_load(response["Body"])
except yaml.YAMLError as exc:
    st.error("Error in downloading configuration")

authenticator = Authenticate(
    configfile['credentials'],
    configfile['cookie']['name'],
    configfile['cookie']['key'],
    configfile['cookie']['expiry_days'],
    configfile['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    dict_songs = GetJSON("data_songs.json")



    def DropList(list_, instances = []):
        new_list_ = []
        for i in list_:
            if i not in instances:
                new_list_.append(i)
        return new_list_

    st.title("Canción del verano")


    tab1, tab2 = st.tabs(["Vota", "Resultados"])
    with tab1:
        user_select = st.selectbox("Input user", options = pd.unique(dict_songs["users"]))
        select_player = st.checkbox("View YouTube Player")
        if select_player:

            col_0_0, col_0_1 = st.columns([2,2])

            with col_0_0:
                song_video_select = st.selectbox("Listen to song", options = dict_songs["songs"])
                ind_song = dict_songs["songs"].index(song_video_select)
                st.video(dict_songs["yt"][ind_song])
            with col_0_1:
                songs_not_available = []
                for i in range(len(dict_songs["songs"])):
                    if dict_songs["users"][i] == user_select:
                        songs_not_available.append(dict_songs["songs"][i])
                st.write("Vota tus tres canciones favoritas")
                song1 = st.selectbox("Give 5 points to:", options = DropList(dict_songs["songs"], songs_not_available))
                song2 = st.selectbox("Give 2 points to:", options = DropList(dict_songs["songs"], songs_not_available + [song1]))
                song3 = st.selectbox("Give 1 points to:", options = DropList(dict_songs["songs"], songs_not_available + [song1, song2]))
        else:
            songs_not_available = []
            for i in range(len(dict_songs["songs"])):
                if dict_songs["users"][i] == user_select:
                    songs_not_available.append(dict_songs["songs"][i])
            song1 = st.selectbox("Give 5 points to:", options = DropList(dict_songs["songs"], songs_not_available))
            song2 = st.selectbox("Give 3 points to:", options = DropList(dict_songs["songs"], songs_not_available + [song1]))
            song3 = st.selectbox("Give 1 points to:", options = DropList(dict_songs["songs"], songs_not_available + [song1, song2]))

        if st.button("Votar"):
            try:
                dict_votes = GetJSON("data_votes.json")
            except:
                dict_votes = {}
            
            if user_select not in dict_votes.keys():
                dict_votes[user_select] = [song1, song2, song3]
                
                PutJSON("data_votes.json", dict_votes)
            else:
                st.warning("¡Ya has votado!")
                
    with tab2:
        st.title("Results")

        votes_weights = [5,2,1]


        try:
            dict_votes = GetJSON("data_votes.json")
        except:
            dict_votes = {}
            st.warning("Nadie ha votado todavía")
        
        people_voted = len(list(dict_votes.keys()))
        people_left =  len(pd.unique(dict_songs["users"])) - people_voted

        list_dicts = []
        for user in dict_votes.keys():
            for i in range(len(dict_votes[user])):
                dict_ = {
                    "Song": dict_votes[user][i],
                    "Vote": votes_weights[i],
                    "User": user
                }
                list_dicts.append(dict_)
        data_votes = pd.DataFrame(list_dicts)
        data_grouped = data_votes[["Song", "Vote"]].groupby(["Song"]).sum()
        data_grouped = data_grouped.reset_index(level = "Song").sort_values("Vote", ascending = False)

        data_grouped.columns = ["Canción", "Votos"]

        winner_song = data_grouped["Canción"].tolist()[0]

        col_status, col_left, col_winner = st.columns([1,1,4])

        with col_status:
            st.metric("Votos", people_voted)
        with col_left:
            st.metric("Restantes", people_left)
        with col_winner:
            st.metric("Ganador", winner_song)

        col_0_0, col_0_1, col_0_2 = st.columns([1,2,2])

        with col_0_0:
            st.dataframe(data_grouped)
        with col_0_1:
            fig = px.pie(data_votes, names = "Song")
            st.plotly_chart(fig,use_container_width=False)
        with col_0_2:
            fig = px.bar(data_grouped[0:3], x = "Canción", y = "Votos")
            st.plotly_chart(fig, use_container_width= True)

elif authentication_status == False:
    st.error('Username/password is incorrect')