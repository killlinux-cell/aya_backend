# 📺 Système de Publicités Vidéo - Aya+

## Vue d'Ensemble

Système complet de gestion des publicités vidéo permettant d'uploader, gérer et diffuser des vidéos publicitaires depuis le dashboard Django vers l'application mobile Flutter.

## 🏗️ Architecture

### Backend Django

#### Modèle (`dashboard/models_ads.py`)
- **VideoAdvertisement** : Gestion des vidéos publicitaires
  - Titre, description
  - Fichier vidéo + miniature
  - Durée d'affichage, priorité
  - Statut (active/inactive/programmée)
  - Planification (dates de début/fin)
  - Statistiques (compteur de vues)

#### API (`dashboard/views_ads.py`)
- `GET /api/advertisements/active/` - Récupérer les publicités actives
- `POST /api/advertisements/{id}/view/` - Incrémenter les vues

#### Dashboard (`dashboard/templates/dashboard/advertisements.html`)
- Interface de gestion complète
- Upload de vidéos
- Activation/désactivation
- Statistiques de vues

### Frontend Flutter

#### Service (`lib/services/advertisement_service.dart`)
- Récupération des publicités actives depuis l'API
- Incrémentation des compteurs de vues
- Modèle `Advertisement` pour les données

#### Widget (`lib/widgets/api_video_widget.dart`)
- Affichage des vidéos en rotation
- Sélection aléatoire pondérée par priorité
- Lecture automatique en boucle
- Changement automatique selon durée configurée

## 🚀 Utilisation

### 1. Dashboard - Ajouter une Vidéo

1. Connectez-vous au dashboard : `http://localhost:8000/dashboard/`
2. Allez sur "Publicités Vidéo" (ou `/dashboard/advertisements/`)
3. Cliquez sur "Ajouter une Vidéo Publicitaire"
4. Remplissez le formulaire :
   - Titre
   - Description (optionnel)
   - Fichier vidéo MP4 (max 50MB)
   - Miniature (optionnel)
   - Durée d'affichage (secondes)
   - Priorité (0-10)
   - Statut (Active/Inactive)
5. Enregistrez

### 2. Application Mobile

Les vidéos s'affichent automatiquement :
- **Position** : En bas de la page d'accueil
- **Lecture** : Automatique, en boucle, muette
- **Rotation** : Change automatiquement selon la durée configurée
- **Sélection** : Aléatoire avec poids de priorité

## ⚙️ Configuration

### Priorité des Vidéos

Le système utilise un algorithme de sélection pondérée :
- **Priorité 0** : Chance normale
- **Priorité 5** : 5x plus de chances d'être affichée
- **Priorité 10** : 10x plus de chances

### Durée d'Affichage

- **Recommandé** : 5-10 secondes
- **Minimum** : 1 seconde
- **Maximum** : 30 secondes

### Formats Acceptés

- **Vidéo** : MP4
- **Taille max** : 50MB
- **Résolution recommandée** : 1080p ou moins
- **Miniature** : JPG, PNG

## 📊 Statistiques

Le dashboard affiche :
- Total de publicités
- Publicités actives/inactives
- Total de vues
- Vues par publicité

## 🔧 API Endpoints

### Récupérer les publicités actives
```
GET /api/advertisements/active/
Response: {
  "count": 5,
  "advertisements": [
    {
      "id": "uuid",
      "title": "Pub Aya Huile",
      "description": "...",
      "video_url": "http://...",
      "thumbnail_url": "http://...",
      "duration": 5,
      "priority": 10,
      "status": "active"
    }
  ]
}
```

### Incrémenter les vues
```
POST /api/advertisements/{ad_id}/view/
Response: {
  "success": true,
  "views": 156
}
```

## 📁 Structure des Fichiers

```
aya_backend/
├── dashboard/
│   ├── models_ads.py              # Modèle VideoAdvertisement
│   ├── serializers_ads.py         # Serializer API
│   ├── views_ads.py               # Vues dashboard + API
│   ├── urls_api.py                # Routes API
│   └── templates/dashboard/
│       ├── advertisements.html     # Liste des pubs
│       └── create_advertisement.html  # Formulaire upload

lib/
├── services/
│   └── advertisement_service.dart  # Service API
└── widgets/
    └── api_video_widget.dart       # Widget affichage
```

## ✅ Avantages

1. **Gestion centralisée** : Tout depuis le dashboard
2. **Pas de recompilation** : Changez les vidéos sans rebuild l'app
3. **Statistiques** : Suivez les performances
4. **Planification** : Programmez les dates de diffusion
5. **Priorité** : Contrôlez la fréquence d'affichage
6. **Professionnel** : Système de niveau entreprise

## 🎯 Prochaines Étapes

1. Accédez au dashboard
2. Uploadez vos 10 vidéos MP4
3. Configurez priorité et durée
4. Activez les publicités
5. L'app mobile les affichera automatiquement !

