# File: app/crud.py
import uuid
import datetime
from sqlalchemy.orm import Session
from app import models, schemas
from app.security import encrypt_secret, decrypt_secret
from cachetools import TTLCache
from fastapi import HTTPException

# Простой in-memory кеш
cache = TTLCache(maxsize=1000, ttl=300)  # 5 минут

def log_action(db: Session, action: str, secret_id: int = None, ip: str = None, metadata: dict = None):
    # Проверяем, активна ли сессия перед использованием
    if not db.is_active:
        # Можно попытаться восстановить сессию или просто пропустить логгирование
        print("Warning: Database session is not active during logging.")
        

    try:
        db_log = models.SecretLog(
            action=action,
            secret_id=secret_id,
            ip_address=ip,
            metadata=metadata
        )
        db.add(db_log)
        db.commit()
    except Exception as log_error:
        print(f"Error logging action {action}: {log_error}")
        db.rollback() # Откатываем изменения лога в случае ошибки


def create_secret(db: Session, secret: schemas.SecretCreate, ip: str = None):
    secret_key = str(uuid.uuid4())
    encrypted_secret = encrypt_secret(secret.secret)

    expires_at = None
    if secret.ttl_seconds:
        # Убедимся, что используем UTC для согласованности
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=secret.ttl_seconds)

    db_secret = models.Secret(
        secret_key=secret_key,
        secret=encrypted_secret,
        passphrase=secret.passphrase, 
        expires_at=expires_at
    )
    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)

    # Кеширование - кешируем объект после коммита
    cache[secret_key] = db_secret

    # Лог
    log_action(db, "create", db_secret.id, ip, {"ttl": secret.ttl_seconds})

    return {"secret_key": secret_key}

def get_secret(db: Session, secret_key: str, ip: str = None):
    secret = None
    retrieved_from_cache = False
    secret_id_for_logging = None # Для логгирования ID, даже если объект удален

    try:
        # Ищем в кеше
        cached_secret = cache.get(secret_key)

        if cached_secret:
            # Если нашли в кеше, присоединяем объект к текущей сессии
            # db.merge() возвращает объект, присоединенный к сессии
            secret = db.merge(cached_secret)
            retrieved_from_cache = True
            secret_id_for_logging = getattr(secret, 'id', None) # Сохраняем ID для лога
            # print(f"Secret {secret_key} found in cache and merged to session.")
        else:
            # Если не нашли в кеше, извлекаем из базы
            secret = db.query(models.Secret).filter(models.Secret.secret_key == secret_key).first()
            if secret:
                secret_id_for_logging = secret.id # Сохраняем ID для лога
            # print(f"Secret {secret_key} fetched from database.")


        if not secret:
            # Логируем попытку доступа к несуществующему секрету
            log_action(db, "read_attempt_failed", ip=ip, metadata={"secret_key": secret_key, "reason": "not_found"})
            # print(f"Secret {secret_key} not found.")
            return None # Возвращаем None, если секрет не найден

        try:
            # Проверяем срок действия секрета
            if secret.expires_at:
                if secret.expires_at.tzinfo is None:
                    # Преобразуем в offset-aware, если это offset-naive
                    secret.expires_at = secret.expires_at.replace(tzinfo=datetime.timezone.utc)
                if secret.expires_at < datetime.datetime.now(datetime.timezone.utc):
                    # Логируем попытку доступа к истекшему секрету
                    log_action(db, "read_attempt_failed", secret_id=secret_id_for_logging, ip=ip, metadata={"secret_key": secret_key, "reason": "expired"})
                    # print(f"Secret {secret_key} expired at {secret.expires_at}.")
                    # Удаляем истекший секрет из базы и кеша
                    try:
                        db.delete(secret)
                        db.commit()
                        cache.pop(secret_key, None) # Удаляем из кеша
                        # print(f"Expired secret {secret_key} deleted.")
                    except Exception as delete_error:
                        print(f"Error deleting expired secret {secret_key}: {delete_error}")
                        db.rollback()
                        # Логируем ошибку удаления истекшего секрета
                        log_action(db, "delete_expired_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(delete_error)})
                    return None # Возвращаем None, так как секрет истек
        except Exception as e:
            print(f"Error during expiration check for secret {secret_key}: {str(e)}")
            log_action(db, "expiration_check_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(e)})
            db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error during expiration check.")

        decrypted = None
        try:
            # Дешифруем секрет
            decrypted = decrypt_secret(secret.secret)
            # print(f"Secret {secret_key} decrypted successfully.")
        except Exception as e:
            print(f"Error decrypting secret {secret_key}: {str(e)}")
            log_action(db, "read_decrypt_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(e)})
            # Решаем, удалять ли секрет при ошибке дешифровки. Текущая логика - удалять.
            try:
                db.delete(secret)
                db.commit()
                cache.pop(secret_key, None)
                # print(f"Secret {secret_key} deleted due to decryption error.")
            except Exception as delete_error:
                 print(f"Error deleting secret {secret_key} after decryption error: {delete_error}")
                 db.rollback()
                 log_action(db, "delete_decrypt_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(delete_error)})

            raise HTTPException(status_code=500, detail="Could not decrypt secret.") # Возвращаем ошибку клиенту

      
        try:
            db.delete(secret)
            db.commit()
            cache.pop(secret_key, None)
            
        except Exception as delete_error:
            print(f"Error deleting secret {secret_key} after read: {delete_error}")
            db.rollback()
        
            log_action(db, "delete_after_read_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(delete_error)})
        
            raise HTTPException(status_code=500, detail="Internal server error during secret cleanup.")


        # Логируем успешное чтение
        log_action(db, "read_success", secret_id=secret_id_for_logging, ip=ip)

        return {"secret": decrypted}

    except HTTPException as http_exc:
        
        raise http_exc
    except Exception as e:
        
        print(f"Unexpected error in get_secret for key {secret_key}: {str(e)}")
        log_action(db, "get_secret_unexpected_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(e), "secret_key": secret_key})
        db.rollback() 
        raise HTTPException(status_code=500, detail="Internal server error during secret retrieval.")


def delete_secret(db: Session, secret_key: str, passphrase: str = None, ip: str = None):
    
    secret = db.query(models.Secret).filter(models.Secret.secret_key == secret_key).first()
    secret_id_for_logging = getattr(secret, 'id', None) if secret else None

    if not secret:
        log_action(db, "delete_attempt_failed", ip=ip, metadata={"secret_key": secret_key, "reason": "not_found"})
        return None 


    if secret.passphrase:
       
        if secret.passphrase != passphrase: 
            log_action(db, "delete_attempt_failed", secret_id=secret_id_for_logging, ip=ip, metadata={"secret_key": secret_key, "reason": "invalid_passphrase"})
            # Можно вернуть ошибку авторизации
            raise HTTPException(status_code=403, detail="Invalid passphrase")
          
    try:
        db.delete(secret)
        db.commit()
        cache.pop(secret_key, None) # Удаляем из кеша на всякий случай
        log_action(db, "delete_success", secret_id=secret_id_for_logging, ip=ip, metadata={"passphrase_used": bool(passphrase)})
        return {"status": "secret_deleted"}
    except Exception as e:
        print(f"Error deleting secret {secret_key}: {e}")
        db.rollback()
        log_action(db, "delete_error", secret_id=secret_id_for_logging, ip=ip, metadata={"error": str(e)})
        raise HTTPException(status_code=500, detail="Internal server error during secret deletion.")

