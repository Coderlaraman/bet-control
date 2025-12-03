"""
Script de verificación manual de autenticación
"""

import requests
import json

BASE_URL = "http://localhost:8075"

def test_admin_login():
    """Probar login con usuario admin"""
    print("\n" + "="*60)
    print("🔐 Probando login con usuario ADMIN")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "Admin123!"
        }
    )
    
    if response.status_code == 200:
        print("✅ Login exitoso!")
        data = response.json()
        print(f"   Access Token: {data['access_token'][:50]}...")
        print(f"   Token Type: {data['token_type']}")
        print(f"   Expires In: {data['expires_in']} seconds")
        return data['access_token']
    else:
        print(f"❌ Login fallido: {response.status_code}")
        print(f"   Error: {response.json()}")
        return None


def test_user_login():
    """Probar login con usuario normal"""
    print("\n" + "="*60)
    print("🔐 Probando login con usuario NORMAL")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": "usuario",
            "password": "Usuario123!"
        }
    )
    
    if response.status_code == 200:
        print("✅ Login exitoso!")
        data = response.json()
        print(f"   Access Token: {data['access_token'][:50]}...")
        print(f"   Token Type: {data['token_type']}")
        print(f"   Expires In: {data['expires_in']} seconds")
        return data['access_token']
    else:
        print(f"❌ Login fallido: {response.status_code}")
        print(f"   Error: {response.json()}")
        return None


def test_failed_login_attempts():
    """Probar límite de intentos fallidos"""
    print("\n" + "="*60)
    print("🚫 Probando límite de intentos fallidos")
    print("="*60)
    
    # Crear usuario temporal para esta prueba
    requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "testlimit",
            "email": "testlimit@example.com",
            "password": "TestLimit123!",
            "full_name": "Test Limit"
        }
    )
    
    # Intentar login con contraseña incorrecta múltiples veces
    for i in range(6):
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={
                "username": "testlimit",
                "password": "WrongPassword123!"
            }
        )
        
        print(f"   Intento {i+1}: Status {response.status_code}")
        
        if response.status_code == 423:
            print(f"   ✅ Cuenta bloqueada después de {i+1} intentos fallidos")
            print(f"   Mensaje: {response.json()['detail']}")
            break
    else:
        print("   ❌ La cuenta no se bloqueó después de múltiples intentos")


def test_password_change(token):
    """Probar cambio de contraseña"""
    print("\n" + "="*60)
    print("🔑 Probando cambio de contraseña")
    print("="*60)
    
    # Crear usuario temporal
    reg_response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "testchange",
            "email": "testchange@example.com",
            "password": "OldPass123!",
            "full_name": "Test Change"
        }
    )
    
    # Login para obtener token
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": "testchange",
            "password": "OldPass123!"
        }
    )
    
    if login_response.status_code == 200:
        user_token = login_response.json()['access_token']
        
        # Cambiar contraseña
        change_response = requests.post(
            f"{BASE_URL}/api/v1/auth/change-password",
            json={
                "old_password": "OldPass123!",
                "new_password": "NewPass123!"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if change_response.status_code == 200:
            print("   ✅ Contraseña cambiada exitosamente")
            
            # Verificar que la nueva contraseña funciona
            new_login = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                data={
                    "username": "testchange",
                    "password": "NewPass123!"
                }
            )
            
            if new_login.status_code == 200:
                print("   ✅ Login con nueva contraseña exitoso")
            else:
                print("   ❌ Login con nueva contraseña falló")
        else:
            print(f"   ❌ Cambio de contraseña falló: {change_response.json()}")


def test_weak_password_registration():
    """Probar registro con contraseña débil"""
    print("\n" + "="*60)
    print("🔒 Probando validación de contraseña débil")
    print("="*60)
    
    weak_passwords = [
        ("short", "Muy corta"),
        ("lowercase123!", "Sin mayúsculas"),
        ("UPPERCASE123!", "Sin minúsculas"),
        ("NoNumbers!", "Sin números"),
        ("NoSpecial123", "Sin caracteres especiales")
    ]
    
    for password, description in weak_passwords:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": f"test_{password}",
                "email": f"test_{password}@example.com",
                "password": password,
                "full_name": "Test User"
            }
        )
        
        if response.status_code == 422:
            print(f"   ✅ {description}: Rechazada correctamente")
        else:
            print(f"   ❌ {description}: No fue rechazada (status: {response.status_code})")


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("🧪 VERIFICACIÓN MANUAL DE AUTENTICACIÓN MEJORADA")
    print("="*60)
    print("\nAsegúrese de que el servidor esté corriendo en http://localhost:8075")
    input("\nPresione Enter para continuar...")
    
    try:
        # Probar logins
        admin_token = test_admin_login()
        user_token = test_user_login()
        
        # Probar validación de contraseñas débiles
        test_weak_password_registration()
        
        # Probar límite de intentos
        test_failed_login_attempts()
        
        # Probar cambio de contraseña
        if admin_token:
            test_password_change(admin_token)
        
        print("\n" + "="*60)
        print("✅ VERIFICACIÓN COMPLETADA")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Asegúrese de que el servidor esté corriendo en http://localhost:8075")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


if __name__ == "__main__":
    main()
