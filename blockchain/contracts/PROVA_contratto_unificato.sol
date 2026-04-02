// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract Contract_bn is AccessControl {

    
    bytes32 public constant Studente  = keccak256("Studente");
    bytes32 public constant EnteCert  = keccak256("EnteCert");
    bytes32 public constant Azienda   = keccak256("Azienda");
    bytes32 public constant Admin     = keccak256("Admin");

    
    enum State {
        NOT_INITIALIZED,
        INITIALIZED,
        EVIDENCE_DECLARED,
        EVIDENCE_VERIFIED,
        READY_FOR_CALC,
        VIEW_PROB // ho aggiunto questo stato per far si che sia l'ente certificatore a fare l'update delle nuove probabilità
    }

    State public currentState = State.NOT_INITIALIZED;

    event StateChanged(State oldState, State newState);

    modifier onlyInState(State required) {
        require(currentState == required, "Invalid state transition");
        _;
    }

    modifier transitionTo(State newState) {
        _;
        emit StateChanged(currentState, newState);
        currentState = newState;
    }

    
    uint[4] public Evidence;
    uint16 internal apost_BasiProg;
    uint16 internal apost_ProgPy;

    struct FactsProb {
        uint16 BasiProg;
        uint16 ProgPy;
    }

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
        FactsProb    prob_facts;
        IDCERTProb   prob_IDCERT;
        CorsoPyProb  prob_CorsoPy;
        FondInfoProb prob_FondInfo;
        IngSoftProb  prob_IngSoft;
    }

    OffChain_Info public prob;

    // -------------------------------------------------------
    // COSTRUTTORE
    // — assegna DEFAULT_ADMIN_ROLE e i ruoli ai rispettivi indirizzi
    // -------------------------------------------------------
    constructor(
        address _admin,
        address _entecert,
        address _azienda,
        address _studente
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin); 
        _grantRole(Admin,    _admin);
        _grantRole(EnteCert, _entecert);
        _grantRole(Azienda,  _azienda);
        _grantRole(Studente, _studente);
    }

    
    function set_apriorProb(
        uint16 _BasiProg,
        uint16 _ProgPy,
        IDCERTProb   calldata _IDCERTprob,
        CorsoPyProb  calldata _CorsoPyprob,
        FondInfoProb calldata _FondInfoprob,
        IngSoftProb  calldata _IngSoftprob
    )
        external
        onlyRole(Admin)
        onlyInState(State.NOT_INITIALIZED)
        transitionTo(State.INITIALIZED)
    {
        prob.prob_facts.BasiProg = _BasiProg;
        prob.prob_facts.ProgPy   = _ProgPy;
        prob.prob_IDCERT         = _IDCERTprob;
        prob.prob_CorsoPy        = _CorsoPyprob;
        prob.prob_FondInfo       = _FondInfoprob;
        prob.prob_IngSoft        = _IngSoftprob;
    }

    

    function studentDeclaredEvidence()
        external
        onlyRole(Studente)
        onlyInState(State.INITIALIZED)
        transitionTo(State.EVIDENCE_DECLARED)
    {}

    function set_Evidence(uint[4] calldata _Evidence)
        external
        onlyRole(EnteCert)
        onlyInState(State.EVIDENCE_DECLARED)
        transitionTo(State.EVIDENCE_VERIFIED)
    {
        Evidence = _Evidence;
    }

    function enablePosteriorCalc()
        external
        onlyRole(EnteCert)
        onlyInState(State.EVIDENCE_VERIFIED)
        transitionTo(State.READY_FOR_CALC)
    {}

    function calculate_apostProb() internal view returns (uint16,uint16) {
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

    function update_apostProb()
        external
        onlyRole(EnteCert)
        onlyInState(State.READY_FOR_CALC)
        transitionTo(State.VIEW_PROB)
    {
        (uint16 nuovoBasiprog, uint16 nuovoProgPy) = calculate_apostProb();
        apost_BasiProg = nuovoBasiprog;
        apost_ProgPy   = nuovoProgPy;
    }

    function get_apriorInfoFacts(uint8 _fact_ID) external view onlyRole(Azienda)
        onlyInState(State.VIEW_PROB) returns (uint16) {
        if (_fact_ID == 1) return prob.prob_facts.BasiProg;
        if (_fact_ID == 2) return prob.prob_facts.ProgPy;
        return 0;
    }

    function get_apostInfoFacts(uint8 _fact_ID)
        external view
        onlyRole(Azienda)
        onlyInState(State.VIEW_PROB)
        returns (uint16)
    {
        if (_fact_ID == 1) return apost_BasiProg;
        if (_fact_ID == 2) return apost_ProgPy;
        return 0;
    }
}