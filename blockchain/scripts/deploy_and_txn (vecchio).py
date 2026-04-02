from brownie import accounts, Contract_bn

def deploy_and_set_values():

    #Usare la directory: C:\Users\nome_user\...\...\SS-B.group2\blockchain>
    #1) brownie networks add Ethereum ganache-gui host=http://127.0.0.1:7545 chainid=5777 per la connessione a ganache
    #2) brownie run scripts/deploy_and_txn.py --network ganache-gui per eseguire lo script su ganache

    #Cambiare a ogni accesso su ganache la PRIVATE_KEY nel file ".env"

    account = accounts[0]
    
    print(f"Sto eseguendo il deploy con l'account: {account}...")
    contract_bn = Contract_bn.deploy({"from": account})

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
            BasiProgprob = float(input("P(Basi di Programmazione=True): "))
            ProgPyprob = float(input("P(Programmazione Python=True): "))
            
            if 0 <= BasiProgprob <= 1 and 0 <= ProgPyprob <= 1:
                BasiProg = int(BasiProgprob * Fattore)
                ProgPy = int(ProgPyprob * Fattore)
                break
            else:
                print("ERRORE: probabilità non valida")
        except ValueError:
            print("ERRORE: input non numerico")
    

    Evidenze = [1, 1, 0, 0]
    contract_bn.set_Evidence(Evidenze, {"from": account})

    print(f"Invio probabilità all'indirizzo: {contract_bn.address}...")
    
    tx = contract_bn.set_apriorProb(
        BasiProg, ProgPy, IDCERTprob_struct, CorsoPyprob_struct, FondInfoprob_struct, IngSoftprob_struct, 
        {"from": account}
    )

    #per essere sicuro che evidenze e probabilità siano settate prima di fare il calcolo successivo
    tx.wait(1) 

    print("Eseguo il calcolo Bayesiano on-chain...")
    tx_calc = contract_bn.update_apostProb({"from": account})

def main():
    deploy_and_set_values()