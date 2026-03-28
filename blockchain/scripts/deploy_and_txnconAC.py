from brownie import accounts, AccessControl4Roles, Contract_bn
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

    account = accounts.add(os.environ.get("PRIVATE_KEY")) #IO
    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    #account_Studente = accounts.add(os.environ.get("PRIVATE_KEY_Studente")) 
    account_Admin = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))
#-------------------------------------------------------------------------------------


    print(f"Sto eseguendo il deploy con l'account: {account}...")

    contract_bn = Contract_bn.deploy({"from": account})

#--------------------------------------------------------------------------------------
    #N.B. qua bisogna rispettare l'ordine degli ingressi del constructor che definisce i ruoli in AccessControl4Roles.sol
    #prima ci va l'account che simula EnteCert, poi Azienda, poi Studente e infine Admin
    accesscontrol = AccessControl4Roles.deploy(
        account_EnteCert.address,  # entecert 
        account_Azienda.address,  # azienda
        #account_Studente.address,  # studente

        account.address, #IO (in questo caso sto simulando l'Admin, quindi "account.address" va messo alla fine,
        #se avessi simulato tipo EnteCert, avrei messo "account.address" come primo ingresso, commentato
        #l'ingresso "account_EnteCert.address" e decommentato "account_Admin.address"

        account_Admin.address,  # admin
    {"from": account})
#--------------------------------------------------------------------------------------

    Fattore = 1000

    # ── Carica i valori dai JSON ──────────────────────────────
    cv_inf  = load_json('cv_informatico.json')
    cv_ele  = load_json('cv_elettronico.json')
    cpt     = load_json('cpt.json')
    evidenze = load_json('Evidenze.json')
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



    tx1 = accesscontrol.permissions_EnteCert(
        contract_bn.address,
            evidenze,
        {"from": account}
    )



    print(f"Invio probabilità all'indirizzo: {accesscontrol.address}...")
    tx2 = accesscontrol.permissions_Admin(
        contract_bn.address,
        BasiProg_scelta,
        ProgPy_scelta,
        IDCERTprob_struct,
        CorsoPyprob_struct,
        FondInfoprob_struct,
        IngSoftprob_struct,
        {"from": account}
    )




    print("Eseguo il calcolo Bayesiano on-chain...")
    contract_bn.update_apostProb({"from": account})



def main():
    deploy_and_set_values()