// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract Contract_bn is AccessControl {

    bytes32 public constant Studente  = keccak256("Studente");
    bytes32 public constant EnteCert  = keccak256("EnteCert");
    bytes32 public constant Azienda   = keccak256("Azienda");
    bytes32 public constant Admin     = keccak256("Admin");

    enum State {
        NOT_INITIALIZED,      // 0: Stato di default di ogni nuovo studente
        EVIDENCE_DECLARED,    // 1: Lo studente ha fatto richiesta
        EVIDENCE_VERIFIED,    // 2: L'Ente ha caricato i voti
        READY_FOR_CALC,       // 3: Calcolo abilitato
        VIEW_PROB             // 4: Probabilità a posteriori pronte per l'Azienda
    }

    // Variabile globale: indica se l'Admin ha caricato la rete bayesiana
    bool public isSystemInitialized = false; 

    // Mapping: lo "schedario" per gestire infiniti studenti
    // Serve per associare in modo univoco una chiave (in questo caso l'indirizzo del wallet, address) a un valore specifico.
    mapping(address => State) public studentState; // Questo mapping associa l'indirizzo di ogni studente al suo stato attuale nel processo
    mapping(address => uint[4]) public studentEvidence; // Associa l'indirizzo di uno studente a un uint[4] corrispondente 
                                                        // ai voti o i risultati delle 4 prove/certificazioni associate a quel particolare indirizzo.
    mapping(address => uint16) internal student_apost_BasiProg; // Memorizza la probabilità a posteriori calcolata dal sistema riguardante 
                                                                // la competenza "BasiProg" per quello specifico studente.
    mapping(address => uint16) internal student_apost_ProgPy; // Salva il risultato del calcolo della probabilità a posteriori per la competenza "ProgPy" dello studente.

    mapping(address => uint16) internal student_prior_BasiProg;
    mapping(address => uint16) internal student_prior_ProgPy;
    
    
    // Evento aggiornato per tracciare lo stato del singolo studente
    event StudentStateChanged(address indexed student, State oldState, State newState);

    modifier onlyIfSystemInitialized() {
        require(isSystemInitialized == true, "Sistema non ancora inizializzato dall'Admin");
        _;
    }

    modifier onlyInStudentState(address _student, State required) {
        require(studentState[_student] == required, "Stato dello studente non valido");
        _;
    }

    modifier doubleStudentState(address _student,State required1,State required2){
        require(
        studentState[msg.sender] == State.NOT_INITIALIZED || 
        studentState[msg.sender] == State.VIEW_PROB, 
        "Lo studente deve essere in stato NOT_INITIALIZED o VIEW_PROB"
        );

        _;
    }

    modifier transitionStudentTo(address _student, State newState) {
        _;
        emit StudentStateChanged(_student, studentState[_student], newState);
        studentState[_student] = newState;
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
        IDCERTProb   prob_IDCERT;
        CorsoPyProb  prob_CorsoPy;
        FondInfoProb prob_FondInfo;
        IngSoftProb  prob_IngSoft;
    }

    OffChain_Info public prob;

     // COSTRUTTORE
    
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

   
    // FUNZIONI GLOBALI (Admin)
    
    function set_apriorProb(
    address[]    calldata _students,
    uint16[]     calldata _BasiProgValues,
    uint16[]     calldata _ProgPyValues,
    IDCERTProb   calldata _IDCERTprob,
    CorsoPyProb  calldata _CorsoPyprob,
    FondInfoProb calldata _FondInfoprob,
    IngSoftProb  calldata _IngSoftprob
)
    external
    onlyRole(Admin)
{
    require(!isSystemInitialized, "Probabilita' gia' inizializzate");

    // CPT globali della rete bayesiana
    prob.prob_IDCERT   = _IDCERTprob;
    prob.prob_CorsoPy  = _CorsoPyprob;
    prob.prob_FondInfo = _FondInfoprob;
    prob.prob_IngSoft  = _IngSoftprob;

    // Prior per-studente: scritti nel mapping di ciascuno, nessuna sovrascrittura
    for (uint256 i = 0; i < _students.length; i++) {
        student_prior_BasiProg[_students[i]] = _BasiProgValues[i];
        student_prior_ProgPy[_students[i]]   = _ProgPyValues[i];
    }

    isSystemInitialized = true;
}
    
    function studentDeclaredEvidence()
    external
    onlyRole(Studente)
    onlyIfSystemInitialized
    doubleStudentState(msg.sender, State.NOT_INITIALIZED, State.VIEW_PROB)
    transitionStudentTo(msg.sender, State.EVIDENCE_DECLARED)
{}

    function set_Evidence(address _student, uint[4] calldata _Evidence)
        external
        onlyRole(EnteCert)
        onlyInStudentState(_student, State.EVIDENCE_DECLARED)
        transitionStudentTo(_student, State.EVIDENCE_VERIFIED)
    {
        studentEvidence[_student] = _Evidence;
    }

    function enablePosteriorCalc(address _student)
        external
        onlyRole(EnteCert)
        onlyInStudentState(_student, State.EVIDENCE_VERIFIED)
        transitionStudentTo(_student, State.READY_FOR_CALC)
    {}

    function calculate_apostProb(address _student) internal view returns (uint16,uint16) {
        uint256 fattore = 1000;
        
        uint256 EvidenceProb_FF = EvidenceProb(_student, prob.prob_IDCERT.IDCERT_FF, prob.prob_CorsoPy.CorsoPy_FF, prob.prob_FondInfo.FondInfo_FF, prob.prob_IngSoft.IngSoft_FF, fattore);
        uint256 EvidenceProb_FT = EvidenceProb(_student, prob.prob_IDCERT.IDCERT_FT, prob.prob_CorsoPy.CorsoPy_FT, prob.prob_FondInfo.FondInfo_FT, prob.prob_IngSoft.IngSoft_FT, fattore);
        uint256 EvidenceProb_TF = EvidenceProb(_student, prob.prob_IDCERT.IDCERT_TF, prob.prob_CorsoPy.CorsoPy_TF, prob.prob_FondInfo.FondInfo_TF, prob.prob_IngSoft.IngSoft_TF, fattore);
        uint256 EvidenceProb_TT = EvidenceProb(_student, prob.prob_IDCERT.IDCERT_TT, prob.prob_CorsoPy.CorsoPy_TT, prob.prob_FondInfo.FondInfo_TT, prob.prob_IngSoft.IngSoft_TT, fattore);
     
       // calculate_apostProb: legge dal mapping per-studente
        uint256 BasiProb = student_prior_BasiProg[_student];
        uint256 ProgPy   = student_prior_ProgPy[_student];

        uint256 Prob_FF = (fattore - BasiProb) * (fattore - ProgPy) * EvidenceProb_FF;
        uint256 Prob_FT = (fattore - BasiProb) * ProgPy * EvidenceProb_FT;
        uint256 Prob_TF = (BasiProb) * (fattore - ProgPy) * EvidenceProb_TF;
        uint256 Prob_TT = (BasiProb) * ProgPy * EvidenceProb_TT;

        uint256 denominatore = Prob_FF + Prob_FT + Prob_TF + Prob_TT;
        require(denominatore > 0,"Denominatore non valido");

        uint256 numeratore_BasiProgT = Prob_TF + Prob_TT;
        uint256 numeratore_ProgPyT = Prob_FT + Prob_TT;

        return (
            uint16((uint256(numeratore_BasiProgT) * fattore) / denominatore),
            uint16((uint256(numeratore_ProgPyT) * fattore) / denominatore)
        );
    }

    function EvidenceProb(address _student, uint16 _IDCERT, uint16 _CorsoPy, uint16 _FondInfo, uint16 _IngSoft, uint256 _fattore) internal view returns (uint256) {  
        uint256 termine1;
        uint256 termine2;
        uint256 termine3;
        uint256 termine4;

        if (studentEvidence[_student][0] > 0) {
            termine1 = uint256(_IDCERT);
        } else {
            termine1 = _fattore - uint256(_IDCERT);
        }
        if (studentEvidence[_student][1] > 0) {
            termine2 = uint256(_CorsoPy);
        } else {
            termine2 = _fattore - uint256(_CorsoPy);
        }
        if (studentEvidence[_student][2] > 0) {
            termine3 = uint256(_FondInfo);
        } else {
            termine3 = _fattore - uint256(_FondInfo);
        }
        if (studentEvidence[_student][3] > 0) {
            termine4 = uint256(_IngSoft);
        } else {
            termine4 = _fattore - uint256(_IngSoft);
        }
        return termine1 * termine2 * termine3 * termine4;
    }

    function update_apostProb(address _student)
        external
        onlyRole(EnteCert)
        onlyInStudentState(_student, State.READY_FOR_CALC)
        transitionStudentTo(_student, State.VIEW_PROB)
    {
        (uint16 nuovoBasiprog, uint16 nuovoProgPy) = calculate_apostProb(_student);
        student_apost_BasiProg[_student] = nuovoBasiprog;
        student_apost_ProgPy[_student]   = nuovoProgPy;
    }

    function get_apriorInfoFacts(address _student, uint8 _fact_ID)
    external view onlyRole(Azienda) returns (uint16)
{
    require(isSystemInitialized, "Sistema non inizializzato");
    if (_fact_ID == 1) return student_prior_BasiProg[_student];
    if (_fact_ID == 2) return student_prior_ProgPy[_student];
    return 0;
}

    function get_apostInfoFacts(address _student, uint8 _fact_ID)
        external view
        onlyRole(Azienda)
        onlyInStudentState(_student, State.VIEW_PROB)
        returns (uint16)
    {
        if (_fact_ID == 1) return student_apost_BasiProg[_student];
        if (_fact_ID == 2) return student_apost_ProgPy[_student];
        return 0;
    }
}