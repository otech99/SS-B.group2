#!/bin/bash

echo "In attesa che il nodo Ganache sia pronto (5 secondi)..."
sleep 5

echo "Applico le migrazioni del database Django..."
python manage.py migrate

echo "Configuro la rete virtuale per Brownie sulla porta 8546..."
brownie networks add Ethereum ganache-docker host=http://ganache:8546 chainid=1337 || true

echo "Avvio il server web Django..."
python manage.py runserver 0.0.0.0:8000