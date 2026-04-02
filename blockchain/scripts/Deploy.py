from brownie import accounts, Contract_bn
import json
import os

#Ho fatto uno script separato per il deploy altrimenti le variabili di stato si azzeravano ogni volta che chiamavo
# deploy_and_txn.py, quindi mi rimaneva impossibile simulare ruoli diversi e poi era un casino a prescindere perchè
# su ganache appariva contract creation 70 volte

#brownie run scripts/Deploy.py --network ganache-gui

def deploy():

    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    account_Studente = accounts.add(os.environ.get("PRIVATE_KEY_Studente")) 
    account_Admin = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))

    print(f"Sto eseguendo il deploy con l'account: {account_Admin}...")

    #bisogna rispettare l'ordine degli ingressi nel costruttore, sennò da errore
    contract_bn = Contract_bn.deploy(
    account_Admin.address,
    account_EnteCert.address,
    account_Azienda.address,
    account_Studente.address,
    {"from": account_Admin})

    #Salva l'indirizzo per gli script successivi
    with open("contract_address.json", "w") as f:
        json.dump({"address": contract_bn.address}, f)

    print(f"Contratto deployato all'indirizzo: {contract_bn.address}")

def main():
    deploy()