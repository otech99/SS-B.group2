// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

//Usare la directory: C:\Users\nome_user\...\...\SS-B.group2\blockchain>
//0) brownie compile -all


//E' il programma che modella l'on-chain oracle (occorre consultare OpenZeppelin per fare modifiche di sicurezza
//tipo verifica della firma digitale di una transazione, autorizzazione ad accedere a certe aree, ecc...)




//OPENZEPPELIN
//import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";


contract Contract_bn {


    //uint 16:
    //perchè ho fissato una precisione di 3 cifre dopo la virgola, quindi
    //tipo 0.990 lo rappresenterò come 0.990*fattore (con fattore = 1000) = 990 perchè in solidity non si può lavorare con i decimali
    //che è un numero compreso tra 0 e 2^16-1 (ovviamente più aumenta la precisione più tocca allocare memoria per il valore)


    //public per le variabili:
    //se il risultato della variabile si vuole che sia visibile a tutti sulla blockchain


    uint[4] public Evidence; //Vettore di dimensione fissa: [4], per le 4 evidenze
    uint16 internal apost_BasiProg; //variabile contenente il risultato del calcolo bayesiano per Basi di Programmazione = T
    //condizionato all'evidenza osservata
    uint16 internal apost_ProgPy;  //variabile contenente il risultato del calcolo bayesiano per Programmazione Python = T
    //condizionato all'evidenza osservata


    //Probabilità a priori dei fatti, quindi in questo caso delle conoscenze
    struct FactsProb {
        uint16 BasiProg;
        uint16 ProgPy;
    }


    //Probabilità condizionate delle evidenze condizionate alle conoscenze
    struct IDCERTProb {
        uint16 IDCERT_FF; 
        uint16 IDCERT_FT; 
        uint16 IDCERT_TF; 
        uint16 IDCERT_TT;
    }


    struct CorsoPyProb {
        uint16 CorsoPy_FF; 
        uint16 CorsoPy_FT; 
        uint16 CorsoPy_TF; 
        uint16 CorsoPy_TT;
    }


    struct FondInfoProb {
        uint16 FondInfo_FF; 
        uint16 FondInfo_FT; 
        uint16 FondInfo_TF; 
        uint16 FondInfo_TT;
  }


    struct IngSoftProb {
        uint16 IngSoft_FF;
        uint16 IngSoft_FT;
        uint16 IngSoft_TF;
        uint16 IngSoft_TT;
    }


    struct OffChain_Info {
        FactsProb prob_facts;
        IDCERTProb prob_IDCERT;
        CorsoPyProb prob_CorsoPy;
        FondInfoProb prob_FondInfo;
        IngSoftProb prob_IngSoft;
    }

    OffChain_Info public prob;

    //OPENZEPPELIN
    //using ECDSA for bytes32;


    //function _verify(bytes32 data, bytes memory signature, address account) internal pure returns (bool){
        //return data
            //.toEthSignedMessageHash()
            //.recover(signature) == account;
    //}

    //E' la funzione che viene chiamata nel file "deploy_and_txn.py" per eseguire il setup delle probabilità iniziali nell'oracolo on-chain
    
    address public authorized_role;



//Modifiche suggerite da Claude
//----------------------------------------------------------------------
    modifier onlyAuthorized() {
        require(msg.sender == authorized_role, "Non autorizzato");
        _;
    }

    function set_AuthorizedCaller(address _new) external onlyAuthorized {
    require(_new != address(0), "Indirizzo non valido");
    authorized_role = _new;
}

constructor(address _authorizedCaller) {
    require(_authorizedCaller != address(0), "Indirizzo non valido");
    authorized_role = _authorizedCaller;
}
//----------------------------------------------------------------------



    
    function set_apriorProb(uint16 _BasiProg, uint16 _ProgPy,IDCERTProb calldata _IDCERTprob,
        CorsoPyProb calldata _CorsoPyprob,
        FondInfoProb calldata _FondInfoprob,
        IngSoftProb calldata _IngSoftprob) external onlyAuthorized{ //_verify(data,signature,account){


        //prob.prob_facts = FactsProb(_BasiProg, _ProgPy);
        //facts["Basi di Programmazione"] = Fact('Basi di Programmazione', _BasiProg);
        //facts["Programmazione Python"] = Fact('Programmazione Python', _ProgPy);

        prob.prob_facts.BasiProg=_BasiProg;
        prob.prob_facts.ProgPy=_ProgPy;
        prob.prob_IDCERT = _IDCERTprob;
        prob.prob_CorsoPy = _CorsoPyprob;
        prob.prob_FondInfo = _FondInfoprob;
        prob.prob_IngSoft = _IngSoftprob;
        }

    function get_apriorInfoFacts(uint8 _fact_ID) external view returns (uint16){


        if (_fact_ID == 1) return prob.prob_facts.BasiProg;
        if (_fact_ID == 2) return prob.prob_facts.ProgPy;


        return 0;
 
    }

    function set_Evidence(uint[4] calldata _Evidence) external onlyAuthorized{
        Evidence = _Evidence;
        //Le imposta l'ente certificatore in base a ciò che osserva off-chain, quindi in questo caso se lo studente ha ottenuto o meno i 4 certificati (IDCERT, CorsoPy, FondInfo, IngSoft)
        //Le imposta lo studente
    }

    function calculate_apostProb() public view returns (uint16,uint16) {
    // Con view posso accedere direttamente ai dati salvati nello storage (leggerli direttamente dal contratto)

    uint256 fattore = 1000;

    //applico uint256 perchè il risultato di questa funzione è un numero non rappresentabile nel range [0, 2^16-1]
    uint256 EvidenceProb_FF = EvidenceProb(prob.prob_IDCERT.IDCERT_FF, prob.prob_CorsoPy.CorsoPy_FF, prob.prob_FondInfo.FondInfo_FF, prob.prob_IngSoft.IngSoft_FF, fattore);
    uint256 EvidenceProb_FT = EvidenceProb(prob.prob_IDCERT.IDCERT_FT, prob.prob_CorsoPy.CorsoPy_FT, prob.prob_FondInfo.FondInfo_FT, prob.prob_IngSoft.IngSoft_FT, fattore);
    uint256 EvidenceProb_TF = EvidenceProb(prob.prob_IDCERT.IDCERT_TF, prob.prob_CorsoPy.CorsoPy_TF, prob.prob_FondInfo.FondInfo_TF, prob.prob_IngSoft.IngSoft_TF, fattore);
    uint256 EvidenceProb_TT = EvidenceProb(prob.prob_IDCERT.IDCERT_TT, prob.prob_CorsoPy.CorsoPy_TT, prob.prob_FondInfo.FondInfo_TT, prob.prob_IngSoft.IngSoft_TT, fattore);
 
    uint256 BasiProb = prob.prob_facts.BasiProg;
    uint256 ProgPy = prob.prob_facts.ProgPy;

    uint256 Prob_FF = (fattore - BasiProb) * (fattore - ProgPy) * EvidenceProb_FF;
    uint256 Prob_FT = (fattore - BasiProb) * ProgPy * EvidenceProb_FT;
    uint256 Prob_TF = (BasiProb) * (fattore - ProgPy) * EvidenceProb_TF;
    uint256 Prob_TT = (BasiProb) * ProgPy * EvidenceProb_TT;

    // Calcolo denominatore
    uint256 denominatore = Prob_FF + Prob_FT + Prob_TF + Prob_TT;
    require(denominatore > 0,"Denominatore non valido");

    // Calcolo numeratori
    uint256 numeratore_BasiProgT = Prob_TF + Prob_TT;
    uint256 numeratore_ProgPyT = Prob_FT + Prob_TT;

    return (
    uint16((uint256(numeratore_BasiProgT) * fattore) / denominatore),
    uint16((uint256(numeratore_ProgPyT) * fattore) / denominatore));

    //applico uint16 al risultato in modo che la probabilità finale occupi lo stesso spazio che occupavano quelle iniziali
}

function EvidenceProb(uint16 _IDCERT, uint16 _CorsoPy, uint16 _FondInfo, uint16 _IngSoft, uint256 _fattore) internal view returns (uint256) {  
    uint256 termine1;
    uint256 termine2;
    uint256 termine3;
    uint256 termine4;

    // Logica stile C: controllo esplicito e assegnazione
    if (Evidence[0] > 0) {
        termine1 = uint256(_IDCERT);
    } else {
        termine1 = _fattore - uint256(_IDCERT);
    }
    if (Evidence[1] > 0) {
        termine2 = uint256(_CorsoPy);
    } else {
        termine2 = _fattore - uint256(_CorsoPy);
    }
    if (Evidence[2] > 0) {
        termine3 = uint256(_FondInfo);
    } else {
        termine3 = _fattore - uint256(_FondInfo);
    }
    if (Evidence[3] > 0) {
        termine4 = uint256(_IngSoft);
    } else {
        termine4 = _fattore - uint256(_IngSoft);
    }
    return termine1 * termine2 * termine3 * termine4;
}

function update_apostProb() external {
    //Calcolo bayesiano
    (uint16 nuovoBasiprog, uint16 nuovoProgPy) = calculate_apostProb();

    //Salvataggio nello storage
    apost_BasiProg = nuovoBasiprog;
    apost_ProgPy = nuovoProgPy;
}

function get_apostInfoFacts(uint8 _Fact_ID) external view returns (uint16) {
        if (_Fact_ID == 1) return apost_BasiProg;
        if (_Fact_ID == 2) return apost_ProgPy;

        return 0;
    }
}
