# Guide de Test du Système de Conversations

Ce document explique comment tester le nouveau système de gestion des conversations.

## Nouveautés

Le système inclut maintenant :
- **Génération automatique d'un `conversation_id`** lors du premier message
- **Persistance de l'historique** de la conversation
- **Contexte conservé** entre les messages

## Endpoints Disponibles

### 1. `/api/chat` (POST)
Envoyer un message dans une conversation.

**Premier message (nouvelle conversation) :**
```json
{
  "message": "مرحبا، أريد معرفة حالة خدمتي"
}
```

**Messages suivants (conversation existante) :**
```json
{
  "message": "رقم CIL الخاص بي هو: 1071324-101",
  "conversation_id": "uuid-from-first-response"
}
```

**Réponse :**
```json
{
  "response": "مرحبا بك...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_new_conversation": true,
  "status": "success"
}
```

### 2. `/api/chat/history/<conversation_id>` (GET)
Récupérer l'historique d'une conversation.

**Réponse :**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-12-04T10:30:00",
  "messages": [
    {
      "role": "user",
      "content": "مرحبا",
      "timestamp": "2024-12-04T10:30:00"
    },
    {
      "role": "assistant",
      "content": "مرحبا بك...",
      "timestamp": "2024-12-04T10:30:05"
    }
  ],
  "message_count": 2,
  "status": "success"
}
```

## Tests via cURL

### Test 1 : Créer une nouvelle conversation
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_conversation_new.json"
```

### Test 2 : Continuer la conversation
1. Copier le `conversation_id` de la réponse précédente
2. Remplacer `REPLACE_WITH_ACTUAL_CONVERSATION_ID` dans `test_conversation_continue.json`
3. Exécuter :
```powershell
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "@test_conversation_continue.json"
```

### Test 3 : Récupérer l'historique
```powershell
curl http://localhost:5000/api/chat/history/CONVERSATION_ID_HERE
```

## Exemple de Flux Complet

```powershell
# 1. Premier message (création de conversation)
$response1 = curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d '{"message": "مرحبا"}' | ConvertFrom-Json

$convId = $response1.conversation_id
Write-Host "Conversation ID: $convId"

# 2. Deuxième message (avec CIL)
curl -X POST http://localhost:5000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"message\": \"رقم CIL الخاص بي هو: 1071324-101\", \"conversation_id\": \"$convId\"}"

# 3. Récupérer l'historique
curl http://localhost:5000/api/chat/history/$convId
```

## Validation

✅ Le premier message génère un nouveau `conversation_id`
✅ Les messages suivants utilisent le même `conversation_id`
✅ L'historique est accessible via l'endpoint `/history`
✅ Chaque message est horodaté
✅ Le contexte est conservé entre les messages
