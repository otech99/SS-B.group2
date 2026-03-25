
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "./Contract_bn.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract AccessControl4Roles is Contract_bn, AccessControl {
    // Definizione dei due ruoli
    bytes32 public constant Studente = keccak256("Studente");
    bytes32 public constant EnteCert = keccak256("EnteCert");
    bytes32 public constant Azienda = keccak256("Azienda");
    bytes32 public constant Admin = keccak256("Admin");

    error CallerNotEnteCert(address caller);
    error CallerNotStudente(address caller);
    error CallerNotAzienda(address caller);
    error CallerNotAdmin(address caller);

    //-----------------------------------------------------------------------------------------
    //Qua è dove posso scegliere chi impersonare
    constructor(address entecert, address azienda, address studente, address admin) {
        // Assegna i ruoli agli indirizzi specificati


        //address IOEnteCert = (entecert == address(0)) ? msg.sender : entecert;
        //_grantRole(EnteCert, IOEnteCert); // Assegno il ruolo di entecert a chi distribuisce il contratto

        //address IOstudente = (studente == address(0)) ? msg.sender : studente;
        //_grantRole(Studente, IOstudente); // Assegno il ruolo di studente a chi distribuisce il contratto

        address IOAdmin = (admin == address(0)) ? msg.sender : admin;
        _grantRole(Admin, IOAdmin); // Assegno il ruolo di admin a chi distribuisce il contratto

        //address IOazienda = (azienda == address(0)) ? msg.sender : azienda;
        //_grantRole(Azienda, IOazienda); // Assegno il ruolo di azienda a chi distribuisce il contratto



        _grantRole(EnteCert, entecert);

        _grantRole(Studente, studente); 

        //_grantRole(Admin, admin);

        _grantRole(Azienda, azienda);
         
    }
  //-----------------------------------------------------------------------------------------


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
    function permissions_Admin(address _contractbnAddress, 
            uint16 _BasiProg, 
            uint16 _ProgPy,
            Contract_bn.IDCERTProb calldata _IDCERTprob, 
            Contract_bn.CorsoPyProb calldata _CorsoPyprob,
            Contract_bn.FondInfoProb calldata _FondInfoprob,
            Contract_bn.IngSoftProb calldata _IngSoftprob) external {
        //msg.sender è l'indirizzo di chi chiama la funzione, se non ha il ruolo di Admin, viene generato un errore
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

