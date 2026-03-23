from brownie import accounts, AccessControl3Roles, Contract_bn

def deploy_and_set_values():

    #Usare la directory: C:\Users\nome_user\...\...\SS-B.group2\blockchain>
    #1) brownie networks add Ethereum ganache-gui host=http://127.0.0.1:7545 chainid=5777 per la connessione a ganache
    #2) brownie run scripts/deploy_and_txnAC.py --network ganache-gui per eseguire lo script su ganache

    #Cambiare a ogni accesso su ganache la PRIVATE_KEY nel file ".env"

    account = accounts[0]
    
    print(f"Sto eseguendo il deploy con l'account: {account}...")
    contract_bn = Contract_bn.deploy({"from": account})
    accesscontrol = AccessControl3Roles.deploy({"from": account})

    Fattore = 1000 #è un fattore per trasformare le probabilità in numeri interi

    mapping_bits = {
        0: False,
        1: True,
    }

    mapping_evidence={
        0: "IDCERT Coding",
        1: "Corso Python",
        2: "Fondamenti di Info",
        3: "Ingegneria del Soft"
    }


    CV_dict ={1:"Ingegneria Informatica"
                 ,2:"Ingegneria Elettronica"}
    

    IDCERTprob_struct=()
    CorsoPyprob_struct=()
    FondInfoprob_struct=()
    IngSoftprob_struct=()

    for i in range(len(mapping_evidence)): 
        for j in range(0,2):
            for k in range(0,2):
                while True:
                        try:
                            prob_evidence = float(input(f"P({mapping_evidence[i]}=True | BP={mapping_bits[j]}, PP={mapping_bits[k]}): "))
                            if 0 <= prob_evidence <= 1:
                                if i==0:
                                    IDCERTprob_struct += (int(prob_evidence * Fattore),)
                                elif i==1:
                                    CorsoPyprob_struct += (int(prob_evidence * Fattore),)
                                elif i==2:
                                    FondInfoprob_struct += (int(prob_evidence * Fattore),)
                                elif i==3:
                                    IngSoftprob_struct += (int(prob_evidence * Fattore),)
                                break
                            else:
                                print("ERRORE: probabilità fuori range")
                        except ValueError:
                            print("ERRORE: input non numerico")
    
    

    while True:
            try:
                print("\nProbabilità a priori delle conoscenze:")
                BasiProgprob_Inf = float(input("P(Basi di Programmazione CV Info=True): "))
                ProgPyprob_Inf = float(input("P(Programmazione Python CV Info=True): "))
                BasiProgprob_Ele = float(input("P(Basi di Programmazione CV Ele=True): "))
                ProgPyprob_Ele = float(input("P(Programmazione Python CV Ele=True): "))
                if 0 <= BasiProgprob_Inf <= 1 and 0 <= ProgPyprob_Inf <= 1 and 0 <= BasiProgprob_Ele <= 1 and 0 <= ProgPyprob_Ele <= 1:
                    BasiProg_Inf = int(BasiProgprob_Inf * Fattore)
                    ProgPy_Inf = int(ProgPyprob_Inf * Fattore)
                    BasiProg_Ele = int(BasiProgprob_Ele * Fattore)
                    ProgPy_Ele = int(ProgPyprob_Ele * Fattore)
                    break
                else:
                    print("ERRORE: probabilità non valida")
            except ValueError:
                print("ERRORE: input non numerico")

    
    

    while True:
        try:
            print("Scelta del curriculum:")
            for numero, cv in CV_dict.items():
                print(f"{numero}) {cv}")
            CV = int(input("\nScegli un'opzione: "))
            if CV == 1:
                BasiProgprob_scelta=BasiProgprob_Inf 
                ProgPyprob_scelta=ProgPyprob_Inf               
                break
            elif CV == 2:
                BasiProgprob_scelta=BasiProgprob_Ele
                ProgPyprob_scelta=ProgPyprob_Ele
                break
            else:
                print(f"ERRORE: Inserisci un numero tra 1 e {len(CV_dict)}")
        except ValueError:
            print("ERRORE: input non numerico")
        

    Evidenze = []
    for i in range(len(mapping_evidence)):
        while True:
                try:
                    boolevidence = int(input(f"{mapping_evidence[i]} superato? (0 = NO o 1 = SI): "))
                    if (boolevidence in [0,1]):
                        Evidenze.append(boolevidence)
                        break
                    else:
                        print("ERRORE: valore non valido, inserisci 0 o 1")
                except ValueError:
                    print("ERRORE: input non numerico")
                
            
            
    

    #Evidenze = [1, 1, 0, 0]
    contract_bn.set_Evidence(Evidenze, {"from": account})

    print(f"Invio probabilità all'indirizzo: {accesscontrol.address}...")
    
    tx = accesscontrol.permissions_Admin(
        contract_bn.address,
        BasiProg_Inf,
        ProgPy_Inf,
        BasiProg_Ele,
        ProgPy_Ele,
        IDCERTprob_struct,
        CorsoPyprob_struct,
        FondInfoprob_struct,
        IngSoftprob_struct,
        {"from": account}
    )

    #per essere sicuro che evidenze e probabilità siano settate prima di fare il calcolo successivo
    tx.wait(1) 

    print("Eseguo il calcolo Bayesiano on-chain...")
    tx_calc = contract_bn.update_apostProb({"from": account})

def main():
    deploy_and_set_values()