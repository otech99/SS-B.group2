import os
import sys
import json
import django
from pathlib import Path
from brownie import accounts, Contract_bn

# --- 1. CONFIGURAZIONE PERCORSI DINAMICI ---
# Risale dal file attuale fino alla radice del progetto SS-B-G2
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# Inizializzazione Django per accedere ai Modelli (CustomUser)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certchain_project.settings')
django.setup()

from certchain.models import CustomUser

# --- 2. FUNZIONI DI SUPPORTO ---

def load_json(filename):
    """Carica i dati JSON dalla cartella data/json usando percorsi dinamici."""
    path = BASE_DIR / 'data' / 'json' / filename
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)

def get_student_data(student_idx, cv_inf, cv_ele, fattore):
    """Recupera evidenze e calcola i dati Bayesiani per uno studente specifico."""
    evidenze_file = load_json(f'Evidenze_s{student_idx}.json')
    cv_file = load_json(f'cv_inserito_s{student_idx}.json')

    if not evidenze_file or not cv_file:
        return None

    cv_scelto = cv_file.get('CV', 1)
    # Selezione del set di probabilità a priori (Informatico o Elettronico)
    source_cv = cv_inf if cv_scelto == 1 else cv_ele

    return {
        'BasiProg': int(source_cv['BasiProg'] * fattore),
        'ProgPy':   int(source_cv['ProgPy']   * fattore),
        'evidenze': evidenze_file['Evidenze'],
    }

# --- 3. LOGICA PRINCIPALE ---

def role_management(ruolo_simulato, studente_target_id):
    # Recupero indirizzo contratto
    addr_file = BASE_DIR / 'blockchain' / 'contract_address.json'
    with open(addr_file) as f:
        addr = json.load(f)["address"]
    contract_bn = Contract_bn.at(addr)

    # Account istituzionali firmati dal backend (.env)
    account_admin    = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))
    account_entecert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_azienda  = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    
    # --- RECUPERO STUDENTI DAL DATABASE ---
    # Prendiamo tutti gli utenti con ruolo STUDENT che hanno collegato MetaMask
    studenti_db = CustomUser.objects.filter(role='STUDENT').exclude(wallet_address__isnull=True)
    studenti_map = {s.student_index: s.wallet_address for s in studenti_db}
    
    if not studenti_map:
        print("Errore: Nessuno studente con wallet trovato nel Database.")
        return

    # Parametri globali Rete Bayesiana
    FATTORE = 1000
    cv_inf = load_json('cv_informatico.json')
    cv_ele = load_json('cv_elettronico.json')
    cpt = load_json('cpt.json')

    # Hash Ruolo (standard OpenZeppelin AccessControl)
    STUDENTE_ROLE_HASH = "0xc0cd2e616535ef39d3e47c23fef2910aa6d6610ec0ef24d4c2909f5fc44601fc"

    # --- AZIONI PER RUOLO ---

    if ruolo_simulato == "Admin":
        print(f"\n[ADMIN] Inizializzazione massiva per {len(studenti_map)} studenti...")

        # Prepariamo le liste per la chiamata in blocco
        list_addresses = []
        list_basi_prog = []
        list_prog_py = []

        IDCERT_cpt   = tuple(int(v * FATTORE) for v in cpt['IDCERT'].values())
        CorsoPy_cpt  = tuple(int(v * FATTORE) for v in cpt['CorsoPy'].values())
        FondInfo_cpt = tuple(int(v * FATTORE) for v in cpt['FondInfo'].values())
        IngSoft_cpt  = tuple(int(v * FATTORE) for v in cpt['IngSoft'].values())

        for s_idx, s_addr in studenti_map.items():
            data = get_student_data(s_idx, cv_inf, cv_ele, FATTORE)
            if data:
                print(f" -> Assegno ruolo Studente a: {s_addr} (s{s_idx})")
                try:
                    # Grant Role lo facciamo uno per volta, va bene
                    contract_bn.grantRole(STUDENTE_ROLE_HASH, s_addr, {"from": account_admin})
                except Exception as e:
                    print(f"    [⚠️] Impossibile assegnare ruolo: {e}")

                # Aggiungiamo i dati alle liste
                list_addresses.append(s_addr)
                list_basi_prog.append(data['BasiProg'])
                list_prog_py.append(data['ProgPy'])

        # ORA FACCIAMO LA CHIAMATA MASSIVA AL CONTRATTO
        print(f"\n -> Caricamento Probabilità a Priori in blocco nella Blockchain...")
        try:
            contract_bn.set_apriorProb(
                list_addresses,
                list_basi_prog,
                list_prog_py,
                IDCERT_cpt,
                CorsoPy_cpt,
                FondInfo_cpt,
                IngSoft_cpt,
                {"from": account_admin}
            )
            print(" [✅] Probabilità inizializzate con successo per tutti gli studenti!")
        except Exception as e:
            print(f" [⏭️] Errore o Probabilità già presenti. Dettaglio: {e}")

        print("\n[ADMIN] Configurazione massiva completata.\n")
    elif ruolo_simulato == "EnteCert":
        target_addr = studenti_map.get(studente_target_id)
        if not target_addr:
            print(f"Errore: Studente {studente_target_id} non trovato.")
            return

        print(f"[ENTECERT] Validazione evidenze per: {target_addr}")
        data = get_student_data(studente_target_id, cv_inf, cv_ele, FATTORE)
        
        # Sequenza di validazione e calcolo
        contract_bn.set_Evidence(target_addr, data['evidenze'], {"from": account_entecert})
        contract_bn.enablePosteriorCalc(target_addr, {"from": account_entecert})
        contract_bn.update_apostProb(target_addr, {"from": account_entecert})
        print(f"[ENTECERT] Calcolo Bayesiano a posteriori completato.")

    elif ruolo_simulato == "Azienda":
        target_addr = studenti_map.get(studente_target_id)
        # ID per recupero variabili specifiche (es. BasiProg)
        ID_aprior = load_json('scelta_aprior_azienda.json')['ID_apriorProb']
        ID_apost  = load_json('scelta_apost_azienda.json')['ID_apostProb']

        res_prior = contract_bn.get_apriorInfoFacts(target_addr, ID_aprior, {"from": account_azienda})
        res_apost = contract_bn.get_apostInfoFacts(target_addr, ID_apost, {"from": account_azienda})

        print(f"\n[AZIENDA] Risultati per Studente {studente_target_id}:")
        print(f" > Probabilità A Priori:   {res_prior / FATTORE}")
        print(f" > Probabilità A Posteriori: {res_apost / FATTORE}")

    else:
        print(f"Ruolo '{ruolo_simulato}' non gestito o non riconosciuto.")

def main(*args):
    # Utilizzo: brownie run scripts/role_management.py main [Ruolo] [ID_Studente]
    ruolo = args[0] if args else "Admin"
    studente_id = int(args[1]) if len(args) > 1 else 1
    
    role_management(ruolo, studente_id)