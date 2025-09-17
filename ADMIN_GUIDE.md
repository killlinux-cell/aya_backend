# 🎛️ Guide d'Administration Django - AYA+

## 📋 Vue d'ensemble

L'interface d'administration Django permet de gérer tous les aspects de l'application AYA+ :
- **Utilisateurs** : Clients et vendeurs
- **Vendeurs** : Gestion des partenaires commerciaux
- **Échanges** : Suivi des transactions
- **QR Codes** : Gestion des codes de points
- **Jeux** : Historique des parties

## 🚀 Démarrage rapide

### 1. Créer les utilisateurs de test
```bash
cd aya_backend
python create_admin_and_vendors.py
```

### 2. Démarrer le serveur admin
```bash
python start_admin_server.py
```

### 3. Accéder à l'admin
- **URL** : http://localhost:8000/admin/
- **Admin** : admin@aya.com / admin123

## 👥 Gestion des Vendeurs

### Interface Vendeurs
- **Liste** : Nom, code, email, statut, ville, pays
- **Filtres** : Statut, pays, ville, date de création
- **Recherche** : Nom, code, email, téléphone, ville
- **Actions** : Activer, désactiver, suspendre en masse

### Champs disponibles
- **Informations générales** : Utilisateur, code vendeur, nom entreprise, statut
- **Contact** : Téléphone, adresse
- **Localisation** : GPS, ville, région, pays
- **Métadonnées** : Créateur, dates

### Actions disponibles
- ✅ **Activer** : Mettre le statut à "actif"
- ❌ **Désactiver** : Mettre le statut à "inactif"
- ⚠️ **Suspendre** : Mettre le statut à "suspendu"

## 💰 Gestion des Échanges

### Interface Échanges
- **Liste** : Email client, points, code, statut, vendeur, dates
- **Filtres** : Statut, vendeur, dates
- **Recherche** : Email client, code, vendeur
- **Actions** : Approuver, rejeter en masse

### Statuts des échanges
- 🔄 **En attente** : En cours de validation
- ✅ **Complété** : Validé par le vendeur
- ❌ **Rejeté** : Refusé par le vendeur

### Actions disponibles
- ✅ **Approuver** : Valider les échanges sélectionnés
- ❌ **Rejeter** : Refuser les échanges sélectionnés

## 👤 Gestion des Utilisateurs

### Interface Utilisateurs
- **Liste** : Email, nom, points, statut, date d'inscription
- **Filtres** : Statut, date d'inscription
- **Recherche** : Email, nom, prénom

### Champs disponibles
- **Informations personnelles** : Email, nom, prénom
- **Points et QR Code** : Points disponibles, échangés, codes collectés
- **Permissions** : Statut actif, staff, superuser
- **Dates** : Dernière connexion, inscription

## 🎯 Utilisateurs de test créés

### Administrateur
- **Email** : admin@aya.com
- **Mot de passe** : admin123
- **Rôle** : Superutilisateur

### Vendeurs (5)
- **vendeur1@aya.com** : Restaurant Le Bon Goût (Abidjan)
- **vendeur2@aya.com** : Boutique Mode & Style (Yamoussoukro)
- **vendeur3@aya.com** : Super Marché Central (Bouaké)
- **vendeur4@aya.com** : Pharmacie du Centre (Abidjan)
- **vendeur5@aya.com** : Station Service Total (Abidjan)
- **Mot de passe** : vendeur123

### Clients (3)
- **client1@aya.com** : Alice Martin (150 points)
- **client2@aya.com** : Bob Johnson (75 points)
- **client3@aya.com** : Charlie Brown (200 points)
- **Mot de passe** : client123

## 🔧 Fonctionnalités avancées

### Filtres et recherche
- **Filtres multiples** : Combiner plusieurs critères
- **Recherche globale** : Rechercher dans tous les champs
- **Tri** : Cliquer sur les en-têtes de colonnes

### Actions en masse
- **Sélection multiple** : Cocher plusieurs éléments
- **Actions groupées** : Appliquer une action à tous les éléments sélectionnés
- **Confirmation** : Confirmer avant d'exécuter

### Export et import
- **Export CSV** : Exporter les données
- **Import** : Importer des données en masse
- **Format** : Compatible avec Excel

## 📊 Tableaux de bord

### Statistiques générales
- **Nombre total d'utilisateurs**
- **Nombre de vendeurs actifs**
- **Échanges du jour/mois**
- **Points distribués**

### Rapports
- **Rapport des vendeurs** : Performance par vendeur
- **Rapport des échanges** : Statistiques des transactions
- **Rapport des utilisateurs** : Activité des clients

## 🛡️ Sécurité

### Permissions
- **Superutilisateur** : Accès complet
- **Staff** : Accès limité selon les permissions
- **Utilisateur** : Accès à son profil uniquement

### Audit
- **Logs d'actions** : Traçabilité des modifications
- **Historique** : Suivi des changements
- **Sauvegarde** : Sauvegarde automatique des données

## 🚨 Dépannage

### Problèmes courants
1. **Erreur de connexion** : Vérifier les identifiants
2. **Permissions insuffisantes** : Contacter l'administrateur
3. **Données manquantes** : Exécuter les migrations

### Support
- **Logs** : Consulter les logs Django
- **Documentation** : Documentation Django officielle
- **Communauté** : Forum Django

## 📱 Intégration Mobile

### API REST
- **Endpoints** : Tous les modèles exposés via API
- **Authentification** : JWT tokens
- **Documentation** : Swagger/OpenAPI

### Synchronisation
- **Temps réel** : Mise à jour automatique
- **Offline** : Synchronisation différée
- **Conflits** : Résolution automatique

---

## 🎉 Félicitations !

Vous avez maintenant accès à une interface d'administration complète pour gérer votre application AYA+. 

**Prochaines étapes :**
1. Explorer les différentes sections
2. Créer vos propres vendeurs
3. Configurer les permissions
4. Personnaliser l'interface selon vos besoins

**Bonne gestion !** 🚀
