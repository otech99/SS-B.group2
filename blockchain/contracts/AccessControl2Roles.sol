// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract AccessControlTwoRoles is Contract_bn, AccessControl {
    // Definizione dei due ruoli
    bytes32 public constant Studente = keccak256("Studente");
    bytes32 public constant EnteCert = keccak256("EnteCert");

    error CallerNotEnteCert(address caller);
    error CallerNotStudente(address caller);

    constructor(address entecert, address studente) {
        // Assegna i ruoli agli indirizzi specificati
        _grantRole(EnteCert, entecert);
        _grantRole(Studente, studente);
    }

    // Funzione riservata agli EnteCert
    function In(address to, uint16 ...) public {
        if (!hasRole(EnteCert, msg.sender)) {
            revert CallerNotEnteCert(msg.sender);
        }
       
	        //Logica per l'ente certificatore

    }

    // Funzione riservata agli Studenti
    function visualizzaCertificato(address to, uint16 ...) public {
        if (!hasRole(Studente, msg.sender)) {
            revert CallerNotStudente(msg.sender);
        }

        //Logica per lo studente
        
    }
}

