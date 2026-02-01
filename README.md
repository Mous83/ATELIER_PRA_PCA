------------------------------------------------------------------------------------------------------
ATELIER API-DRIVEN INFRASTRUCTURE
------------------------------------------------------------------------------------------------------
L’idée en 30 secondes : **Orchestration de services AWS via API Gateway et Lambda dans un environnement émulé**.  
Cet atelier propose de concevoir une architecture **API-driven** dans laquelle une requête HTTP déclenche, via **API Gateway** et une **fonction Lambda**, des actions d’infrastructure sur des **instances EC2**, le tout dans un **environnement AWS simulé avec LocalStack** et exécuté dans **GitHub Codespaces**. L’objectif est de comprendre comment des services cloud serverless peuvent piloter dynamiquement des ressources d’infrastructure, indépendamment de toute console graphique.Cet atelier propose de concevoir une architecture API-driven dans laquelle une requête HTTP déclenche, via API Gateway et une fonction Lambda, des actions d’infrastructure sur des instances EC2, le tout dans un environnement AWS simulé avec LocalStack et exécuté dans GitHub Codespaces. L’objectif est de comprendre comment des services cloud serverless peuvent piloter dynamiquement des ressources d’infrastructure, indépendamment de toute console graphique.
  
-------------------------------------------------------------------------------------------------------
Séquence 1 : Codespace de Github
-------------------------------------------------------------------------------------------------------
Objectif : Création d'un Codespace Github  
Difficulté : Très facile (~5 minutes)
-------------------------------------------------------------------------------------------------------
RDV sur Codespace de Github : <a href="https://github.com/features/codespaces" target="_blank">Codespace</a> **(click droit ouvrir dans un nouvel onglet)** puis créer un nouveau Codespace qui sera connecté à votre Repository API-Driven.
  
---------------------------------------------------
Séquence 2 : Création de votre serveur de Streaming
---------------------------------------------------
Objectif : Créer un serveur Web utilisant Dash.js  
Difficulté : Simple (~10 minutes)
---------------------------------------------------

Dans votre instance du laboratoire copier/coller les codes ci-dessous etape par étape :  

**Installation de l'environnement**  
```
git clone https://github.com/bstocker/Streaming_Adaptatif.git
cd Streaming_Adaptatif
mkdir -p site/media nginx
apk add nano ffmpeg
```
**Création du manisfest et des fichiers .m4s**  
```
ffmpeg -i Sample.mp4 -map 0 -b:v 1M -s:v:0 1280x720 -c:v libx264 -c:a aac -f dash manifest.mpd
```
**On déplace le manisfest et les fichiers .m4s dans le répertoire media** 
```
mv manifest.mpd *.m4s site/media
```
**Création de votre index.html** 
```
nano site/index.html
```
```
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>DASH Player (dash.js)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body{font-family:system-ui,Arial,sans-serif;max-width:900px;margin:2rem auto;padding:1rem}
    video{width:100%;max-height:70vh;background:#000}
    code{background:#f3f3f3;padding:.1rem .3rem;border-radius:4px}
    .log{font:12px/1.4 ui-monospace,Consolas,monospace;white-space:pre-wrap;background:#fafafa;border:1px solid #eee;padding:.75rem;border-radius:8px}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/dashjs@4/dist/dash.all.min.js"></script>
</head>
<body>
  <h1>DASH Player</h1>
  <p>Par défaut, la page charge <code>/media/manifest.mpd</code>.<br>
     Vous pouvez aussi passer une URL via <code>?src=...</code></p>

  <video id="video" controls></video>

  <div class="log" id="log"></div>

  <script>
    const params = new URLSearchParams(location.search);
    const src = params.get('src') || '/media/manifest.mpd';
    const v = document.getElementById('video');
    const log = (m)=>document.getElementById('log').textContent += m + "\n";

    const player = dashjs.MediaPlayer().create();
    player.updateSettings({ 'debug': { 'logLevel': dashjs.Debug.LOG_LEVEL_INFO }});
    player.on(dashjs.MediaPlayer.events.ERROR, e => log('ERROR: ' + JSON.stringify(e)));
    player.on(dashjs.MediaPlayer.events.PLAYBACK_STARTED, ()=>log('PLAYBACK_STARTED'));
    player.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, ()=>log('STREAM_INITIALIZED'));
    player.on(dashjs.MediaPlayer.events.BUFFER_LEVEL_UPDATED, e=>log('BUFFER: ' + e.mediaType + ' ' + e.bufferLevel.toFixed(2) + 's'));

    log('Loading: ' + src);
    player.initialize(v, src, true);
  </script>
</body>
</html>
```
Ctrl+s  
Ctrl+x  
**Création de votre configuration Nginx** 
```
nano nginx/default.conf
```
```
server {
  listen 80;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  # Table MIME standard (text/html, css, js, mp4, etc.)
  include /etc/nginx/mime.types;

  # Page web
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Médias DASH sous /media/
  location /media/ {
    # Types spécifiques DASH (on n'altère pas la table globale)
    types {
      application/dash+xml mpd;
      video/iso.segment m4s;
    }

    # CORS utiles pour tests (VR / mobile / autre origine)
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Range, Origin, Accept, Content-Type";
    add_header Access-Control-Expose-Headers "Content-Length, Content-Range";
    add_header Accept-Ranges bytes;

    # autoindex on;   # <- décommente pour lister les fichiers (debug)
    try_files $uri =404;
  }
}
```
Ctrl+s  
Ctrl+x  
**Création de votre configuration Nginx** 
```
nano nginx/default.conf
```
```
server {
  listen 80;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  # Table MIME standard (text/html, css, js, mp4, etc.)
  include /etc/nginx/mime.types;

  # Page web
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Médias DASH sous /media/
  location /media/ {
    # Types spécifiques DASH (on n'altère pas la table globale)
    types {
      application/dash+xml mpd;
      video/iso.segment m4s;
    }

    # CORS utiles pour tests (VR / mobile / autre origine)
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, OPTIONS";
    add_header Access-Control-Allow-Headers "Range, Origin, Accept, Content-Type";
    add_header Access-Control-Expose-Headers "Content-Length, Content-Range";
    add_header Accept-Ranges bytes;

    # autoindex on;   # <- décommente pour lister les fichiers (debug)
    try_files $uri =404;
  }
}
```
Ctrl+s  
Ctrl+x  
**Création du docker-compose** 
```
nano docker-compose.yml
```
```
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      # Un seul montage pour le site (inclut le dossier media)
      - ./site:/usr/share/nginx/html:ro
      # On monte un REPERTOIRE de conf => plus robuste
      - ./nginx:/etc/nginx/conf.d:ro
    restart: unless-stopped
```
Ctrl+s  
Ctrl+x

**Lancement du serveur Web**   
```
docker compose up -d
```
  
**Votre serveur de Streaming est prêt**  
Cliquez sur le Bouton **[OPEN PORT]** de votre instance du laboratoire puis tappez **8080**  
C'est terminé !
  
---------------------------------------------------
Capitalisation
---------------------------------------------------
Vous avez apris au travers de cet atelier comment créer un serveur Web pour la diffusion de vidéo en streaming adaptatif.
