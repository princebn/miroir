# Données

Les fichiers de données ne sont pas versionnés (voir .gitignore). Ce dossier
documente où les télécharger et comment reconstituer le pipeline.

## Structure
- `raw/`        données sources brutes, téléchargées (non versionnées)
- `processed/`  données transformées par le pipeline (régénérables)
- `synthetic/`  couche synthétique générée (profils clients, feedback)

## Téléchargement

### 1. Fashion Product Images (~44 000 articles + images)
Version complète (haute résolution) :
https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset
Version légère (~280 Mo, si la complète est trop lourde) :
https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small
Mapping articles -> métadonnées dans styles.csv ; image d'un article via images/<id>.jpg.
À placer dans `data/raw/fashion/`.

### 2. H&M Personalized Fashion Recommendations
https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations/data
Fichiers utilisés : articles.csv, customers.csv, transactions_train.csv
(les images ne sont pas téléchargées, pour économiser l'espace disque).
À placer dans `data/raw/hm/`.

### Téléchargement en ligne de commande (Kaggle CLI)
    pip install kaggle
    # déposer kaggle.json dans ~/.kaggle/ (chmod 600), puis :
    kaggle datasets download -d paramaggarwal/fashion-product-images-dataset -p data/raw/fashion --unzip
    kaggle competitions download -c h-and-m-personalized-fashion-recommendations -p data/raw/hm --unzip
    # (accepter au préalable les règles de la compétition H&M sur le site)

## Notes
- Les prix H&M sont normalisés et ne doivent jamais être affichés comme une devise.
- La couche synthétique (data/synthetic/) est régénérée par les scripts du projet,
  elle n'est pas stockée dans le dépôt.
