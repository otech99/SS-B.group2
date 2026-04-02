from brownie import accounts, Contract_bn
from eth_utils import keccak
import json
import os

#questo è lo script per eseguire solo le transazioni sul contratto

#brownie run scripts/Role_based_txn.py --network ganache-gui


def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'json', filename)
    with open(path, 'r') as f:
        return json.load(f)



def role_management(ruolo_simulato):

    with open("contract_address.json") as f:
        addr = json.load(f)["address"]
        
    contract_bn = Contract_bn.at(addr)

    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    account_Studente = accounts.add(os.environ.get("PRIVATE_KEY_Studente")) 
    account_Admin = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))


    Fattore = 1000

    # ── Carica i valori dai JSON ──────────────────────────────
    cv_inf  = load_json('cv_informatico.json')
    cv_ele  = load_json('cv_elettronico.json')
    cpt     = load_json('cpt.json')
    evidenze = load_json('Evidenze.json')['Evidenze']
    CV = load_json('cv_inserito.json')['CV']




    BasiProg_Inf = int(cv_inf['BasiProg'] * Fattore)
    ProgPy_Inf   = int(cv_inf['ProgPy']   * Fattore)
    BasiProg_Ele = int(cv_ele['BasiProg'] * Fattore)
    ProgPy_Ele   = int(cv_ele['ProgPy']   * Fattore)

    IDCERTprob_struct  = tuple(int(v * Fattore) for v in cpt['IDCERT'].values())
    CorsoPyprob_struct = tuple(int(v * Fattore) for v in cpt['CorsoPy'].values())
    FondInfoprob_struct= tuple(int(v * Fattore) for v in cpt['FondInfo'].values())
    IngSoftprob_struct = tuple(int(v * Fattore) for v in cpt['IngSoft'].values())

    print("Valori caricati dai JSON:")
    print(f"  CV Informatico: BasiProg={cv_inf['BasiProg']}, ProgPy={cv_inf['ProgPy']}")
    print(f"  CV Elettronico: BasiProg={cv_ele['BasiProg']}, ProgPy={cv_ele['ProgPy']}")
    # ─────────────────────────────────────────────────────────

    mapping_evidence = {
        0: "IDCERT Coding",
        1: "Corso Python",
        2: "Fondamenti di Info",
        3: "Ingegneria del Soft"
    }

    CV_dict = {1: "Ingegneria Informatica", 2: "Ingegneria Elettronica"}

    # Scelta CV
    while True:
        try:
            #print("\nScelta del curriculum:")
            #for numero, cv in CV_dict.items():
                #print(f"{numero}) {cv}")
            #CV = int(input("\nScegli un'opzione: "))
            if CV == 1:
                BasiProg_scelta = BasiProg_Inf
                ProgPy_scelta   = ProgPy_Inf
                break
            elif CV == 2:
                BasiProg_scelta = BasiProg_Ele
                ProgPy_scelta   = ProgPy_Ele
                break
            else:
                print(f"ERRORE: Inserisci 1 o 2")
        except ValueError:
            print("ERRORE: input non numerico")

    # Evidenze
    #Evidenze = []
    #for i in range(len(mapping_evidence)):
        #while True:
            #try:
                #boolevidence = int(input(f"{mapping_evidence[i]} superato? (0=NO, 1=SI): "))
                #if boolevidence in [0, 1]:
                    #Evidenze.append(boolevidence)
                    #break
                #else:
                    #print("ERRORE: inserisci 0 o 1")
            #except ValueError:
                #print("ERRORE: input non numerico")



    #contract_bn.set_Evidence(evidenze, {"from": account})

    
    hash_ruolo = keccak(ruolo_simulato.encode('utf-8'))
   

    ruolo_EnteCert = "EnteCert"
    hash_ruolo_EnteCert = keccak(ruolo_EnteCert.encode('utf-8'))

    ruolo_Azienda ="Azienda"
    hash_ruolo_Azienda = keccak(ruolo_Azienda.encode('utf-8'))

    ruolo_Studente ="Studente"
    hash_ruolo_Studente = keccak(ruolo_Studente.encode('utf-8'))

    ruolo_Admin = "Admin"
    hash_ruolo_Admin = keccak(ruolo_Admin.encode('utf-8'))

    #Assegno address (msg.sender in PROVA_Contratto_unificato.sol) in base al ruolo scelto
       
    
    if hash_ruolo == hash_ruolo_Admin:
            account = account_Admin
            print(f"[{ruolo_simulato}] Calling set_apriorProb()...")
            tx1 = contract_bn.set_apriorProb(
                BasiProg_scelta, ProgPy_scelta,
                IDCERTprob_struct, CorsoPyprob_struct,
                FondInfoprob_struct, IngSoftprob_struct,
                {"from": account}
            )
            print(f"✓ set_apriorProb() success: {tx1.txid}\n")
        
    elif hash_ruolo == hash_ruolo_Studente:
            account = account_Studente
            print(f"[{ruolo_simulato}] chiama studentDeclaredEvidence()...")
            tx2 = contract_bn.studentDeclaredEvidence({"from": account})
            print(f"studentDeclaredEvidence ok: {tx2.txid}\n")
        
    elif hash_ruolo == hash_ruolo_EnteCert:
            account = account_EnteCert
            print(f"[{ruolo_simulato}] chiama set_Evidence()...")
            tx3 = contract_bn.set_Evidence(evidenze, {"from": account})
            print(f"set_Evidence ok: {tx3.txid}\n")
            
            print(f"[{ruolo_simulato}] chiama enablePosteriorCalc()...")
            tx4 = contract_bn.enablePosteriorCalc({"from": account})
            print(f"enablePosteriorCalc ok: {tx4.txid}\n")
            
            print(f"[{ruolo_simulato}] chiama update_apostProb()...")
            tx5 = contract_bn.update_apostProb({"from": account})
            print(f"update_apostProb ok: {tx5.txid}\n")
        
    elif hash_ruolo == hash_ruolo_Azienda:
            account = account_Azienda
            print(f"[{ruolo_simulato}] chiama get_priorInfoFacts()...")
            result_aprior = contract_bn.get_apriorInfoFacts(1, {"from": account})
            print(f"BasiProg a priori ok: {result_aprior / 1000}\n")
            
            print(f"[{ruolo_simulato}] chiama get_apostInfoFacts()...")
            result_apost = contract_bn.get_apostInfoFacts(1, {"from": account})
            print(f"BasiProg a posteriori ok: {result_apost / 1000}\n")
    
    


def main():
    ruolo_simulato = "Azienda"
    role_management(ruolo_simulato)