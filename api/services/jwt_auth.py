from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTQueryParamAuthentication(JWTAuthentication):
    """
    Extends SimpleJWT authentication to support reading tokens from
    the 'token' query parameter, allowing file downloads (like PDFs)
    via window.open() to authenticate.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            # Check the query parameter for 'token'
            raw_token = request.query_params.get('token')
            if raw_token:
                if raw_token.startswith('Bearer '):
                    raw_token = raw_token.split('Bearer ')[1].strip()
                try:
                    validated_token = self.get_validated_token(raw_token)
                    return self.get_user(validated_token), validated_token
                except Exception:
                    return None
        return super().authenticate(request)

