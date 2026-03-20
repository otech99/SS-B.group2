from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPToken


# ── Helper ────────────────────────────────────────────────────

def _get_user_role(user):
    if user.role == 'ADMIN':
        return 'Admin'
    elif user.role == 'CERTIFYING_AUTHORITY':
        return 'CertifyingAuthority'
    else:
        return 'Student'

def _redirect_by_role(user):
    role = _get_user_role(user)
    if role == 'Admin':
        return redirect('dashboard_admin')
    elif role == 'CertifyingAuthority':
        return redirect('dashboard_authority')
    else:
        return redirect('dashboard_student')
# ── Views ─────────────────────────────────────────────────────

def home(request):
    """Pagina iniziale pubblica."""
    return render(request, 'certchain/index.html')


def login_view(request):
    """Step 1 — verifica username e password, invia OTP via email."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Genera OTP
            token_value = OTPToken.generate_token()
            OTPToken.objects.create(user=user, token=token_value)

            # Salva username in sessione per lo step 2
            request.session['otp_user_id'] = user.id

            # Invia email con OTP
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
    """Step 2 — verifica il codice OTP ricevuto via email."""
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
                # Marca il token come usato
                otp.is_used = True
                otp.save()

                # Login completo
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                # Genera JWT e salva in sessione
                refresh = RefreshToken.for_user(user)
                request.session['access_token']  = str(refresh.access_token)
                request.session['refresh_token'] = str(refresh)
                request.session['user_role']      = _get_user_role(user)

                # Pulisci otp_user_id dalla sessione
                del request.session['otp_user_id']

                return _redirect_by_role(user)
            else:
                error = 'Codice scaduto o già utilizzato.'

        except (User.DoesNotExist, OTPToken.DoesNotExist):
            error = 'Codice non valido.'

    return render(request, 'certchain/verify_otp.html', {'error': error})


def logout_view(request):
    """Logout — invalida sessione."""
    logout(request)
    request.session.flush()
    return redirect('home')


@login_required
def dashboard(request):
    return _redirect_by_role(request.user)


@login_required
def dashboard_admin(request):
    if not request.user.is_admin():
        return redirect('home')
    return render(request, 'certchain/dashboard_admin.html', {
        'user': request.user,
        'token': request.session.get('access_token', ''),
    })


@login_required
def dashboard_authority(request):
    if not request.user.groups.filter(name='CertifyingAuthority').exists():
        return redirect('home')
    return render(request, 'certchain/dashboard_authority.html', {
        'user': request.user,
        'token': request.session.get('access_token', ''),
    })


@login_required
def dashboard_student(request):
    if not request.user.groups.filter(name='Student').exists():
        return redirect('home')
    return render(request, 'certchain/dashboard_student.html', {
        'user': request.user,
        'token': request.session.get('access_token', ''),
    })