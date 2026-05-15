# 🎓 CertChain: Sistema di Certificazione Decentralizzata Ibrido

CertChain è un Proof of Concept (PoC) per la gestione, l'emissione e la verifica di certificati digitali. Il progetto implementa un'architettura **Defense in Depth** che combina la robustezza del Web2 (Django) con l'immutabilità del Web3 (Ethereum/Solidity) per garantire l'integrità dei dati e la non ripudiabilità delle certificazioni.

---

## 🏗 Architettura di Sistema (4 Layer)

Il sistema è stato progettato seguendo il principio della separazione delle responsabilità:

1.  **Client Layer:** Interfaccia utente e firma crittografica delle transazioni tramite **MetaMask**.
2.  **Backend Layer:** Logica applicativa, gestione API REST (**Django**), RBAC off-chain e motore di inferenza.
3.  **Smart Contract Layer:** Logica decentralizzata, enforcement dei ruoli tramite **OpenZeppelin** e registro immutabile.
4.  **Infrastructure Layer:** Ambiente isolato e containerizzato tramite **Docker** che ospita il nodo **Ganache** e i servizi backend.

---

## 🛡️ Caratteristiche di Sicurezza
* **RBAC Dual-Layer:** Controllo degli accessi implementato sia a livello di viste Django (Off-Chain) che a livello di Smart Contract (On-Chain).
* **Firma Asimmetrica:** Le transazioni critiche sono firmate localmente dall'utente tramite chiave privata, senza mai esporre le credenziali al server.
* **Isolamento Runtime:** L'intera infrastruttura è segregata in container Docker per limitare la superficie di attacco.
* **Fail-Safe Defaults:** Ogni rotta non riconosciuta o tentativo di escalation viene reindirizzato automaticamente verso risorse sicure.

---

## 📋 Prerequisiti

Prima di iniziare, assicurati di avere installato:
* [Docker](https://www.docker.com/products/docker-desktop/) e Docker Compose.
* L'estensione [MetaMask](https://metamask.io/) nel tuo browser.
* **Ganache** (Se non utilizzi la versione containerizzata nel docker-compose). port 8546

---

## 🚀 Installazione e Avvio

Segui questi passaggi per configurare l'ambiente di test:

### 1. Clonazione del Repository
```bash
git clone <url-del-tuo-repository>
cd <nome-cartella-progetto>

## Creazione file .env
cp .env.example .env

##Avvio dell'Infrastruttura Docker
docker-compose up --build