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

    # 1. Recuperiamo l'indice dello studente (es. 1, 2 o 3)
    student_id = request.user.student_index if request.user.student_index else 1
    
    try:
        # 2. Percorsi dei file JSON
        base_path = os.path.join(settings.BASE_DIR, 'data', 'json')
        cv_path = os.path.join(base_path, f'cv_inserito_s{student_id}.json')
        evidenze_path = os.path.join(base_path, f'Dichiarazione_s{student_id}.json')

        # 3. Lettura del CV scelto (Informatica = 1, Elettronica = 2)
        with open(cv_path, 'r') as f:
            cv_data = json.load(f)
            # Definiamo la variabile che mancava
            cv_val = cv_data.get('CV', 1) 
            cv_scelto = "Percorso Informatico" if cv_val == 1 else "Percorso Elettronico"

        # 4. Lettura delle evidenze (esami)
        with open(evidenze_path, 'r') as f:
            evidenze_data = json.load(f)
            # Creiamo una lista di tuple (NomeEsame, Esito) per il template
            nomi_esami = ["IDCERT Coding", "Corso Python", "Fondamenti Info", "Ingegneria Soft"]
            valori_esiti = evidenze_data.get('Evidenze', [0, 0, 0, 0])
            evidenze_list = zip(nomi_esami, valori_esiti)

        # 5. Stato (Per ora lo mettiamo fisso, poi lo leggeremo dalla Blockchain)
        state = "IDLE" 

    except Exception as e:
        print(f"Errore nel caricamento dati studente: {e}")
        cv_scelto = "Dati non disponibili"
        evidenze_list = []
        state = "ERROR"

    context = {
        'student_id': student_id,
        'cv_scelto': cv_scelto,      # <-- Ora è definita!
        'evidenze': evidenze_list,
        'state': state,
    }
    
    return render(request, 'certchain/dashboard_student.html', context)
@login_required
def dashboard_company(request):
    # Controlla se l'utente ha il ruolo corretto (adattalo al tuo modello CustomUser)
    if request.user.role != 'COMPANY': 
        return redirect('home')
        
    return render(request, 'certchain/dashboard_company.html', {
        'user': request.user,
    })

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
            # Usiamo l'ambiente corrente per passare le API Key e le Private Key
            current_env = os.environ.copy()

            # Indentazione corretta: 12 spazi (o 3 tab) dal margine sinistro
            result = subprocess.run(
                ["brownie", "run", "scripts/Deploy.py", "--network", "ganache-local"],
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=current_env,
                timeout=60
            )

            if result.returncode == 0:
                messages.success(request, "Smart Contract deployato con successo!")
            else:
                messages.error(request, f"Errore Brownie: {result.stderr}")
        except subprocess.TimeoutExpired:
            messages.error(request, "Timeout: Ganache non risponde.")
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
                ["brownie", "run", "scripts/Role_based_txn.py", "main", "--network", "ganache-local"],
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=current_env,
                timeout=180 # Aumentiamo a 3 min perché le TX sono tante
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
            base_path = os.path.join(settings.BASE_DIR, 'data', 'json')
            # CORRETTO: Aggiunto underscore per coerenza con la dashboard Ente
            evidenze_path = os.path.join(base_path, f'Dichiarazione_s{stud_id}.json')
            
            with open(evidenze_path, 'w') as f:
                json.dump({"Evidenze": new_evidences}, f, indent=4)
            
            blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
            script_path = os.path.join(blockchain_path, 'scripts', 'Role_based_txn.py')
            
            # CORRETTO: Aggiunto "main" prima di "Studente"
            result = subprocess.run(
                ["brownie", "run", script_path, "main", "Studente", str(stud_id), "--network", "ganache-local"],
                cwd=blockchain_path, capture_output=True, text=True, env=os.environ.copy()
            )

            if "confirmed" in result.stdout:
                messages.success(request, "Dichiarazione inviata con successo alla Blockchain!")
            else:
                messages.warning(request, "Dichiarazione salvata, ma verifica lo stato on-chain.")

        except Exception as e:
            messages.error(request, f"Errore: {str(e)}")

    return redirect('dashboard_student')
@login_required
def ente_action(request, student_id):
    if not request.user.is_certifying_authority():
        return redirect('home')

    if request.method == 'POST':
        try:
            blockchain_path = os.path.join(settings.BASE_DIR, 'blockchain')
            script_path = os.path.join(blockchain_path, 'scripts', 'Role_based_txn.py')
            
            # Lancio Brownie: Assicurati che l'ordine sia main -> EnteCert -> ID
            result = subprocess.run(
                ["brownie", "run", script_path, "main", "EnteCert", str(student_id), "--network", "ganache-local"],
                cwd=blockchain_path,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )

            if "confirmed" in result.stdout or "Evidenze inserite" in result.stdout:
                messages.success(request, f"Validazione e Calcolo completati per lo Studente {student_id}!")
            else:
                # DEBUG: Stampiamo l'errore nel terminale per capire se è un Revert
                print(f"BROWNIE ERROR: {result.stderr}")
                messages.error(request, f"Errore Blockchain: {result.stderr if result.stderr else 'Transazione fallita'}")
        
        except Exception as e:
            messages.error(request, f"Errore di sistema: {str(e)}")

    return redirect('dashboard_entecert')