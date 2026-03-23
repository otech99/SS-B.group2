from brownie import accounts, AccessControl3Roles, Contract_bn
import json
import os

def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'json', filename)
    with open(path, 'r') as f:
        return json.load(f)

def deploy_and_set_values():

    account = accounts.add(os.environ.get("PRIVATE_KEY"))
    
    print(f"Sto eseguendo il deploy con l'account: {account}...")
    contract_bn = Contract_bn.deploy({"from": account})
    accesscontrol = AccessControl3Roles.deploy(
    account.address,  # entecert
    account.address,  # studente
    account.address,  # azienda
    account.address,  # admin
    {"from": account}
)
    Fattore = 1000

    # ── Carica i valori dai JSON ──────────────────────────────
    cv_inf  = load_json('cv_informatico.json')
    cv_ele  = load_json('cv_elettronico.json')
    cpt     = load_json('cpt.json')

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
            print("\nScelta del curriculum:")
            for numero, cv in CV_dict.items():
                print(f"{numero}) {cv}")
            CV = int(input("\nScegli un'opzione: "))
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
    Evidenze = []
    for i in range(len(mapping_evidence)):
        while True:
            try:
                boolevidence = int(input(f"{mapping_evidence[i]} superato? (0=NO, 1=SI): "))
                if boolevidence in [0, 1]:
                    Evidenze.append(boolevidence)
                    break
                else:
                    print("ERRORE: inserisci 0 o 1")
            except ValueError:
                print("ERRORE: input non numerico")

    contract_bn.set_Evidence(Evidenze, {"from": account})

    print(f"Invio probabilità all'indirizzo: {accesscontrol.address}...")
    tx = accesscontrol.permissions_Admin(
        contract_bn.address,
        BasiProg_scelta,
        ProgPy_scelta,
        IDCERTprob_struct,
        CorsoPyprob_struct,
        FondInfoprob_struct,
        IngSoftprob_struct,
        {"from": account}
    )
    tx.wait(1)

    print("Eseguo il calcolo Bayesiano on-chain...")
    contract_bn.update_apostProb({"from": account})

def main():
    deploy_and_set_values()