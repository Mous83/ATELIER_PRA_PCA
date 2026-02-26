------------------------------------------------------------------------------------------------------
ATELIER PRA/PCA
------------------------------------------------------------------------------------------------------
L’idée en 30 secondes : Cet atelier met en œuvre un **mini-PRA** sur **Kubernetes** en déployant une **application Flask** avec une **base SQLite** stockée sur un **volume persistant (PVC pra-data)** et des **sauvegardes automatiques réalisées chaque minute vers un second volume (PVC pra-backup)** via un **CronJob**. L’**image applicative est construite avec Packer** et le **déploiement orchestré avec Ansible**, tandis que Kubernetes assure la gestion des pods et de la disponibilité applicative. Nous observerons la différence entre **disponibilité** (recréation automatique des pods sans perte de données) et **reprise après sinistre** (perte volontaire du volume de données puis restauration depuis les backups), nous mesurerons concrètement les RTO et RPO, et comprendrons les limites d’un PRA local non répliqué. Cet atelier illustre de manière pratique les principes de continuité et de reprise d’activité, ainsi que le rôle respectif des conteneurs, du stockage persistant et des mécanismes de sauvegarde.
  
**Architecture cible :** Ci-dessous, voici l'architecture cible souhaitée.   
  
![Screenshot Actions](Architecture_cible.png)  
  
-------------------------------------------------------------------------------------------------------
Séquence 1 : Codespace de Github
-------------------------------------------------------------------------------------------------------
Objectif : Création d'un Codespace Github  
Difficulté : Très facile (~5 minutes)
-------------------------------------------------------------------------------------------------------
**Faites un Fork de ce projet**. Si besoin, voici une vidéo d'accompagnement pour vous aider à "Forker" un Repository Github : [Forker ce projet](https://youtu.be/p33-7XQ29zQ) 
  
Ensuite depuis l'onglet **[CODE]** de votre nouveau Repository, **ouvrez un Codespace Github**.
  
---------------------------------------------------
Séquence 2 : Création du votre environnement de travail
---------------------------------------------------
Objectif : Créer votre environnement de travail  
Difficulté : Simple (~10 minutes)
---------------------------------------------------
Vous allez dans cette séquence mettre en place un cluster Kubernetes K3d contenant un master et 2 workers, installer les logiciels Packer et Ansible. Depuis le terminal de votre Codespace copier/coller les codes ci-dessous étape par étape :  

**Création du cluster K3d**  
```
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```
```
k3d cluster create pra \
  --servers 1 \
  --agents 2
```
**vérification de la création de votre cluster Kubernetes**  
```
kubectl get nodes
```
**Installation du logiciel Packer (création d'images Docker)**  
```
PACKER_VERSION=1.11.2
curl -fsSL -o /tmp/packer.zip \
  "https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip"
sudo unzip -o /tmp/packer.zip -d /usr/local/bin
rm -f /tmp/packer.zip
```
**Installation du logiciel Ansible**  
```
python3 -m pip install --user ansible kubernetes PyYAML jinja2
export PATH="$HOME/.local/bin:$PATH"
ansible-galaxy collection install kubernetes.core
```
  
---------------------------------------------------
Séquence 3 : Déploiement de l'infrastructure
---------------------------------------------------
Objectif : Déployer l'infrastructure sur le cluster Kubernetes
Difficulté : Facile (~15 minutes)
---------------------------------------------------  
Nous allons à présent déployer notre infrastructure sur Kubernetes. C'est à dire, créér l'image Docker de notre application Flask avec Packer, déposer l'image dans le cluster Kubernetes et enfin déployer l'infratructure avec Ansible (Création du pod, création des PVC et les scripts des sauvegardes aututomatiques).  

**Création de l'image Docker avec Packer**  
```
packer init .
packer build -var "image_tag=1.0" .
docker images | head
```
  
**Import de l'image Docker dans le cluster Kubernetes**  
```
k3d image import pra/flask-sqlite:1.0 -c pra
```
  
**Déploiment de l'infrastructure dans Kubernetes**  
```
ansible-playbook ansible/playbook.yml
```
  
**Forward du port 8080 qui est le port d'exposition de votre application Flask**  
```
kubectl -n pra port-forward svc/flask 8080:80 >/tmp/web.log 2>&1 &
```
  
---------------------------------------------------  
**Réccupération de l'URL de votre application Flask**. Votre application Flask est déployée sur le cluster K3d. Pour obtenir votre URL cliquez sur l'onglet **[PORTS]** dans votre Codespace (à coté de Terminal) et rendez public votre port 8080 (Visibilité du port). Ouvrez l'URL dans votre navigateur et c'est terminé.  

**Les routes** à votre disposition sont les suivantes :  
1. https://...**/** affichera dans votre navigateur "Bonjour tout le monde !".
2. https://...**/health** pour voir l'état de santé de votre application.
3. https://...**/add?message=test** pour ajouter un message dans votre base de données SQLite.
4. https://...**/count** pour afficher le nombre de messages stockés dans votre base de données SQLite.
5. https://...**/consultation** pour afficher les messages stockés dans votre base de données.
  
---------------------------------------------------  
### Processus de sauvegarde de la BDD SQLite

Grâce à une tâche CRON déployée par Ansible sur le cluster Kubernetes (un CronJob), toutes les minutes une sauvegarde de la BDD SQLite est faite depuis le PVC pra-data vers le PCV pra-backup dans Kubernetes.  

Pour visualiser les sauvegardes périodiques déposées dans le PVC pra-backup, coller les commandes suivantes dans votre terminal Codespace :  

```
kubectl -n pra run debug-backup \
  --rm -it \
  --image=alpine \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "debug",
      "image": "alpine",
      "command": ["sh"],
      "stdin": true,
      "tty": true,
      "volumeMounts": [{
        "name": "backup",
        "mountPath": "/backup"
      }]
    }],
    "volumes": [{
      "name": "backup",
      "persistentVolumeClaim": {
        "claimName": "pra-backup"
      }
    }]
  }
}'
```
```
ls -lh /backup
```
**Pour sortir du cluster et revenir dans le terminal**
```
exit
```

---------------------------------------------------
Séquence 4 : 💥 Scénarios de crash possibles  
Difficulté : Facile (~30 minutes)
---------------------------------------------------
### 🎬 **Scénario 1 : PCA — Crash du pod**  
Nous allons dans ce scénario **détruire notre Pod Kubernetes**. Ceci simulera par exemple la supression d'un pod accidentellement, ou un pod qui crash, ou un pod redémarré, etc..

**Destruction du pod :** Ci-dessous, la cible de notre scénario   
  
![Screenshot Actions](scenario1.png)  

Nous perdons donc ici notre application mais pas notre base de données puisque celle-ci est déposée dans le PVC pra-data hors du pod.  

Copier/coller le code suivant dans votre terminal Codespace pour détruire votre pod :
```
kubectl -n pra get pods
```
Notez le nom de votre pod qui est différent pour tout le monde.  
Supprimez votre pod (pensez à remplacer <nom-du-pod-flask> par le nom de votre pod).  
Exemple : kubectl -n pra delete pod flask-7c4fd76955-abcde  
```
kubectl -n pra delete pod <nom-du-pod-flask>
```
**Vérification de la suppression de votre pod**
```
kubectl -n pra get pods
```
👉 **Le pod a été reconstruit sous un autre identifiant**.  
Forward du port 8080 du nouveau service  
```
kubectl -n pra port-forward svc/flask 8080:80 >/tmp/web.log 2>&1 &
```
Observez le résultat en ligne  
https://...**/consultation** -> Vous n'avez perdu aucun message.
  
👉 Kubernetes gère tout seul : Aucun impact sur les données ou sur votre service (PVC conserve la DB et le pod est reconstruit automatiquement) -> **C'est du PCA**. Tout est automatique et il n'y a aucune rupture de service.
  
---------------------------------------------------
### 🎬 **Scénario 2 : PRA - Perte du PVC pra-data** 
Nous allons dans ce scénario **détruire notre PVC pra-data**. C'est à dire nous allons suprimer la base de données en production. Ceci simulera par exemple la corruption de la BDD SQLite, le disque du node perdu, une erreur humaine, etc. 💥 Impact : IL s'agit ici d'un impact important puisque **la BDD est perdue**.  

**Destruction du PVC pra-data :** Ci-dessous, la cible de notre scénario   
  
![Screenshot Actions](scenario2.png)  

🔥 **PHASE 1 — Simuler le sinistre (perte de la BDD de production)**  
Copier/coller le code suivant dans votre terminal Codespace pour détruire votre base de données :
```
kubectl -n pra scale deployment flask --replicas=0
```
```
kubectl -n pra patch cronjob sqlite-backup -p '{"spec":{"suspend":true}}'
```
```
kubectl -n pra delete job --all
```
```
kubectl -n pra delete pvc pra-data
```
👉 Vous pouvez vérifier votre application en ligne, la base de données est détruite et la service n'est plus accéssible.  

✅ **PHASE 2 — Procédure de restauration**  
Recréer l’infrastructure avec un PVC pra-data vide.  
```
kubectl apply -f k8s/
```
Vérification de votre application en ligne.  
Forward du port 8080 du service pour tester l'application en ligne.  
```
kubectl -n pra port-forward svc/flask 8080:80 >/tmp/web.log 2>&1 &
```
https://...**/count** -> =0.  
https://...**/consultation** Vous avez perdu tous vos messages.  

Retaurez votre BDD depuis le PVC Backup.  
```
kubectl apply -f pra/50-job-restore.yaml
```
👉 Vous pouvez vérifier votre application en ligne, **votre base de données a été restaureé** et tous vos messages sont bien présents.  

Relance des CRON de sauvgardes.  
```
kubectl -n pra patch cronjob sqlite-backup -p '{"spec":{"suspend":false}}'
```
👉 Nous n'avons pas perdu de données mais Kubernetes ne gère pas la restauration tout seul. Nous avons du protéger nos données via des sauvegardes régulières (du PVC pra-data vers le PVC pra-backup). -> **C'est du PRA**. Il s'agit d'une stratégie de sauvegarde avec une procédure de restauration.  

---------------------------------------------------
Séquence 5 : Exercices  
Difficulté : Moyenne (~45 minutes)
---------------------------------------------------
**Complétez et documentez ce fichier README.md** pour répondre aux questions des exercices.  
Faites preuve de pédagogie et soyez clair dans vos explications et procedures de travail.  

**Exercice 1 :**  
Quels sont les composants dont la perte entraîne une perte de données ?  
  
Exercice 1 : Quels sont les composants dont la perte entraîne une perte de données ?

Ce serait la perte du volume pra-backup en même temps que le volume de base. Vu qu'on tourne en local avec K3d pour ce TP, nos deux volumes (prod et backup) sont en fait stockés sur le même disque dur physique de la machine. Du coup, si ce disque lâche, on perd la base ET les sauvegardes d'un coup. C'est le crash total.

Exercice 2 : Expliquez-nous pourquoi nous n'avons pas perdu les données lors de la suppression du PVC pra-data.

En fait, on a bel et bien détruit la base de données en production ! Mais on n'a rien perdu définitivement parce qu'il y avait un CronJob qui tournait en tâche de fond. Il faisait une copie du fichier SQLite toutes les minutes sur un autre volume isolé (pra-backup). Du coup, il a suffi de lancer notre petit script de restauration pour reprendre la dernière sauvegarde et la remettre en prod.

Exercice 3 : Quels sont les RTO et RPO de cette solution ?

Pour le RPO (la perte de données max) : C'est 1 minute. Comme le script de backup s'exécute toutes les minutes, si ça plante juste avant la sauvegarde suivante, on perd au maximum les 59 dernières secondes de données.

Pour le RTO (le temps de coupure) : Il n'est pas fixe, car ça dépend du temps de réaction humain. C'est le temps que je mette à me rendre compte que l'appli est down, que je recrée l'infrastructure et que je lance la commande de restauration à la main (je dirais environ 5 minutes).

Exercice 4 : Pourquoi cette solution (cet atelier) ne peut pas être utilisée dans un vrai environnement de production ? Que manque-t-il ?

Déjà, tout est sur le même disque physique, c'est trop risqué (SPOF). Ensuite, SQLite c'est pas vraiment fait pour une grosse prod. Surtout, il manque des alertes : si le backup plante pendant la nuit, on n'est pas prévenu. Et en cas de pépin, on doit tout restaurer à la ligne de commande manuellement, ce qui n'est pas hyper rassurant en condition de stress.

Exercice 5 : Proposez une architecture plus robuste.

Pour faire un truc vraiment propre pour la prod, je remplacerais SQLite par une vraie base de données managée (genre Cloud SQL ou AWS RDS) avec réplication sur plusieurs datacenters. Pour les sauvegardes, au lieu de les garder sur un PVC local, je les enverrais direct sur un stockage externe comme un bucket S3. Et bien sûr, j'utiliserais un cluster Kubernetes réparti sur plusieurs nœuds physiques.

**Exercice 2 :**  
Expliquez nous pourquoi nous n'avons pas perdu les données lors de la supression du PVC pra-data  
  
En fait, on a bel et bien détruit la base de données en production ! Mais on n'a rien perdu définitivement parce qu'il y avait un CronJob qui tournait en tâche de fond. Il faisait une copie du fichier SQLite toutes les minutes sur un autre volume isolé (pra-backup). Du coup, il a suffi de lancer notre petit script de restauration pour reprendre la dernière sauvegarde et la remettre en prod.

**Exercice 3 :**  
Quels sont les RTO et RPO de cette solution ?  
  
-Pour le RPO (la perte de données max) : C'est 1 minute. Comme le script de backup s'exécute toutes les minutes, si ça plante juste avant la sauvegarde suivante, on perd au maximum les 59 dernières secondes de données.

-Pour le RTO (le temps de coupure) : Il n'est pas fixe, car ça dépend du temps de réaction humain. C'est le temps que je mette à me rendre compte que l'appli est down, que je recrée l'infrastructure et que je lance la commande de restauration à la main (je dirais environ 5 minutes).

**Exercice 4 :**  
Pourquoi cette solution (cet atelier) ne peux pas être utilisé dans un vrai environnement de production ? Que manque-t-il ?   
  
Déjà, tout est sur le même disque physique, c'est trop risqué (SPOF). Ensuite, SQLite c'est pas vraiment fait pour une grosse prod. Surtout, il manque des alertes : si le backup plante pendant la nuit, on n'est pas prévenu. Et en cas de pépin, on doit tout restaurer à la ligne de commande manuellement, ce qui n'est pas hyper rassurant en condition de stress.
  
**Exercice 5 :**  
Proposez une archtecture plus robuste.   
  
Pour faire un truc vraiment propre pour la prod, je remplacerais SQLite par une vraie base de données managée (genre Cloud SQL ou AWS RDS) avec réplication sur plusieurs datacenters. Pour les sauvegardes, au lieu de les garder sur un PVC local, je les enverrais direct sur un stockage externe comme un bucket S3. Et bien sûr, j'utiliserais un cluster Kubernetes réparti sur plusieurs nœuds physiques.

---------------------------------------------------
Séquence 6 : Ateliers  
Difficulté : Moyenne (~2 heures)
---------------------------------------------------
### **Atelier 1 : Ajoutez une fonctionnalité à votre application**  
**Ajouter une route GET /status** dans votre application qui affiche en JSON :
* count : nombre d’événements en base
* last_backup_file : nom du dernier backup présent dans /backup
* backup_age_seconds : âge du dernier backup

*![alt text](image.png)
---------------------------------------------------
### **Atelier 2 : Choisir notre point de restauration**  
Aujourd’hui nous restaurobs “le dernier backup”. Nous souhaitons **ajouter la capacité de choisir un point de restauration**.

Ma procédure de restauration ciblée (Runbook) :

Si la dernière sauvegarde est elle aussi corrompue et que je dois remonter plus loin dans le temps, voici les étapes que j'applique :

1. Lister les sauvegardes disponibles :
Je lance un pod de debug temporaire pour aller fouiller dans le volume pra-backup et voir la liste des fichiers :

```
kubectl -n pra run debug-backup --rm -it --image=alpine --overrides='{"spec": {"containers": [{"name": "debug","image": "alpine","command": ["sh"],"stdin": true,"tty": true,"volumeMounts": [{"name": "backup","mountPath": "/backup"}]}],"volumes": [{"name": "backup","persistentVolumeClaim": {"claimName": "pra-backup"}}]}}'

```
Une fois dans le pod, je tape ls -lh /backup pour voir les dates et je choisis le fichier qui m'intéresse (ex: app-1772112961.db). Je tape exit pour sortir.

2. Modifier le Job de restauration :
J'ouvre le fichier pra/50-job-restore.yaml dans mon éditeur.
Je modifie la ligne de la commande cp (copie) pour remplacer la sélection automatique par le nom de mon fichier exact :

```
command: ["/bin/sh", "-c"]
args: ["cp /backup/app-1772112961.db /data/app.db"]

```

3. Lancer la restauration :
J'applique mon fichier YAML modifié pour déclencher le remplacement de la base de données de production par mon fichier spécifique :

```

kubectl apply -f pra/50-job-restore.yaml

```

4. Vérification :
Je retourne sur mon application en ligne (sur la route /consultation) pour vérifier que l'état de mes données correspond bien au moment ciblé.

---------------------------------------------------
Evaluation
---------------------------------------------------
Cet atelier PRA PCA, **noté sur 20 points**, est évalué sur la base du barème suivant :  
- Série d'exerices (5 points)
- Atelier N°1 - Ajout d'un fonctionnalité (4 points)
- Atelier N°2 - Choisir son point de restauration (4 points)
- Qualité du Readme (lisibilité, erreur, ...) (3 points)
- Processus travail (quantité de commits, cohérence globale, interventions externes, ...) (4 points) 

