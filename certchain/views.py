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
    elif user.role == 'COMPANY': # <--- AGGIUNGI QUESTO
        return 'Company'
    else:
        return 'Student'

def _redirect_by_role(user):
    role = _get_user_role(user)
    if role == 'Admin':
        return redirect('dashboard_admin')
    elif role == 'CertifyingAuthority':
        return redirect('dashboard_authority')
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
    Dashboard principale per l'Admin: gestisce l'anteprima CPT, 
    lo stato della blockchain e la lista degli utenti di sistema.
    """
    # Sicurezza: solo l'admin può accedere
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

    # 2. Controllo Stato Blockchain e Indirizzo Contratto
    addr_path = os.path.join(settings.BASE_DIR, 'blockchain', 'contract_address.json')
    contract_address = "Non ancora distribuito"
    is_initialized = False

    if os.path.exists(addr_path):
        try:
            with open(addr_path, 'r') as f:
                data = json.load(f)
                # Recuperiamo l'indirizzo salvato dal deploy di Brownie
                contract_address = data.get('address', 'Indirizzo non trovato')
                is_initialized = True 
        except Exception as e:
            print(f"Errore lettura contract_address.json: {e}")

    # 3. Recupero lista utenti per la sezione User Management
    # Escludiamo magari lo stesso admin loggato per chiarezza
    all_users = CustomUser.objects.all().order_by('-date_joined')

    # 4. Rendering della dashboard con il contesto completo
    return render(request, 'certchain/dashboard_admin.html', {
        'user': request.user,
        'token': request.session.get('access_token', ''),
        'cpt': cpt_data,                 # Dati per l'anteprima tabelle
        'is_initialized': is_initialized, # Booleano per il tasto carica
        'contract_address': contract_address, # Indirizzo reale da mostrare nel box
        'users_list': all_users,         # Lista per visualizzare chi è già registrato
    })

@login_required
def init_bn(request):
    """
    Lancia lo script Brownie. Non servono più i float() perché i dati sono presi
    direttamente dai JSON dallo script role_based_txn.py.
    """
    if not request.user.is_admin():
        return redirect('home')

    if request.method == 'POST':
        try:
            # Percorso dello script Brownie
            script_path = os.path.join(settings.BASE_DIR, 'blockchain', 'scripts', 'role_based_txn.py')
            
            # Eseguiamo il comando esterno. 
            # NOTA: Assicurati che '--network development' (o besu) sia corretto per il tuo setup
            result = subprocess.run(
                ['brownie', 'run', script_path, 'main', '--network', 'development'], 
                capture_output=True, 
                text=True,
                cwd=os.path.join(settings.BASE_DIR, 'blockchain')
            )

            if result.returncode == 0:
                messages.success(request, 'Blockchain inizializzata con successo via Brownie!')
            else:
                # Se Brownie fallisce, riportiamo l'errore tecnico per il debug
                messages.error(request, f'Errore Brownie: {result.stderr}')
                
        except Exception as e:
            messages.error(request, f'Errore di sistema: {str(e)}')

    return redirect('dashboard_admin')
# -------------------------------------

@login_required
def dashboard_authority(request):
    if not request.user.role == 'CERTIFYING_AUTHORITY':
        return redirect('home')
    return render(request, 'certchain/dashboard_authority.html', {
        'user': request.user,
    })

@login_required
def dashboard_student(request):
    if not request.user.role == 'STUDENT':
        return redirect('home')
    return render(request, 'certchain/dashboard_student.html', {
        'user': request.user,
    })

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