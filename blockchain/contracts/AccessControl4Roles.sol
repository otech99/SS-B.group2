
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "./Contract_bn.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract AccessControl4Roles is AccessControl {
   
    bytes32 public constant Studente = keccak256("Studentee2026");
    bytes32 public constant EnteCert = keccak256("EnteCertt2026");
    bytes32 public constant Azienda = keccak256("Aziendaa2026");
    bytes32 public constant Admin = keccak256("Adminn2026");

    Contract_bn public immutable contract_bn;

    constructor(address _contractbnAddress,address entecert, address azienda, address studente, address admin) {
        
        contract_bn = Contract_bn(_contractbnAddress);

        _grantRole(EnteCert, entecert);

        _grantRole(Studente, studente); 

        _grantRole(Admin, admin);

        _grantRole(Azienda, azienda);
         
    }
  


        function Access_set_apriorProb( 
        uint16 _BasiProg, 
        uint16 _ProgPy,
        Contract_bn.IDCERTProb calldata _IDCERTprob, 
        Contract_bn.CorsoPyProb calldata _CorsoPyprob,
        Contract_bn.FondInfoProb calldata _FondInfoprob,
        Contract_bn.IngSoftProb calldata _IngSoftprob
    ) internal {
        
        contract_bn.set_apriorProb(
            _BasiProg, 
            _ProgPy, 
            _IDCERTprob, 
            _CorsoPyprob, 
            _FondInfoprob, 
            _IngSoftprob
        );
    }


    function Access_set_Evidence(uint[4] calldata _Evidence) internal{
        contract_bn.set_Evidence(_Evidence);
    }

    function get_Access_apostInfofacts(uint8 _fact_ID) internal view returns (uint16){
        return contract_bn.get_apostInfoFacts(_fact_ID);
    }
    
//-------------------------------------------
//Funzioni per i permessi dei ruoli
//-------------------------------------------

    // Funzione riservata agli EnteCert
    function permissions_EnteCert(uint[4] calldata _Evidence) external {
        if (!hasRole(EnteCert, msg.sender)) {
            revert("Non autorizzato");
        }
       
       //Dopo che ha certificato lo studente, l'ente certificatore chiama questa funzione per impostare le evidenze
       //on-chain, che poi lo studente potrà utilizzare per dimostrare le sue competenze alle aziende

       //forse bisogna fa una funzione di lettura anche per EnteCert
	    Access_set_Evidence(_Evidence);    

    }




    // Funzione riservata all'azienda
    function permissions_Azienda( uint8 _fact_ID) external view returns (uint16) {
        if (!hasRole(Azienda, msg.sender)) {
            revert("Non autorizzato");
        }
       
	    return get_Access_apostInfofacts(_fact_ID); //L'azienda chiama questa funzione per ottenere
        // le informazioni a posteriori sullo studente, in modo da valutare se assumerlo o meno

    }


    // Funzione riservata agli Admin
    function permissions_Admin( uint16 _BasiProg, uint16 _ProgPy,Contract_bn.IDCERTProb calldata _IDCERTprob, 
            Contract_bn.CorsoPyProb calldata _CorsoPyprob,
            Contract_bn.FondInfoProb calldata _FondInfoprob,
            Contract_bn.IngSoftProb calldata _IngSoftprob) external {
        
        if (!hasRole(Admin, msg.sender)) {
            revert("Non autorizzato");
        }
    
        Access_set_apriorProb(_BasiProg,_ProgPy,_IDCERTprob,_CorsoPyprob,_FondInfoprob,_IngSoftprob);
        
 
    }
}

