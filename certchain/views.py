import os
import json
import subprocess  # Fondamentale per l'integrazione blockchain senza crash
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required # Questo risolve il NameError
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, OTPToken
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from web3 import Web3
import random
from django.db.models import Max
from django.shortcuts import get_object_or_404
# ── Helper ────────────────────────────────────────────────────

def _get_user_role(user):
    if user.role == 'ADMIN':
        return 'Admin'
    elif user.role == 'CERTIFYING_AUTHORITY':
        return 'CertifyingAuthority'
    elif user.role == 'COMPANY':
        return 'Company'
    else:
        return 'Student'

def _redirect_by_role(user):
    role = _get_user_role(user)
    if role == 'Admin':
        return redirect('dashboard_admin')
    elif role == 'CertifyingAuthority':
        return redirect('dashboard_entecert')
    elif role == 'Company':
        return redirect('dashboard_company')
    else:
        return redirect('dashboard_student')

# ── Views ─────────────────────────────────────────────────────

def home(request):
    """Pagina iniziale pubblica."""
    return render(request, 'certchain/index.html')

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            token_value = OTPToken.generate_token()
            OTPToken.objects.create(user=user, token=token_value)
            request.session['otp_user_id'] = user.id

            send_mail(
                subject='CertChain — Codice di accesso',
                message=f'Il tuo codice di accesso è: {token_value}\n\nScade tra 5 minuti.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return redirect('verify_otp')
        else:
            error = 'Credenziali non valide. Riprova.'

    return render(request, 'certchain/login.html', {'error': error})

def verify_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('login')

    error = None
    if request.method == 'POST':
        token_input = request.POST.get('otp', '').strip()
        try:
            user = CustomUser.objects.get(id=user_id)
            otp  = OTPToken.objects.filter(
                user=user,
                token=token_input,
                is_used=False
            ).latest('created_at')

            if otp.is_valid():
                otp.is_used = True
                otp.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                refresh = RefreshToken.for_user(user)
                request.session['access_token']  = str(refresh.access_token)
                request.session['refresh_token'] = str(refresh)
                request.session['user_role']      = _get_user_role(user)
                del request.session['otp_user_id']

                return _redirect_by_role(user)
            else:
                error = 'Codice scaduto o già utilizzato.'
        except Exception:
            error = 'Codice non valido.'

    return render(request, 'certchain/verify_otp.html', {'error': error})

@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('home')

@login_required
def dashboard(request):
    return _redirect_by_role(request.user)
@login_required
def dashboard_admin(request):
    """
    Dashboard principale per l'Admin con caricamento dinamico dei CV dai file JSON.
    """
    if not request.user.is_admin():
        return redirect('home')

    # 1. Caricamento dati CPT (Anteprima Oracle)
    cpt_path = os.path.join(settings.BASE_DIR, 'data', 'json', 'cpt.json')
    cpt_data = {}
    if os.path.exists(cpt_path):
        try:
            with open(cpt_path, 'r') as f:
                cpt_data = json.load(f)
        except Exception as e:
            print(f"Errore lettura cpt.json: {e}")

    # 2. Controllo Stato Blockchain
    addr_path = os.path.join(settings.BASE_DIR, 'blockchain', 'contract_address.json')
    contract_address = "Non ancora distribuito"
    is_initialized = False
    if os.path.exists(addr_path):
        try:
            with open(addr_path, 'r') as f:
                data = json.load(f)
                contract_address = data.get('address', 'Indirizzo non trovato')
                is_initialized = True 
        except Exception as e:
            print(f"Errore lettura contract_address.json: {e}")

    # 3. Recupero lista utenti e ARRICCHIMENTO con dati JSON
    all_users = CustomUser.objects.all().order_by('-date_joined')
    
    for u in all_users:
        u.cv_display = "—" # Valore di default
        if u.role == 'STUDENT' and u.student_index:
            # Costruiamo il percorso: data/json/cv_inserito_s1.json, ecc.
            cv_file_path = os.path.join(settings.BASE_DIR, 'data', 'json', f'cv_inserito_s{u.student_index}.json')
            
            if os.path.exists(cv_file_path):
                try:
                    with open(cv_file_path, 'r') as f:
                        cv_json = json.load(f)
                        valore_cv = cv_json.get('CV')
                        # Mappatura basata sui tuoi file
                        if valore_cv == 1:
                            u.cv_display = "Ingegneria Informatica"
                        elif valore_cv == 2:
                            u.cv_display = "Ingegneria Elettronica"
                        else:
                            u.cv_display = f"CV ID: {valore_cv}"
                except Exception as e:
                    print(f"Errore lettura JSON per {u.username}: {e}")

    # 4. Rendering
    return render(request, 'certchain/dashboard_admin.html', {
        'user': request.user,
        'token': request.session.get('access_token', ''),
        'cpt': cpt_data,
        'is_initialized': is_initialized,
        'contract_address': contract_address,
        'users_list': all_users, # Ora gli oggetti u hanno l'attributo u.cv_display
    })
@login_required
def dashboard_entecert(request):
    if not request.user.is_certifying_authority():
        return redirect('home')

    # 1. Prendi tutti gli utenti che hanno il ruolo STUDENT dal database
    # Usiamo il campo role che hai definito nel tuo CustomUser
    db_students = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).order_by('student_index')

    base_path = os.path.join(settings.BASE_DIR, 'data', 'json')
    enriched_students = []

    for s in db_students:
        # Usiamo lo student_index del DB (es. 1, 2, 3) per trovare i file
        idx = s.student_index
        
        # Se lo studente non ha un indice, saltalo o gestiscilo
        if idx is None:
            continue

        libretto_path = os.path.join(base_path, f'Evidenze_s{idx}.json')
        dichiarazione_path = os.path.join(base_path, f'Dichiarazione_s{idx}.json')
        
        status_info = {
            'id': idx,
            'username': s.username,
            'full_name': f"{s.username.capitalize()}", # O un eventuale campo 'first_name'
            'has_declared': False,
            'is_valid': False,
            'details': "In attesa di dichiarazione"
        }

        # 2. Logica di confronto file
        if os.path.exists(dichiarazione_path) and os.path.exists(libretto_path):
            try:
                with open(libretto_path, 'r') as f1, open(dichiarazione_path, 'r') as f2:
                    libretto_val = json.load(f1).get('Evidenze', [])
                    dichiarato_val = json.load(f2).get('Evidenze', [])
                
                status_info['has_declared'] = True
                status_info['is_valid'] = (libretto_val == dichiarato_val)
                status_info['details'] = "Dati Coerenti" if status_info['is_valid'] else "ERRORE: Dati non corrispondenti"
            except Exception as e:
                status_info['details'] = f"Errore lettura: {str(e)}"
        
        enriched_students.append(status_info)

    context = {
        'students': enriched_students,
    }
    return render(request, 'certchain/dashboard_entecert.html', context)
@login_required
def dashboard_student(request):
    if not request.user.is_student():
        return redirect('home')

    # 1. Recuperiamo l'indice e i dati base dello studente
    student_id = request.user.student_index if request.user.student_index else 1
    student_name = request.user.username
    
    # 2. Recupero Indirizzo Contratto Dinamico dal JSON di Brownie
    addr_path = os.path.join(settings.BASE_DIR, 'blockchain', 'contract_address.json')
    contract_address = ""
    if os.path.exists(addr_path):
        try:
            with open(addr_path, 'r') as f:
                contract_address = json.load(f).get('address', "")
        except Exception as e:
            print(f"Errore lettura contract_address.json: {e}")

    try:
        # 3. Percorsi dei file JSON per i dati
        base_path = os.path.join(settings.BASE_DIR, 'data', 'json')
        cv_path = os.path.join(base_path, f'cv_inserito_s{student_id}.json')
        evidenze_path = os.path.join(base_path, f'Evidenze_s{student_id}.json')

        # Lettura CV
        cv_scelto = "Dati non disponibili"
        if os.path.exists(cv_path):
            with open(cv_path, 'r') as f:
                cv_data = json.load(f)
                cv_val = cv_data.get('CV', 1) 
                cv_scelto = "Percorso Informatico" if cv_val == 1 else "Percorso Elettronico"

        # Lettura evidenze (esami)
        valori_esiti = [0, 0, 0, 0]
        if os.path.exists(evidenze_path):
            with open(evidenze_path, 'r') as f:
                valori_esiti = json.load(f).get('Evidenze', [0, 0, 0, 0])
        
        nomi_esami = ["IDCERT Coding", "Corso Python", "Fondamenti Info", "Ingegneria Soft"]
        evidenze_list = list(zip(nomi_esami, valori_esiti))

        # 4. Stato Blockchain tramite Web3
        state = "IDLE"
        student_wallet = getattr(request.user, 'wallet_address', None)

        if not student_wallet:
            state = "WALLET_NOT_CONNECTED"
        else:
            contract = get_blockchain_contract() 
            if contract:
                try:
                    # Importiamo Web3 qui per evitare l'errore di "local variable"
                    from web3 import Web3
                    
                    clean_address = student_wallet.strip()
                    
                    # Usiamo il metodo più compatibile per il checksum
                    if hasattr(Web3, 'to_checksum_address'):
                        checksum_address = Web3.to_checksum_address(clean_address)
                    else:
                        # Fallback per versioni Web3.py più vecchie
                        w3_temp = Web3()
                        checksum_address = w3_temp.toChecksumAddress(clean_address)
                    
                    # Chiamata al contratto
                    raw_state = contract.functions.studentState(checksum_address).call()
                    
                    state_mapping = {
                        0: "IDLE",
                        1: "DICHIARATO",
                        2: "VALIDATO",
                        3: "CALCOLO...",
                        4: "COMPLETATO"
                    }
                    state = state_mapping.get(int(raw_state), f"SCONOSCIUTO ({raw_state})")
                    print(f"✅ Successo! Stato letto: {raw_state}")

                except Exception as e:
                    print(f"❌ ERRORE CHIAMATA CONTRATTO: {e}")
                    state = "BLOCKCHAIN_ERROR"
            else:
                state = "BLOCKCHAIN_CONNECTION_FAILED"
    except Exception as e:
        print(f"Errore critico: {e}")
        state = "ERROR"

    context = {
        'student_id': student_id,
        'student_name': student_name,
        'cv_scelto': cv_scelto,     
        'evidenze': evidenze_list,
        'state': state,
        'idcert_val': valori_esiti[0],
        'corsopy_val': valori_esiti[1],
        'fondinfo_val': valori_esiti[2],
        'ingsoft_val': valori_esiti[3],
        # Dati per MetaMask
        'contract_address': contract_address,
        'contract_abi': json.dumps(settings.BLOCKCHAIN_CONTRACT_ABI), 
    }
    
    return render(request, 'certchain/dashboard_student.html', context)
@login_required
def dashboard_company(request):
    if request.user.role != 'COMPANY':
        return redirect('home')

    studenti_db = CustomUser.objects.filter(role='STUDENT').exclude(student_index__isnull=True)
    studenti_con_dati_onchain = []

    for s in studenti_db:
        s.onchain_state = 0   
        s.onchain_prior = 0
        s.onchain_apost = 0

        try:
            # FIX 1: Cambiato network in ganache-8546
            # FIX 2: Aumentato timeout a 40 secondi
            result = subprocess.run(
                ["brownie", "run", "scripts/Role_based_txn.py", "main", "Azienda", str(s.student_index), "--network", "ganache-8546"],
                cwd="/home/otmane/SS-B-G2/blockchain",
                capture_output=True, 
                text=True,
                timeout=40 
            )

            output = result.stdout
            # DEBUG: Vediamo cosa risponde Brownie nel terminale Django
            print(f"--- DEBUG AZIENDA PER {s.username} ---")
            print(output)

            for line in output.splitlines():
                # Il parsing deve essere molto preciso
                if "A Priori" in line:
                    try:
                        # Gestisce formati tipo "A Priori: 0.75" o "A Priori (CV): 0.75"
                        val_str = line.split(":")[-1].strip()
                        s.onchain_prior = int(float(val_str) * 100)
                    except (ValueError, IndexError):
                        pass
                
                if "A Posteriori" in line:
                    try:
                        val_str = line.split(":")[-1].strip()
                        s.onchain_apost = int(float(val_str) * 100)
                    except (ValueError, IndexError):
                        pass

            # Stato basato sulla presenza di dati a posteriori
            if s.onchain_apost > 0:
                s.onchain_state = 2
            else:
                s.onchain_state = 0

        except Exception as e:
            print(f"--- Errore lettura Blockchain per {s.username}: {e} ---")
        
        studenti_con_dati_onchain.append(s)

    return render(request, 'certchain/dashboard_company.html', {
        'studenti': studenti_con_dati_onchain,
    })
@login_required
def company_view_report(request, student_id):
    if not request.user.is_company():
        return redirect('home')

    # 1. Troviamo lo studente nel DB
    studente = get_object_or_404(CustomUser, student_index=student_id)

    try:
        blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
        script_path = os.path.join(blockchain_path, 'scripts', 'Role_based_txn.py')
        
        # 2. Lanciamo Brownie con l'azione "Azienda"
        # L'azienda non ha bisogno di passare la propria chiave per la lettura pubblica
        result = subprocess.run(
            ["brownie", "run", script_path, "main", "Azienda", str(student_id), "--network", "ganache-46"],
            cwd=blockchain_path,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )

        # 3. Parsing dell'output (cerca le righe stampate dallo script)
        prior = "N/D"
        apost = "N/D"
        
        for line in result.stdout.splitlines():
            if "BasiProg (A Priori):" in line:
                prior = line.split(":")[1].strip()
            if "BasiProg (A Posteriori):" in line:
                apost = line.split(":")[1].strip()

        return render(request, 'certchain/azienda_report_detail.html', {
            'studente': studente,
            'prior': prior,
            'apost': apost,
            'raw_output': result.stdout # Utile per debug
        })

    except Exception as e:
        messages.error(request, f"Errore durante il recupero dei dati: {str(e)}")
        return redirect('dashboard_company')

@login_required
def create_user(request):
    if not request.user.is_admin():
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        email    = request.POST.get('email')
        password = request.POST.get('password')
        role     = request.POST.get('role')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" già esistente.')
        else:
            CustomUser.objects.create_user(username=username, email=email, password=password, role=role)
            messages.success(request, f'Utente "{username}" creato con ruolo {role}.')
    return redirect('dashboard_admin')
@login_required
def deploy_contract(request):
    if not request.user.is_admin():
        return redirect('home')

    if request.method == 'POST':
        try:
            blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
            current_env = os.environ.copy()

            # FIX 1: Cambiato "ganache-46" in "ganache-8546"
            # FIX 2: Aumentato il timeout a 90 secondi per sicurezza
            result = subprocess.run(
                ["brownie", "run", "scripts/Deploy.py", "--network", "ganache-8546"],
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=current_env,
                timeout=90
            )

            # Stampiamo nel terminale di Django per debug
            print("--- STDOUT DEPLOY ---")
            print(result.stdout)
            print("--- STDERR DEPLOY ---")
            print(result.stderr)

            if result.returncode == 0:
                messages.success(request, "Smart Contract deployato con successo!")
            else:
                messages.error(request, f"Errore Brownie: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            messages.error(request, "Timeout: Ganache non risponde. (La rete era ganache-8546?)")
        except Exception as e:
            messages.error(request, f"Errore di sistema: {str(e)}")

    return redirect('dashboard_admin')
@login_required
def init_bn(request):
    if not request.user.is_admin():
        return redirect('home')

    if request.method == 'POST':
        print("\n--- DEBUG: Inizio procedura Inizializzazione BN ---")
        try:
            blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
            current_env = os.environ.copy()
            
            print(f"DEBUG: Eseguo Brownie in: {blockchain_path}")
            
            # Lanciamo il processo
            result = subprocess.run(
                ["brownie", "run", "scripts/Role_based_txn.py", "main", "Admin", "--network", "ganache-8546"], # Aggiunto 'Admin' e porta 8546
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=current_env,
                timeout=180 
            )

            # Log dell'output nel terminale Django
            print("--- STDOUT BROWNIE ---")
            print(result.stdout)
            print("--- STDERR BROWNIE ---")
            print(result.stderr)

            if result.returncode == 0:
                flag_path = os.path.join(blockchain_path, 'bn_initialized.flag')
                with open(flag_path, 'w') as f:
                    f.write('initialized')
                print("DEBUG: Inizializzazione completata con successo!")
                messages.success(request, 'Rete Bayesiana e Permessi configurati!')
            else:
                # Se Brownie fallisce, mostriamo l'errore specifico nel banner rosso
                error_msg = result.stderr if result.stderr else "Errore sconosciuto durante l'esecuzione dello script."
                print(f"DEBUG: Brownie è fallito con codice {result.returncode}")
                messages.error(request, f"Errore Brownie: {error_msg}")

        except subprocess.TimeoutExpired:
            print("DEBUG: Timeout scaduto!")
            messages.error(request, "Il processo ha impiegato troppo tempo (Timeout).")
        except Exception as e:
            print(f"DEBUG: Errore di sistema: {str(e)}")
            messages.error(request, f"Errore di sistema: {str(e)}")
        
        print("--- DEBUG: Fine procedura ---\n")

    return redirect('dashboard_admin')
@login_required
def student_declare(request):
    if not request.user.is_student():
        return redirect('home')

    if request.method == 'POST':
        stud_id = request.user.student_index if request.user.student_index else 1
        
        new_evidences = [
            1 if request.POST.get('IDCERT') else 0,
            1 if request.POST.get('CorsoPy') else 0,
            1 if request.POST.get('FondInfo') else 0,
            1 if request.POST.get('IngSoft') else 0
        ]

        try:
            # 1. Salvataggio JSON locale (Unica cosa che fa Django ora)
            base_path = os.path.join(settings.BASE_DIR, 'data', 'json')
            evidenze_path = os.path.join(base_path, f'Dichiarazione_s{stud_id}.json')
            
            with open(evidenze_path, 'w') as f:
                json.dump({"Evidenze": new_evidences}, f, indent=4)
            
            # Se arriviamo qui, significa che MetaMask ha già fatto il lavoro sporco sulla blockchain!
            messages.success(request, "Dichiarazione inviata e confermata dalla Blockchain!")

        except Exception as e:
            messages.error(request, f"Errore nel salvataggio JSON: {str(e)}")

    return redirect('dashboard_student')
@login_required
def ente_action(request, student_id):
    if not request.user.is_certifying_authority():
        return redirect('home')

    if request.method == 'POST':
        try:
            blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
            
            # Prepariamo l'ambiente con le chiavi del .env
            current_env = os.environ.copy()
            
            # Lancio Brownie
            result = subprocess.run(
                ["brownie", "run", "scripts/Role_based_txn.py", "main", "EnteCert", str(student_id), "--network", "ganache-8546"],
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=current_env  # <--- Fondamentale per leggere le chiavi!
            )

            if "confirmed" in result.stdout or "Evidenze inserite" in result.stdout:
                messages.success(request, f"Validazione completata per lo Studente {student_id}!")
            else:
                messages.error(request, f"Errore: {result.stderr}")
        
        except Exception as e:
            messages.error(request, f"Errore di sistema: {str(e)}")

    return redirect('dashboard_entecert')
#METAMASK
@login_required
@require_POST
def update_wallet_address(request):
    """Riceve l'indirizzo da MetaMask e lo salva nel DB per l'utente corrente."""
    try:
        # Legge i dati inviati da JavaScript
        data = json.loads(request.body)
        wallet = data.get('wallet_address')
        
        if wallet:
            # Salva nel database
            request.user.wallet_address = wallet
            request.user.save()
            return JsonResponse({'status': 'success', 'message': 'Wallet salvato!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Nessun wallet fornito'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
def get_blockchain_contract():
    from web3 import Web3
    import os
    import json
    from django.conf import settings
    
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_NODE_URL))
    
    # 1. Test connessione
    connected = False
    try:
        connected = w3.is_connected()
    except AttributeError:
        connected = w3.isConnected()

    if not connected:
        print(f"❌ Nodo non raggiungibile su {settings.BLOCKCHAIN_NODE_URL}")
        return None

    # FIX: Leggiamo l'indirizzo dinamicamente dal JSON, non dal settings!
    addr_path = os.path.join(settings.BASE_DIR, 'blockchain', 'contract_address.json')
    addr = None
    if os.path.exists(addr_path):
        try:
            with open(addr_path, 'r') as f:
                addr = json.load(f).get('address')
        except Exception as e:
            print(f"Errore lettura JSON address: {e}")

    abi = settings.BLOCKCHAIN_CONTRACT_ABI

    if not addr or not abi:
        print("❌ Indirizzo o ABI mancante")
        return None

    try:
        if hasattr(Web3, 'to_checksum_address'):
            target_address = Web3.to_checksum_address(addr)
        else:
            target_address = w3.toChecksumAddress(addr)
            
        return w3.eth.contract(address=target_address, abi=abi)
    
    except Exception as e:
        print(f"DEBUG ERROR: Fallita creazione contratto: {e}")
        return None
def register_student(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. Calcolo student_index
        max_idx = CustomUser.objects.filter(role='STUDENT').aggregate(Max('student_index'))['student_index__max']
        new_index = (max_idx + 1) if max_idx is not None else 1

        try:
            # 2. Creazione Utente
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=CustomUser.Role.STUDENT,
                student_index=new_index
            )

            # 3. GENERAZIONE AUTOMATICA FILE JSON
            generate_student_json_files(new_index)

            return redirect('login')
        except Exception as e:
            print(f"Errore: {e}")
            
    return render(request, 'certchain/register.html')

def generate_student_json_files(student_index):
    """Genera i file JSON necessari per la Rete Bayesiana con dati standard/random."""
    
    # Percorso della cartella json (assicurati che esista!)
    json_folder = os.path.join(settings.BASE_DIR, 'data', 'json')
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # --- File 1: cv_inserito_sX.json ---
    # Scegliamo a caso tra 1 (Informatico) e 2 (Elettronico)
    import random
    tipo_cv = random.choice([1, 2])
    cv_data = {"CV": tipo_cv}
    
    cv_path = os.path.join(json_folder, f'cv_inserito_s{student_index}.json')
    with open(cv_path, 'w') as f:
        json.dump(cv_data, f, indent=4)

    # --- File 2: Evidenze_sX.json ---
    # Generiamo evidenze casuali (Superato/Non Superato)
    # 1 = Superato, 0 = Non Superato
    evidenze_data = {
        "Evidenze": [
            random.choice([0, 1]), # IDCERT Coding
            random.choice([0, 1]), # Corso Python
            random.choice([0, 1]), # Fondamenti Info
            random.choice([0, 1])  # Ingegneria Soft
        ]
    }
    
    evidenze_path = os.path.join(json_folder, f'Evidenze_s{student_index}.json')
    with open(evidenze_path, 'w') as f:
        json.dump(evidenze_data, f, indent=4)

    print(f"File generati correttamente per lo studente {student_index}")