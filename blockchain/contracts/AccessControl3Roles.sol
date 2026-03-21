// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract AccessControlTwoRoles is Contract_bn, AccessControl {
    // Definizione dei due ruoli
    bytes32 public constant Studente = keccak256("Studente");
    bytes32 public constant EnteCert = keccak256("EnteCert");
    bytes32 public constant Azienda = keccak256("Azienda");
    bytes32 public constant Admin = keccak256("Admin");

    error CallerNotEnteCert(address caller);
    error CallerNotStudente(address caller);
    error CallerNotAzienda(address caller);
    error CallerNotAdmin(address caller);

    constructor(address entecert, address studente, address azienda, address admin) {
        // Assegna i ruoli agli indirizzi specificati
        _grantRole(EnteCert, entecert);
        _grantRole(Studente, studente);
        _grantRole(Azienda, azienda);
        _grantRole(Admin, admin); 
    }

    // Funzione riservata agli EnteCert
    function (address to, uint16 ...) public {
        if (!hasRole(EnteCert, msg.sender)) {
            revert CallerNotEnteCert(msg.sender);
        }
       
	        //Logica per l'ente certificatore

    }

    

    // Funzione riservata agli EnteCert
    function (address to, uint16 ...) public {
        if (!hasRole(Studente, msg.sender)) {
            revert CallerNotStudente(msg.sender);
        }

        //Logica per lo studente
        
    }

    // Funzione riservata agli EnteCert
    function (address to, uint16 ...) public {
        if (!hasRole(Azienda, msg.sender)) {
            revert CallerNotAzienda(msg.sender);
        }
       
	        //Logica per l'Azienda

    }

    // Funzione riservata agli Studenti
    function (address to, uint16 ...) public {
        if (!hasRole(Admin, msg.sender)) {
            revert CallerNotAdmin(msg.sender);
        }

        //Logica per l'admin
        
    }
}

