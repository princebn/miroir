# ADR 0004 — Docker Compose ET Kubernetes

## Statut
Accepte

## Contexte
Besoin d'une boucle dev rapide et d'un deploiement orchestre reproductible.

## Decision
Docker Compose pour le developpement local ; Helm chart Kubernetes pour le deploiement
orchestre (cluster Docker Desktop en local, GKE en cible).

## Consequences
- Dev rapide sans surcout K8s au quotidien.
- Deploiement reproductible et portable (Helm values).
- Services K8s en ClusterIP : pas de conflit de ports avec Compose.
