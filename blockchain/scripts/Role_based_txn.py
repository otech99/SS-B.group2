from brownie import accounts, Contract_bn 
from eth_utils import keccak
import json
import os

def load_json(filename):
    # Carica i dati dai file JSON nella cartella data/json
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'json', filename)
    with open(path, 'r') as f:
        return json.load(f)

def role_management(ruolo_simulato, studente_target_id):
    # Recupero indirizzo contratto dal file generato dal deploy
    with open("contract_address.json") as f:
        addr = json.load(f)["address"]
    contract_bn = Contract_bn.at(addr)

    # Caricamento dei vari Account dal .env tranne quello degli studenti
    account_Admin    = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))
    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda  = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    
    # Lista studenti autorizzati (mettere quelli creati nel .env)
    studenti = {
        1: accounts.add(os.environ.get("PRIVATE_KEY_Studente")),
        2: accounts.add(os.environ.get("PRIVATE_KEY_Studente2")),
        3: accounts.add(os.environ.get("PRIVATE_KEY_Studente3")),
        #4: accounts.add(os.environ.get("PRIVATE_KEY_Studente4")),
        #5: accounts.add(os.environ.get("PRIVATE_KEY_Studente5")),
        #6: accounts.add(os.environ.get("PRIVATE_KEY_Studente6")),
        #7: accounts.add(os.environ.get("PRIVATE_KEY_Studente7"))

    }
    
    target_student_account = studenti[studente_target_id]

    # Preparazione dati Bayesiani 
    Fattore = 1000
    #-----------------------------------------------------------------
    #Controllare se le probabilità inserite non sforano il range [0,1]
    #-----------------------------------------------------------------

    cv_inf   = load_json('cv_informatico.json')
    cv_ele = load_json('cv_elettronico.json')
    cpt      = load_json('cpt.json')
    evidenze_s1 = load_json('Evidenze_s1.json')['Evidenze']
    evidenze_s2 = load_json('Evidenze_s2.json')['Evidenze']
    evidenze_s3 = load_json('Evidenze_s3.json')['Evidenze']
    cv_s1   = load_json('cv_inserito_s1.json')['CV']
    cv_s2   = load_json('cv_inserito_s2.json')['CV']
    cv_s3   = load_json('cv_inserito_s3.json')['CV']
    ID_apriorProb = load_json('scelta_aprior_azienda.json')['ID_apriorProb']
    ID_apostProb = load_json('scelta_apost_azienda.json')['ID_apostProb']


    def check_prob(v):
        if not (0 <= v <= 1000):
            raise ValueError(f"Valore non valido: {v}")
        return v

    dati_studenti = {
        1: {
            'BasiProg': check_prob(int(cv_inf['BasiProg'] * Fattore)) if cv_s1 == 1 else check_prob(int(cv_ele['BasiProg'] * Fattore)),
            'ProgPy':   check_prob(int(cv_inf['ProgPy']   * Fattore)) if cv_s1 == 1 else check_prob(int(cv_ele['ProgPy']   * Fattore)),
            'evidenze': evidenze_s1,
        },
        2: {
            'BasiProg': check_prob(int(cv_inf['BasiProg'] * Fattore)) if cv_s2 == 1 else check_prob(int(cv_ele['BasiProg'] * Fattore)),
            'ProgPy':   check_prob(int(cv_inf['ProgPy']   * Fattore)) if cv_s2 == 1 else check_prob(int(cv_ele['ProgPy']   * Fattore)),
            'evidenze': evidenze_s2,
        },

        3: {
            'BasiProg': check_prob(int(cv_inf['BasiProg'] * Fattore)) if cv_s3 == 1 else check_prob(int(cv_ele['BasiProg'] * Fattore)),
            'ProgPy':   check_prob(int(cv_inf['ProgPy']   * Fattore)) if cv_s3 == 1 else check_prob(int(cv_ele['ProgPy']   * Fattore)),
            'evidenze': evidenze_s3,
        },
    }

    IDCERTprob_struct   = tuple(check_prob(int(v * Fattore)) for v in cpt['IDCERT'].values())
    CorsoPyprob_struct  = tuple(check_prob(int(v * Fattore)) for v in cpt['CorsoPy'].values())
    FondInfoprob_struct = tuple(check_prob(int(v * Fattore)) for v in cpt['FondInfo'].values())
    IngSoftprob_struct  = tuple(check_prob(int(v * Fattore)) for v in cpt['IngSoft'].values())

    # Gestione Ruoli tramite Hash 
    hash_ruolo = keccak(ruolo_simulato.encode('utf-8'))
    STUDENTE_ROLE_HASH = "0xc0cd2e616535ef39d3e47c23fef2910aa6d6610ec0ef24d4c2909f5fc44601fc"

    if ruolo_simulato == "Admin":
        print(f"[Admin] Generazione dell'autorizzazione per gli studenti in corso...")
        for s_id, s_acc in studenti.items():
            print(f"Abilitazione accesso per Studente {s_id}: {s_acc.address}")
            contract_bn.grantRole(STUDENTE_ROLE_HASH, s_acc.address, {"from": account_Admin})

        # Array paralleli con tutti gli studenti e i loro prior
        # Costruiti indipendentemente da studente_target_id
        students_addresses = [studenti[s_id].address for s_id in sorted(studenti)]
        basi_prog_values   = [dati_studenti[s_id]['BasiProg'] for s_id in sorted(studenti)]
        prog_py_values     = [dati_studenti[s_id]['ProgPy']   for s_id in sorted(studenti)]

        print(f"[Admin] Inizializzazione CPT e prior per tutti gli studenti...")
        contract_bn.set_apriorProb(
            students_addresses,
            basi_prog_values,
            prog_py_values,
            IDCERTprob_struct,
            CorsoPyprob_struct,
            FondInfoprob_struct,
            IngSoftprob_struct,
            {"from": account_Admin}
        )
        print("Configurazione Admin completata con successo.\n")

    elif ruolo_simulato == "Studente":
        print(f"[Studente {studente_target_id}] ({target_student_account.address}) dichiara la partecipazione.")
        contract_bn.studentDeclaredEvidence({"from": target_student_account})
        print(f"Stato aggiornato a EVIDENCE_DECLARED.\n")

    elif ruolo_simulato == "EnteCert":
        print(f"[EnteCert] Caricamento dati per Studente {studente_target_id}...")
        contract_bn.set_Evidence(target_student_account.address, dati_studenti[studente_target_id]['evidenze'], {"from": account_EnteCert})
        contract_bn.enablePosteriorCalc(target_student_account.address, {"from": account_EnteCert})
        contract_bn.update_apostProb(target_student_account.address, {"from": account_EnteCert})
        print(f"Evidenze inserite per lo studente {studente_target_id}.\n")

    elif ruolo_simulato == "Azienda":
        #print(f"[Azienda] Lettura risultati finali per studente {studente_target_id}:")
        res_prior = contract_bn.get_apriorInfoFacts(target_student_account.address, ID_apriorProb, {"from": account_Azienda})
        res_apost = contract_bn.get_apostInfoFacts(target_student_account.address, ID_apostProb, {"from": account_Azienda})
        print(f"[Azienda] REPORT FINALE PER STUDENTE {studente_target_id}:\n")
        print(f"BasiProg (A Priori): {res_prior / Fattore}")
        print(f"BasiProg (A Posteriori): {res_apost / Fattore}\n")

    elif ruolo_simulato == "GetState":
        current_state = contract_bn.studentState(target_student_account.address)
        print(f"RAW_STATE: {current_state}")

    else:
        print("\nIl ruolo inserito non è valido, potrebbe contenere errori grammaticali, di punteggiatura o "
               "di spazi.\nLa preghiamo di controllare e di riprovare.\n")


#def main():
    # Modificare il ruolo e il numero dello studente per testare il funzionamento

    #ruolo = "Admin"    # "Admin", "Studente", "EnteCert", "Azienda"
    #studente = 2    # Inserire il numero dello studente di cui vogliamo fare il test
    
    
    #role_management(ruolo, studente)

def main(*args):
    # Valori di default nel caso lo lanci senza parametri dal terminale
    ruolo = "Admin"
    studente = 1

    # Se passiamo argomenti (es: brownie run scripts/Role_based_txn.py Studente 2)
    if args:
        ruolo = args[0]
        if len(args) > 1:
            studente = int(args[1])

    print(f"\n--- [BROWNIE SCRIPT] ---")
    print(f"Azione: {ruolo}")
    print(f"Target Studente ID: {studente}")
    print(f"------------------------\n")
    
    # Chiama la tua funzione esistente con i nuovi parametri dinamici
    role_management(ruolo, studente)