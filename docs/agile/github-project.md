# GitHub Project — Configuration

## Source de vérité

- **Backlog :** GitHub Issues.
- **Planification et suivi :** GitHub Projects.
- **Code :** branches et Pull Requests.
- **Décisions et documentation :** `docs/` versionné dans Git.

## Project fields

| Field | Type | Values / purpose |
|---|---|---|
| Status | Single select | BACKLOG, READY, IN PROGRESS, REVIEW, VALIDATED |
| Priority | Single select | P0 Critical, P1 High, P2 Medium, P3 Low |
| Type | Single select | User Story, Technical Task, Bug, Documentation, Test |
| Area | Single select | Patient, Séjour, Prescription, Agenda, Care, Staff, Integration, Testing |
| Estimate | Number | Story points: 1, 2, 3, 5, 8, 13 |
| Iteration | Iteration | Sprint 1, Sprint 2, ... |
| Milestone | Built-in | Release target, e.g. v0.1 |

## Views

### 1. Kanban — Daily Flow

Group by `Status`.

### 2. Product Backlog

Table containing at least: Title, Type, Priority, Area, Estimate, Iteration, Milestone, Assignee, Status.

### 3. Current Sprint

Filter on the current `Iteration`.

### 4. Roadmap / Releases

Use `Iteration` and `Milestone` to show the planned increments.

## Workflow

```text
BACKLOG -> READY -> IN PROGRESS -> REVIEW -> VALIDATED
```

- **BACKLOG** : idée ou travail non engagé.
- **READY** : raffiné et prêt pour une Sprint.
- **IN PROGRESS** : en cours de développement.
- **REVIEW** : PR ouverte, revue et tests en cours.
- **VALIDATED** : critères d'acceptation satisfaits et validation fonctionnelle effectuée.

## Sprint workflow

1. Refinement : rendre les Issues Ready et les estimer.
2. Sprint Planning : sélectionner les Issues et définir le Sprint Goal.
3. Développement : déplacer les Issues dans le flux et ouvrir des PRs.
4. Sprint Review : démontrer le produit et recueillir la validation.
5. Rétrospective : identifier des améliorations concrètes.
6. Release : documenter l'increment livré dans `docs/releases/`.

## Automation

Activer l'ajout automatique des nouvelles Issues au Project si souhaité. Les workflows intégrés du Project peuvent également synchroniser certains changements de statut avec la fermeture des Issues et la fusion des PRs ; garder néanmoins la règle fonctionnelle `VALIDATED` comme une validation humaine, pas comme une simple fermeture automatique.
