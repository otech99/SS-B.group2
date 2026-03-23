

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "./Contract_bn.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract AccessControl3Roles is Contract_bn, AccessControl {
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



    function Access_set_apriorProb(
    address _contractbnAddress, 
    uint16 _BasiProg, 
    uint16 _ProgPy,
    Contract_bn.IDCERTProb calldata _IDCERTprob, 
    Contract_bn.CorsoPyProb calldata _CorsoPyprob,
    Contract_bn.FondInfoProb calldata _FondInfoprob,
    Contract_bn.IngSoftProb calldata _IngSoftprob
) public {
    // Inizializzi il contratto usando l'indirizzo
    Contract_bn contract_bn = Contract_bn(_contractbnAddress);
    
    contract_bn.set_apriorProb(
        _BasiProg, 
        _ProgPy, 
        _IDCERTprob, 
        _CorsoPyprob, 
        _FondInfoprob, 
        _IngSoftprob
    );
}

/*

    // Funzione riservata agli EnteCert
    function permissions_EnteCert(address to, uint16 ...) public {
        if (!hasRole(EnteCert, msg.sender)) {
            revert CallerNotEnteCert(msg.sender);
        }
       
	        //Logica per l'ente certificatore

    }

*/


/*

    // Funzione riservata agli EnteCert
    function permissions_Studente(address to, uint16 ...) public {
        if (!hasRole(Studente, msg.sender)) {
            revert CallerNotStudente(msg.sender);
        }

         
        
    }

*/


/*

    // Funzione riservata agli EnteCert
    function permissions_Azienda(address to, uint16 ...) public {
        if (!hasRole(Azienda, msg.sender)) {
            revert CallerNotAzienda(msg.sender);
        }
       
	        //Logica per l'Azienda

    }

*/
    // Funzione riservata agli Admin
    function permissions_Admin(address _contractbnAddress, // Indirizzo del contratto BN
            uint16 _BasiProg, 
            uint16 _ProgPy,
            Contract_bn.IDCERTProb calldata _IDCERTprob, 
            Contract_bn.CorsoPyProb calldata _CorsoPyprob,
            Contract_bn.FondInfoProb calldata _FondInfoprob,
            Contract_bn.IngSoftProb calldata _IngSoftprob) public {
        if (!hasRole(Admin, msg.sender)) {
            revert CallerNotAdmin(msg.sender);
        }
    
        Access_set_apriorProb(
        _contractbnAddress,
        _BasiProg,
        _ProgPy,
        _IDCERTprob,
        _CorsoPyprob,
        _FondInfoprob,
        _IngSoftprob);
        
 
    }
}

