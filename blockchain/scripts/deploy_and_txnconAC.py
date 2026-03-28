from brownie import accounts, AccessControl4Roles, Contract_bn
from eth_utils import keccak
import json
import os

#brownie run scripts/deploy_and_txnconAC.py --network ganache-gui


def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'json', filename)
    with open(path, 'r') as f:
        return json.load(f)

def deploy_and_set_values():

#-------------------------------------------------------------------------------------
#QUI "account" è l'account che distribuisce il contratto, e che ha i permessi di Admin in questo esempio

#Se vuoi simulare un altro ruolo, ad esempio: EnteCert, basta che commenti la riga "account_EnteCert"
#perchè l'account per simulare il ruolo è "account" e decommenti la riga "account_Admin"

    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    account_Studente = accounts.add(os.environ.get("PRIVATE_KEY_Studente")) 
    account_Admin = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))
#-------------------------------------------------------------------------------------


    print(f"Sto eseguendo il deploy con l'account: {account_Admin}...")

    contract_bn = Contract_bn.deploy({"from": account_Admin})

#--------------------------------------------------------------------------------------
    #N.B. qua bisogna rispettare l'ordine degli ingressi del constructor che definisce i ruoli in AccessControl4Roles.sol
    #prima ci va l'account che simula EnteCert, poi Azienda, poi Studente e infine Admin
    accesscontrol = AccessControl4Roles.deploy(
        account_EnteCert.address,  
        account_Azienda.address,  
        account_Studente.address, 
        account_Admin.address, 

    {"from": account_Admin})
#--------------------------------------------------------------------------------------

    Fattore = 1000

    # ── Carica i valori dai JSON ──────────────────────────────
    cv_inf  = load_json('cv_informatico.json')
    cv_ele  = load_json('cv_elettronico.json')
    cpt     = load_json('cpt.json')
    evidenze = load_json('Evidenze.json')
    CV = load_json('cv_inserito.json')['CV']
    dati_valid_ruolo = load_json('dati_valid_ruolo.json')




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

    

    ruolo = dati_valid_ruolo["Ente Certificatore"]["Ruolo"] # Simula il ruolo di Admin (decommenta se stai simulando Admin)

    if ruolo == "Studente":
        account = account_Studente
    if ruolo == "Ente Certificatore":
        account = account_EnteCert
    if ruolo == "Azienda":
        account = account_Azienda
    if ruolo == "Admin":
        account = account_Admin

    #tx1 = accesscontrol.permissions_EnteCert(
        #contract_bn.address,
            #evidenze,
            #ruolo,
        #{"from": account}
    #)



    print(f"Invio probabilità all'indirizzo: {accesscontrol.address}...")
    tx2 = accesscontrol.permissions_Admin(
        contract_bn.address,
        BasiProg_scelta,
        ProgPy_scelta,
        IDCERTprob_struct,
        CorsoPyprob_struct,
        FondInfoprob_struct,
        IngSoftprob_struct,
        account,
        {"from": account_Admin}
    )




    print("Eseguo il calcolo Bayesiano on-chain...")
    contract_bn.update_apostProb({"from": account_Admin})



def main():
    deploy_and_set_values()