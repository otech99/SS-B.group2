from brownie import Contract_bn,accounts,config


#3) brownie run scripts/read_Info.py --network ganache-gui per eseguire lo script da ganache


def read_contract():

    fattore=1000

    #Mapping per associare ciascun indice a un Evidence
    #Evidences_dict = {
        #1:"IDCERT Coding",
        #2:"Corso Python",
        #3:"Fondamenti di Info",
        #4:"Ingegneria del Soft"
    #}


    Facts_dict ={1:"Basi di Programmazione"
                 ,2:"Programmazione Python"}


    while True:
        try:
            i = int(input("Scegli un contratto: "))
            if i >= 1 :
                contract_bn = Contract_bn[i-1]
                break
            else:
                print(f"ERRORE: Inserisci un numero >= 1")
           
        except ValueError:
            print("ERRORE: input non numerico")

    print("Probabilità(CONOSCENZE)")
    for numero, fatto in Facts_dict.items():
        print(f"{numero}) {fatto}")


    while True:
        try:
            Fact = int(input("\nScegli un'opzione: "))
            if Fact in Facts_dict:
                risultato=contract_bn.get_apriorInfoFacts(Fact)
                print(risultato/fattore)


                break
            else:
                print(f"ERRORE: Inserisci un numero tra 1 e {len(Facts_dict)}")
        except ValueError:
            print("ERRORE: input non numerico")

    #print("\nProbabilità(EVIDENZE | CONOSCENZE)")
    #for numero, evidenza in Evidences_dict.items():
        #print(f"{numero}) {evidenza}")


    #while True:
        #try:
            #evidence = int(input("\nScegli un'opzione: "))
            #if evidence in Evidences_dict:
                #probabilities = contract_bn.prob()
                #print(probabilities[evidence])
                #break
            #else:
                #print(f"ERRORE: Inserisci un numero tra 1 e {len(Evidences_dict)}")
        #except ValueError:
           # print("ERRORE: input non numerico")

    print("\nProbabilità(CONOSCENZE | EVIDENZE osservate)")
    for numero, fatto in Facts_dict.items():
            print(f"{numero}) {fatto}")

    while True:
        try:
            Fact = int(input("\nScegli un'opzione: "))
            if Fact in Facts_dict:
                    risultato=contract_bn.get_apostInfoFacts(Fact)
                    print(risultato/fattore)
                    break
            else:
                print(f"ERRORE: Inserisci un numero tra 1 e {len(Facts_dict)}")
        except ValueError:
            print("ERRORE: input non numerico")
   
def main():
    read_contract()


