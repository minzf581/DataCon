from google.cloud import firestore
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

class FirestoreManager:
    def __init__(self):
        self.project_id = settings.FIRESTORE_PROJECT_ID
        self.collection_prefix = settings.FIRESTORE_COLLECTION_PREFIX
        self._init_firebase()
        self.db = firestore.Client(project=self.project_id)

    def _init_firebase(self):
        """初始化 Firebase Admin SDK"""
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            })

    def get_collection_name(self, name):
        """获取带前缀的集合名称"""
        return f"{self.collection_prefix}_{name}"

    async def create_document(self, collection_name, data, doc_id=None):
        """创建文档"""
        collection = self.db.collection(self.get_collection_name(collection_name))
        if doc_id:
            doc_ref = collection.document(doc_id)
            await doc_ref.set(data)
            return doc_id
        else:
            doc_ref = await collection.add(data)
            return doc_ref.id

    async def get_document(self, collection_name, doc_id):
        """获取文档"""
        doc_ref = self.db.collection(self.get_collection_name(collection_name)).document(doc_id)
        doc = await doc_ref.get()
        return doc.to_dict() if doc.exists else None

    async def update_document(self, collection_name, doc_id, data):
        """更新文档"""
        doc_ref = self.db.collection(self.get_collection_name(collection_name)).document(doc_id)
        await doc_ref.update(data)

    async def delete_document(self, collection_name, doc_id):
        """删除文档"""
        doc_ref = self.db.collection(self.get_collection_name(collection_name)).document(doc_id)
        await doc_ref.delete()

    async def query_documents(self, collection_name, filters=None, order_by=None, limit=None):
        """查询文档"""
        collection = self.db.collection(self.get_collection_name(collection_name))
        query = collection

        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)

        if order_by:
            for field, direction in order_by:
                query = query.order_by(field, direction=direction)

        if limit:
            query = query.limit(limit)

        docs = await query.get()
        return [doc.to_dict() for doc in docs]

# 创建全局实例
firestore_manager = FirestoreManager() 