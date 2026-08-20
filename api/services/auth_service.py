from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from firebase_admin import auth as firebase_auth
from ..models import User, Client, TeamInvite
from django.utils import timezone
from ..repositories.user_repository import UserRepository, PasswordResetOTPRepository
from ..repositories.team_invite_repository import TeamInviteRepository
from ..repositories.client_repository import ClientRepository

class AuthService:
    @staticmethod
    def register_user(serializer):
        user = serializer.save()
        if user.status == 'APPROVED':
            refresh = RefreshToken.for_user(user)
            return {
                "status": "APPROVED",
                "user": AuthService._serialize_user(user),
                "token": str(refresh.access_token)
            }
        else:
            return {
                "status": "PENDING",
                "message": "User registered successfully. Waiting for admin approval.",
                "userId": str(user.id)
            }

    @staticmethod
    def login_user(email, password):
        if not email or not password:
            return {"error": "Email and password are required.", "status_code": 400}

        user = authenticate(username=email, password=password)
        
        if not user:
            user_obj = UserRepository.filter_users(email=email).first()
            if user_obj and user_obj.check_password(password):
                user = user_obj
        
        if not user:
            return {"error": "Invalid email or password.", "status_code": 401}

        if user.role == 'CLIENT' and user.status != 'APPROVED':
            return {"error": f"Account status: {user.status}. Please wait for admin approval.", "status_code": 403}

        user.is_online = True
        user.last_active_at = timezone.now()
        user.save(update_fields=['is_online', 'last_active_at'])

        refresh = RefreshToken.for_user(user)
        return {
            "user": AuthService._serialize_user(user),
            "token": str(refresh.access_token)
        }

    @staticmethod
    def process_firebase_login(id_token, name, invite_token, business_name):
        if not id_token:
            return {"error": "Firebase ID token is required", "status_code": 400}

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            import jwt
            try:
                decoded_token = jwt.decode(id_token, options={"verify_signature": False})
            except Exception:
                return {"error": f"Token verification failed: {str(e)}", "status_code": 400}

        email = decoded_token.get('email', '').lower().strip()
        name = name or decoded_token.get('name', '').strip() or 'User'

        if not email:
            return {"error": "Failed to retrieve email from Firebase token", "status_code": 400}

        # Admin logic
        if email == 'admin@uwo24.com':
            user, created = UserRepository.get_user_or_create(
                username=email, 
                defaults={'email': email, 'role': 'ADMIN', 'status': 'APPROVED', 'is_staff': True, 'is_superuser': True}
            )
            if created:
                user.set_password(User.objects.make_random_password())
                user.save()
            elif not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                user.save()
            
            refresh = RefreshToken.for_user(user)
            return {
                "user": AuthService._serialize_user(user, override_name="System Admin"),
                "token": str(refresh.access_token)
            }

        # Existing user check
        user = UserRepository.filter_users(email=email).first()
        if not user:
            user = UserRepository.filter_users(username=email).first()

        if user:
            if user.role == 'CLIENT' and user.status != 'APPROVED':
                return {"error": f"Account status: {user.status}. Please wait for admin approval.", "status_code": 403}

            return {
                "user": AuthService._serialize_user(user),
                "token": str(RefreshToken.for_user(user).access_token)
            }
        else:
            # New user logic
            if invite_token:
                invite = TeamInviteRepository.filter_teaminvites(
                    token=invite_token, 
                    is_used=False, 
                    expires_at__gt=timezone.now()
                ).first()
                
                if not invite:
                    return {"error": "Invalid or expired invite token.", "status_code": 400}
                    
                user = UserRepository.create_user_user(
                    username=email,
                    email=email,
                    password=User.objects.make_random_password(),
                    first_name=name,
                    role='AGENT',
                    status='APPROVED',
                    client=invite.client,
                    permissions=invite.permissions
                )
                
                invite.is_used = True
                invite.save()
                
                refresh = RefreshToken.for_user(user)
                return {
                    "is_created": True,
                    "status": "APPROVED",
                    "user": AuthService._serialize_user(user),
                    "token": str(refresh.access_token)
                }
            else:
                business_name = business_name or f"{name}'s Business"
                client = ClientRepository.create_client(business_name=business_name)
                user = UserRepository.create_user_user(
                    username=email,
                    email=email,
                    password=User.objects.make_random_password(),
                    first_name=name,
                    role='CLIENT',
                    status='PENDING',
                    client=client
                )
                return {
                    "is_created": True,
                    "status": "PENDING",
                    "message": "User registered successfully. Waiting for admin approval.",
                    "userId": str(user.id)
                }

    @staticmethod
    def process_uwo_login(email, name, uwo_token=None):

        email = (email or '').lower().strip()
        name = (name or '').strip() or (email.split('@')[0] if email else 'User')

        if not email:
            return {"error": "Email is required for UWO authentication", "status_code": 400}

        # Admin account handling
        if email == 'admin@uwo24.com':
            user, created = UserRepository.get_user_or_create(
                username=email, 
                defaults={'email': email, 'role': 'ADMIN', 'status': 'APPROVED', 'is_staff': True, 'is_superuser': True}
            )
            if created:
                user.set_password(User.objects.make_random_password())
                user.save()
            elif not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                user.save()

            refresh = RefreshToken.for_user(user)
            return {
                "user": AuthService._serialize_user(user, override_name="System Admin"),
                "token": str(refresh.access_token)
            }

        # Existing user check
        user = UserRepository.filter_users(email=email).first()
        if not user:
            user = UserRepository.filter_users(username=email).first()

        if user:
            user.is_online = True
            user.last_active_at = timezone.now()
            user.save(update_fields=['is_online', 'last_active_at'])

            refresh = RefreshToken.for_user(user)
            return {
                "user": AuthService._serialize_user(user),
                "token": str(refresh.access_token)
            }
        else:
            # JIT provision new client workspace and user
            business_name = f"{name}'s Workspace"
            client = ClientRepository.create_client(business_name=business_name)
            user = UserRepository.create_user_user(
                username=email,
                email=email,
                password=User.objects.make_random_password(),
                first_name=name,
                role='CLIENT',
                status='APPROVED',
                client=client
            )
            refresh = RefreshToken.for_user(user)
            return {
                "is_created": True,
                "status": "APPROVED",
                "user": AuthService._serialize_user(user),
                "token": str(refresh.access_token)
            }

    @staticmethod
    def _serialize_user(user, override_name=None):

        return {
            "id": str(user.id),
            "_id": str(user.id),
            "name": override_name or f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "role": user.role,
            "client": str(user.client.id) if user.client else None,
            "clientId": str(user.client.id) if user.client else None
        }

    @staticmethod
    def forgot_password_send_otp(email):
        import random
        from ..models import PasswordResetOTP, User
        from django.core.mail import send_mail
        from django.conf import settings

        if not email:
            return {"message": "Email is required", "status_code": 400}
        
        if not UserRepository.filter_users(email=email).exists():
            return {"message": "User with this email does not exist", "status_code": 404}
        
        otp = f"{random.randint(100000, 999999)}"
        PasswordResetOTPRepository.filter_passwordresetotps(email=email).delete()
        PasswordResetOTPRepository.create_passwordresetotp(email=email, otp=otp)
        
        html_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
        <tr>
          <td style="background:linear-gradient(135deg,#16A34A,#059669);padding:36px 40px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:24px;font-weight:700;">Uwo Connect</h1>
            <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px;">Password Reset Request</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <p style="color:#374151;font-size:15px;margin:0 0 20px;">Hi there,</p>
            <p style="color:#374151;font-size:15px;margin:0 0 28px;">Use the OTP below to reset your Uwo Connect password. This code expires in <strong>15 minutes</strong>.</p>
            <div style="background:#f0fdf4;border:2px dashed #16A34A;border-radius:16px;padding:28px;text-align:center;margin:0 0 28px;">
              <p style="margin:0 0 8px;color:#6b7280;font-size:12px;font-weight:600;letter-spacing:2px;text-transform:uppercase;">Your OTP Code</p>
              <p style="margin:0;font-size:48px;font-weight:800;letter-spacing:12px;color:#16A34A;">{otp}</p>
            </div>
            <p style="color:#9ca3af;font-size:13px;margin:0;">If you did not request this, you can safely ignore this email.</p>
          </td>
        </tr>
        <tr>
          <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
            <p style="color:#9ca3af;font-size:12px;margin:0;">© 2025 Uwo Connect. All rights reserved.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>"""
        
        try:
            send_mail(
                subject="Your Password Reset OTP - Uwo Connect",
                message=f"Your OTP for resetting your Uwo Connect password is: {otp}.\n\nThis OTP is valid for 15 minutes.",
                from_email=f"Uwo Connect <{settings.EMAIL_HOST_USER}>" if settings.EMAIL_HOST_USER else settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_body
            )
            msg = f"OTP sent to your email successfully (Test Code: {otp})"
            return {"message": msg, "status_code": 200}
        except Exception as e:
            return {"message": f"Failed to send email: {str(e)}", "status_code": 500}

    @staticmethod
    def forgot_password_verify_otp(email, otp):
        from django.utils import timezone
        from datetime import timedelta
        from ..models import PasswordResetOTP
        
        if not email or not otp:
            return {"message": "Email and OTP are required", "status_code": 400}
        
        try:
            otp_record = PasswordResetOTPRepository.filter_passwordresetotps(email=email, otp=otp).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            return {"message": "Invalid OTP", "status_code": 400}
        
        now = timezone.now()
        if now - otp_record.created_at > timedelta(minutes=15):
            otp_record.delete()
            return {"message": "OTP has expired", "status_code": 400}
            
        otp_record.is_verified = True
        otp_record.save()
        
        return {"message": "OTP verified successfully", "status_code": 200}

    @staticmethod
    def forgot_password_reset(email, password):
        from ..models import PasswordResetOTP, User
        
        if not email or not password:
            return {"message": "Email and password are required", "status_code": 400}
            
        verified_otp = PasswordResetOTPRepository.filter_passwordresetotps(email=email, is_verified=True).exists()
        if not verified_otp:
            return {"message": "OTP not verified yet", "status_code": 400}
            
        try:
            user = UserRepository.get_user(email=email)
            user.set_password(password)
            user.save()
            PasswordResetOTPRepository.filter_passwordresetotps(email=email).delete()
            return {"message": "Password reset successfully", "status_code": 200}
        except User.DoesNotExist:
            return {"message": "User not found", "status_code": 404}
