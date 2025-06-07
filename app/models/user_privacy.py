from datetime import datetime
from bson import ObjectId
from app.extensions import privacy_vault
from app.utils.encryption import encrypt_data, decrypt_data


class UserPrivacy:
    _collection = None

    @classmethod
    def get_collection(cls):
        if cls._collection is None:
            cls._collection = privacy_vault.user_privacy
        return cls._collection

    @classmethod
    def get_privacy_data(cls, user_id):
        return cls.get_collection().find_one({"user_id": str(user_id)})

    @classmethod
    def set_privacy_data(cls, user_id, data):
        return cls.get_collection().update_one(
            {"user_id": str(user_id)}, {"$set": data}, upsert=True
        )

    def __init__(self, user_id, email, phone=None, address=None, payment_info=None):
        self.user_id = user_id
        self.email = email
        self.phone = phone
        self.address = address
        self.payment_info = payment_info
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._id = None

    @classmethod
    def create(cls, user_id, email, phone=None, address=None, payment_info=None):
        # Encrypt sensitive data before storing
        encrypted_data = {
            "user_id": str(user_id),
            "email": encrypt_data(email),
            "phone": encrypt_data(phone) if phone else None,
            "address": encrypt_data(address) if address else None,
            "payment_info": encrypt_data(payment_info) if payment_info else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = cls.get_collection().insert_one(encrypted_data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_email(cls, email):
        """Find user privacy data by email"""
        # Since email is encrypted, we need to search through all documents
        # This is not efficient for large datasets, consider adding an index
        for doc in cls.get_collection().find():
            try:
                decrypted_email = decrypt_data(doc["email"])
                if decrypted_email == email:
                    return cls._decrypt_document(doc)
            except Exception:
                continue
        return None

    @classmethod
    def get_by_user_id(cls, user_id):
        doc = cls.get_collection().find_one({"user_id": str(user_id)})
        if doc:
            return cls._decrypt_document(doc)
        return None

    @classmethod
    def get_by_id(cls, _id):
        doc = cls.get_collection().find_one({"_id": ObjectId(_id)})
        if doc:
            return cls._decrypt_document(doc)
        return None

    @classmethod
    def _decrypt_document(cls, doc):
        # Decrypt sensitive data
        decrypted = {
            "user_id": doc["user_id"],
            "email": decrypt_data(doc["email"]),
            "phone": decrypt_data(doc["phone"]) if doc.get("phone") else None,
            "address": decrypt_data(doc["address"]) if doc.get("address") else None,
            "payment_info": (
                decrypt_data(doc["payment_info"]) if doc.get("payment_info") else None
            ),
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
            "_id": doc["_id"],
        }
        return decrypted

    def update(self, **kwargs):
        update_data = {}
        for key, value in kwargs.items():
            if (
                key in ["email", "phone", "address", "payment_info"]
                and value is not None
            ):
                update_data[key] = encrypt_data(value)

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            self.get_collection().update_one(
                {"user_id": str(self.user_id)}, {"$set": update_data}
            )
            return self.get_by_user_id(self.user_id)
        return None

    def delete(self):
        return self.get_collection().delete_one({"user_id": str(self.user_id)})
