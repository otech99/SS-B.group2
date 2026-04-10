from brownie import accounts, Contract_bn
import json
import os

def deploy():
    account_EnteCert = accounts.add(os.environ.get("PRIVATE_KEY_EnteCert"))
    account_Azienda = accounts.add(os.environ.get("PRIVATE_KEY_Azienda"))
    account_Studente = accounts.add(os.environ.get("PRIVATE_KEY_Studente")) 
    account_Admin = accounts.add(os.environ.get("PRIVATE_KEY_Admin"))

    print(f"Sto eseguendo il deploy con l'account: {account_Admin}...")

    # Usa Contract_bn per il deploy
    contract_bn = Contract_bn.deploy(
        account_Admin.address,
        account_EnteCert.address,
        account_Azienda.address,
        account_Studente.address,
        {"from": account_Admin}
    )

    with open("contract_address.json", "w") as f:
        json.dump({"address": contract_bn.address}, f)

    print(f"Contratto deployato all'indirizzo: {contract_bn.address}")

def main():
    deploy()