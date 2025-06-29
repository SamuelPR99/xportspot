from ytmusicapi import YTMusic
import csv

ytmusic = YTMusic('browser.json')

nombre_lista = "Techno"
id_lista = ytmusic.create_playlist(nombre_lista, "Importada desde Spotify")

with open('csv.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
    
        titulo = row[1]
        artista = row[3]
        consulta_busqueda = f"{titulo} {artista}"
        resultados_busqueda = ytmusic.search(consulta_busqueda, filter="songs")
        id_video_seleccionado = None
        if resultados_busqueda:
            for result in resultados_busqueda:
                if titulo.lower() in result.get('title', '').lower():
                    id_video_seleccionado = result['videoId']
                    break
            
            if not id_video_seleccionado:
                id_video_seleccionado = resultados_busqueda[0]['videoId']
            try:
                ytmusic.add_playlist_items(id_lista, [id_video_seleccionado])
            except Exception as error:
                if "HTTP 409" in str(error):
                    print(f"Ignorando duplicado: {titulo}")
                else:
                    raise error